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

Cycle 3 complete (2026-05-10). 1 memory edit applied, hallucination-guard skill installed.
change_log.json and friction_log.txt created (were missing — now initialized with full history).

**Applied this cycle:**
- Memory #18: sycophantic hallucination guard (don't defend before verifying)
- Skill: hallucination-guard installed to skills/user/hallucination-guard/SKILL.md

**Queued profile diffs (apply manually — see change_log.json):**
- c3-prof-001: AUDIT mode enhancement (no observation gate — apply at next profile review)
- c3-prof-002: Task-completion anti-collapse (observe 4.7 in live session first)
- c3-prof-003: Effort transparency disclosure (observe 4.7 in live session first)

**CLAIRE-A graduation criteria (cycle 1 of 6):**
- Consecutive eval runs logged: 1 of 6 required
- Reliability ledger hypotheses scored: 7 of 10 required
- Escalations in last 3 runs: 0 (clean)
- Next eval cycle: 2026-05-17

**Build 8 candidates (design in browser Project first):**
- Same-day memory filtering in triage (CLAIRE-A flagged redundancy — c3 friction log)
- Technique candidates separate output stream in digest
- Cost log merge (two entries per run)
- X/Twitter + Substack RSS ingest sources
- Track A cost trajectory monitoring (approaching $0.60-0.70/run)
- feature_praise signal utilization audit (c3 friction log)

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
10. **Score hypotheses before applying deferred candidates** — eval data should inform the next batch

---

## Browser Project

All architecture, prompt design, and build scaffolding lives in the
Claude browser Project named CLAIRE. When in doubt about a design
decision, stop and check the browser Project before proceeding.

Do not make architectural decisions in Cowork. Execute, report, repeat.

---

## Commit Convention

```
git add .
git commit -m "CLAIRE Build [N] [description]"
```

Examples:
- `CLAIRE Build 1 complete — 520 post clean corpus`
- `CLAIRE Build 2 dry-run validated — triage running`
- `CLAIRE Build 2 complete — synthesis queues written`

---
*Last updated: 2026-05-10 — Cycle 3 complete, Build 8 candidates queued, change_log.json + friction_log.txt initialized*
