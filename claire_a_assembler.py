# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
claire_a_assembler.py
---------------------
CLAIRE-A Build 8 â€” Input Assembler

Reads candidate JSON files (tracks A/B/C) and change_log.json, then
produces the structured JSON payload the decision engine prompt expects.

Build 8 additions:
  - Semantic memory filter: candidates with similarity >= 0.85 against
    memory_edits_snapshot.txt are suppressed before engine payload assembly.
    Suppressed candidates logged to data/suppressed_candidates_[timestamp].json.
  - Assembler cost appended to the daily merged cost_log.json entry.

Outputs: data/claire_a_input_{timestamp}.json
         data/suppressed_candidates_{timestamp}.json

Usage:
    python claire_a_assembler.py
    python claire_a_assembler.py --output data/my_input.json
"""

import hashlib
import json
import logging
import re
import uuid
import argparse
from datetime import datetime, timezone
from pathlib import Path

import anthropic as _anthropic

from claire_utils import compute_cost, append_cost_log

# ---------------------------------------------------------------------------
# PATHS  (relative to this script's location)
# ---------------------------------------------------------------------------

BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "data"

CANDIDATE_PATHS = {
    "a": DATA_DIR / "candidates_track_a.json",
    "b": DATA_DIR / "candidates_track_b.json",
    "c": DATA_DIR / "candidates_track_c.json",
}
CHANGE_LOG_PATH      = Path(__file__).parent / "change_log.json"
SESSION_HISTORY_PATH = DATA_DIR / "claire_a_session_history.json"
MEMORY_SNAPSHOT_PATH = DATA_DIR / "memory_edits_snapshot.txt"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("claire_a_assembler")

# ---------------------------------------------------------------------------
# CONFIG LOADER
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load config.json. Returns empty dict on failure."""
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.warning(f"config.json load error: {e} â€” using defaults")
        return {}

# ---------------------------------------------------------------------------
# CANDIDATE LOADING + NORMALISATION
# ---------------------------------------------------------------------------

# Maps each candidate category to its primary text field (for fingerprint
# verification) and a human-readable signal_type label.
CATEGORY_META = {
    "memory_edit_candidates":      {"text_field": "control",        "signal_type": "memory_edit"},
    "profile_diff_candidates":     {"text_field": "proposed_change", "signal_type": "profile_change"},
    "skill_draft_candidates":      {"text_field": "skill_name",      "signal_type": "skill_draft"},
    "profile_addition_candidates": {"text_field": "proposed_text",   "signal_type": "profile_addition"},
    "technique_candidates":        {"text_field": "technique_name",  "signal_type": "technique"},
}


def _confidence_to_float(confidence_str: str, source_posts: list) -> float:
    """Converts HIGH/MEDIUM confidence + evidence count to a calibrated
    signal_strength float, introducing real variance across candidates.

    Base values:  HIGH=0.80  MEDIUM=0.55  unknown=0.45
    Evidence bonus: each source post adds +0.02, capped at +0.10.

    Result ranges:
      HIGH    -> 0.80 - 0.90
      MEDIUM  -> 0.55 - 0.65
      unknown -> 0.45 - 0.55
    """
    bases = {"HIGH": 0.80, "MEDIUM": 0.55}
    base  = bases.get(str(confidence_str).upper(), 0.45)
    bonus = min(len(source_posts), 5) * 0.02
    return round(base + bonus, 4)


