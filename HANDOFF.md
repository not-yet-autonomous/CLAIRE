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
├── claire_ingest.py          ✅ Build 1 — ingestion
├── claire_triage.py          ✅ Build 2 — triage complete
├── claire_synthesize.py      ✅ Build 4 — parallel synthesis (3 tracks concurrent)
├── claire_output.py          🔄 Build 3 — digest generation (file pending)
├── config.json               ✅ Pipeline config — locked decisions
├── requirements.txt          ✅ requests, anthropic, python-dotenv
├── .env                      ✅ ANTHROPIC_API_KEY (never touch)
├── .gitignore                ✅ Secrets and data excluded
├── HANDOFF.md                ✅ This file
├── .venv\                    ✅ Virtual environment
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
│   └── archive.json          ✅ Build 2 output — Accumulates LOW-confidence posts across weekly runs. Empty = all Build 2 posts were HIGH/MEDIUM. Revisit size quarterly.
├── prompts\
│   ├── triage_prompt.txt     ✅ Haiku system prompt
│   ├── synthesis_prompts.py  ✅ Three Sonnet prompts
│   └── profile_intent_summary.txt  ✅ Injected into Track A + B
├── logs\
│   ├── ingest.log            ✅ Ingest run log (UTF-8, FileHandler)
│   └── triage.log            ✅ Build 2 output
├── output\                   ⬜ Build 3 — weekly digest .docx
├── skill_drafts\             ⬜ Build 3 — SKILL.md skeletons
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

---

## Known Issues

| Issue | Detail |
|-------|--------|
| Opus filter log count | Reports against full corpus not just new posts — misleading log line, triage behavior correct |

---

## Current Session Task

Build 4 complete. CLAIRE is in weekly steady state.

Open items:
- Cost log merge (two entries per run — design decision pending)
- Opus filter log line (cosmetic fix — reports full corpus count not new posts)

Run manually in order:

```powershell
python claire_ingest.py
python claire_triage.py
python claire_synthesize.py
python claire_output.py
```

Review digest: `output\CLAIRE_Weekly_Digest_[date].docx`

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
*Last updated: 2026-04-26 — Build 4 closed, Track A batching complete*
