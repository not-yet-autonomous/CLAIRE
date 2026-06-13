# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
STEP 6 verification for claire_official_signal — the official-signal lane.

Two layers:
  * Deterministic (default): gate, dedup, and tag logic on constructed events.
    No API calls. Run: python tests/test_official_signal.py
  * Live extraction (opt-in): feeds the captured fixture through the Haiku
    extraction and asserts the three known events are emitted. Costs a few cents.
    Run: python tests/test_official_signal.py --live

Deterministic assertions cover the spec's gate-level, tag-level, and dedup bullets.
The block-level gate is the key one: a Fable event passes EVEN THOUGH no routing
slot names Fable — a per-slot test would have failed it.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import claire_official_signal as lane  # noqa: E402

RN  = lane.RELEASE_NOTES_URL
DEP = lane.DEPRECATIONS_URL

# The three design-session events (Fable/Mythos modelled per-model), plus an
# off-domain launch that must be suppressed.
EV_OPUS48_ADD = {"model_name": "Claude Opus 4.8", "event_sign": "ADD",
                 "event_date": "2026-05-28", "source_url": RN,
                 "raw_excerpt": "We've launched Claude Opus 4.8"}
EV_FABLE5_ADD = {"model_name": "Claude Fable 5", "event_sign": "ADD",
                 "event_date": "2026-06-09", "source_url": RN,
                 "raw_excerpt": "We've launched Claude Fable 5"}
EV_MYTHOS5_ADD = {"model_name": "Claude Mythos 5", "event_sign": "ADD",
                  "event_date": "2026-06-09", "source_url": RN,
                  "raw_excerpt": "alongside Claude Mythos 5"}
EV_FABLE5_WD = {"model_name": "Claude Fable 5", "event_sign": "WITHDRAW",
                "event_date": "2026-06-12", "source_url": RN,
                "raw_excerpt": "temporarily suspended Claude Fable 5"}
EV_OFFDOMAIN = {"model_name": "Claude Embed 2", "event_sign": "ADD",
                "event_date": "2026-06-01", "source_url": RN,
                "raw_excerpt": "We've launched Claude Embed 2, a new text embedding model"}

KNOWN_EVENTS = [EV_OPUS48_ADD, EV_FABLE5_ADD, EV_MYTHOS5_ADD, EV_FABLE5_WD]


def _results():
    passed, failed = [], []
    def check(name, cond):
        (passed if cond else failed).append(name)
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    return passed, failed, check


def test_gate_block_level():
    """All routing-domain events pass at BLOCK level; off-domain is suppressed."""
    print("\n[gate-level]")
    passed, failed, check = _results()
    index = lane.load_change_log_index()

    for ev in KNOWN_EVENTS:
        ok, label = lane.gate(ev, index)
        check(f"{ev['model_name']} {ev['event_sign']} intersects routing block",
              ok and label == f"routing-block({lane.ROUTING_ANCHOR})")

    # The decisive block-level assertion: Fable passes though no slot names it.
    ok_fable, _ = lane.gate(EV_FABLE5_ADD, index)
    check("Fable passes block-level despite no pre-existing Fable slot", ok_fable)

    # Off-domain (embedding model, not routing-slot-capable) is suppressed.
    ok_off, label_off = lane.gate(EV_OFFDOMAIN, index)
    check("off-domain Claude Embed 2 is suppressed (no intersection)",
          ok_off is False and label_off is None)
    return passed, failed


def test_tag_provisional():
    """Every candidate is confirmed-existence and cannot read as a quality endorsement."""
    print("\n[tag-level]")
    passed, failed, check = _results()
    for ev in KNOWN_EVENTS:
        c = lane.emit_candidate(ev, f"routing-block({lane.ROUTING_ANCHOR})")
        check(f"{ev['model_name']} {ev['event_sign']} authority_tag=confirmed-existence",
              c["authority_tag"] == "confirmed-existence")
        check(f"{ev['model_name']} {ev['event_sign']} quality is provisional, not endorsed",
              c["quality_status"] == "provisional-quality" and "does NOT" in c["routing_action"])
        check(f"{ev['model_name']} {ev['event_sign']} carries provenance",
              c["source_url"] and c["raw_excerpt"] and c["type"] == "capability-delta")
    return passed, failed


