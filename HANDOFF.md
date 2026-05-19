 # CLAIRE — Session Handoff
> Read this first. Every session. No exceptions.

---

## Machine Context

| Item | Value |
|------|-------|
| Project root | `C:\Users\<redacted>\OneDrive\Claude Projects\CLAIRE` |
| Python | `python` (via .venv) |
| Pip | `python -m pip` |
| Venv activate (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Venv activate (CMD/bat) | `.\.venv\Scripts\activate.bat` |
| Git | initialized, local only, no remote |
| Execution policy | RemoteSigned (already set) |

---

## Session Start Checklist

Run these three lines at the start of every Cowork session before
doing anything else:

```powershell
cd "C:\DEV\CLAIRE"
.\.venv\Scripts\Activate.ps1
python -c "import anthropic, requests; print('Deps OK')"
```

Expected output: `(.venv)` in prompt + `Deps OK`
If venv fails: use `.\.venv\Scripts\activate.bat` instead
If deps fail: `python -m pip install -r requirements.txt`

---

## Directory Structure

```
CLAIRE\
├── claire_ingest.py          ✅ Build 7 — dev.to practitioner feed added (Reddit + HN + dev.to)
├── claire_triage.py          ✅ Build 2 — triage complete
├── claire_synthesize.py      ✅ Build 5 — fingerprints + change_target field added
├── claire_output.py          ✅ Build 3 — digest generation
├── claire_a_assembler.py     ✅ Build 5 — CLAIRE-A input assembler
├── claire_a_runner.py        ✅ Build 5 — decision engine runner (Opus)
├── claire_a_scorer.py        ✅ Build 5/6 — eval scoring layer (Sonnet)
├── config.json               ✅ Pipeline config — locked decisions
├── requirements.txt          ✅ requests, anthropic, python-dotenv
├── .env                      ✅ ANTHROPIC_API_KEY (never touch)
├── .gitignore                ✅ Secrets and data excluded
├── HANDOFF.md                ✅ This file
├── claire_weekly.ps1         ✅ Build 6 — scheduled pipeline wrapper (CLAIRE + CLAIRE-A)
├── .git\                     ✅ Local git, no remote
├── data\
│   ├── raw_posts.json        ✅ 520 posts — clean corpus
│   ├── friction_log.txt      ✅ Weekly friction notes (human-maintained)
│   ├── change_log.json       ✅ Applied changes + eval loop
│   ├── memory_edits_snapshot.txt  ✅ Current Claude memory baseline
│   ├── tagged_posts.json     ✅ Build 2 output — 520 posts tagged
│   ├── synthesis_queue_track_a.json  ✅ Build 2 output — 148 posts
│   ├── synthesis_queue_track_b.json  ✅ Build 2 output — 5 posts
│   ├── synthesis_queue_track_c.json  ✅ Build 2 output — 8 posts
│   ├── archive.json          ✅ Build 2 output — Accumulates LOW-confidence posts across weekly runs. Empty = all Build 2 posts were HIGH/MEDIUM. Revisit size quarterly.
│   ├── claire_a_input_[timestamp].json     ✅ Build 5 — assembler output, engine input payload
│   ├── claire_a_decisions_[timestamp].json ✅ Build 5 — shadow decision record (Opus output)
│   ├── claire_a_reasoning_[timestamp].txt  ✅ Build 5 — auditable reasoning scratchpad
│   ├── claire_a_source_reliability.json    ✅ Build 6 — rolling source reliability scores (created on first scorer run)
│   └── claire_a_session_history.json       ✅ Build 6 — cross-run fingerprint tracking for prior_appearances
├── prompts\
│   ├── triage_prompt.txt     ✅ Haiku system prompt
│   ├── synthesis_prompts.py  ✅ Three Sonnet prompts
│   └── profile_intent_summary.txt  ✅ Injected into Track A + B
├── logs\
│   ├── ingest.log            ✅ Ingest run log (UTF-8, FileHandler)
│   └── triage.log            ✅ Build 2 output
├── output\                   ✅ Build 3 — weekly digest .docx (Section 6 = CLAIRE-A decisions)
├── skill_drafts\             ✅ Build 3 — SKILL.md skeletons
├── archive\                  ⬜ Quarterly review artifacts
└── docs\
    ├── claire_pipeline_flow.jsx   ✅ Decision flow diagram
    └── reddit_app_setup.md        ✅ Reddit API reference
```

---

## Build Status

| Build | File | Status | Notes |
|-------|------|--------|-------|
| 0 | Infrastructure | ✅ Complete | Config, prompts, eval files |
| 1 | `claire_ingest.py` | ✅ Complete | 520 post clean corpus in raw_posts.json |
| 2 | `claire_triage.py` | ✅ Complete | 520 posts triaged — A:148 B:5 C:8 routed |
| 3 | `claire_synthesize.py` | ✅ Complete | File delivered; Build 4 parallelized tracks |
| 4 | `claire_synthesize.py` | ✅ Complete | Parallel synthesis via ThreadPoolExecutor — commit c8a6272 |
| 3 | `claire_output.py` | ✅ Complete | Digest generation — duplicate main block removed |
| 4 | `claire_utils.py` | ✅ Complete | Shared compute_cost, append_cost_log |
| 4 | `cost_log.json` | ✅ Complete | Cost tracking confirmed working |
| 4 | config externalization | ✅ Complete | HN terms, signal map moved to config |
| 4 | Exception handling | ✅ Complete | All bare reads protected |
| 4 | ThreadPoolExecutor | ✅ Complete | Synthesis tracks parallelized |
| 4 | Keyword filter | ✅ Complete | Opus posts excluded at triage |
| 4 | Track A batching | ✅ Complete | Signal cluster batching, max_batch=50 |
| 5 | `claire_synthesize.py` | ✅ Complete | Fingerprint injection + change_target field |
| 5 | `claire_a_assembler.py` | ✅ Complete | Reads candidates + change_log, builds engine payload |
| 5 | `claire_a_runner.py` | ✅ Complete | Opus decision engine, shadow log writer |
| 5 | `claire_a_scorer.py` | ✅ Complete | Sonnet eval scorer, reliability ledger |
| 6 | `claire_a_runner.py` | ✅ Complete | Session history writer added |
| 6 | `claire_a_assembler.py` | ✅ Complete | Full prior_appearances from session history |
| 6 | `claire_output.py` | ✅ Complete | Section 6 added — CLAIRE-A decisions in digest |
| 6 | `claire_weekly.ps1` | ✅ Complete | Scheduled wrapper with per-script exit checks |
| 7 | `claire_ingest.py` | ✅ Complete | dev.to feed added — tags: anthropic, claudeai, claude |
| 7 | `claire_weekly.ps1` | ✅ Complete | --source all flag added |

---

## Locked Pipeline Decisions

| Decision | Value |
|----------|-------|
| Config injection | Partial (intent summary + memory list) |
| Developer persona | Filter out entirely |
| Hypothesis authorship | Human-written |
| Evidence threshold | 3 corroborating posts minimum |
| Triage model | claude-haiku-4-5-20251001 |
| Synthesis model | claude-sonnet-4-6 |
| Noise prefilter | score < 5 AND comments < 2 → drop |
| Scheduling | Windows Task Scheduler, weekly Sunday |
| Cost log entries | Two per run (triage + synthesis separate) — merge TBD |
| Opus exclusion | exclude_keywords in config.json — config-driven |
| Shared utilities | claire_utils.py — home for all cross-script helpers |
| Track A batching | Signal cluster by signal_type, max 50 posts per call |
| track_a_max_batch | 50 — tunable in config.json under "synthesis" |
| CLAIRE-A mode | Shadow only — reads everything, writes nothing to live config |
| Decision engine model | claude-opus-4-5 |
| Eval scoring model | claude-sonnet-4-6 |
| Batch size ceiling | 15 candidates per decision engine run |
| Signal strength | Source-post-weighted within confidence tier (HIGH: 0.80–0.90, MEDIUM: 0.55–0.65) |
| Hypothesis authorship | Decision engine (Opus) — all three decision types require one |
| Eval window | 14d (format/behavior changes), 21d (behavioral/memory changes) |
| Ingest sources | Reddit (native + search) + HackerNews + dev.to (--source all) |
| dev.to tags | anthropic, claudeai, claude |
| dev.to min reactions | 5 (raise from 2 after Build 7 validation) |
| dev.to pages per tag | 2 (60 candidates per tag before dedup) |

---

## Known Issues

| Issue | Detail |
|-------|--------|
| Opus filter log count | Reports against full corpus not just new posts — misleading log line, triage behavior correct |

---

## Current Session Task

Cycle 4 complete (2026-05-19). 6 memory edits applied (#19-24). 4 profile diffs queued. c3-prof-001 applied (overdue from Cycle 3).

**Applied this cycle:**
- Memory #19: Anthropic platform reliability as operational vendor risk
- Memory #20: Opus 4.6 preference for planning/doc outputs
- Memory #21: Never rewrite full docs on section edits
- Memory #22: Prompt injection flagging on external docs
- Memory #23: /compact before 50% context
- Memory #24: PDF-to-spreadsheet verification callout
- Profile c3-prof-001: AUDIT mode enhancement (applied, was queued from Cycle 3)

**Queued profile diffs (apply at next profile review session — no observation gates):**
- c4-prof-001: Surgical edit as default
- c4-prof-002: Tic suppression extends to functional equivalents
- c4-prof-003: HANDOFF mode
- c4-prof-004: Numerical self-consistency gate

**Still queued from Cycle 3 (observation gates not yet met):**
- c3-prof-002: Task-completion anti-collapse (needs live 4.7 session confirmation)
- c3-prof-003: Effort transparency disclosure (needs live 4.7 session confirmation)

**CLAIRE-A graduation criteria (cycle 2 of 6):**
- Consecutive eval runs logged: 2 of 6 required
- Reliability ledger hypotheses scored: update after scorer runs this cycle
- Escalations in last 3 runs: 0 (clean)
- Next eval cycle: 2026-05-26

**Friction log items for this cycle:**
- hallucination_guard skill not caught as ALREADY_APPLIED by engine — memory_state filtering gap now confirmed for skill installs, not just memory entries
- feature_praise at 107, second cycle with zero candidates — pipeline resolution still pending
- Digest candidates #23 and #27 were duplicates — add dedup check to Build 8 candidates
- Mem #3 (skip epistemic disclaimers) held — confirm in live session before applying

**Build 8 candidates (updated):**
- Same-day memory filtering in triage (now also covers skill installs)
- Duplicate candidate dedup before digest output
- Technique candidates separate output stream
- Cost log merge
- X/Twitter + Substack RSS ingest sources
- feature_praise signal utilization audit

---

## Key Rules for This Project

1. **Never hardcode credentials** — always via .env
2. **Never append to raw_posts.json** — always overwrite ("w" mode confirmed)
3. **Never run synthesis before triage completes**
4. **Never apply a config change without a human-written hypothesis**
5. **Always use `python -m pip`** not bare `pip`
6. **Always use PowerShell syntax** not bash
7. **Design decisions happen in browser Project** — execute only here
8. **Update this file** at the end of every build
9. **CLAIRE-A is shadow only** — never wire its output to live config without human review
10. **Score hypotheses before applying 