# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
claire_a_runner.py
------------------
CLAIRE-A Build 5 â€” Decision Engine Runner

Loads an assembler input payload, calls Opus with the decision engine
prompt, parses the structured response, and writes the shadow decision
log to data/claire_a_decisions_TIMESTAMP.json.

SHADOW MODE: reads everything, writes nothing to live CLAIRE config.

Usage:
    python claire_a_runner.py
    python claire_a_runner.py --input data/claire_a_input_20260426_132906.json
    python claire_a_runner.py --input data/claire_a_input_20260426_132906.json --dry-run
"""

import json
import logging
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

import os
from dotenv import load_dotenv
import anthropic
load_dotenv()

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

BASE_DIR             = Path(__file__).parent
DATA_DIR             = BASE_DIR / "data"
SESSION_HISTORY_PATH = DATA_DIR / "claire_a_session_history.json"

# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

DECISION_ENGINE_MODEL = "claude-opus-4-5"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("claire_a_runner")

# ---------------------------------------------------------------------------
# DECISION ENGINE SYSTEM PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the CLAIRE-A Decision Engine, running in shadow mode.

OPERATING CONSTRAINTS
- You read everything. You write nothing to live configuration.
- Your output is a structured decision record consumed by the shadow log.
- You are not the final actor. You are the reasoned recommendation layer.
- Treat every candidate as if your decision will be reviewed by a skeptical
  human auditor who knows the full history.

YOUR INPUTS
You will receive a JSON payload containing:
  1. candidates â€” proposed changes or additions from the CLAIRE digest pipeline
  2. memory_state â€” current applied CLAIRE configuration (derived from change_log)
  3. change_log â€” history of prior decisions with hypotheses and eval notes
  4. eval_history â€” metric scores correlated with past changes

YOUR JOB
For each candidate, produce:
  - A decision: apply | skip | defer
  - A confidence score: 0.0â€“1.0
  - Structured reasoning across four dimensions
  - A falsifiable hypothesis tied to the decision
  - Any risk flags
  - Any dependencies on other candidates in this batch

DECISION DEFINITIONS

apply
  The signal is clear and actionable. The candidate is consistent with
  memory state, supported by eval history, and the risk is bounded and
  reversible. Applying it in shadow mode is the right call.

skip
  The candidate does not warrant action. Reasons: noise, contradiction with
  strong eval history, duplicate of existing memory, source reliability too
  low, or signal below threshold. Skipping is a decision â€” record the reason.

defer
  The signal is real but the conditions for action are not met. Reasons:
  dependency on an unresolved candidate, timing is wrong, context is
  incomplete, or confidence falls in the ambiguous middle range where more
  data would change the call. Defer includes a condition for resolution.

REASONING PROTOCOL
Before assigning a decision for each candidate, reason through these four
dimensions. This reasoning is part of the output â€” do not suppress it.

  1. SIGNAL ASSESSMENT
     What is the candidate actually proposing? Is the signal genuine or
     is this noise amplified by repetition? Does signal_strength reflect
     actual evidence or pipeline artifact?

  2. MEMORY CONSISTENCY
     Does this candidate duplicate, reinforce, contradict, or extend
     existing memory? If it contradicts established memory, what is
     the evidence quality on each side?

  3. EVAL ALIGNMENT
     Does eval history support this class of change? Have similar
     candidates produced positive or negative outcomes? Is the eval
     record thin enough that you cannot draw a confident inference?

  4. RISK ASSESSMENT
     What is the worst-case outcome if this decision is wrong? Is that
     outcome reversible? Does prior_appearances suggest the digest
     pipeline is stuck on this candidate?

HYPOTHESIS GENERATION
Every decision requires a falsifiable hypothesis the eval scoring layer
can check later.

Required fields per hypothesis:
  - prediction: specific statement of expected outcome
  - metric: which eval metric to watch
  - expected_direction: increase | decrease | no_change
  - expected_magnitude: numeric estimate with unit (e.g. "+0.05 on coherence")
  - eval_window_days: integer â€” how long before this is measurable
  - falsification_condition: one sentence stating what would disprove it

For skip decisions: hypothesize the absence of harm from inaction.
For defer decisions: hypothesize the condition that would resolve to apply or skip.

CONFIDENCE CALIBRATION
  0.90â€“1.00  High. Evidence strong and consistent. Decide cleanly.
  0.70â€“0.89  Moderate. Signal present; some uncertainty. Note what would move this.
  0.50â€“0.69  Low. Lean defer unless strong asymmetry argument exists.
  0.00â€“0.49  Do not apply. Skip or defer with full reasoning.

RISK FLAGS â€” use zero or more per candidate
  HIGH_VARIANCE           Signal strength varies significantly across appearances
  CONTRADICTS_MEMORY      Directly conflicts with established memory entry
  DEPENDENCY_UNRESOLVED   Requires another candidate in this batch first
  EVAL_REGRESSION_RISK    Similar past changes correlated with metric decline
  LOW_SIGNAL              signal_strength < 0.4
  SOURCE_NEW              source_reliability_score is default (0.5)
  STUCK_CANDIDATE         prior_appearances > 2
  ALREADY_APPLIED         Candidate appears to duplicate an existing change_log entry

ESCALATION
Set escalation_required: true when:
  - Any candidate has HIGH_VARIANCE + CONTRADICTS_MEMORY simultaneously
  - Confidence distribution across the batch is flat (no candidate clears 0.70)
  - Eval history shows regression in last 2 eval cycles
  - More than 3 candidates defer on the same unresolved condition

CROSS-BATCH AWARENESS
After evaluating all candidates individually, write session_notes covering:
  - Patterns across the candidate set
  - Dependency graph among candidates
  - Any signal about the digest pipeline itself

OUTPUT FORMAT
Respond with a reasoning scratchpad followed by the JSON decision record.

Format your response as:

<reasoning>
[Per-candidate thinking, each labeled with candidate fingerprint and summary]
[Cross-batch observations at the end]
</reasoning>

<decision_record>
{
  "session_id": "(copy from input payload)",
  "engine_version": "1.0.0",
  "model": "claude-opus-4-5",
  "evaluated_at": "(current ISO8601 timestamp)",
  "memory_snapshot_hash": "(copy from input payload)",
  "input_candidate_count": (integer),
  "decisions": [
    {
      "candidate_id": "(id field from candidate)",
      "fingerprint": "(fingerprint field from candidate)",
      "candidate_summary": "(your restatement of what this proposes)",
      "decision": "apply|skip|defer",
      "confidence": 0.0,
      "reasoning": {
        "signal_assessment": "string",
        "memory_consistency": "string",
        "eval_alignment": "string",
        "risk_assessment": "string"
      },
      "hypothesis": {
        "id": "(generate a new UUID v4)",
        "prediction": "string",
        "metric": "string",
        "expected_direction": "increase|decrease|no_change",
        "expected_magnitude": "string",
        "eval_window_days": 14,
        "falsification_condition": "string",
        "outcome": null,
        "outcome_recorded_at": null
      },
      "risk_flags": [],
      "dependencies": [],
      "defer_condition": null,
      "defer_until": null
    }
  ],
  "apply_count": 0,
  "skip_count": 0,
  "defer_count": 0,
  "session_notes": "string",
  "escalation_required": false,
  "escalation_reason": null
}
</decision_record>

The reasoning scratchpad is auditable output. Write it as if someone will
read it when a hypothesis fails."""

# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

def build_user_message(payload: dict) -> str:
    """Serialises the assembler payload as the user turn for Opus."""
    return (
        "Here is the CLAIRE-A input payload for this session. "
        "Evaluate all candidates and produce the decision record.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )

# ---------------------------------------------------------------------------
# RESPONSE PARSER
# ---------------------------------------------------------------------------

def parse_response(text: str) -> tuple[str, dict | None]:
    """Extracts <reasoning> and <decision_record> blocks from Opus response.

    Returns (reasoning_text, decision_dict).
    decision_dict is None if JSON parsing fails.
    """
    reasoning_match = re.search(
        r"<reasoning>(.*?)</reasoning>",
        text, re.DOTALL
    )
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    record_match = re.search(
        r"<decision_record>(.*?)</decision_record>",
        text, re.DOTALL
    )

    if not record_match:
        log.error("No <decision_record> block found in response")
        return reasoning, None

    raw_json = record_match.group(1).strip()
    # Strip any accidental markdown fences
    raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json)
    raw_json = re.sub(r"\s*```$", "", raw_json)

    try:
        record = json.loads(raw_json)
        return reasoning, record
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse decision_record JSON: {e}")
        log.debug(f"Raw JSON attempt:\n{raw_json[:500]}")
        return reasoning, None

# ---------------------------------------------------------------------------
# OUTPUT WRITER
# ---------------------------------------------------------------------------