def test_dedup():
    """Second pass over the same events yields zero new."""
    print("\n[dedup]")
    passed, failed, check = _results()
    seen = set()
    new1 = [e for e in KNOWN_EVENTS if lane.event_key(e) not in seen]
    seen |= {lane.event_key(e) for e in new1}
    new2 = [e for e in KNOWN_EVENTS if lane.event_key(e) not in seen]
    check(f"first pass emits all {len(KNOWN_EVENTS)} events", len(new1) == len(KNOWN_EVENTS))
    check("second pass emits zero new events", len(new2) == 0)
    # ADD and WITHDRAW for the same model/date are distinct keys.
    check("Fable ADD and Fable WITHDRAW are distinct keys",
          lane.event_key(EV_FABLE5_ADD) != lane.event_key(EV_FABLE5_WD))
    return passed, failed


def _norm(s: str) -> str:
    """Markdown-tolerant normalization for the fabrication check."""
    return re.sub(r"\s+", " ", re.sub(r"[*`\\]", "", (s or "").lower())).strip()


def test_live_extraction():
    """Opt-in: Haiku on prose release notes + regex on the deprecations table.
    Asserts recall of the known events AND a fabrication check (every emitted event
    traces to the source). Costs a few cents."""
    print("\n[live extraction + fabrication]  (--live)")
    passed, failed, check = _results()
    import json
    import anthropic
    fixture = Path(__file__).resolve().parent / "fixture_official_signal.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    rn_text, dep_text = payload["release_notes"], payload["deprecations"]
    client = anthropic.Anthropic()
    ev_rn, _ = lane.extract_events_from_source(rn_text, RN, client)   # Haiku (prose)
    ev_dep   = lane.parse_deprecations(dep_text, DEP)                 # regex (table)
    events = ev_rn + ev_dep
    print(f"    release-notes (Haiku): {[(e['model_name'], e['event_sign'], e.get('event_date')) for e in ev_rn]}")
    print(f"    deprecations  (regex): {[(e['model_name'], e['event_sign'], e.get('event_date')) for e in ev_dep]}")

    # Recall — the design events.
    check("Opus 4.8 ADD extracted (release notes)",
          any("opus 4.8" in e["model_name"].lower() and e["event_sign"].upper() == "ADD" for e in ev_rn))
    check("Fable 5 ADD extracted (release notes)",
          any("fable 5" in e["model_name"].lower() and e["event_sign"].upper() == "ADD" for e in ev_rn))
    check("Mythos 5 ADD extracted (release notes)",
          any("mythos 5" in e["model_name"].lower() and e["event_sign"].upper() == "ADD" for e in ev_rn))
    # Corrected scope: the Fable June 12 suspension IS in scope (prose) and must be emitted.
    check("Fable 5 WITHDRAW extracted via release-notes prose (in scope, true positive)",
          any("fable 5" in e["model_name"].lower() and e["event_sign"].upper() == "WITHDRAW" for e in ev_rn))
    # Deprecations table -> WITHDRAW via regex, no LLM.
    check("Opus 4.1 WITHDRAW parsed from deprecations table (regex)",
          any("opus-4-1" in e["model_name"].lower() and e["event_sign"].upper() == "WITHDRAW" for e in ev_dep))

    # Fabrication check — every Haiku event's model name AND excerpt trace to source.
    src = _norm(rn_text)
    fab_bad = [e for e in ev_rn
               if _norm(e["model_name"]) not in src or _norm(e.get("raw_excerpt", "")) not in src]
    for e in fab_bad:
        print(f"    FABRICATION? {e['model_name']!r} excerpt not in source: {e.get('raw_excerpt')!r}")
    check("no fabricated release-notes events (model + excerpt trace to source)", not fab_bad)
    # Regex events are deterministic; the model id must appear in the deprecations source.
    dsrc = _norm(dep_text)
    check("regex WITHDRAW model ids trace to deprecations source",
          all(_norm(e["model_name"]) in dsrc for e in ev_dep))

    # Cross-source dedup: the same withdrawal in prose + table collapses to one key.
    check("canonical dedup collapses model-name variants",
          lane._canonical_model("Claude Opus 4.1") == lane._canonical_model("claude-opus-4-1-20250805"))

    # Off-domain Embed 2 (if Haiku extracted it) is suppressed by the gate.
    index = lane.load_change_log_index()
    embed = [e for e in events if "embed" in e["model_name"].lower()]
    if embed:
        ok, _ = lane.gate(embed[0], index)
        check("off-domain Embed 2 suppressed by gate", ok is False)
    return passed, failed


def main():
    live = "--live" in sys.argv
    suites = [test_gate_block_level, test_tag_provisional, test_dedup]
    if live:
        suites.append(test_live_extraction)
    all_passed, all_failed = [], []
    for suite in suites:
        p, f = suite()
        all_passed += p
        all_failed += f
    print(f"\n==== {len(all_passed)} passed, {len(all_failed)} failed ====")
    if all_failed:
        print("FAILURES:", all_failed)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
