# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Shared utilities
compute_cost:      Calculate API call cost from token usage and pricing config.
append_cost_log:   Persist run cost data to data/cost_log.json (one entry per run,
                   upserted by run_id — multiple callers in the same pipeline merge
                   into a single record).
atomic_write_json: Write JSON via temp file + os.replace so an interrupted
                   write never leaves a truncated file at the final path.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
COST_LOG_PATH = DATA_DIR / "cost_log.json"

log = logging.getLogger("claire.utils")


def atomic_write_json(path, obj, *, indent: int = 2, ensure_ascii: bool = True) -> None:
    """Write JSON atomically: dump to a temp file in the same directory,
    then os.replace() onto the final path.

    A direct open(path, "w") + json.dump leaves a truncated file if the
    write is interrupted — the OneDrive FUSE mount is a documented offender.
    os.replace() is atomic on the same filesystem, so readers see either
    the old complete file or the new complete file, never a partial write.
    """
    path = Path(path)
    tmp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=indent, ensure_ascii=ensure_ascii)
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in USD for a single API call.
    Reads pricing from CONFIG["api_pricing"] in config.json.
    Returns 0.0 if model is not found in pricing config.
    """
    try:
        with open(BASE_DIR / "config.json") as f:
            config = json.load(f)
        pricing = config.get("api_pricing", {}).get(model)
        if not pricing:
            log.warning(f"compute_cost: no pricing entry for model '{model}'")
            return 0.0
        return round(
            (input_tokens  / 1_000_000) * pricing["input_per_mtok"] +
            (output_tokens / 1_000_000) * pricing["output_per_mtok"],
            4
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        log.warning(f"compute_cost: config error — {e}")
        return 0.0


def _load_cost_alert_threshold() -> float:
    """Read track_a_cost_alert_usd from config.json. Default 0.65."""
    try:
        with open(BASE_DIR / "config.json") as f:
            config = json.load(f)
        return float(config.get("synthesis", {}).get("track_a_cost_alert_usd", 0.65))
    except Exception:
        return 0.65


def append_cost_log(
    run_id: str,
    triage_cost_usd: float = 0.0,
    synthesis_cost_usd: float = 0.0,
    assembler_cost_usd: float = 0.0,
    posts_processed: int = 0,
) -> dict:
    """Upsert one cost entry per run_id into data/cost_log.json.

    Multiple callers in the same pipeline run (triage, synthesis, assembler)
    should pass the same run_id — typically today's date (YYYYMMDD) — and
    each call accumulates its cost into the shared entry.

    Entry schema:
        {
          "run_id":              str  (ISO timestamp of first call),
          "triage_cost_usd":     float,
          "synthesis_cost_usd":  float,
          "assembler_cost_usd":  float,
          "total_cost_usd":      float,
          "track_a_alert":       bool,   # True if synthesis_cost >= threshold
          "posts_processed":     int,
          "last_updated":        str (ISO)
        }

    Returns the final entry dict after the upsert.
    """
    alert_threshold = _load_cost_alert_threshold()

    existing = {
        "meta": {
            "total_runs":          0,
            "cumulative_cost_usd": 0.0,
            "last_updated":        None,
        },
        "runs": [],
    }

    if COST_LOG_PATH.exists():
        try:
            with open(COST_LOG_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"cost_log.json unreadable ({e}) — starting fresh")

    # Find existing entry by run_id (upsert)
    now_iso = datetime.now(timezone.utc).isoformat()
    entry = None
    for run in existing["runs"]:
        if run.get("run_id") == run_id:
            entry = run
            break

    if entry is None:
        entry = {
            "run_id":             now_iso,       # ISO timestamp on first creation
            "_match_key":         run_id,         # internal key for upsert matching
            "triage_cost_usd":    0.0,
            "synthesis_cost_usd": 0.0,
            "assembler_cost_usd": 0.0,
            "total_cost_usd":     0.0,
            "track_a_alert":      False,
            "posts_processed":    0,
            "last_updated":       now_iso,
        }
        existing["runs"].append(entry)
    else:
        entry["last_updated"] = now_iso

    # Accumulate costs (non-zero values win over zeros so callers can pass
    # only their own slice without zeroing out other callers' data)
    if triage_cost_usd:
        entry["triage_cost_usd"] = round(
            entry["triage_cost_usd"] + triage_cost_usd, 4)
    if synthesis_cost_usd:
        entry["synthesis_cost_usd"] = round(
            entry["synthesis_cost_usd"] + synthesis_cost_usd, 4)
    if assembler_cost_usd:
        entry["assembler_cost_usd"] = round(
            entry["assembler_cost_usd"] + assembler_cost_usd, 4)
    if posts_processed:
        entry["posts_processed"] = max(entry["posts_processed"], posts_processed)

    entry["total_cost_usd"] = round(
        entry["triage_cost_usd"] +
        entry["synthesis_cost_usd"] +
        entry["assembler_cost_usd"],
        4
    )
    entry["track_a_alert"] = entry["synthesis_cost_usd"] >= alert_threshold

    # Update meta
    existing["meta"]["total_runs"] = len(existing["runs"])
    # Recompute cumulative from all entries
    existing["meta"]["cumulative_cost_usd"] = round(
        sum(r["total_cost_usd"] for r in existing["runs"]), 4
    )
    existing["meta"]["last_updated"] = now_iso

    atomic_write_json(COST_LOG_PATH, existing)

    alert_flag = " [TRACK A ALERT]" if entry["track_a_alert"] else ""
    log.info(
        f"Cost log updated (run_id={run_id}) — "
        f"triage=${entry['triage_cost_usd']:.4f} | "
        f"synthesis=${entry['synthesis_cost_usd']:.4f} | "
        f"assembler=${entry['assembler_cost_usd']:.4f} | "
        f"total=${entry['total_cost_usd']:.4f}{alert_flag}"
    )

    return entry
