# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Build 3a: Synthesis Layer
Input:   data/synthesis_queue_track_a/b/c.json
         prompts/profile_intent_summary.txt
         data/memory_edits_snapshot.txt
Output:  data/candidates_track_a.json
         data/candidates_track_b.json
         data/candidates_track_c.json

Run:     python claire_synthesize.py
         python claire_synthesize.py --track a   (single track)
         python claire_synthesize.py --dry-run   (validate inputs, no API calls)
"""

import json
import argparse
import logging
import types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
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

SYNTHESIS_LOG_PATH      = LOGS_DIR / "synthesis.log"
PROFILE_SUMMARY_PATH    = BASE_DIR / "prompts" / "profile_intent_summary.txt"
MEMORY_EDITS_PATH       = DATA_DIR / "memory_edits_snapshot.txt"

QUEUE_PATHS = {
    "a": DATA_DIR / "synthesis_queue_track_a.json",
    "b": DATA_DIR / "synthesis_queue_track_b.json",
    "c": DATA_DIR / "synthesis_queue_track_c.json",
}

CANDIDATE_PATHS = {
    "a": DATA_DIR / "candidates_track_a.json",
    "b": DATA_DIR / "candidates_track_b.json",
    "c": DATA_DIR / "candidates_track_c.json",
}

with open(BASE_DIR / "config.json") as f:
    CONFIG = json.load(f)

SYNTHESIS_MODEL      = CONFIG["synthesis"]["model"]
EVIDENCE_THRESHOLD   = CONFIG["synthesis"]["evidence_threshold"]
LOCKED_SECTIONS      = CONFIG["synthesis"]["locked_profile_sections"]
TRACK_A_MAX_BATCH    = CONFIG["synthesis"]["track_a_max_batch"]

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SYNTHESIS_LOG_PATH, encoding="utf-8"),
    ]
)
log = logging.getLogger("claire.synthesis")

# ─────────────────────────────────────────────────────────────────────────────
# RESOURCE LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_profile_summary() -> str:
    if not PROFILE_SUMMARY_PATH.exists():
        log.error(f"Profile summary not found: {PROFILE_SUMMARY_PATH}")
        return ""
    with open(PROFILE_SUMMARY_PATH, encoding="utf-8") as f:
        return f.read().strip()


def load_memory_edits() -> str:
    if not MEMORY_EDITS_PATH.exists():
        log.warning("memory_edits_snapshot.txt not found — synthesis runs without memory context")
        return "(no memory edits on file)"
    with open(MEMORY_EDITS_PATH, encoding="utf-8") as f:
        content = f.read().strip()
    lines = [l for l in content.splitlines()
             if l.strip() and not l.strip().startswith("#")]
    return "\n".join(lines) if lines else "(memory edits file is empty)"


def load_queue(track: str) -> list:
    path = QUEUE_PATHS[track]
    if not path.exists():
        log.error(f"Synthesis queue not found: {path}")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    posts = data.get("posts", [])
    log.info(f"Track {track.upper()}: loaded {len(posts)} posts from queue")
    return posts


def serialize_posts_for_synthesis(posts: list) -> str:
    """Condense posts to essential signal for synthesis prompt."""
    condensed = []
    for post in posts:
        triage = post.get("triage", {})
        condensed.append({
            "post_id":      post.get("post_id", ""),
            "permalink":    post.get("permalink", ""),
            "subreddit":    post.get("subreddit", ""),
            "title":        post.get("title", "")[:200],
            "body":         post.get("body", "")[:400],
            "score":        post.get("score", 0),
            "signal_type":  triage.get("signal_type", ""),
            "confidence":   triage.get("confidence", ""),
            "top_comments": [
                c["body"][:150] for c in post.get("comments", [])[:5]
            ],
        })
    return json.dumps(condensed, ensure_ascii=False, separators=(',', ':'))


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHESIS PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

def build_track_a_prompt(profile_summary: str, memory_edits: str) -> str:
    return f"""You are the synthesis layer of CLAIRE, a personal AI configuration