def _ensure_fingerprint(candidate: dict, category: str) -> str:
    """Returns existing fingerprint or generates one on the fly.

    claire_synthesize.py now injects fingerprints at save time, so this
    is a safety net for candidate files produced before that change.
    """
    if "fingerprint" in candidate:
        return candidate["fingerprint"]
    text_field = CATEGORY_META[category]["text_field"]
    raw = f"{category}:{candidate.get(text_field, '')}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _load_track(path: Path, track: str) -> list:
    """Loads one track's candidate JSON and returns a flat normalised list."""
    if not path.exists():
        log.warning(f"Track {track.upper()} file not found: {path.name} â€” skipping")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    raw_candidates = data.get("candidates", {})
    posts_input    = data.get("meta", {}).get("posts_input", 0)
    normalised     = []

    for category, meta in CATEGORY_META.items():
        for c in raw_candidates.get(category, []):
            text_field = meta["text_field"]
            fingerprint = _ensure_fingerprint(c, category)

            normalised.append({
                "id":                     str(uuid.uuid4()),
                "fingerprint":            fingerprint,
                "track":                  track,
                "category":               category,
                "source":                 f"claire_synthesize:track_{track}",
                "content": {
                    "type":    meta["signal_type"],
                    "summary": c.get(text_field, "")[:120],
                    "detail":  c,
                },
                "signal_strength":          _confidence_to_float(c.get("confidence", "MEDIUM"), c.get("source_posts", [])),
                "source_reliability_score": 0.5,   # no track record yet; updated by eval scorer
                "created_at":               datetime.now(timezone.utc).isoformat(),
                "prior_appearances":        0,      # updated by prior_appearances resolver below
                "posts_input":              posts_input,
            })

    log.info(f"Track {track.upper()}: loaded {len(normalised)} candidates from {path.name}")
    return normalised


def load_all_candidates() -> list:
    """Loads and merges candidates from all three tracks."""
    candidates = []
    for track, path in CANDIDATE_PATHS.items():
        candidates.extend(_load_track(path, track))
    log.info(f"Total candidates loaded: {len(candidates)}")
    return candidates

# ---------------------------------------------------------------------------
# CHANGE LOG LOADING
# ---------------------------------------------------------------------------

def _normalise_source(entry: dict) -> str:
    """change_log entries use 'source_signal' (profile changes) or
    'source' (memory edits) interchangeably. Normalise to one field."""
    return entry.get("source_signal") or entry.get("source") or "unknown"


def _content_for_entry(entry: dict) -> str:
    """memory_edit entries lack a 'summary' field â€” fall back to hypothesis.
    NOTE: This is a known gap in the change log schema. Adding 'summary' to
    memory_edit entries will improve decision engine memory consistency checks.
    """
    return entry.get("summary") or entry.get("hypothesis") or ""


def _parse_eval_notes(eval_notes: list) -> list:
    """Parses eval_note strings of the form:
        DATE | SESSION_CONTEXT | DID_HYPOTHESIS_HOLD: yes/partial/no | NOTES
    Returns structured dicts. Skips malformed entries with a warning.
    """
    parsed = []
    pattern = re.compile(
        r"^(?P<date>[^|]+)\|(?P<context>[^|]+)\|[^:]+:\s*(?P<held>yes|partial|no)\s*\|(?P<notes>.+)$",
        re.IGNORECASE,
    )
    for note in eval_notes:
        m = pattern.match(note.strip())
        if m:
            parsed.append({
                "date":              m.group("date").strip(),
                "session_context":   m.group("context").strip(),
                "hypothesis_held":   m.group("held").strip().lower(),
                "notes":             m.group("notes").strip(),
            })
        else:
            log.debug(f"Skipping malformed eval_note: {note!r}")
    return parsed


