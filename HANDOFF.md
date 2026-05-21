 # CLAIRE — Session Handoff
> Read this first. Every session. No exceptions.

---

## Machine Context

| Item | Value |
|------|-------|
| Project root | `C:\Users\<redacted>\OneDrive\Claude Projects\CLAIRE` |
| Python | `python` (via .venv) |
| Pip | `python -m pip` |
| Venv activate (PowerShell) | `.\.venv\Scripts\Activate.ps1` [local dev only] |
| Venv activate (CMD/bat) | `.\.venv\Scripts\activate.bat` [local dev only] |
| Git | initialized, remote on GitHub |
| Execution policy | RemoteSigned (already set) [local dev only] |
| CI/CD | GitHub Actions — `.github/workflows/claire_weekly.yml` |
| GHA trigger | Cron `0 14 * * 0` (Sundays 14:00 UTC) + `workflow_dispatch` |

---

## Session Start Checklist

**GitHub Actions runs require no manual start** — the pipeline triggers
automatically on the Sunday 14:00 UTC cron, or via `workflow_dispatch` in
the GitHub Actions UI. Monitor runs at the repo's Actions tab.

For local Cowork sessions, run these three lines before doing anything else:

```powershell
cd "C:\Users\<redacted>\OneDrive\Claude Projects\CLAIRE"
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
├── claire_output.py          ✅ Build 8 — digest generation (docx default; --format pdf for GHA)
├── claire_a_assembler.py     ✅ Build 5 — CLAIRE-A input assembler
├── claire_a_runner.py        ✅ Build 5 — decision engine runner (Opus)
├── claire_a_scorer.py        ✅ Build 5/6 — eval scoring layer (Sonnet)
├── claire_utils.py           ✅ Build 4 — shared compute_cost, append_cost_log
├── config.json               ✅ Pipeline config — locked decisions
├── requirements.txt          ✅ requests, anthropic, python-dotenv
├── .env                      ✅ ANTHROPIC_API_KEY (never touch)
├── .gitignore                ✅ Secrets and data excluded
├── HANDOFF.md                ✅ This file
├── README.md                 ✅ Repo readme
├── change_log.json           ✅ CANONICAL — Applied changes + eval loop (v1.1 schema, Cycles 2-4)
├── friction_log.txt          ✅ CANONICAL — Weekly friction notes, human-maintained (Cycles 1-4)
├── claire_weekly.ps1         ✅ Build 6 — scheduled pipeline wrapper [local dev only]
├── claire_notify.py          ✅ Build 8 — Pushover notification (PDF attach or text fallback)
├── activate.bat              ✅ Venv activation shortcut
├── claire.bat                ✅ Pipeline launcher (CMD)
├── claire_runner.bat         ✅ Alternative pipeline runner
├── claire_scheduler.xml      ✅ Windows Task Scheduler import file [local dev only]
├── .github\
│   └── workflows\
│       └── claire_weekly.yml ✅ Build 8 — GitHub Actions weekly pipeline
├── .git\                     ✅ Local git, no remote
├── data\
│   ├── raw_posts.json        ✅ Current corpus — grows each ingest run
│   ├── tagged_posts.json     ✅ Build 2 output — posts with triage tags
│   ├── synthesis_queue_track_a.json  ✅ Triage output — Track A queue (⚠ JSON corruption, regenerate on next run)
│   ├── synthesis_queue_track_b.json  ✅ Triage output — Track B queue (⚠ JSON corruption, regenerate on next run)
│   ├── synthesis_queue_track_c.json  ✅ Triage output — Track C queue (⚠ JSON corruption, regenerate on next run)
│   ├── candidates_track_a.json       ✅ Build 5 — synthesis output, assembler input (⚠ JSON corruption, regenerate on next run)
│   ├── candidates_track_b.json       ✅ Build 5 — synthesis output, assembler input
│   ├── candidates_track_c.json       ✅ Build 5 — synthesis output, assembler input (⚠ JSON corruption, regenerate on next run)
│   ├── archive.json          ✅ Build 2 output — LOW-confidence post accumulator. Revisit size quarterly.
│   ├── memory_edits_snapshot.txt     ✅ Current Claude memory baseline (human-maintained)
│   ├── cost_log.json         ✅ Build 4 — per-run API cost tracking
│   ├── ingest_run_log.json   ✅ Ingest run history — source counts per run
│   ├── claire_a_input_[timestamp].json     ✅ Build 5 — assembler output, engine input payload
│   ├── claire_a_decisions_[timestamp].json ✅ Build 5 — shadow decision record (Opus output)
│   ├── claire_a_reasoning_[timestamp].txt  ✅ Build 5 — auditable reasoning scratchpad
│   ├── claire_a_source_reliability.json    ⬜ Build 6 — expected; created on first scorer run (not yet present)
│   ├── claire_a_session_history.json       ✅ Build 6 — cross-run fingerprint tracking for prior_appearances
│   └── change_log_v1_legacy.json           ✅ v1.0 schema archive — superseded by root change_log.json
├── prompts\
│   ├── triage_prompt.txt     ✅ Haiku system prompt
│   ├── synthesis_prompts.py  ✅ Three Sonnet prompts
│   └── profile_intent_summary.txt  ✅ Injected into Track A + B
├── logs\
│   ├── ingest.log            ✅ Ingest run log (UTF-8, FileHandler)
│   ├── triage.log            ✅ Triage run log
│   ├── synthesis.log         ✅ Synthesis run log
│   └── output.log            ✅ Digest generation log
├── output\                   ✅ Build 3/8 — weekly digest .docx + claire_digest_YYYY-MM-DD.pdf
├── skill_drafts\             ✅ Build 3 — SKILL.md drafts (hallucination-guard, source-integrity-enforcer)
├── skills\user\              ✅ Installed user skills (hallucination-guard)
├── archive\                  ⬜ Quarterly review artifacts (directory to be created)
└── docs\
    ├── claire_pipeline_flow.jsx   ✅ Decision flow diagram
    └── reddit_app_setup.md        ✅ Reddit API reference
```

