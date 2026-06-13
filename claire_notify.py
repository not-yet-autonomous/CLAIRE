# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Build 8: Pushover Notification
Reads pipeline artifacts from the current run and sends a Pushover
notification with PDF digest attached (or a text fallback if the PDF
is missing or oversized).

Environment variables consumed:
  DIGEST_DATE         — date string matching the PDF filename (YYYY-MM-DD)
  PUSHOVER_APP_TOKEN  — Pushover application token
  PUSHOVER_USER_KEY   — Pushover user/group key
  GITHUB_SHA          — commit SHA (set automatically by GHA)
  GITHUB_REPOSITORY   — owner/repo (set automatically by GHA)
  GITHUB_SERVER_URL   — e.g. https://github.com (set automatically by GHA)

Run (GitHub Actions): called by claire_weekly.yml notify step
Run (local test):     set env vars manually then python claire_notify.py
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR         = Path(__file__).parent
DATA_DIR         = BASE_DIR / "data"
OUTPUT_DIR       = BASE_DIR / "output"
CONFIG_PATH      = BASE_DIR / "config.json"

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PDF_SIZE_LIMIT   = 2_500_000   # 2.5 MB — Pushover attachment ceiling

# Cycle identity is owned by config (config.pipeline.current_cycle), never the
# change log. The applied-count queries change_log only for the count, scoped
# to that cycle. APPLIED_ACTIONS are actions executed against live config;
# 'queued' (proposed, not applied) is excluded.
APPLIED_ACTIONS  = frozenset({"add", "apply", "modify", "retire"})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("claire.notify")


# ─────────────────────────────────────────────────────────────────────────────
# DATA READERS
# ─────────────────────────────────────────────────────────────────────────────

def read_latest_run_cost() -> float:
    """Return total_cost_usd from the most recent cost_log.json entry."""
    path = DATA_DIR / "cost_log.json"
    if not path.exists():
        log.warning("cost_log.json not found — cost will show as 0.000")
        return 0.0
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        runs = data.get("runs", [])
        if not runs:
            return 0.0
        # Runs are appended chronologically; last entry is most recent.
        return float(runs[-1].get("total_cost_usd", 0.0))
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.error(f"Failed to parse cost_log.json: {e}")
        return 0.0


def read_cycle_number() -> int:
    """Return cycle identity from config.pipeline.current_cycle — the sole
    source of cycle identity. Never derived from change_log.

    Cycle identity is owned by config. If the key is missing or unreadable,
    fail loudly rather than fall back to a change_log-derived value: a silent
    wrong cycle title is the exact failure this removes.
    """
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        return int(cfg["pipeline"]["current_cycle"])
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        log.error(
            f"Cannot read config.pipeline.current_cycle — cycle identity "
            f"unavailable, refusing to send a mistitled notification: {e}"
        )
        raise SystemExit(1)


def read_graduation_run_count() -> int:
    """Return count of distinct CLAIRE-A session IDs logged in session_history.

    Session history is a flat dict keyed by candidate fingerprint. Each
    value includes a 'sessions' list of session UUIDs for that fingerprint.
    The graduation run count is the number of unique session IDs across all
    fingerprints — each session represents one full engine run.
    """
    path = DATA_DIR / "claire_a_session_history.json"
    if not path.exists():
        log.warning("claire_a_session_history.json not found — A-runs will show as 0")
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        unique_sessions: set = set()
        for entry in data.values():
            if isinstance(entry, dict):
                for sid in entry.get("sessions", []):
                    unique_sessions.add(sid)
        return len(unique_sessions)
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        log.error(f"Failed to parse claire_a_session_history.json: {e}")
        return 0