def load_change_log() -> tuple[list, list]:
    """Returns (change_log_entries, eval_history_entries).

    change_log_entries  â†’ formatted for the 'change_log' field in engine input
    eval_history_entries â†’ formatted for the 'eval_history' field
    """
    if not CHANGE_LOG_PATH.exists():
        log.warning(f"change_log.json not found at {CHANGE_LOG_PATH} â€” using empty history")
        return [], []

    with open(CHANGE_LOG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    change_log_entries = []
    eval_history_entries = []

    for entry in data.get("changes", []):
        eval_notes_raw = entry.get("eval_notes", [])
        parsed_notes   = _parse_eval_notes(eval_notes_raw)
        content        = _content_for_entry(entry)

        change_log_entries.append({
            "id":                    str(uuid.uuid4()),
            "applied_at":            entry.get("date", "unknown"),
            "type":                  entry.get("type", "unknown"),
            "summary":               content[:200],
            "source":                _normalise_source(entry),
            "hypothesis":            entry.get("hypothesis", ""),
            "outcome_measured":      len(parsed_notes) > 0,
            "eval_notes":            parsed_notes,
        })

        # Build eval_history entries from any notes that recorded outcomes
        for note in parsed_notes:
            eval_history_entries.append({
                "eval_id":   str(uuid.uuid4()),
                "eval_date": note["date"],
                "metric":    "hypothesis_held",
                "score":     {"yes": 1.0, "partial": 0.5, "no": 0.0}.get(note["hypothesis_held"], 0.5),
                "delta_from_prior": None,
                "correlated_candidate_ids": [],
                "notes": note["notes"],
            })

    # Also surface quarterly_evals if they exist
    for qe in data.get("quarterly_evals", []):
        eval_history_entries.append({
            "eval_id":                  str(uuid.uuid4()),
            "eval_date":                qe.get("date", "unknown"),
            "metric":                   "quarterly_eval",
            "score":                    None,
            "delta_from_prior":         None,
            "correlated_candidate_ids": [],
            "notes":                    json.dumps(qe),
        })

    log.info(f"Change log: {len(change_log_entries)} entries, "
             f"{len(eval_history_entries)} eval history points")
    return change_log_entries, eval_history_entries

# ---------------------------------------------------------------------------
# MEMORY SNAPSHOT
# ---------------------------------------------------------------------------

def build_memory_snapshot(change_log_entries: list) -> dict:
    """Derives the current memory state from the change log.

    The applied changes array IS the memory state â€” what has been applied
    and is currently live. The snapshot hash lets the decision engine detect
    if memory changed between runs.
    """
    # Deterministic serialisation for stable hashing
    canonical = json.dumps(change_log_entries, sort_keys=True, ensure_ascii=False)
    snapshot_hash = hashlib.sha256(canonical.encode()).hexdigest()

    entries = [
        {
            "id":               entry["id"],
            "key":              f"{entry['type']}:{entry['applied_at']}",
            "value":            entry["summary"],
            "established_at":   entry["applied_at"],
            "last_reinforced_at": entry["applied_at"],
            "reinforcement_count": 0,
            "source_candidate_ids": [],
        }
        for entry in change_log_entries
    ]

    return {
        "snapshot_at":   datetime.now(timezone.utc).isoformat(),
        "snapshot_hash": snapshot_hash,
        "entries":       entries,
    }

# ---------------------------------------------------------------------------
# SESSION HISTORY
# ---------------------------------------------------------------------------

def load_session_history() -> dict:
    """Loads the cross-run session history.

    Structure:
    {
      "fingerprint": {
        "appearances": 3,
        "first_seen": "ISO8601",
        "last_seen": "ISO8601",
        "last_decision": "apply|skip|defer|null",
        "sessions": ["session_id_1", "session_id_2"]
      }
    }
    """
    if not SESSION_HISTORY_PATH.exists():
        log.info("No session history found â€” starting fresh")
        return {}
    with open(SESSION_HISTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# PRIOR APPEARANCES
# ---------------------------------------------------------------------------

def resolve_prior_appearances(candidates: list, change_log_entries: list) -> list:
    """Resolves prior_appearances for each candidate from two sources:

    1. Session history (claire_a_session_history.json) â€” cross-run tracking.
       Written by the runner after each decision session.
    2. Change log â€” candidates matching applied changes get prior_appearances=1
       minimum, flagging them as already actioned.

    The two sources are additive: a candidate seen in 3 prior sessions AND
    matching an applied change gets appearances=3, not 1.
    """
    history = load_session_history()

    # Source 1: session history fingerprint counts
    for c in candidates:
        fp = c["fingerprint"]
        if fp in history:
            entry = history[fp]
            c["prior_appearances"] = entry.get("appearances", 0)
            last_decision = entry.get("last_decision")
            if last_decision:
                log.debug(
                    f"Fingerprint {fp}: {c['prior_appearances']} prior appearances, "
                    f"last decision={last_decision}"
                )

    # Source 2: change log â€” mark already-applied candidates
    applied_summaries = {e["summary"][:60] for e in change_log_entries}
    for c in candidates:
        summary_60 = c["content"]["summary"][:60]
        if summary_60 in applied_summaries:
            # Floor at 1 â€” don't zero out session history count
            c["prior_appearances"] = max(c["prior_appearances"], 1)
            log.debug(
                f"Candidate {c['fingerprint']} matches applied change â€” "
                f"prior_appearances floored at 1"
            )

    return candidates

# ---------------------------------------------------------------------------
# MEMORY FILTER (Build 8) â€” semantic duplicate suppression
# ---------------------------------------------------------------------------

def _semantic_similarity(
    candidate: dict,
    memory_text: str,
    model: str,
    client: "_anthropic.Anthropic",
) -> tuple[float, float]:
    """Call Haiku to score semantic similarity between one candidate and the
    memory snapshot.

    Returns (score: float 0.0-1.0, cost_usd: float).
    Raises on API error â€” caller handles and passes the candidate through.
    """
    text_a = f"{candidate['content']['type']}: {candidate['content']['summary']}"

    response = client.messages.create(
        model=model,
        max_tokens=50,
        system=(
            'You are a semantic similarity scorer. Return only a JSON object: '
            '{"score": float} where score is 0.0-1.0 representing semantic '
            'similarity between two texts.'
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Text A: {text_a}\n"
                f"Text B: {memory_text}\n"
                f"Score how similar Text A is to any content already present in Text B."
            ),
        }],
    )

    raw = response.content[0].text.strip()
    score = float(json.loads(raw)["score"])
    cost = compute_cost(model, response.usage.input_tokens, response.usage.output_tokens)
    return score, cost