**Path rule:** `change_log.json` and `friction_log.txt` live at **project root**. The `data/` directory does not contain canonical versions of either. `data/change_log_v1_legacy.json` is a read-only archive of the v1.0 schema.

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
| 8 | `requirements.txt` | ✅ Complete | reportlab added |
| 8 | `claire_output.py` | ✅ Complete | --format pdf; generate_pdf() via reportlab |
| 8 | `claire_notify.py` | ✅ Complete | Pushover notification — PDF attach or text fallback |
| 8 | `.github/workflows/claire_weekly.yml` | ✅ Complete | Full GHA pipeline, cron Sunday 14:00 UTC |

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
| Commit-back strategy | GHA pipeline commits data/, output/, logs/, change_log.json, friction_log.txt after each run |
| PDF output | reportlab, six-section mirror of docx digest; filename `claire_digest_YYYY-MM-DD.pdf` |
| Pushover oversize fallback | PDF > 2,500,000 bytes → text-only notification with commit URL; no attachment |

---

## GitHub Secrets

Required in repo Settings → Secrets and variables → Actions:

| Secret | Used by | Notes |
|--------|---------|-------|
| `ANTHROPIC_API_KEY` | triage, synthesize, claire_a_runner, claire_a_scorer | Anthropic API — all model calls |
| `GH_PAT` | commit-state | Personal access token with `contents: write` scope; needed to push commits from the workflow |
| `PUSHOVER_APP_TOKEN` | notify | Pushover application token |
| `PUSHOVER_USER_KEY` | notify | Pushover user/group delivery key |
| `REDDIT_CLIENT_ID` | ingest (reserved) | Required when upgrading to authenticated Reddit OAuth API |
| `REDDIT_CLIENT_SECRET` | ingest (reserved) | Required when upgrading to authenticated Reddit OAuth API |
| `REDDIT_USERNAME` | ingest (reserved) | Required when upgrading to authenticated Reddit OAuth API |
| `REDDIT_PASSWORD` | ingest (reserved) | Required when upgrading to authenticated Reddit OAuth API |

**Currently active:** `ANTHROPIC_API_KEY`, `GH_PAT`, `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY`.
Reddit secrets are defined but unused until the ingest layer upgrades from public JSON to OAuth API.

---

## Known Issues

| Issue | Detail |
|-------|--------|
| Opus filter log count | Reports against full corpus not just new posts — misleading log line, triage behavior correct |
| change_log.json corruption | Root file truncated mid-write on 2026-05-10 (ends with dangling `{` after c3-prof-003). Repaired 2026-05-19 — trailing `{` removed, JSON closed. Cycle 4 entries appended in same session. 21 entries total. |
| Cycle 2-4 confidence scores understated | `FRICTION_LOG_PATH` in `claire_triage.py` pointed to `data/friction_log.txt` (original April template) instead of root `friction_log.txt` (live log). Cross-reference gate ran against example data for all three live cycles. Signals matching documented friction scored MEDIUM instead of HIGH. Fix applied 2026-05-19 — takes effect Cycle 5. Historical scores not retroactively adjusted; directionally correct but not corroboration-weighted. |
| synthesis_queue JSON corruption | synthesis_queue_track_a/b/c.json all have JSON parse errors — truncated writes from a previous pipeline run. Regenerate by re-running triage on current raw_posts.json. |
| candidates_track JSON corruption | candidates_track_a.json and candidates_track_c.json have JSON parse errors. Regenerate by re-running synthesis. |
| claire_a_source_reliability.json missing | Expected by Build 6 scorer but never written. Created on first successful scorer run — not a bug, just never run to completion with scorer active. |

---

## Current Session Task

**Build 8 complete (2026-05-21) — GitHub Actions migration, reportlab PDF, Pushover notify.**

**Delivered this build:**
- `requirements.txt` — reportlab added
- `claire_output.py` — `--format pdf` argument; `generate_pdf()` via reportlab (six-section digest mirror)
- `claire_notify.py` — Pushover notification with PDF attachment or text fallback
- `.github/workflows/claire_weekly.yml` — full GHA pipeline (cron Sunday 14:00 UTC)
- `HANDOFF.md` — six surgical updates (GHA machine context, session start note, directory structure, locked decisions, GitHub Secrets section, this task block)

**Next actions before Cycle 5:**
1. Push repo to GitHub remote (create remote, `git remote add origin`, `git push -u origin main`)
2. Add four active secrets to repo: `ANTHROPIC_API_KEY`, `GH_PAT`, `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY`
3. Run `workflow_dispatch` to validate GHA pipeline end-to-end before relying on cron
4. Confirm Pushover notification received with PDF attachment

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

**Build 9 candidates (carry-forward from Build 8 scope):**
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
*Last updated: 2026-05-21 — Build 8 complete. GitHub Actions migration, reportlab PDF output, Pushover notify. HANDOFF updated: GHA machine context, session start note, directory structure (claire_notify.py + .github/workflows/), locked decisions (3 new rows), GitHub Secrets section added.*
