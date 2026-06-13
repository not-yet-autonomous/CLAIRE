# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Official-signal ingest lane (capability-delta)

Proposal 1 from the 2026-06-13 design session. An authoritative Anthropic source,
SEPARATE from the HN/dev.to community-friction lane. The friction lane is
effect-based (how a model behaves); this lane is event-based (a model launched,
became default, changed tier, was deprecated/retired). Those discrete events
invalidate routing calls and arrive as announcements, not friction.

Pipeline position: a separate step before digest generation. It does NOT route
through claire_ingest's HN/dev.to path, the noise prefilter, or the 3-post
evidence threshold. n=1 authoritative source is sufficient for existence/default
claims. Output: capability-delta candidates -> data/candidates_capability_delta.json,
surfaced as their own digest section.

Sources (confirmed 2026-06-13; docs.anthropic.com -> platform.claude.com 301):
  ADD       release notes        prose; events extracted by Haiku
  WITHDRAW  model-deprecations   structured tables; events extracted by Haiku
Known gap: abrupt suspensions / access-loss are notified by email/status page and
do NOT appear in either source. Documented in HANDOFF as a known blind spot.

Gate (ratified 2026-06-13): block-level, not per-slot. An event intersects if its
model is in the routing DOMAIN the MODEL ROUTING block governs (any Opus/Sonnet/
Haiku/Fable/Mythos-class model that could occupy a routing slot), anchored to
change_log c8-prof-001 — EVEN IF no slot currently names that model. A per-slot
test would have stayed silent on the Fable launch, which is exactly the event the
lane exists to catch. profile_snapshot.txt is treated as stale (it still carries
the retired per-version preference) and is NOT used as the intersection source.

Run:  python claire_official_signal.py [--dry-run] [--fixture PATH]
"""

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
import anthropic

from claire_utils import atomic_write_json, compute_cost

# Required before anthropic.Anthropic() — the friction log records three separate
# incidents of a missing load_dotenv() causing silent auth failure. Not a fourth.
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CHANGE_LOG_PATH = BASE_DIR / "change_log.json"
CANDIDATES_PATH = DATA_DIR / "candidates_capability_delta.json"

try:
    with open(BASE_DIR / "config.json", encoding="utf-8") as _f:
        CONFIG = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    CONFIG = {}

# config['official_signal'] is authorized + written separately (locked-decision
# rule). These defaults let the lane build and be tested before that edit lands;
# once the block exists it becomes the source of truth.
_OS = CONFIG.get("official_signal", {})
ENABLED           = _OS.get("enabled", True)
RELEASE_NOTES_URL = _OS.get("release_notes_url",
                            "https://platform.claude.com/docs/en/release-notes/api")
DEPRECATIONS_URL  = _OS.get("deprecations_url",
                            "https://platform.claude.com/docs/en/docs/about-claude/model-deprecations")
SEEN_PATH         = DATA_DIR / _OS.get("seen_filename", "official_signal_seen.json")
EXTRACT_MODEL     = CONFIG.get("triage", {}).get("model", "claude-haiku-4-5-20251001")
MAX_EXTRACT_TOKENS = _OS.get("max_extract_tokens", 4096)
MAX_SOURCE_CHARS  = _OS.get("max_source_chars", 24000)

# Routing domain: model families that can occupy a slot the MODEL ROUTING block
# (change_log c8-prof-001) governs. Block-level membership, not slot naming.
ROUTING_DOMAIN_FAMILIES = frozenset({"opus", "sonnet", "haiku", "fable", "mythos"})
ROUTING_ANCHOR = "c8-prof-001"
_FAMILY_RE = re.compile(r"\b(opus|sonnet|haiku|fable|mythos)\b", re.IGNORECASE)

HTTP_HEADERS = {"User-Agent": "CLAIRE-official-signal/1.0 personal-use-signal-pipeline"}
HTTP_TIMEOUT = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("claire.official_signal")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# FETCH  (per-source HTTPError discipline per Build 14 — caller skips the lane)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_text(url: str) -> str:
    """GET url and return response text. Raises requests.HTTPError on 4xx/5xx so
    the caller can log-and-skip the lane without aborting the pipeline. requests
    follows 301s, so the docs.anthropic.com -> platform.claude.com move is handled.
    """
    resp = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.text


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION  (Haiku — prose/table -> discrete model events)
# ─────────────────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You extract DISCRETE MODEL LIFECYCLE EVENTS from an official Anthropic documentation page.

Return ONLY a JSON array (no prose, no code fences). Each element:
  {{"model_name": str, "event_sign": "ADD"|"WITHDRAW", "event_date": "YYYY-MM-DD", "raw_excerpt": str}}

event_sign:
  ADD       — a model is newly launched, OR an existing model becomes the default / moves to a higher tier.
  WITHDRAW  — a model is deprecated, retired, moved down a tier, suspended, or loses access.

Rules:
- Emit ONLY model lifecycle events. IGNORE API/SDK/parameter/feature/tooling changes that are not
  about a model's existence, default status, tier, or retirement (e.g. a new endpoint, a parameter
  deprecation, an SDK update, a docs change).
- A single announcement can yield MULTIPLE events. A launch that also deprecates a prior default is
  one ADD plus one WITHDRAW — emit each separately.
- event_date: ISO YYYY-MM-DD, the announcement or effective date stated in the source.
- raw_excerpt: a SHORT VERBATIM quote from the source supporting the event. Do not paraphrase or invent.
- model_name: the human-readable model name exactly as written (e.g. "Claude Opus 4.8", "Claude Fable 5").
- If there are no model lifecycle events, return [].

SOURCE PAGE:
{source}
"""


