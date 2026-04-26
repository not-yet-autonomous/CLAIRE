# CLAIRE — Session Handoff
> Read this first. Every session. No exceptions.

---

## Machine Context

| Item | Value |
|------|-------|
| Project root | `C:\DEV\CLAIRE` |
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
├── claire_synthesize.py      🔄 Build 3 — synthesis (file pending)
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
│   └── archive.json          ✅ Build 2 output
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
| 3 | `claire_synthesize.py` | 🔄 In progress | Awaiting file from browser Project |
| 3 | `claire_output.py` | 🔄 In progress | Awaiting file from browser Project |

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

---

## Current Session Task

**Build 3 — Awaiting claire_synthesize.py from browser Project.**

Once the file is dropped into the project root:

```powershell
python claire_synthesize.py --dry-run
```

Review synthesis candidates before running full synthesis.
Do NOT run full synthesis until dry-run output is reviewed
in the browser Project.

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
*Last updated: 2026-04-25 — Build 2 complete, Build 3 in progress*