def write_outputs(
    session_id: str,
    reasoning: str,
    decision_record: dict | None,
    raw_response: str,
    usage: object,
) -> tuple[Path, Path]:
    """Writes reasoning scratchpad and decision record to data/."""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Reasoning scratchpad â€” plain text, human-readable audit trail
    reasoning_path = DATA_DIR / f"claire_a_reasoning_{ts}.txt"
    with open(reasoning_path, "w", encoding="utf-8") as f:
        f.write(f"CLAIRE-A Reasoning Scratchpad\n")
        f.write(f"Session: {session_id}\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
        f.write("=" * 72 + "\n\n")
        f.write(reasoning if reasoning else "[No reasoning block extracted]")
    log.info(f"Reasoning written â†’ {reasoning_path.name}")

    # Decision record â€” structured JSON
    decisions_path = DATA_DIR / f"claire_a_decisions_{ts}.json"
    output = {
        "_meta": {
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "session_id":     session_id,
            "model":          DECISION_ENGINE_MODEL,
            "input_tokens":   getattr(usage, "input_tokens", None),
            "output_tokens":  getattr(usage, "output_tokens", None),
            "parse_success":  decision_record is not None,
        },
        "decision_record": decision_record,
        "raw_response":    raw_response if decision_record is None else None,
    }

    with open(decisions_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    log.info(f"Decision record written â†’ {decisions_path.name}")

    return reasoning_path, decisions_path

# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# SESSION HISTORY WRITER
# ---------------------------------------------------------------------------

def update_session_history(
    session_id: str,
    payload: dict,
    decision_record: dict | None,
) -> None:
    """Writes fingerprint appearances and last decision to the session history.

    Called after every successful run â€” even if the decision record parse
    failed (in which case decisions are unknown but appearances still count).

    The assembler reads this file on the next run to resolve prior_appearances.
    """
    # Load existing history
    if SESSION_HISTORY_PATH.exists():
        with open(SESSION_HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    now = datetime.now(timezone.utc).isoformat()

    # Build fingerprint -> decision map from this session
    decision_map = {}
    if decision_record:
        for d in decision_record.get("decisions", []):
            fp = d.get("fingerprint")
            if fp:
                decision_map[fp] = d.get("decision")

    # Update history for every candidate that appeared in this session
    for candidate in payload.get("candidates", []):
        fp = candidate.get("fingerprint")
        if not fp:
            continue

        if fp not in history:
            history[fp] = {
                "appearances":    0,
                "first_seen":     now,
                "last_seen":      now,
                "last_decision":  None,
                "sessions":       [],
            }

        entry = history[fp]
        entry["appearances"] += 1
        entry["last_seen"]    = now
        entry["last_decision"] = decision_map.get(fp, entry["last_decision"])

        if session_id not in entry["sessions"]:
            entry["sessions"].append(session_id)

    with open(SESSION_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    total_fingerprints = len(history)
    updated = len(payload.get("candidates", []))
    log.info(
        f"Session history updated â€” {updated} fingerprints this session, "
        f"{total_fingerprints} total tracked"
    )


def run(input_path: Path, dry_run: bool = False) -> None:
    log.info("â”€â”€ CLAIRE-A Decision Engine Runner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    log.info(f"Input: {input_path.name}")
    log.info(f"Model: {DECISION_ENGINE_MODEL}")

    with open(input_path, encoding="utf-8") as f:
        payload = json.load(f)

    session_id       = payload.get("session_id", "unknown")
    candidate_count  = len(payload.get("candidates", []))

    log.info(f"Session ID: {session_id}")
    log.info(f"Candidates to evaluate: {candidate_count}")

    if dry_run:
        log.info("DRY RUN â€” skipping Opus call. Input payload looks valid.")
        log.info("â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        return

    client       = anthropic.Anthropic()
    user_message = build_user_message(payload)

    log.info("Calling Opus â€” this may take 30â€“90 seconds for 15 candidatesâ€¦")

    response = client.messages.create(
        model=DECISION_ENGINE_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text
    usage    = response.usage

    log.info(f"Response received â€” {usage.input_tokens} in / {usage.output_tokens} out tokens")

    reasoning, decision_record = parse_response(raw_text)

    # Inject source field into each decision from the input payload.
    # The scorer uses this to key the reliability ledger by track.
    if decision_record:
        candidate_source_map = {
            c["id"]: c.get("source", "unknown")
            for c in payload.get("candidates", [])
        }
        for d in decision_record.get("decisions", []):
            d["source"] = candidate_source_map.get(d.get("candidate_id"), "unknown")

    if decision_record:
        apply_count = decision_record.get("apply_count", 0)
        skip_count  = decision_record.get("skip_count", 0)
        defer_count = decision_record.get("defer_count", 0)
        escalation  = decision_record.get("escalation_required", False)
        log.info(f"Decisions: {apply_count} apply / {skip_count} skip / {defer_count} defer")
        if escalation:
            log.warning(f"ESCALATION REQUIRED: {decision_record.get('escalation_reason', '')}")
    else:
        log.error("Decision record parse failed â€” raw response saved for inspection")

    reasoning_path, decisions_path = write_outputs(
        session_id, reasoning, decision_record, raw_text, usage
    )

    # Write session history â€” always, even on parse failure
    update_session_history(session_id, payload, decision_record)

    log.info("â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    log.info(f"Complete. Review: {decisions_path.name}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _latest_input_file() -> Path | None:
    """Finds the most recent claire_a_input_*.json in data/."""
    files = sorted(DATA_DIR.glob("claire_a_input_*.json"), reverse=True)
    return files[0] if files else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLAIRE-A Decision Engine Runner")
    parser.add_argument(
        "--input", type=Path, default=None,
        help="Path to assembler input JSON (default: most recent in data/)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate input without calling Opus"
    )
    args = parser.parse_args()

    input_path = args.input
    if input_path is None:
        input_path = _latest_input_file()
        if input_path is None:
            log.error("No input file found in data/. Run claire_a_assembler.py first.")
            raise SystemExit(1)
        log.info(f"Auto-selected most recent input: {input_path.name}")

    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        raise SystemExit(1)

    run(input_path=input_path, dry_run=args.dry_run)