improvement pipeline. Your job is to analyze filtered Reddit signal
about Claude AI and generate structured improvement candidates for
a specific user's configuration.

You are NOT a general Claude improvement engine. You are analyzing
signal on behalf of one specific user and generating candidates
relevant to their established configuration and intent.

---

USER CONTEXT

Profile Intent Summary:
{profile_summary}

Current Memory Edits (do not suggest duplicates):
{memory_edits}

---

EVIDENCE THRESHOLD

Only generate a candidate if supported by {EVIDENCE_THRESHOLD} or more distinct posts
in the input. A pattern described in fewer posts is insufficient.
If fewer than {EVIDENCE_THRESHOLD} posts support a candidate, omit it entirely —
do not note it, do not flag it, do not mention it.

---

CANDIDATE TYPES

Generate candidates in three categories:

1. memory_edit_candidates
   Improvements expressible as a new or modified memory edit.
   - command: "add" only
   - control: exact memory edit text under 100 characters, written as a
     factual statement about the user (e.g., "User prefers X in context Y")
   Do NOT suggest edits that duplicate existing memory edits listed above.

2. profile_diff_candidates
   Improvements requiring a change to a specific named section of the
   user's profile. Only suggest additions or refinements — not restructuring.
   Identify the target section by name. Describe the change in plain language.
   Do not rewrite the full section.

3. behavior_watch
   Patterns that appear in the signal but are NOT yet actionable.
   Flag only. No candidate generated.

---

DO NOT:
- Write hypotheses. The user writes those.
- Generate candidates for developer-persona use cases.
- Speculate beyond what the source posts describe.
- Suggest changes to: {", ".join(LOCKED_SECTIONS)}

---

OUTPUT FORMAT — JSON only, no preamble, no markdown fences.

{{
  "memory_edit_candidates": [
    {{
      "command": "add",
      "control": "exact memory edit text under 100 chars",
      "rationale": "2-3 sentences describing the pattern and why this edit addresses it",
      "confidence": "HIGH|MEDIUM",
      "source_posts": ["permalink1", "permalink2", "permalink3"]
    }}
  ],
  "profile_diff_candidates": [
    {{
      "target_section": "section name from profile",
      "proposed_change": "plain language description of what to add or refine",
      "rationale": "2-3 sentences",
      "confidence": "HIGH|MEDIUM",
      "source_posts": ["permalink1", "permalink2", "permalink3"]
    }}
  ],
  "behavior_watch": [
    {{
      "pattern": "one sentence description",
      "why_not_actioned": "one sentence",
      "source_posts": ["permalink1", "permalink2"]
    }}
  ]
}}"""


def build_track_b_prompt(profile_summary: str, memory_edits: str) -> str:
    return f"""You are analyzing Reddit signal where users praise ChatGPT, Gemini,
or other AI tools for capabilities that imply Claude lacks them.
Your job is to identify genuine capability gaps and generate
skill or profile addition candidates.

USER CONTEXT

Profile Intent Summary:
{profile_summary}

Current Memory Edits:
{memory_edits}

EVIDENCE THRESHOLD: {EVIDENCE_THRESHOLD} corroborating posts minimum. No exceptions.

CANDIDATE TYPES

1. skill_draft_candidates
   Gaps addressable by building a new Claude skill. Generate a SKILL.md skeleton:
   name, description trigger, and 3-5 bullet points of what the skill should encode.
   Do not write full implementation — skeleton only.

2. profile_addition_candidates
   Gaps addressable by adding a new behavioral instruction to the profile.
   Track B generates additions only — not changes to existing sections.

DO NOT generate candidates for developer/API use cases.
DO NOT write hypotheses.
For each profile_addition_candidate, set change_target to "claude_behavior" if the
instruction directs Claude to do something, or "user_behavior" if it advises the
user to change how they prompt or interact.

OUTPUT FORMAT — JSON only, no markdown fences.

