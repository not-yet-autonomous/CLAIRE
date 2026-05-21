# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
claire_a_scorer.py
------------------
CLAIRE-A Build 6 — Eval Scoring Layer

Runs on a schedule (weekly or on-demand). For each open hypothesis in
the decision record whose eval_window_days has elapsed, calls Sonnet to
assess whether the prediction held based on user-provided session notes.

Updates hypothesis outcomes in-place in the decision record JSON.
Updates source_reliability_scores in a rolling ledger for use by the
assembler on the next run.

SHADOW MODE: reads and writes only CLAIRE-A files. Never touches live config.

Usage:
    python claire_a_scorer.py
    python claire_a_scorer.py --decisions data/claire_a_decisions_20260426_150005.json
    python claire_a_scorer.py --decisions data/claire_a_decisions_20260426_150005.json --notes "session_notes.txt"
"""

import json
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

BASE_DIR         = Path(__file__).parent
DATA_DIR         = BASE_DIR / "data"
RELIABILITY_PATH = DATA_DIR / "claire_a_source_reliability.json"

# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

SCORING_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("claire_a_scorer")

# ---------------------------------------------------------------------------
# RELIABILITY LEDGER
# ---------------------------------------------------------------------------

def load_reliability_ledger() -> dict:
    """Loads rolling source reliability scores.

    Structure:
    {
      "claire_synthesize:track_a": {
        "score": 0.5,
        "observations": 0,
        "last_updated": "ISO8601"
      }
    }
    """
    if not RELIABILITY_PATH.exists():
        log.info("No reliability ledger found — starting fresh")
        return {}
    with open(RELIABILITY_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_reliability_ledger(ledger: dict) -> None:
    with open(RELIABILITY_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    log.info(f"Reliability ledger updated → {RELIABILITY_PATH.name}")


def update_reliability(ledger: dict, source: str, outcome_score: float) -> dict:
    """Rolling average: new_score = (old_score * n + outcome) / (n + 1)."""
    if source not in ledger:
        ledger[source] = {"score": 0.5, "observations": 0, "last_updated": None}

    entry = ledger[source]
    n     = entry["observations"]
    old   = entry["score"]

    entry["score"]        = round((old * n + outcome_score) / (n + 1), 4)
    entry["observations"] = n + 1
    entry["last_updated"] = datetime.now(timezone.utc).isoformat()

    return ledger

# ---------------------------------------------------------------------------
# HYPOTHESIS ELIGIBILITY
# ---------------------------------------------------------------------------

def find_open_hypotheses(decision_record: dict, decisions_path: Path) -> list:
    """Returns decisions whose hypotheses are open and eval window has elapsed."""
    eligible = []
    now      = datetime.now(timezone.utc)

    for d in decision_record.get("decisions", []):
        h = d.get("hypothesis", {})

        if h.get("outcome") is not None:
            continue  # already scored

        # Parse session date from filename as proxy for decision date
        # Format: claire_a_decisions_YYYYMMDD_HHMMSS.json
        try:
            ts_str = decisions_path.stem.split("_decisions_")[1]  # YYYYMMDD_HHMMSS
            decided_at = datetime.strptime(ts_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        except (IndexError, ValueError):
            decided_at = now  # can't parse — treat as just decided, skip

        window_days = h.get("eval_window_days", 14)
        eligible_at = decided_at + timedelta(days=window_days)

        if now >= eligible_at:
            eligible.append({
                "decision":     d,
                "hypothesis":   h,
                "decided_at":   decided_at.isoformat(),
                "eligible_at":  eligible_at.isoformat(),
                "days_elapsed": (now - decided_at).days,
            })

    return eligible


def find_all_open_hypotheses(decision_record: dict, decisions_path: Path) -> list:
    """Returns ALL open hypotheses regardless of eval window — for manual scoring."""
    result = []
    for d in decision_record.get("decisions", []):
        h = d.get("hypothesis", {})
        if h.get("outcome") is None:
            result.append({
                "decision":   d,
                "hypothesis": h,
                "decided_at": "unknown",
                "eligible_at": "manual",
                "days_elapsed": 0,
            })
    return result

# ---------------------------------------------------------------------------
# SCORING PROMPT
# ---------------------------------------------------------------------------

SCORING_SYSTEM_PROMPT = """You are the CLAIRE-A Eval Scoring Layer, running in shadow mode.

Your job is to assess whether hypotheses from the CLAIRE-A decision engine
held true, partially held, or failed to hold based on session observation notes.

