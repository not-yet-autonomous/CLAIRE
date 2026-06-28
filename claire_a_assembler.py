# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
claire_a_assembler.py
---------------------
CLAIRE-A Build 8 â€” Input Assembler

Reads candidate JSON files (tracks A/B/C) and change_log.json, then
produces the structured JSON payload the decision engine prompt expects.

Build 8 additions:
  - Semantic memory filter: candidates with similarity >= 0.85 against
    claire_session_context.txt are suppressed before engine payload assembly.
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
from dotenv import load_dotenv

load_dotenv()

from claire_utils import compute_cost, append_cost_log, atomic_write_json

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
MEMORY_SNAPSHOT_PATH = DATA_DIR / "claire_session_context.txt"  # renamed from memory_edits_snapshot.txt 2026-06-02

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

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log.error(
            f"{path.name} is corrupt and cannot be parsed: {e}. "
            f"Delete or repair {path} and re-run claire_synthesize.py."
        )
        raise SystemExit(1)

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
# SOURCE-URL SUPPRESSION (Build 14 / c8-process-003)
# ---------------------------------------------------------------------------
#
# Catches the same-source re-synthesis class (Type B): a candidate re-derived
# from a post that already motivated an applied change. The Build 11/12 semantic
# filter misses this when re-phrasing drops below the 0.85 threshold. Here we
# match on the SOURCE ITSELF, not on phrasing.
#
# source_signal in change_log.json is FREE TEXT. candidate source_posts are
# URLs/permalinks. Both are normalised to stable keys (hn:<id>, reddit:<id>,
# devto:<slug>). A citation the normaliser cannot resolve is a SILENT FALSE
# NEGATIVE — so every unresolved token is written to a parse-miss log, never
# swallowed.

_HN_URL_RE          = re.compile(r"news\.ycombinator\.com/item\?id=(\d+)", re.IGNORECASE)
_HN_PREFIX_RE       = re.compile(r"^hn[/:]\s*(\d+)$", re.IGNORECASE)
_DEVTO_URL_RE       = re.compile(r"dev\.to/[^/\s?#]+/([^/\s?#]+)", re.IGNORECASE)
_DEVTO_PREFIX_RE    = re.compile(r"^dev\.?to[/:]\s*([^/\s?#]+)$", re.IGNORECASE)
_REDDIT_COMMENTS_RE = re.compile(r"r/[A-Za-z0-9_]+/comments/([A-Za-z0-9]+)", re.IGNORECASE)
_REDDIT_SHORT_RE    = re.compile(r"r/[A-Za-z0-9_]+/([A-Za-z0-9]+)", re.IGNORECASE)


def _normalize_source_token(token: str) -> str | None:
    """Normalise a single citation token to a stable cross-source key.

    Returns 'hn:<id>' | 'reddit:<id>' | 'devto:<slug>' or None when the token
    cannot be resolved (caller logs None results as parse-misses).

    Handles every form observed in the live change_log and candidate files:
        HN/47043484
        https://news.ycombinator.com/item?id=47043484
        r/automation/1tkejnh                       (short reddit form)
        /r/automation/comments/1tkejnh/some_title/ (full reddit permalink)
        https://dev.to/user/some-article-slug
        devto/some-article-slug
    """
    t = (token or "").strip().strip(".,;:()[]{}<>\"'")
    if not t:
        return None

    m = _HN_URL_RE.search(t)
    if m:
        return f"hn:{m.group(1)}"
    m = _HN_PREFIX_RE.match(t)
    if m:
        return f"hn:{m.group(1)}"

    m = _DEVTO_URL_RE.search(t)
    if m:
        return f"devto:{m.group(1).lower()}"
    m = _DEVTO_PREFIX_RE.match(t)
    if m:
        return f"devto:{m.group(1).lower()}"

    # Full permalink (.../comments/<id>/...) before short form, so we never
    # capture the literal segment "comments" as a post id.
    m = _REDDIT_COMMENTS_RE.search(t)
    if m:
        return f"reddit:{m.group(1).lower()}"
    m = _REDDIT_SHORT_RE.search(t)
    if m and m.group(1).lower() != "comments":
        return f"reddit:{m.group(1).lower()}"

    return None


def _extract_source_keys_from_text(text: str) -> tuple[set, list]:
    """Parse a free-text source_signal field.

    Splits on whitespace/commas. A token is citation-like iff it contains '/'
    (every observed citation form does; prose like 'Track', 'Cycle 5',
    'Sources:' does not). Citation-like tokens that fail to normalise are
    returned as misses — they are the silent-false-negative surface.

    Returns (resolved_keys: set, unresolved_tokens: list).
    """
    keys: set = set()
    misses: list = []
    for raw in re.split(r"[\s,]+", text or ""):
        cleaned = raw.strip().strip(".,;:()[]{}<>\"'")
        if "/" not in cleaned:
            continue  # prose, not a citation
        key = _normalize_source_token(cleaned)
        if key:
            keys.add(key)
        else:
            misses.append(raw)
    return keys, misses


