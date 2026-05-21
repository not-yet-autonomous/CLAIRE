# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Shared utilities
compute_cost:     Calculate API call cost from token usage and pricing config.
append_cost_log:  Persist run cost data to data/cost_log.json.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
COST_LOG_PATH = DATA_DIR / "cost_log.json"

log = logging.getLogger("claire.utils")


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


def append_cost_log(run_id: str,
                    triage_data: dict,
                    synthesis_data: dict,
                    posts_processed: int) -> None:
    """
    Append a run entry to data/cost_log.json.
    If the file is missing or corrupt, starts fresh.
    Updates meta totals and writes back with indent=2.

    triage_data format:
        {"model": str, "input_tokens": int, "output_tokens": int,
         "cost_usd": float, "batches": int}
    synthesis_data format:
        {"model": str, "tracks": {"a": {...}, "b": {...}, "c": {...}},
         "total_cost_usd": float}
    """
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

    total_run_cost = round(
        triage_data.get("cost_usd", 0.0) +
        synthesis_data.get("total_cost_usd", 0.0),
        4
    )

    run_entry = {
        "run_id":          run_id,
        "run_at":          datetime.now(timezone.utc).isoformat(),
        "posts_processed": posts_processed,
        "triage":          triage_data,
        "synthesis":       synthesis_data,
        "total_cost_usd":  total_run_cost,
    }

    existing["runs"].append(run_entry)
    existing["meta"]["total_runs"]          = len(existing["runs"])
    existing["meta"]["cumulative_cost_usd"] = round(
        existing["meta"].get("cumulative_cost_usd", 0.0) + total_run_cost, 4
    )
    existing["meta"]["last_updated"] = run_entry["run_at"]

    with open(COST_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    log.info(
        f"Cost log updated — run: ${total_run_cost:.4f} | "
        f"cumulative: ${existing['meta']['cumulative_cost_usd']:.4f}"
    )