def filter_candidates_by_memory(
    candidates: list,
    config: dict,
) -> tuple[list, list, float]:
    """Suppress candidates semantically similar to memory_edits_snapshot.txt.

    Sequential Haiku calls â€” one per candidate, fine at â‰¤15 candidates.
    Returns (unsuppressed, suppressed_log_entries, total_cost_usd).

    Writes data/suppressed_candidates_{timestamp}.json (always, even if empty).
    """
    assembler_cfg = config.get("assembler", {})
    enabled   = assembler_cfg.get("memory_filter_enabled", True)
    model     = assembler_cfg.get("memory_filter_model", "claude-haiku-4-5-20251001")
    threshold = assembler_cfg.get("memory_filter_threshold", 0.85)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suppressed_path = DATA_DIR / f"suppressed_candidates_{ts}.json"

    def _write_suppressed(entries: list):
        with open(suppressed_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        log.info(f"Suppressed candidates log â†’ {suppressed_path.name} ({len(entries)} entries)")

    if not enabled:
        log.info("Memory filter disabled in config â€” skipping")
        _write_suppressed([])
        return candidates, [], 0.0

    if not MEMORY_SNAPSHOT_PATH.exists():
        log.warning("memory_edits_snapshot.txt not found â€” memory filter skipped")
        _write_suppressed([])
        return candidates, [], 0.0

    memory_text = MEMORY_SNAPSHOT_PATH.read_text(encoding="utf-8").strip()
    if not memory_text:
        log.warning("memory_edits_snapshot.txt is empty â€” memory filter skipped")
        _write_suppressed([])
        return candidates, [], 0.0

    log.info(f"Memory filter: scoring {len(candidates)} candidates "
             f"(model={model}, threshold={threshold})")

    client = _anthropic.Anthropic()
    unsuppressed = []
    suppressed   = []
    total_cost   = 0.0

    for candidate in candidates:
        try:
            score, cost = _semantic_similarity(candidate, memory_text, model, client)
            total_cost += cost

            if score >= threshold:
                entry = {
                    "id":               candidate["id"],
                    "change_target":    candidate["content"]["type"],
                    "similarity_score": round(score, 4),
                    "reason":           "semantic_duplicate",
                    "suppressed_at":    datetime.now(timezone.utc).isoformat(),
                }
                suppressed.append(entry)
                log.info(
                    f"Suppressed {candidate['fingerprint']} "
                    f"(score={score:.3f} >= {threshold}) â€” "
                    f"{candidate['content']['summary'][:60]!r}"
                )
            else:
                unsuppressed.append(candidate)
                log.debug(f"Passed {candidate['fingerprint']} (score={score:.3f})")

        except Exception as e:
            log.warning(
                f"Memory filter error for {candidate['fingerprint']}: {e} "
                f"â€” passing through"
            )
            unsuppressed.append(candidate)

    log.info(
        f"Memory filter complete: {len(unsuppressed)} pass, "
        f"{len(suppressed)} suppressed, cost=${total_cost:.4f}"
    )

    _write_suppressed(suppressed)
    return unsuppressed, suppressed, total_cost


# ---------------------------------------------------------------------------
# PRIORITY PRE-FILTER (top N by signal_strength Ã— source_reliability)
# ---------------------------------------------------------------------------

MAX_BATCH_SIZE = 15


def apply_priority_filter(candidates: list, max_batch: int = MAX_BATCH_SIZE) -> tuple[list, list]:
    """Sorts candidates by priority score and returns (selected, deferred).

    priority_score = signal_strength Ã— source_reliability Ã— (1 + 0.2 Ã— min(prior_appearances, 5))
    Older stuck candidates float up gradually rather than being permanently
    displaced by high-signal newcomers.
    """
    for c in candidates:
        c["_priority"] = (
            c["signal_strength"]
            * c["source_reliability_score"]
            * (1 + 0.2 * min(c["prior_appearances"], 5))
        )

    candidates.sort(key=lambda c: c["_priority"], reverse=True)

    for c in candidates:
        del c["_priority"]  # internal field â€” don't leak into engine input

    selected = candidates[:max_batch]
    deferred = candidates[max_batch:]

    if deferred:
        log.info(f"Priority filter: {len(selected)} selected, {len(deferred)} deferred to next run")

    return selected, deferred

# ---------------------------------------------------------------------------
# ASSEMBLE
# ---------------------------------------------------------------------------

def assemble(output_path: Path | None = None, max_batch: int = MAX_BATCH_SIZE) -> dict:
    """Loads all inputs, applies memory filter + priority filter, and returns
    the engine payload.
    """

    log.info("â”€â”€ CLAIRE-A Input Assembler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")

    config = load_config()

    candidates                       = load_all_candidates()
    change_log_entries, eval_history = load_change_log()
    candidates                       = resolve_prior_appearances(candidates, change_log_entries)

    # â”€â”€ Build 8: semantic memory filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    candidates, suppressed, assembler_cost = filter_candidates_by_memory(candidates, config)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    selected, deferred               = apply_priority_filter(candidates, max_batch)
    memory_state                     = build_memory_snapshot(change_log_entries)

    payload = {
        "session_id":           str(uuid.uuid4()),
        "run_at":               datetime.now(timezone.utc).isoformat(),
        "memory_snapshot_hash": memory_state["snapshot_hash"],
        "candidates":           selected,
        "memory_state":         memory_state,
        "change_log":           change_log_entries,
        "eval_history":         eval_history,
        "_meta": {
            "assembler_version":      "2.0.0",
            "total_candidates_in":    len(candidates) + len(deferred) + len(suppressed),
            "candidates_loaded":      len(candidates) + len(deferred),
            "candidates_suppressed":  len(suppressed),
            "candidates_selected":    len(selected),
            "candidates_deferred":    len(deferred),
            "max_batch_size":         max_batch,
            "assembler_cost_usd":     round(assembler_cost, 4),
            "eval_history_points":    len(eval_history),
            "notes": (
                "memory_edit entries in change_log lack 'summary' field â€” "
                "hypothesis used as proxy. Add 'summary' to change_log schema "
                "to improve memory consistency checks."
                if any(e["type"] == "memory_edit" for e in change_log_entries)
                else ""
            ),
        },
    }

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = DATA_DIR / f"claire_a_input_{ts}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info(f"Engine input written â†’ {output_path.name}")
    log.info(f"Session ID: {payload['session_id']}")
    log.info(f"Candidates: {len(selected)} selected / {len(deferred)} deferred / "
             f"{len(suppressed)} suppressed by memory filter")
    log.info(f"Memory snapshot hash: {memory_state['snapshot_hash'][:16]}â€¦")
    log.info(f"Assembler cost: ${assembler_cost:.4f}")

    # â”€â”€ Build 8: append assembler cost to merged run entry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    run_id = datetime.now().strftime("%Y%m%d")
    append_cost_log(run_id=run_id, assembler_cost_usd=assembler_cost)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    log.info("â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")

    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLAIRE-A Input Assembler")
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output path for engine input JSON (default: data/claire_a_input_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--max-batch", type=int, default=MAX_BATCH_SIZE,
        help=f"Maximum candidates per batch (default: {MAX_BATCH_SIZE})"
    )
    args = parser.parse_args()

    assemble(output_path=args.output, max_batch=args.max_batch)
