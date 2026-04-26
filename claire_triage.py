"""
CLAIRE — Build 2: Triage Layer
Input:   data/raw_posts.json
Output:  data/tagged_posts.json
         data/synthesis_queue_track_a.json  (claude_native, non-developer, MEDIUM+)
         data/synthesis_queue_track_b.json  (competitor_gap, non-developer, MEDIUM+)
         data/synthesis_queue_track_c.json  (cross_platform_workflow, MEDIUM+)
         data/archive.json                  (LOW confidence items)

Run:     python claire_triage.py
         python claire_triage.py --dry-run   (classify only, skip gate routing)
         python claire_triage.py --batch-size 10  (override default batch size)
"""

import json
import sys
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from claire_utils import compute_cost, append_cost_log

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR    = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

RAW_POSTS_PATH      = DATA_DIR / "raw_posts.json"
TAGGED_POSTS_PATH   = DATA_DIR / "tagged_posts.json"
ARCHIVE_PATH        = DATA_DIR / "archive.json"
TRIAGE_LOG_PATH     = LOGS_DIR / "triage.log"
TRIAGE_PROMPT_PATH  = PROMPTS_DIR / "triage_prompt.txt"
FRICTION_LOG_PATH   = DATA_DIR / "friction_log.txt"

SYNTHESIS_QUEUE_PATHS = {
    "track_a": DATA_DIR / "synthesis_queue_track_a.json",
    "track_b": DATA_DIR / "synthesis_queue_track_b.json",
    "track_c": DATA_DIR / "synthesis_queue_track_c.json",
}

with open(BASE_DIR / "config.json") as f:
    CONFIG = json.load(f)

TRIAGE_MODEL        = CONFIG["triage"]["model"]
BATCH_SIZE          = CONFIG["triage"]["batch_size"]
DEVELOPER_ACTION    = CONFIG["cross_reference_gate"]["developer_persona_action"]
CONFIDENCE_ROUTING  = CONFIG["cross_reference_gate"]["confidence_routing"]

triage_usage = {"input_tokens": 0, "output_tokens": 0, "batches": 0}

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(TRIAGE_LOG_PATH, encoding="utf-8"),
    ]
)
log = logging.getLogger("claire.triage")

# ─────────────────────────────────────────────────────────────────────────────
# FRICTION LOG LOADER
# ─────────────────────────────────────────────────────────────────────────────

def load_friction_log() -> str:
    """Load friction log content for cross-reference gate scoring."""
    if not FRICTION_LOG_PATH.exists():
        log.warning("friction_log.txt not found — all signals will score MEDIUM")
        return ""
    with open(FRICTION_LOG_PATH, encoding="utf-8") as f:
        content = f.read().strip()
    # Strip comment lines for cleaner matching
    lines = [l for l in content.splitlines()
             if l.strip() and not l.strip().startswith("#")]
    return "\n".join(lines)


def score_against_friction_log(triage_result: dict, friction_log: str) -> str:
    """
    Score a classified post against the friction log.
    Returns: HIGH | MEDIUM | LOW | IGNORE

    Logic:
    - drop_flag=True → IGNORE
    - developer persona + filter_out action → IGNORE
    - signal_type=noise → IGNORE
    - friction log empty → MEDIUM for all non-ignored
    - keyword match between post signal and friction log → HIGH
    - no match → MEDIUM
    """
    # Hard drops
    if triage_result.get("drop_flag"):
        return "IGNORE"

    if triage_result.get("signal_type") == "noise":
        return "IGNORE"

    if (DEVELOPER_ACTION == "filter_out"
            and triage_result.get("persona") == "developer"):
        return "IGNORE"

    # No friction log — everything is MEDIUM
    if not friction_log:
        return "MEDIUM"

    # Keyword matching: extract meaningful words from classifier_note
    # and signal_type, check against friction log entries
    signal_text = " ".join([
        triage_result.get("signal_type", ""),
        triage_result.get("classifier_note", ""),
    ]).lower()

    friction_lower = friction_log.lower()

    # High-signal keywords that bridge triage tags to friction log language
    SIGNAL_KEYWORD_MAP = CONFIG["cross_reference_gate"]["signal_keyword_map"]

    signal_type = triage_result.get("signal_type", "")
    keywords = SIGNAL_KEYWORD_MAP.get(signal_type, [])

    for keyword in keywords:
        if keyword in friction_lower:
            log.debug(f"Friction match: '{keyword}' in friction log")
            return "HIGH"

    return "MEDIUM"