def count_candidates(cycle: int) -> tuple[int, int]:
    """Return (total_candidates, applied_count).

    `cycle` is the identity from read_cycle_number() (config-owned). The applied
    count queries change_log ONLY for the count, scoped to that cycle and to
    actions executed against live config (APPLIED_ACTIONS). Zero is a legal
    result — a cycle with no applied entries returns 0, never a fallback.
    """
    total    = 0
    applied  = 0

    # Count candidates across all three tracks
    for track in ("a", "b", "c"):
        cpath = DATA_DIR / f"candidates_track_{track}.json"
        if not cpath.exists():
            continue
        try:
            with open(cpath, encoding="utf-8") as f:
                data = json.load(f)
            cands = data.get("candidates", {})
            # Each track has different top-level keys; count all list values
            for v in cands.values():
                if isinstance(v, list):
                    total += len(v)
        except (json.JSONDecodeError, TypeError):
            pass

    # Count applied from change_log (current cycle)
    clog_path = BASE_DIR / "change_log.json"
    if clog_path.exists():
        try:
            with open(clog_path, encoding="utf-8") as f:
                data = json.load(f)
            changes = data.get("changes", [])
            applied = sum(
                1 for c in changes
                if int(c.get("cycle", 0)) == cycle
                and c.get("action") in APPLIED_ACTIONS
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return total, applied


# ─────────────────────────────────────────────────────────────────────────────
# PUSHOVER SENDER
# ─────────────────────────────────────────────────────────────────────────────

def build_message(
    cycle:      int,
    date_str:   str,
    candidates: int,
    applied:    int,
    cost:       float,
    a_runs:     int,
    commit_url: str,
) -> tuple[str, str]:
    """Return (title, body) for the Pushover message."""
    title = f"CLAIRE Cycle {cycle} — {date_str}"
    body  = (
        f"Candidates: {candidates} | Applied: {applied} | "
        f"Cost: ${cost:.3f} | A-runs: {a_runs}/6\n"
        f"{commit_url}"
    )
    return title, body


def post_with_attachment(
    token:    str,
    user:     str,
    title:    str,
    message:  str,
    pdf_path: Path,
) -> None:
    """POST to Pushover with PDF attached as multipart/form-data."""
    log.info(f"Attaching PDF: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")
    with open(pdf_path, "rb") as pdf_file:
        resp = requests.post(
            PUSHOVER_API_URL,
            data={
                "token":   token,
                "user":    user,
                "title":   title,
                "message": message,
            },
            files={
                "attachment": (pdf_path.name, pdf_file, "application/pdf"),
            },
            timeout=30,
        )
    resp.raise_for_status()
    result = resp.json()
    if result.get("status") != 1:
        raise RuntimeError(f"Pushover returned non-1 status: {result}")
    log.info(f"Pushover notification sent with attachment (request={result.get('request')})")


def post_text_only(
    token:   str,
    user:    str,
    title:   str,
    message: str,
) -> None:
    """POST to Pushover as plain text (no attachment)."""
    resp = requests.post(
        PUSHOVER_API_URL,
        data={
            "token":   token,
            "user":    user,
            "title":   title,
            "message": message,
        },
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("status") != 1:
        raise RuntimeError(f"Pushover returned non-1 status: {result}")
    log.info(f"Pushover notification sent (text only, request={result.get('request')})")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Read environment ──────────────────────────────────────────────────────
    digest_date    = os.environ.get("DIGEST_DATE", "")
    app_token      = os.environ.get("PUSHOVER_APP_TOKEN", "")
    user_key       = os.environ.get("PUSHOVER_USER_KEY", "")
    github_sha     = os.environ.get("GITHUB_SHA", "local")
    github_repo    = os.environ.get("GITHUB_REPOSITORY", "")
    github_server  = os.environ.get("GITHUB_SERVER_URL", "https://github.com")

    missing = [k for k, v in {
        "DIGEST_DATE":         digest_date,
        "PUSHOVER_APP_TOKEN":  app_token,
        "PUSHOVER_USER_KEY":   user_key,
    }.items() if not v]

    if missing:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    log.info(f"claire_notify starting — digest_date={digest_date}")

    # ── Build commit URL ──────────────────────────────────────────────────────
    if github_repo and github_sha != "local":
        commit_url = f"{github_server}/{github_repo}/commit/{github_sha}"
    else:
        commit_url = f"local run — sha={github_sha}"

    # ── Collect stats ─────────────────────────────────────────────────────────
    cost      = read_latest_run_cost()
    cycle     = read_cycle_number()
    a_runs    = read_graduation_run_count()
    total_c, applied_c = count_candidates(cycle)

    log.info(
        f"Stats — cycle={cycle} candidates={total_c} applied={applied_c} "
        f"cost=${cost:.3f} a_runs={a_runs}"
    )

    # ── Build message ─────────────────────────────────────────────────────────
    title, body = build_message(
        cycle=cycle,
        date_str=digest_date,
        candidates=total_c,
        applied=applied_c,
        cost=cost,
        a_runs=a_runs,
        commit_url=commit_url,
    )

    log.info(f"Message title: {title}")
    log.info(f"Message body:  {body}")

    # ── Find PDF ──────────────────────────────────────────────────────────────
    pdf_path = OUTPUT_DIR / f"claire_digest_{digest_date}.pdf"
    use_attachment = False

    if pdf_path.exists():
        size = pdf_path.stat().st_size
        if size <= PDF_SIZE_LIMIT:
            use_attachment = True
            log.info(f"PDF found and within size limit ({size:,} bytes)")
        else:
            log.warning(
                f"PDF exceeds {PDF_SIZE_LIMIT:,} bytes ({size:,}) — "
                f"sending text-only notification"
            )
    else:
        log.warning(f"PDF not found at {pdf_path} — sending text-only notification")

    # ── Send ──────────────────────────────────────────────────────────────────
    try:
        if use_attachment:
            post_with_attachment(app_token, user_key, title, body, pdf_path)
        else:
            post_text_only(app_token, user_key, title, body)
    except requests.HTTPError as e:
        print(f"ERROR: Pushover HTTP error: {e}", file=sys.stderr)
        print(f"Response body: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"ERROR: Pushover request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    log.info("claire_notify complete.")


if __name__ == "__main__":
    main()