{{
  "skill_draft_candidates": [
    {{
      "skill_name": "string",
      "gap_description": "what Claude does not do that others do",
      "trigger_description": "when this skill should activate",
      "skill_md_skeleton": "name:\\ndescription:\\nkey_behaviors:\\n- \\n- \\n- ",
      "estimated_build_effort": "15min|1hr|2hr",
      "confidence": "HIGH|MEDIUM",
      "source_posts": ["permalink1", "permalink2", "permalink3"]
    }}
  ],
  "profile_addition_candidates": [
    {{
      "target_section": "existing section name or NEW",
      "proposed_text": "the actual text to add",
      "rationale": "2-3 sentences",
      "change_target": "claude_behavior|user_behavior",
      "confidence": "HIGH|MEDIUM",
      "source_posts": ["permalink1", "permalink2", "permalink3"]
    }}
  ]
}}"""


def build_track_c_prompt() -> str:
    return f"""You are identifying portable AI workflow techniques from Reddit discussions.
These are prompting patterns, structural approaches, or interaction techniques
that users describe as effective across AI tools, not Claude-specific.

EVIDENCE THRESHOLD: {EVIDENCE_THRESHOLD} corroborating posts minimum.

Generate technique_candidates only — no config changes, no skill drafts.
These are candidates for the user to test manually before any configuration
change is considered.

DO NOT write hypotheses.
Always set change_target to "user_behavior" for technique_candidates — these are
prompting patterns for the user, not behavioral instructions for Claude.

OUTPUT FORMAT — JSON only, no markdown fences.