def _extract_source_keys_from_posts(source_posts: list) -> tuple[set, list]:
    """Normalise a candidate's source_posts list (full URLs/permalinks).

    Unlike source_signal these are dedicated citation fields, so every entry is
    expected to resolve; any that does not is a miss.

    Returns (resolved_keys: set, unresolved_tokens: list).
    """
    keys: set = set()
    misses: list = []
    for raw in source_posts or []:
        if not isinstance(raw, str) or not raw.strip():
            continue
        key = _normalize_source_token(raw)
        if key:
            keys.add(key)
        else:
            misses.append(raw)
    return keys, misses


def build_change_log_source_index() -> tuple[dict, list]:
    """Build {normalised_source_key -> sorted list of change_log ids} from the
    raw change_log.json, preserving the real cN-... ids (load_change_log drops
    them in favour of uuids).

    Returns (index, parse_misses). parse_misses records every unresolved
    citation token with its originating change_log id.
    """
    index: dict = {}
    misses: list = []
    if not CHANGE_LOG_PATH.exists():
        log.warning("change_log.json not found — source index empty")
        return index, misses

    with open(CHANGE_LOG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    for entry in data.get("changes", []):
        cid    = entry.get("id", "unknown")
        signal = _normalise_source(entry)
        keys, entry_misses = _extract_source_keys_from_text(signal)
        for k in keys:
            index.setdefault(k, set()).add(cid)
        for tok in entry_misses:
            misses.append({
                "origin":        "change_log",
                "change_log_id": cid,
                "token":         tok,
                "source_signal": signal,
            })

    return {k: sorted(v) for k, v in index.items()}, misses


def match_candidates_by_source(candidates: list, source_index: dict) -> tuple[dict, list]:
    """Match each candidate's source_posts against the change_log source index.

    Returns (matches, parse_misses) where matches maps candidate id ->
    sorted list of change_log ids whose source_signal shares a citation.
    """
    matches: dict = {}
    misses: list  = []
    for c in candidates:
        detail = c.get("content", {}).get("detail", {})
        posts  = detail.get("source_posts", []) if isinstance(detail, dict) else []
        keys, cand_misses = _extract_source_keys_from_posts(posts)
        matched: set = set()
        for k in keys:
            matched.update(source_index.get(k, []))
        if matched:
            matches[c["id"]] = sorted(matched)
        for tok in cand_misses:
            misses.append({
                "origin":      "candidate",
                "candidate_id": c["id"],
                "fingerprint":  c.get("fingerprint"),
                "token":        tok,
            })
    return matches, misses

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
    # Strip markdown code fences if the model wraps its JSON output
    if raw.startswith(b"```" if isinstance(raw, bytes) else "```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if not raw:
        raise ValueError(
            f"empty response from model (stop_reason={response.stop_reason!r}, "
            f"output_tokens={response.usage.output_tokens})"
        )
    score = float(json.loads(raw)["score"])
    cost = compute_cost(model, response.usage.input_tokens, response.usage.output_tokens)
    return score, cost


def filter_candidates_by_memory(
    candidates: list,
    config: dict,
    change_log_entries: list | None = None,
) -> tuple[list, list, float]:
    """Suppress candidates that duplicate an already-applied change.

    Two independent signals, COMBINED per candidate (neither replaces the other):

    1. Semantic memory filter (Build 8): Haiku scores similarity between the
       candidate and the current memory state (claire_session_context.txt +
       change_log_entries). score >= threshold suppresses. filter_source records
       the comparison basis: snapshot_only | change_log_only | combined.

    2. Source-URL suppression (Build 14 / c8-process-003): the candidate's
       source_posts are normalised and matched against every source_signal in
       change_log.json. A match attaches SOURCE_ALREADY_PROCESSED plus the
       matching change_log id(s). This catches the same-source re-synthesis
       class (Type B) that the semantic filter misses when re-phrasing drops
       below threshold. The flag is a pointer for human adjudication, NOT a
       verdict: the candidate is routed to the suppressed log carrying its
       matched ids so the operator can decide duplicate-vs-distinct. It is
       never hard-dropped (a hard-drop on shared source would have killed the
       distinct c6-prof-002).

    A candidate is routed to suppressed_candidates if EITHER signal fires.
    Source matching runs even when the semantic filter is disabled/unavailable.

    Sequential Haiku calls â€” one per candidate, fine at â‰¤15 candidates.
    Returns (unsuppressed, suppressed_log_entries, total_cost_usd).

    Writes data/suppressed_candidates_{timestamp}.json (always) and
    data/source_parse_misses_{timestamp}.json (always â€” unresolved citations
    are logged, never swallowed, so recall stays auditable).
    """
    assembler_cfg = config.get("assembler", {})
    enabled   = assembler_cfg.get("memory_filter_enabled", True)
    model     = assembler_cfg.get("memory_filter_model", "claude-haiku-4-5-20251001")
    threshold = assembler_cfg.get("memory_filter_threshold", 0.85)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suppressed_path = DATA_DIR / f"suppressed_candidates_{ts}.json"
    parse_miss_path = DATA_DIR / f"source_parse_misses_{ts}.json"

    def _write_suppressed(entries: list):
        atomic_write_json(suppressed_path, entries, ensure_ascii=False)
        log.info(f"Suppressed candidates log â†’ {suppressed_path.name} ({len(entries)} entries)")

    # â”€â”€ Build 14 (c8-process-003): source-URL suppression â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    source_index, cl_parse_misses   = build_change_log_source_index()
    source_matches, cand_parse_misses = match_candidates_by_source(candidates, source_index)
    parse_misses = cl_parse_misses + cand_parse_misses
    atomic_write_json(
        parse_miss_path,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "change_log":   CHANGE_LOG_PATH.name,
            "miss_count":   len(parse_misses),
            "misses":       parse_misses,
        },
        ensure_ascii=False,
    )
    log.info(
        f"Source-URL matcher: {len(source_matches)} candidate(s) matched an "
        f"applied source; {len(parse_misses)} unresolved citation(s) â†’ "
        f"{parse_miss_path.name}"
    )

    # â”€â”€ Semantic filter availability â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    semantic_available = True
    comparison_text = ""
    filter_source   = "source_only"  # overwritten when semantic scoring runs

    if not enabled:
        log.info("Memory filter disabled in config â€” semantic scoring skipped (source matching still runs)")
        semantic_available = False
    elif not MEMORY_SNAPSHOT_PATH.exists():
        log.warning("claire_session_context.txt not found â€” semantic scoring skipped (source matching still runs)")
        semantic_available = False

    if semantic_available:
        memory_text = MEMORY_SNAPSHOT_PATH.read_text(encoding="utf-8").strip()
        cl_text = ""
        if change_log_entries:
            cl_text = "\n".join(
                f"{e['type']}: {e['summary']}"
                for e in change_log_entries
                if e.get("summary")
            )
        if not memory_text and not cl_text:
            log.warning("claire_session_context.txt empty and no change_log entries — semantic scoring skipped (source matching still runs)")
            semantic_available = False
        else:
            comparison_parts = [p for p in [memory_text, cl_text] if p]
            comparison_text  = "\n\n".join(comparison_parts)
            if memory_text and cl_text:
                filter_source = "combined"
            elif memory_text:
                filter_source = "snapshot_only"
            else:
                filter_source = "change_log_only"
        if semantic_available:
            log.info(f"Memory filter: scoring {len(candidates)} candidates "
                     f"(model={model}, threshold={threshold}, source={filter_source})")

    client       = _anthropic.Anthropic() if semantic_available else None
    unsuppressed = []
    suppressed   = []
    total_cost   = 0.0

    for candidate in candidates:
        sem_score = None
        if semantic_available:
            try:
                sem_score, cost = _semantic_similarity(candidate, comparison_text, model, client)
                total_cost += cost
            except Exception as e:
                log.warning(
                    f"Memory filter error for {candidate['fingerprint']}: {e} "
                    f"â€” semantic score unavailable for this candidate"
                )
                log.debug(f"  candidate summary: {candidate['content'].get('summary','?')[:80]!r}")
                sem_score = None

        matched_ids  = source_matches.get(candidate["id"], [])
        sem_suppress = sem_score is not None and sem_score >= threshold
        src_suppress = bool(matched_ids)

        if sem_suppress or src_suppress:
            reasons, flags = [], []
            if sem_suppress:
                reasons.append("semantic_duplicate")
            if src_suppress:
                reasons.append("source_already_processed")
                flags.append("SOURCE_ALREADY_PROCESSED")
            entry = {
                "id":                       candidate["id"],
                "fingerprint":              candidate["fingerprint"],
                "change_target":            candidate["content"]["type"],
                "summary":                  candidate["content"]["summary"][:80],
                "similarity_score":         round(sem_score, 4) if sem_score is not None else None,
                "reason":                   "+".join(reasons),
                "flags":                    flags,
                "source_already_processed": src_suppress,
                "matched_change_log_ids":   matched_ids,
                "filter_source":            filter_source,
                "suppressed_at":            datetime.now(timezone.utc).isoformat(),
            }
            suppressed.append(entry)
            sem_disp = f"{sem_score:.3f}" if sem_score is not None else "n/a"
            log.info(
                f"Suppressed {candidate['fingerprint']} "
                f"(reason={entry['reason']}, sem={sem_disp}, matched={matched_ids or 'â€”'}) â€” "
                f"{candidate['content']['summary'][:60]!r}"
            )
        else:
            unsuppressed.append(candidate)
            sem_disp = f"{sem_score:.3f}" if sem_score is not None else "n/a"
            log.debug(f"Passed {candidate['fingerprint']} (sem={sem_disp})")

    log.info(
        f"Suppression complete: {len(unsuppressed)} pass, "
        f"{len(suppressed)} suppressed, semantic_cost=${total_cost:.4f}"
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
    candidates, suppressed, assembler_cost = filter_candidates_by_memory(candidates, config, change_log_entries)
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
    atomic_write_json(output_path, payload, ensure_ascii=False)

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