For each hypothesis, you will receive:
  - The original prediction
  - The metric being tracked
  - The expected direction and magnitude
  - The falsification condition
  - The decision type (apply/skip/defer)
  - Session observation notes from the user

Your assessment must be structured and conservative:
  - "held": prediction clearly supported by observations
  - "partial": prediction directionally correct but incomplete or weaker than expected
  - "failed": prediction contradicted by observations or falsification condition met
  - "insufficient_data": observations don't provide enough signal to assess

Do not infer. Do not extrapolate. Base assessments only on what the notes explicitly state.
If uncertain, use insufficient_data rather than guessing.

Produce a JSON array of scoring results, one per hypothesis submitted.
No markdown fences. No preamble. JSON only.

Schema per result:
{
  "hypothesis_id": "string",
  "outcome": "held|partial|failed|insufficient_data",
  "outcome_score": 0.0,
  "confidence": 0.0,
  "rationale": "2-3 sentences grounded in the observation notes",
  "evidence_quoted": "brief paraphrase of the note content that drove this assessment"
}

outcome_score mapping:
  held               -> 1.0
  partial            -> 0.5
  failed             -> 0.0
  insufficient_data  -> null (use JSON null, not a number)
"""


def build_scoring_message(eligible: list, session_notes: str) -> str:
    hypotheses_payload = []
    for item in eligible:
        d = item["decision"]
        h = item["hypothesis"]
        hypotheses_payload.append({
            "hypothesis_id":         h["id"],
            "decision_type":         d["decision"],
            "candidate_summary":     d["candidate_summary"],
            "prediction":            h["prediction"],
            "metric":                h["metric"],
            "expected_direction":    h["expected_direction"],
            "expected_magnitude":    h["expected_magnitude"],
            "falsification_condition": h["falsification_condition"],
            "days_elapsed":          item["days_elapsed"],
        })

    return (
        "Score these hypotheses based on the session observation notes below.\n\n"
        "HYPOTHESES:\n"
        + json.dumps(hypotheses_payload, indent=2)
        + "\n\nSESSION OBSERVATION NOTES:\n"
        + session_notes
    )

# ---------------------------------------------------------------------------
# SCORER
# ---------------------------------------------------------------------------

def score_hypotheses(eligible: list, session_notes: str) -> list:
    """Calls Sonnet to score all eligible hypotheses. Returns list of results."""
    client  = anthropic.Anthropic()
    message = build_scoring_message(eligible, session_notes)

    log.info(f"Calling Sonnet to score {len(eligible)} hypothesis/es…")

    response = client.messages.create(
        model=SCORING_MODEL,
        max_tokens=4096,
        system=SCORING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    )

    raw = response.content[0].text.strip()

    try:
        results = json.loads(raw)
        log.info(f"Scoring complete — {len(results)} results received")
        return results
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse scoring response: {e}")
        log.debug(f"Raw response:\n{raw[:500]}")
        return []

# ---------------------------------------------------------------------------
# WRITE BACK
# ---------------------------------------------------------------------------

def apply_scores(
    decision_record: dict,
    scoring_results: list,
    eligible: list,
    decisions_path: Path,
) -> tuple[dict, dict]:
    """Writes outcome scores back into the decision record.
    Returns (updated_decision_record, source_map) where source_map is
    {hypothesis_id: source} for reliability ledger updates.
    """
    results_by_id = {r["hypothesis_id"]: r for r in scoring_results}
    source_map    = {}

    # Build hypothesis_id -> source lookup from eligible items
    for item in eligible:
        h_id = item["hypothesis"]["id"]
        # Source lives on the candidate — find it in decision record
        for d in decision_record["decisions"]:
            if d["hypothesis"]["id"] == h_id:
                source_map[h_id] = d.get("source", "unknown")
                break

    scored_count = 0
    for d in decision_record["decisions"]:
        h    = d.get("hypothesis", {})
        h_id = h.get("id")

        if h_id not in results_by_id:
            continue

        result = results_by_id[h_id]
        h["outcome"]            = result["outcome"]
        h["outcome_score"]      = result.get("outcome_score")
        h["outcome_confidence"] = result.get("confidence")
        h["outcome_rationale"]  = result.get("rationale")
        h["outcome_recorded_at"] = datetime.now(timezone.utc).isoformat()
        scored_count += 1

        outcome = result["outcome"]
        score   = result.get("outcome_score")
        log.info(f"  {h_id[:8]}  {outcome:20}  score={score}  {d['candidate_summary'][:60]}")

    log.info(f"Scored {scored_count} hypotheses")
    return decision_record, source_map

# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

def run(
    decisions_path: Path,
    session_notes: str,
    force: bool = False,
) -> None:
    log.info("── CLAIRE-A Eval Scorer ──────────────────────────────────")
    log.info(f"Decisions file: {decisions_path.name}")
    log.info(f"Scoring model:  {SCORING_MODEL}")

    with open(decisions_path, encoding="utf-8") as f:
        wrapper = json.load(f)

    decision_record = wrapper.get("decision_record")
    if not decision_record:
        log.error("No decision_record found in file — was parsing successful on the runner run?")
        return

    # Find eligible hypotheses
    if force:
        eligible = find_all_open_hypotheses(decision_record, decisions_path)
        log.info(f"Force mode — scoring all {len(eligible)} open hypotheses regardless of window")
    else:
        eligible = find_open_hypotheses(decision_record, decisions_path)
        log.info(f"Found {len(eligible)} hypotheses past eval window")

    if not eligible:
        log.info("Nothing to score. Run with --force to score regardless of eval window.")
        log.info("─────────────────────────────────────────────────────")
        return

    # Score
    scoring_results = score_hypotheses(eligible, session_notes)
    if not scoring_results:
        log.error("No scoring results returned — check Sonnet response")
        return

    # Apply scores back to decision record
    decision_record, source_map = apply_scores(
        decision_record, scoring_results, eligible, decisions_path
    )
    wrapper["decision_record"] = decision_record
    wrapper["_meta"]["last_scored_at"] = datetime.now(timezone.utc).isoformat()

    # Write updated decision record
    with open(decisions_path, "w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2, ensure_ascii=False)
    log.info(f"Decision record updated → {decisions_path.name}")

    # Update reliability ledger
    ledger = load_reliability_ledger()
    for result in scoring_results:
        h_id         = result["hypothesis_id"]
        outcome_score = result.get("outcome_score")
        source        = source_map.get(h_id, "unknown")

        if outcome_score is not None:  # skip insufficient_data
            ledger = update_reliability(ledger, source, outcome_score)
            log.info(f"  Reliability updated: {source} -> {ledger[source]['score']:.4f} "
                     f"(n={ledger[source]['observations']})")

    save_reliability_ledger(ledger)

    # Summary
    outcomes = [r["outcome"] for r in scoring_results]
    log.info(f"Outcomes: held={outcomes.count('held')} "
             f"partial={outcomes.count('partial')} "
             f"failed={outcomes.count('failed')} "
             f"insufficient_data={outcomes.count('insufficient_data')}")
    log.info("─────────────────────────────────────────────────────────")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _latest_decisions_file() -> Path | None:
    files = sorted(DATA_DIR.glob("claire_a_decisions_*.json"), reverse=True)
    return files[0] if files else None


def _load_notes(notes_arg: str | None) -> str:
    """Accepts a file path or inline text. Prompts interactively if neither provided."""
    if notes_arg is None:
        log.info("No --notes provided. Enter session observations below.")
        log.info("Describe what you observed in recent sessions — cite specific behaviors.")
        log.info("Press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) when done.\n")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        return "\n".join(lines)

    path = Path(notes_arg)
    if path.exists():
        return path.read_text(encoding="utf-8")

    # Treat as inline text
    return notes_arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLAIRE-A Eval Scorer")
    parser.add_argument(
        "--decisions", type=Path, default=None,
        help="Path to decision record JSON (default: most recent in data/)"
    )
    parser.add_argument(
        "--notes", type=str, default=None,
        help="Session observation notes — file path or inline text"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Score all open hypotheses regardless of eval window"
    )
    args = parser.parse_args()

    decisions_path = args.decisions
    if decisions_path is None:
        decisions_path = _latest_decisions_file()
        if decisions_path is None:
            log.error("No decisions file found in data/. Run claire_a_runner.py first.")
            raise SystemExit(1)
        log.info(f"Auto-selected most recent decisions: {decisions_path.name}")

    if not decisions_path.exists():
        log.error(f"Decisions file not found: {decisions_path}")
        raise SystemExit(1)

    session_notes = _load_notes(args.notes)
    if not session_notes.strip():
        log.error("No session notes provided — cannot score without observations")
        raise SystemExit(1)

    run(decisions_path=decisions_path, session_notes=session_notes, force=args.force)