{{
  "technique_candidates": [
    {{
      "technique_name": "short label",
      "description": "what the technique is and how it works",
      "test_suggestion": "one sentence: how to try it in a session",
      "change_target": "user_behavior",
      "confidence": "HIGH|MEDIUM",
      "source_posts": ["permalink1", "permalink2", "permalink3"]
    }}
  ]
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# SONNET CALLS
# ─────────────────────────────────────────────────────────────────────────────

def run_synthesis(client: anthropic.Anthropic,
                  system_prompt: str,
                  posts: list,
                  track: str) -> tuple:
    """Run a single Sonnet synthesis call for one track.
    Returns (candidates_dict, response.usage) on success,
    ({}, None) on empty queue or error.
    """

    if not posts:
        log.warning(f"Track {track.upper()}: empty queue — skipping synthesis call")
        return {}, None

    user_message = (
        f"Analyze the following {len(posts)} Reddit posts and generate "
        f"improvement candidates per the schema above.\n\n"
        f"{serialize_posts_for_synthesis(posts)}"
    )

    log.info(f"Track {track.upper()}: calling {SYNTHESIS_MODEL} with {len(posts)} posts")

    try:
        response = client.messages.create(
            model=SYNTHESIS_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown fences if added despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)
        log.info(f"Track {track.upper()}: synthesis complete")
        return result, response.usage

    except json.JSONDecodeError as e:
        log.error(f"Track {track.upper()}: JSON parse error — {e}")
        log.error(f"Raw response preview: {raw[:300]}")
        return {}, None
    except anthropic.APIError as e:
        log.error(f"Track {track.upper()}: API error — {e}")
        return {}, None


# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE COUNTING
# ─────────────────────────────────────────────────────────────────────────────

def count_candidates(result: dict, track: str) -> dict:
    counts = {}
    if track == "a":
        counts["memory_edit_candidates"]  = len(result.get("memory_edit_candidates", []))
        counts["profile_diff_candidates"] = len(result.get("profile_diff_candidates", []))
        counts["behavior_watch"]          = len(result.get("behavior_watch", []))
    elif track == "b":
        counts["skill_draft_candidates"]     = len(result.get("skill_draft_candidates", []))
        counts["profile_addition_candidates"] = len(result.get("profile_addition_candidates", []))
    elif track == "c":
        counts["technique_candidates"] = len(result.get("technique_candidates", []))
    return counts


# ─────────────────────────────────────────────────────────────────────────────
# PARALLEL SYNTHESIS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

# Module-level handles populated by main() before thread dispatch
_client:  anthropic.Anthropic | None = None
_prompts: dict[str, str] = {}


def save_candidates(track: str, candidates: dict, posts_input: int) -> None:
    output = {
        "meta": {
            "track":       track,
            "run_at":      datetime.now(timezone.utc).isoformat(),
            "posts_input": posts_input,
            "model":       SYNTHESIS_MODEL,
        },
        "candidates": candidates,
    }
    with open(CANDIDATE_PATHS[track], "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    log.info(f"Wrote candidates → {CANDIDATE_PATHS[track].name}")


def cluster_posts_by_signal(posts: list, max_batch: int) -> list:
    """Groups posts by signal_type field, splits clusters exceeding max_batch.
    Returns flat list of batches (each batch is a list of posts)."""
    clusters = defaultdict(list)
    for post in posts:
        signal_type = post.get("triage", {}).get("signal_type", "unknown")
        clusters[signal_type].append(post)

    batches = []
    for signal_type, cluster_posts in clusters.items():
        for i in range(0, len(cluster_posts), max_batch):
            batches.append(cluster_posts[i:i + max_batch])
    return batches


def merge_candidates(all_candidates: list) -> dict:
    """Takes list of Track A candidate dicts (one per batch).
    Deduplicates on (signal_type, title[:60]) tuple.
    Returns flat deduplicated dict with same schema as a single Track A result."""
    # Maps category name → primary text field used as dedup key
    CATEGORY_KEY = {
        "memory_edit_candidates":    "control",
        "profile_diff_candidates":   "proposed_change",
        "behavior_watch":            "pattern",
    }

    merged = {cat: [] for cat in CATEGORY_KEY}
    seen: set = set()

    for batch_result in all_candidates:
        for cat, text_field in CATEGORY_KEY.items():
            for candidate in batch_result.get(cat, []):
                signal_type = cat
                title = candidate.get(text_field, "")[:60]
                key = (signal_type, title)
                if key not in seen:
                    seen.add(key)
                    merged[cat].append(candidate)

    return merged


def run_track_a_batched(posts: list, max_batch: int) -> tuple:
    """Clusters Track A posts by signal_type, runs synthesis per batch sequentially,
    accumulates token usage, merges and deduplicates candidates.
    Returns (merged_candidates, total_usage_dict)."""
    batches = cluster_posts_by_signal(posts, max_batch)
    log.info(f"Track A: {len(batches)} batch(es) from {len(posts)} posts "
             f"(max_batch={max_batch})")

    all_batch_candidates = []
    total_input_tokens   = 0
    total_output_tokens  = 0

    for i, batch in enumerate(batches):
        signal_types = sorted({p.get("triage", {}).get("signal_type", "unknown")
                                for p in batch})
        signal_label = ", ".join(signal_types)
        log.info(f"Track A batch {i + 1}/{len(batches)}: "
                 f"{len(batch)} posts — signal: {signal_label}")

        candidates, usage = run_synthesis(_client, _prompts["a"], batch, "a")
        all_batch_candidates.append(candidates if candidates else {})

        if usage is not None:
            total_input_tokens  += usage.input_tokens
            total_output_tokens += usage.output_tokens

    merged = merge_candidates(all_batch_candidates)
    total_candidates = sum(len(v) for v in merged.values())
    log.info(f"Track A merge complete: {len(batches)} batch(es) → "
             f"{total_candidates} deduplicated candidates")

    total_usage = {
        "input_tokens":  total_input_tokens,
        "output_tokens": total_output_tokens,
    }
    return merged, total_usage


def run_track(track: str) -> tuple[str, dict, object]:
    posts = load_queue(track)
    if track == "a":
        candidates, usage_dict = run_track_a_batched(posts, TRACK_A_MAX_BATCH)
        usage = types.SimpleNamespace(
            input_tokens=usage_dict["input_tokens"],
            output_tokens=usage_dict["output_tokens"],
        ) if (usage_dict["input_tokens"] or usage_dict["output_tokens"]) else None
    else:
        candidates, usage = run_synthesis(_client, _prompts[track], posts, track)
    save_candidates(track, candidates, len(posts))
    return track, candidates, usage


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLAIRE synthesis layer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate inputs and prompts, no API calls")
    parser.add_argument("--track",   choices=["a", "b", "c"],
                        help="Run single track only")
    args = parser.parse_args()

    run_start = datetime.now(timezone.utc)
    log.info(f"CLAIRE synthesis started — dry_run={args.dry_run} track={args.track or 'all'}")

    # Load shared resources
    profile_summary = load_profile_summary()
    memory_edits    = load_memory_edits()

    if not profile_summary:
        log.error("Profile summary is empty. Cannot run synthesis.")
        return

    log.info(f"Profile summary: {len(profile_summary)} chars")
    log.info(f"Memory edits: {len(memory_edits.splitlines())} lines")

    # Determine which tracks to run
    tracks = [args.track] if args.track else ["a", "b", "c"]

    # Build prompts
    prompts = {
        "a": build_track_a_prompt(profile_summary, memory_edits),
        "b": build_track_b_prompt(profile_summary, memory_edits),
        "c": build_track_c_prompt(),
    }

    if args.dry_run:
        for track in tracks:
            posts = load_queue(track)
            log.info(f"Track {track.upper()} prompt: {len(prompts[track])} chars | "
                     f"Queue: {len(posts)} posts")
        log.info("DRY RUN complete — no API calls made")
        return

    # Initialize client
    client = anthropic.Anthropic()

    # Run synthesis per track
    all_results             = {}
    synthesis_track_usage   = {}
    synthesis_total_cost    = 0.0
    total_posts_synthesized = 0

    # Pre-compute total posts for cost log (run_track reloads queues internally)
    total_posts_synthesized = sum(len(load_queue(t)) for t in tracks)

    # Share client and prompts with thread workers
    global _client, _prompts
    _client  = client
    _prompts = prompts

    with ThreadPoolExecutor(max_workers=len(tracks)) as executor:
        futures = {executor.submit(run_track, track): track for track in tracks}
        for future in as_completed(futures):
            track = futures[future]
            try:
                trk, candidates, usage = future.result()
                all_results[trk] = candidates

                if candidates:
                    counts = count_candidates(candidates, trk)
                    log.info(f"Track {trk.upper()} candidates: {counts}")
                else:
                    log.warning(f"Track {trk.upper()}: no candidates generated")

                if usage is not None:
                    track_cost = compute_cost(
                        SYNTHESIS_MODEL, usage.input_tokens, usage.output_tokens
                    )
                    synthesis_track_usage[trk] = {
                        "input_tokens":  usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "cost_usd":      track_cost,
                    }
                    synthesis_total_cost = round(synthesis_total_cost + track_cost, 4)
                    log.info(
                        f"Track {trk.upper()} usage — "
                        f"input: {usage.input_tokens:,} | "
                        f"output: {usage.output_tokens:,} | "
                        f"cost: ${track_cost:.4f}"
                    )
                else:
                    synthesis_track_usage[trk] = {
                        "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0
                    }

            except Exception as e:
                log.error(f"Track {track.upper()}: failed — {e}")
                synthesis_track_usage[track] = {
                    "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0
                }
                all_results[track] = {}

    # Summary
    log.info("═" * 60)
    log.info(f"Synthesis total cost: ${synthesis_total_cost:.4f}")
    log.info("CLAIRE synthesis complete.")
    for track, result in all_results.items():
        if result:
            counts = count_candidates(result, track)
            log.info(f"  Track {track.upper()}: {counts}")
        else:
            log.info(f"  Track {track.upper()}: empty")
    log.info("Next step: python claire_output.py")

    run_id = run_start.strftime("%Y%m%d")   # daily key — merges with triage + assembler
    append_cost_log(
        run_id=run_id,
        synthesis_cost_usd=synthesis_total_cost,
        posts_processed=total_posts_synthesized,
    )


if __name__ == "__main__":
    main()