# ─────────────────────────────────────────────────────────────────────────────
# TRIAGE PROMPT
# ─────────────────────────────────────────────────────────────────────────────

def load_triage_prompt() -> str:
    with open(TRIAGE_PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


def build_batch_payload(posts: list) -> str:
    """Serialize a batch of posts for the triage prompt user message."""
    batch = []
    for post in posts:
        batch.append({
            "post_id":    post["post_id"],
            "subreddit":  post["subreddit"],
            "title":      post["title"],
            "body":       post["body"][:500],   # cap for token efficiency
            "score":      post["score"],
            "comment_count": post["comment_count"],
            "top_comments": [
                c["body"][:200] for c in post.get("comments", [])[:5]
            ],
        })
    return json.dumps(batch, ensure_ascii=False, separators=(',', ':'))


# ─────────────────────────────────────────────────────────────────────────────
# HAIKU CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def classify_batch(client: anthropic.Anthropic,
                   posts: list,
                   system_prompt: str) -> list:
    """
    Send a batch of posts to Haiku for classification.
    Returns list of triage result dicts.
    """
    user_message = (
        f"Classify the following {len(posts)} posts.\n\n"
        f"{build_batch_payload(posts)}"
    )

    raw = ""
    try:
        response = client.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()
        triage_usage["input_tokens"]  += response.usage.input_tokens
        triage_usage["output_tokens"] += response.usage.output_tokens
        triage_usage["batches"]       += 1

        # Strip markdown fences if model added them despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        results = json.loads(raw)
        return results

    except json.JSONDecodeError as e:
        log.error(f"JSON parse error in Haiku response: {e}")
        log.error(f"Raw response: {raw[:500]}")
        return []
    except anthropic.APIError as e:
        log.error(f"Anthropic API error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-REFERENCE GATE ROUTING
# ─────────────────────────────────────────────────────────────────────────────

def route_post(post: dict, triage: dict, confidence: str) -> str:
    """
    Determine synthesis track for a post based on triage + confidence.
    Returns: track_a | track_b | track_c | archive | discard
    """
    destination = CONFIDENCE_ROUTING.get(confidence, "discard")

    if destination == "discard":
        return "discard"

    if destination == "archive":
        return "archive"

    # Route to synthesis track based on source
    source = triage.get("source", "")
    if source == "claude_native":
        return "track_a"
    elif source == "competitor_gap":
        return "track_b"
    elif source == "cross_platform_workflow":
        return "track_c"
    else:
        return "archive"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLAIRE triage layer")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Classify posts but skip routing and file writes")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Posts per Haiku call (default: {BATCH_SIZE})")
    args = parser.parse_args()

    run_start = datetime.now(timezone.utc)
    log.info(f"CLAIRE triage started — dry_run={args.dry_run}")

    # Load raw posts
    if not RAW_POSTS_PATH.exists():
        log.error("raw_posts.json not found — run claire_ingest.py first.")
        sys.exit(1)

    try:
        with open(RAW_POSTS_PATH, encoding="utf-8") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        log.error("raw_posts.json not found — run claire_ingest.py first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log.error(
            f"raw_posts.json is corrupt and cannot be parsed: {e}. "
            "Delete or repair data/raw_posts.json and re-run claire_ingest.py."
        )
        sys.exit(1)

    posts = raw_data.get("posts", [])
    log.info(f"Loaded {len(posts)} posts from raw_posts.json")

    # Load already-tagged posts for deduplication
    tagged_cache = {}
    if TAGGED_POSTS_PATH.exists():
        with open(TAGGED_POSTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        for p in existing.get("posts", []):
            if p.get("triage"):
                tagged_cache[p["post_id"]] = p
        log.info(f"Loaded {len(tagged_cache)} already-tagged posts from cache")

    # Filter to untagged posts only
    untagged = [p for p in posts if p["post_id"] not in tagged_cache]
    log.info(f"{len(untagged)} posts need triage")

    if not untagged:
        log.info("All posts already tagged. Nothing to do.")
        return

    # Load supporting resources
    system_prompt = load_triage_prompt()
    friction_log  = load_friction_log()
    log.info(f"Friction log loaded: {len(friction_log)} chars")

    # Initialize Anthropic client
    client = anthropic.Anthropic()

    # ── Classification pass ──────────────────────────────────────────────────
    tagged_posts  = dict(tagged_cache)  # start with existing tagged
    triage_stats  = {
        "total":      len(untagged),
        "classified": 0,
        "failed":     0,
        "by_signal":  {},
        "by_persona": {},
        "by_source":  {},
    }

    batches = [
        untagged[i:i + args.batch_size]
        for i in range(0, len(untagged), args.batch_size)
    ]

    log.info(f"Processing {len(batches)} batches of up to {args.batch_size} posts")

    for batch_num, batch in enumerate(batches, 1):
        log.info(f"Batch [{batch_num}/{len(batches)}] — {len(batch)} posts")

        results = classify_batch(client, batch, system_prompt)

        if not results:
            log.warning(f"Batch {batch_num} returned no results — skipping")
            triage_stats["failed"] += len(batch)
            continue

        # Map results back to posts by post_id
        results_by_id = {r["post_id"]: r for r in results}

        for post in batch:
            pid = post["post_id"]
            triage = results_by_id.get(pid)

            if not triage:
                log.warning(f"No triage result for {pid}")
                triage_stats["failed"] += 1
                continue

            # Score against friction log
            confidence = score_against_friction_log(triage, friction_log)

            # Attach triage to post
            post["triage"] = {
                **triage,
                "confidence":  confidence,
                "triaged_at":  datetime.now(timezone.utc).isoformat(),
            }

            tagged_posts[pid] = post
            triage_stats["classified"] += 1

            # Update breakdown stats
            for field, stat_key in [
                ("signal_type", "by_signal"),
                ("persona",     "by_persona"),
                ("source",      "by_source"),
            ]:
                val = triage.get(field, "unknown")
                triage_stats[stat_key][val] = (
                    triage_stats[stat_key].get(val, 0) + 1
                )

        # Polite delay between Haiku calls
        if batch_num < len(batches):
            time.sleep(1.0)

    log.info(f"Classification complete: {triage_stats['classified']} tagged, "
             f"{triage_stats['failed']} failed")
    log.info(f"Signal breakdown: {triage_stats['by_signal']}")
    log.info(f"Persona breakdown: {triage_stats['by_persona']}")
    log.info(f"Source breakdown: {triage_stats['by_source']}")

    # ── Compute and log triage cost ──────────────────────────────────────────
    triage_cost = compute_cost(
        TRIAGE_MODEL,
        triage_usage["input_tokens"],
        triage_usage["output_tokens"],
    )
    log.info(
        f"Triage API usage — "
        f"input: {triage_usage['input_tokens']:,} tokens | "
        f"output: {triage_usage['output_tokens']:,} tokens | "
        f"batches: {triage_usage['batches']} | "
        f"cost: ${triage_cost:.4f}"
    )

    if args.dry_run:
        log.info("DRY RUN — skipping gate routing and file writes")
        log.info(f"Triage stats: {json.dumps(triage_stats, indent=2)}")
        return

    # ── Cross-reference gate routing ─────────────────────────────────────────
    queues = {
        "track_a": [],
        "track_b": [],
        "track_c": [],
        "archive": [],
        "discard": [],
    }

    for post in tagged_posts.values():
        triage     = post.get("triage", {})
        confidence = triage.get("confidence", "IGNORE")
        destination = route_post(post, triage, confidence)
        queues[destination].append(post)

    log.info(f"Gate routing complete:")
    log.info(f"  Track A (claude_native):     {len(queues['track_a'])}")
    log.info(f"  Track B (competitor_gap):    {len(queues['track_b'])}")
    log.info(f"  Track C (cross_platform):    {len(queues['track_c'])}")
    log.info(f"  Archive (LOW confidence):    {len(queues['archive'])}")
    log.info(f"  Discard (IGNORE):            {len(queues['discard'])}")

    # ── Write outputs ─────────────────────────────────────────────────────────
    # All tagged posts
    with open(TAGGED_POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "run_at":    run_start.isoformat(),
                "total":     len(tagged_posts),
                "stats":     triage_stats,
            },
            "posts": list(tagged_posts.values()),
        }, f, indent=2)
    log.info(f"Wrote {len(tagged_posts)} tagged posts → {TAGGED_POSTS_PATH}")

    # Synthesis queues
    for track, path in SYNTHESIS_QUEUE_PATHS.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "meta": {
                    "track":   track,
                    "run_at":  run_start.isoformat(),
                    "count":   len(queues[track]),
                },
                "posts": queues[track],
            }, f, indent=2)
        log.info(f"Wrote {len(queues[track])} posts → {path.name}")

    # Archive
    archive_data = []
    if ARCHIVE_PATH.exists():
        with open(ARCHIVE_PATH, encoding="utf-8") as f:
            existing_archive = json.load(f)
        archive_data = existing_archive.get("posts", [])

    archive_data.extend(queues["archive"])
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {"last_updated": run_start.isoformat(),
                     "total": len(archive_data)},
            "posts": archive_data,
        }, f, indent=2)
    log.info(f"Archive: {len(archive_data)} total posts → {ARCHIVE_PATH}")

    run_id = run_start.strftime("%Y%m%d_%H%M%S")
    append_cost_log(
        run_id=run_id,
        triage_data={
            "model":         TRIAGE_MODEL,
            "input_tokens":  triage_usage["input_tokens"],
            "output_tokens": triage_usage["output_tokens"],
            "batches":       triage_usage["batches"],
            "cost_usd":      triage_cost,
        },
        synthesis_data={},
        posts_processed=triage_stats.get("classified", 0),
    )

    log.info("CLAIRE triage complete.")


if __name__ == "__main__":
    main()
            }, f, indent=2)
        log.info(f"Wrote {len(queues[track])} posts --> {path.name}")

    # Archive
    archive_data = []
    if ARCHIVE_PATH.exists():
        with open(ARCHIVE_PATH, encoding="utf-8") as f:
            existing_archive = json.load(f)
        archive_data = existing_archive.get("posts", [])

    archive_data.extend(queues["archive"])
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {"last_updated": run_start.isoformat(),
                     "total": len(archive_data)},
            "posts": archive_data,
        }, f, indent=2)
    log.info(f"Archive: {len(archive_data)} total posts --> {ARCHIVE_PATH}")

    run_id = run_start.strftime("%Y%m%d_%H%M%S")
    append_cost_log(
        run_id=run_id,
        triage_data={
            "model":         TRIAGE_MODEL,
            "input_tokens":  triage_usage["input_tokens"],
            "output_tokens": triage_usage["output_tokens"],
            "batches":       triage_usage["batches"],
            "cost_usd":      triage_cost,
        },
        synthesis_data={},
        posts_processed=triage_stats.get("classified", 0),
    )

    log.info("CLAIRE triage complete.")


if __name__ == "__main__":
    main()
)