def _parse_json_array(raw: str) -> list:
    """Parse a JSON array from a model response, tolerating ```json fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        log.error(f"extraction returned non-JSON ({e}); body[:200]={text[:200]!r}")
        return []
    return data if isinstance(data, list) else []


def extract_events_from_source(text: str, source_url: str, client) -> tuple[list, float]:
    """Haiku-extract model events from one source page. Returns (events, cost_usd).
    Each event is tagged with source_url so candidate provenance is unambiguous.
    """
    if not text.strip():
        return [], 0.0
    prompt = EXTRACTION_PROMPT.format(source=text[:MAX_SOURCE_CHARS])
    resp = client.messages.create(
        model=EXTRACT_MODEL,
        max_tokens=MAX_EXTRACT_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    cost = compute_cost(EXTRACT_MODEL, resp.usage.input_tokens, resp.usage.output_tokens)
    # Code-review lesson: a max_tokens truncation surfaces downstream as a parse
    # failure. Check stop_reason explicitly and warn rather than fail silently.
    if resp.stop_reason == "max_tokens":
        log.warning(f"extraction hit max_tokens for {source_url} — event list may be incomplete")
    events = _parse_json_array(resp.content[0].text)
    for e in events:
        if isinstance(e, dict):
            e["source_url"] = source_url
    valid = [e for e in events if isinstance(e, dict) and e.get("model_name") and e.get("event_sign")]
    log.info(f"extracted {len(valid)} model events from {source_url} (cost ${cost:.4f})")
    return valid, cost


# ─────────────────────────────────────────────────────────────────────────────
# DEPRECATIONS TABLE  (deterministic regex — structured source, no LLM)
# ─────────────────────────────────────────────────────────────────────────────

_DEP_SECTION_RE = re.compile(r"(?m)^###\s+(\d{4}-\d{2}-\d{2})\s*:\s*.+?\s*$")
_DEP_ROW_RE     = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`(claude-[^`|]+)`\s*\|", re.MULTILINE)


def parse_deprecations(text: str, source_url: str) -> list:
    """Parse the model-deprecations page's dated history tables. Each deprecated-
    model row under a '### YYYY-MM-DD: ...' subsection becomes one WITHDRAW event.
    The table is structured, so this is exact and free — no LLM, no fabrication risk.
    (Prose-announced withdrawals, e.g. a suspension in the release notes, are caught
    by the Haiku release-notes pass instead and dedup against these by canonical model.)
    """
    events = []
    sections = list(_DEP_SECTION_RE.finditer(text))
    for i, sec in enumerate(sections):
        date = sec.group(1)
        end  = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        body = text[sec.end():end]
        for row in _DEP_ROW_RE.finditer(body):
            retire_date = row.group(1).strip()
            model_id    = row.group(2).strip()
            events.append({
                "model_name":  model_id,
                "event_sign":  "WITHDRAW",
                "event_date":  date,
                "source_url":  source_url,
                "raw_excerpt": f"`{model_id}` deprecated (announced {date}; retirement {retire_date}).",
            })
    log.info(f"parsed {len(events)} WITHDRAW events from deprecations table (regex, no API)")
    return events


# ─────────────────────────────────────────────────────────────────────────────
# DEDUP  (seen-events memory across runs — data/official_signal_seen.json)
# ─────────────────────────────────────────────────────────────────────────────

def _canonical_model(name: str) -> str:
    """Collapse model-name variants to a dedup token: family + major.minor version.
    'Claude Opus 4.1' and 'claude-opus-4-1-20250805' both -> 'opus4.1', so the same
    withdrawal announced in release-notes prose and the deprecations table dedups to
    one event instead of two.
    """
    s    = (name or "").lower()
    fam  = _model_family(s)
    tail = s.split(fam, 1)[-1] if fam else s
    m    = re.search(r"\d+(?:[.\-]\d+)*", tail)
    ver  = ".".join(m.group(0).replace("-", ".").split(".")[:2]) if m else ""
    return f"{fam or ''}{ver}"


def event_key(e: dict) -> str:
    """Dedup key: (canonical model, event_sign, event_date)."""
    return "|".join([
        _canonical_model(e.get("model_name", "")),
        str(e.get("event_sign", "")).strip().upper(),
        str(e.get("event_date", "")).strip(),
    ])


def load_seen() -> set:
    if SEEN_PATH.exists():
        try:
            with open(SEEN_PATH, encoding="utf-8") as f:
                return set(json.load(f).get("seen", []))
        except (json.JSONDecodeError, OSError):
            log.warning(f"{SEEN_PATH.name} unreadable — starting with empty seen set")
    return set()


def save_seen(seen: set) -> None:
    atomic_write_json(SEEN_PATH, {"seen": sorted(seen), "updated_at": _now()})


# ─────────────────────────────────────────────────────────────────────────────
# TOUCH-TEST GATE  (block-level intersection; the core design constraint)
# ─────────────────────────────────────────────────────────────────────────────

def _model_family(model_name: str) -> str | None:
    m = _FAMILY_RE.search(model_name or "")
    return m.group(1).lower() if m else None


def load_change_log_index() -> list[dict]:
    """Return [{id, text}] for change_log intersection target (b)."""
    try:
        with open(CHANGE_LOG_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    index = []
    for c in d.get("changes", []):
        text = " ".join(str(c.get(k, "")) for k in ("target", "summary", "hypothesis", "source_signal"))
        index.append({"id": c.get("id", ""), "text": text})
    return index


def gate(event: dict, change_log_index: list[dict]) -> tuple[bool, str | None]:
    """Block-level intersection. Returns (passes, intersects_label).

    (a) routing domain: the event's model is in the family set the MODEL ROUTING
        block governs (block-level, anchored to c8-prof-001), regardless of whether
        any slot currently names it.
    (b) change_log: the event's model is referenced by an existing change_log entry.

    An event intersecting NEITHER generates no candidate (changelog-summarizer guard).
    """
    fam = _model_family(event.get("model_name", ""))
    if fam in ROUTING_DOMAIN_FAMILIES:
        return True, f"routing-block({ROUTING_ANCHOR})"
    name = (event.get("model_name", "") or "").strip().lower()
    if name:
        for entry in change_log_index:
            if entry["id"] and name in entry["text"].lower():
                return True, f"change_log:{entry['id']}"
    return False, None


# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE EMISSION  (provisional/confirmed tagging)
# ─────────────────────────────────────────────────────────────────────────────

def emit_candidate(event: dict, intersects: str) -> dict:
    """Build a capability-delta candidate from a gated event.

    authority_tag inherits the MODEL ROUTING basis rule: an authoritative source is
    confirmed for a model's EXISTENCE and DEFAULT/TIER status, but ANY quality
    implication is provisional until community signal on the verbosity/hallucination
    axis exists. routing_action makes explicit that a launch note never promotes a
    model into the planning/doc slot on its own — so the candidate cannot be read as
    a quality endorsement.
    """
    return {
        "type":          "capability-delta",
        "event_sign":    str(event.get("event_sign", "")).strip().upper(),
        "model_name":    event.get("model_name", ""),
        "event_date":    event.get("event_date", ""),
        "source_url":    event.get("source_url", ""),
        "intersects":    intersects,
        "authority_tag": "confirmed-existence",
        "quality_status": "provisional-quality",
        "routing_action": (
            "none — authoritative for existence/default only. A launch note does NOT "
            "promote a model into the planning/doc routing slot; promotion requires "
            "community confirmation on the verbosity/hallucination axis."
        ),
        "raw_excerpt":   event.get("raw_excerpt", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# LANE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def _write_output(payload: dict, dry_run: bool) -> dict:
    if dry_run:
        log.info(f"DRY RUN — would write {CANDIDATES_PATH.name}: {payload['meta']}")
    else:
        atomic_write_json(CANDIDATES_PATH, payload)
        log.info(f"wrote {CANDIDATES_PATH.name}: {payload['meta']}")
    return payload


def _status_payload(status: str, error: str | None = None) -> dict:
    meta = {"status": status, "run_at": _now(), "events": 0, "new": 0,
            "suppressed": 0, "candidates": 0, "cost_usd": 0.0}
    if error:
        meta["error"] = error
    return {"meta": meta, "candidates": []}


def run_lane(fixture_path: str | None = None, dry_run: bool = False) -> dict:
    """Fetch -> extract -> dedup -> gate -> emit. Non-fatal: any failure writes a
    status payload so the digest section can say what happened rather than vanish.
    """
    if not ENABLED:
        log.info("official_signal lane disabled in config — skipping")
        return _write_output(_status_payload("disabled"), dry_run)

    # ── Fetch (or load fixture) ──────────────────────────────────────────────
    try:
        if fixture_path:
            with open(fixture_path, encoding="utf-8") as f:
                payload = json.load(f)
            rn_text, dep_text = payload.get("release_notes", ""), payload.get("deprecations", "")
        else:
            rn_text  = fetch_text(RELEASE_NOTES_URL)
            dep_text = fetch_text(DEPRECATIONS_URL)
    except requests.HTTPError as e:
        log.error(f"official_signal fetch failed (HTTP) — lane unavailable this run: {e}")
        return _write_output(_status_payload("unavailable", str(e)), dry_run)
    except (OSError, json.JSONDecodeError) as e:
        log.error(f"official_signal source unreadable — lane unavailable this run: {e}")
        return _write_output(_status_payload("unavailable", str(e)), dry_run)

    # ── Extract: Haiku for prose release notes (ADD + prose-announced WITHDRAW),
    #    deterministic regex for the structured deprecations table (no API). ────
    client = anthropic.Anthropic()
    ev_rn, cost = extract_events_from_source(rn_text, RELEASE_NOTES_URL, client)
    ev_dep = parse_deprecations(dep_text, DEPRECATIONS_URL)
    events = ev_rn + ev_dep
    cost = round(cost, 4)

    # ── Dedup against seen-events memory ─────────────────────────────────────
    seen = load_seen()
    new_events = [e for e in events if event_key(e) not in seen]

    # ── Gate + emit ──────────────────────────────────────────────────────────
    change_log_index = load_change_log_index()
    candidates, suppressed = [], []
    for e in new_events:
        passes, intersects = gate(e, change_log_index)
        if passes:
            candidates.append(emit_candidate(e, intersects))
        else:
            suppressed.append(e)
            # Log every suppression so the lane's silence is auditable: "no events"
            # is distinguishable from "events, all correctly suppressed".
            log.info(f"SUPPRESSED off-domain event (no routing/change_log intersection): "
                     f"{e.get('model_name')!r} {e.get('event_sign')} {e.get('event_date')}")

    # ── Persist seen (emitted AND suppressed, so neither re-emits next run) ───
    if not dry_run:
        save_seen(seen | {event_key(e) for e in new_events})

    meta = {
        "status":     "ok",
        "run_at":     _now(),
        "events":     len(events),
        "new":        len(new_events),
        "suppressed": len(suppressed),
        "candidates": len(candidates),
        "cost_usd":   cost,
    }
    log.info(f"official_signal: {meta['events']} events, {meta['new']} new, "
             f"{meta['suppressed']} suppressed, {meta['candidates']} candidates, "
             f"${cost:.4f}")
    return _write_output({"meta": meta, "candidates": candidates}, dry_run)


def main():
    parser = argparse.ArgumentParser(description="CLAIRE official-signal lane")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing files")
    parser.add_argument("--fixture", help="Path to a captured source payload JSON "
                        "(keys: release_notes, deprecations) instead of fetching live")
    args = parser.parse_args()
    run_lane(fixture_path=args.fixture, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
