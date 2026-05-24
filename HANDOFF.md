 # CLAIRE — Session Handoff
> Read this first. Every session. No exceptions.

---

## Machine Context

| Item | Value |
|------|-------|
| Project root | `C:\DEV\CLAIRE` |
| Python | `python` (via .venv) [local dev only] |
| Pip | `python -m pip` |
| Venv activate (PowerShell) | `C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1` [local dev only] |
| Venv activate (CMD/bat) | `.\.venv\Scripts\activate.bat` [local dev only] |
| Git | initialized, remote on GitHub |
| Execution policy | RemoteSigned (already set) [local dev only] |
| CI/CD | GitHub Actions — `.github/workflows/claire_weekly.yml` |
| GHA trigger | Cron `0 14 * * 0` (Sundays 14:00 UTC) + `workflow_dispatch` |
| Execution (automated) | GitHub Actions — .github/workflows/claire_weekly.yml |
| GitHub repo | https://github.com/not-yet-autonomous/CLAIRE |

---

## GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | All Claude API calls |
| `GH_PAT` | Commit-back push (Contents read+write, fine-grained PAT) |
| `PUSHOVER_APP_TOKEN` | Pushover CLAIRE app token |
| `PUSHOVER_USER_KEY` | Pushover account user key |

Reddit credentials are not required — ingest uses unauthenticated public endpoints.

---

## Session Start Checklist

**GitHub Actions runs require no manual start** — the pipeline triggers
automatically on the Sunday 14:00 UTC cron, or via `workflow_dispatch` in
the GitHub Actions UI. Monitor runs at the repo's Actions tab.

For local Cowork sessions, run these three lines before doing anything else:

> GHA runs unattended on Sunday 14:00 UTC. This checklist is for local dev
> sessions only.
>
> **Pre-Sunday ritual (manual, before cron fires):**
> 1. Update `data/session_notes.txt` with behavioral observations from the week
> 2. `git add data/session_notes.txt && git commit -m "session notes cycle N" && git push`

```powershell
cd "C:\DEV\CLAIRE"
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1
python -c "import anthropic, requests; print('Deps OK')"
```

Expected output: `(.venv)` in prompt + `Deps OK`
If venv fails: use `.\.venv\Scripts\activate.bat` instead
If deps fail: `python -m pip install -r requirements.txt`

**Pre-push verification (run before every commit that touches data/ or git state):**
```powershell
git ls-files data/
```
Expected: only `data/raw_posts.json`. Any other filenames = tracked data files still in index — run `git rm --cached <file>` before pushing. The pre-push hook at `.git/hooks/pre-push` enforces this automatically, but verify manually if hook behavior is in doubt.

```powershell
# Strip FUSE null-byte corruption from key files before working:
python -c "
for f in ['HANDOFF.md', 'change_log.json', 'friction_log.txt', '.git/config', '.git/index']:
    try:
        data = open(f, 'rb').read().rstrip(b'\x00')
        open(f, 'wb').write(data)
    except FileNotFoundError:
        pass
print('Null-byte check OK')
"
```

Expected output after all four steps: `(.venv)` in prompt + `Deps OK` + `Null-byte check OK`

---

## Local vs. GHA -- Operational Discipline

Two execution environments run the same pipeline. Local combined is canonical.

| Item | Local | GHA |
|------|-------|-----|
| Reddit signal | Yes - run and push before Sunday 14:00 UTC | Only if pre-Sunday push completed |
| HackerNews + dev.to | Yes | Yes |
| Trigger | Manual | Cron Sunday 14:00 UTC |
| Canonical digest | Yes - review and apply from local combined run | No - fallback and notification only |

**Rules:**

1. **Local combined digest is the canonical review artifact.** Run Reddit
   ingest locally, push raw_posts.json, let GHA fire, pull, then run the
   full local pipeline with --source all. The digest in output/ after that
   run is what you review and apply from.

2. **Reddit signal requires pre-Sunday discipline.** Run Reddit ingest locally,
   commit and push `raw_posts.json` before Sunday 14:00 UTC. GHA picks it up
   from the repo at triage. Skip it and the Sunday digest is HN + dev.to
   only -- still valid, just Reddit-free.

3. **Pull before editing `change_log.json` or `friction_log.txt`.** GHA commits
   both files back on every run. A local edit without a prior pull will
   conflict on push.

4. **Push `config.json` before Saturday.** GHA runs whatever `config.json` is on
   main at 14:00 UTC Sunday. A local edit that isn't pushed runs silently
   against last week's config with no warning.

5. **Push `session_notes.txt` before Sunday 14:00 UTC.** The CLAIRE-A scorer
   requires current content. Stale notes produce low-quality scorer output --
   not a pipeline failure, a signal quality failure.

6. **One digest per cycle.** If GHA produces a digest and you also run locally,
   you have two digests for the same cycle. The local combined digest is
   canonical -- ignore the GHA one. `change_log.json` has no field to
   distinguish source -- ambiguity compounds at quarterly review.

---

## Directory Structure

```
CLAIRE\
├── claire_ingest.py          ✅ Build 9 — dev.to tag expansion (per-tag thresholds; llm, aitools, machinelearning added)
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
├── claire_weekly.ps1         ✅ Build 6 — scheduled pipeline wrapper [local dev only — Task Scheduler entry retired]
├── claire_pull.ps1           ✅ Build 10 — Task Scheduler git pull (Sunday 09:30 local, pulls GHA digest)
├── claire_pull.xml           ✅ Build 10 — Task Scheduler import (schtasks /create /xml claire_pull.xml /tn "CLAIRE Digest Pull")
├── claire_notify.py          ✅ Build 8 — Pushover dispatch with PDF attachment
├── activate.bat              ✅ Venv activation shortcut
├── claire.bat                ✅ Pipeline launcher (CMD)
├── claire_runner.bat         ✅ Alternative pipeline runner
├── claire_scheduler.xml      ✅ Windows Task Scheduler import file [local dev only]
├── .github\
│   └── workflows\
│       └── claire_weekly.yml ✅ Build 8 — GHA workflow (replaces Task Scheduler)
├── .git\                     ✅ Local git, remote on GitHub
├── data\
│   ├── raw_posts.json        ✅ Current corpus — grows each ingest run
│   ├── tagged_posts.json     ✅ Build 2 output — posts with triage tags
│   ├── synthesis_queue_track_a.json  ✅ Triage output — Track A queue (⚠ JSON corruption, regenerate on next run)
│   ├── synthesis_queue_track_b.json  ✅ Triage output — Track B queue (⚠ JSON corruption, regenerate on next run)
│   ├── synthesis_queue_track_c.json  ✅ Triage output — Track C queue (⚠ JSON corruption, regenerate on next run)
│   ├── candidates_track_a.json       ✅ Build 5 — synthesis output, assembler input (⚠ JSON corruption, regenerate on next run)
│   ├── candidates_track_b.json       ✅ Build 5 — synthesis output, assembler input
│   ├── candidates_track_c.json       ✅ Build 8 — Track C candidates for techniques PDF
│   ├── archive.json          ✅ Build 2 output — LOW-confidence post accumulator. Revisit size quarterly.
│   ├── memory_edits_snapshot.txt     ✅ Current Claude memory baseline (human-maintained)
│   ├── cost_log.json         ✅ Build 4 — per-run API cost tracking
│   ├── ingest_run_log.json   ✅ Ingest run history — source counts per run
│   ├── claire_a_input_[timestamp].json     ✅ Build 5 — assembler output, engine input payload
│   ├── claire_a_decisions_[timestamp].json ✅ Build 5 — shadow decision record (Opus output)
│   ├── claire_a_reasoning_[timestamp].txt  ✅ Build 5 — auditable reasoning scratchpad
│   ├── claire_a_source_reliability.json    ⬜ Build 6 — expected; created on first scorer run (not yet present)
│   ├── claire_a_session_history.json       ✅ Build 6 — cross-run fingerprint tracking for prior_appearances
│   ├── change_log_v1_legacy.json           ✅ v1.0 schema archive — superseded by root change_log.json
│   └── session_notes.txt     ✅ Build 8 — weekly scorer observations (manual update required)
├── prompts\
│   ├── triage_prompt.txt     ✅ Haiku system prompt
│   ├── synthesis_prompts.py  ✅ Three Sonnet prompts
│   └── profile_intent_summary.txt  ✅ Injected into Track A + B
├── logs\
│   ├── ingest.log            ✅ Ingest run log (UTF-8, FileHandler)
│   ├── triage.log            ✅ Triage run log
│   ├── synthesis.log         ✅ Synthesis run log
│   └── output.log            ✅ Digest generation log
├── output\                   ✅ Build 3 — weekly digest PDF (Section 6 = CLAIRE-A decisions)
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
| 8 | `claire_a_assembler.py` | ✅ Complete | Semantic memory filter — Haiku, 0.85 threshold, suppressed_candidates log |
| 8 | `claire_output.py` | ✅ Complete | Track C separate PDF — generate_techniques_pdf(), non-fatal on failure |
| 8 | `claire_utils.py` | ✅ Complete | Cost log merge — upsert by run_id, Track A alert at $0.65 |
| 9 | `claire_ingest.py` | ✅ Complete | dev.to tag expansion — per-tag thresholds; llm (15), aitools (10), machinelearning (20) |
| 9 | `config.json` | ✅ Complete | devto.tags migrated to object array; DEVTO_MIN_REACTIONS constant removed |

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
| Scheduling | Reddit local - run and push before Sunday 14:00 UTC; GHA Sunday 14:00 UTC |
| Cost log entries | Single upsert per run keyed by YYYYMMDD — triage + synthesis + assembler accumulated |
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
| Memory filter threshold | 0.85 semantic similarity (Haiku, assembler stage) — tunable in config.json |
| Track C output | Separate PDF — output/claire_techniques_[timestamp].pdf, non-fatal |
| Track A cost alert | $0.65 synthesis threshold — Write-Warning in claire_weekly.ps1 |
| Pushover oversize fallback | PDF > 2,500,000 bytes → text-only notification with commit URL; no attachment |
| State persistence | Commit-back — data files committed to repo at end of each GHA run |
| Digest format (production) | reportlab PDF — docx retained for local dev only |
| Pushover oversize fallback | Summary notification + repo commit if PDF > 2.5MB |
| Reddit ingestion | Manual — run locally, commit raw_posts.json, GHA picks up from triage |
| GHA ingest sources | HN + dev.to only (--source forum) — Reddit blocked from datacenter IPs |

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
| Reddit GHA IP block | Reddit returns 403 on JSON endpoints and empty RSS feeds from GHA datacenter IPs. Manual ingest is permanent architecture — not a bug to fix. |
| git null-byte corruption | .git/config and .git/index had null-byte padding appended (62 and 130 bytes) — likely OneDrive FUSE mount. Strip with: `python -c "open('.git/config','wb').write(open('.git/config','rb').read().rstrip(b'\\x00'))"` Same fix applies to .git/index. Symptoms: 'bad config line' or 'index file corrupt'. |
| OneDrive FUSE mount write behavior | Silently truncates large file writes. Do not write config.json or other large files through Cowork file tools. Use Windows-side editor or bash heredoc. |
| Git index corruption (2026-05-23) | Null sha1 cache entry in .git/index — resolved by deleting index.lock and index, then running `git reset HEAD` to rebuild from HEAD before restaging. Root cause: FUSE mount null-byte padding. |

---

## Current Session Task

Build 10 complete (2026-05-24). Repo at public-release state on main.

**Build 10 applied (2026-05-24):**
- Email delivery removed from GHA workflow — Outlook.com basic auth disabled, app passwords non-functional
- `claire_pull.ps1` added — Task Scheduler git pull for local digest delivery (Sunday 09:30 local)
- `claire_pull.xml` added — Task Scheduler import file; register with `schtasks /create /xml claire_pull.xml /tn "CLAIRE Digest Pull"`
- `raw_posts.json` gitignore negation rule added (`!data/raw_posts.json`) — Reddit signal now committtable to repo
- README Optional Email section removed; After GHA section updated with pull script docs
- HANDOFF directory structure updated with new files
- SMTP friction entry added to friction_log.txt (2026-05-24)

**Cycle 5 applied (carried forward):**
- c5-mem-001: Suppress session-termination suggestions
- c5-mem-002: Suppress session/token limit caveats
- c5-mem-003: Proactive prompt injection flagging
- c5-prof-001: Never embed reasoning scaffolding in deliverable documents
- c5-prof-002: Surface conflicting instructions explicitly before proceeding

**Queued (observation gate):**
- c5-prof-003: Distinguish document-grounded vs training-derived conclusions (one live doc synthesis session required)
- c3-prof-002: Task-completion anti-collapse (observe 4.7 in live session first)
- c3-prof-003: Effort transparency disclosure (observe 4.7 in live session first)
- c4-prof-001 through c4-prof-004: queued, no gates

**CLAIRE-A graduation criteria (2 of 6):**
- Consecutive eval runs logged: 2 of 6 required
- Reliability ledger hypotheses scored: 7 of 10 required
- Escalations in last 3 runs: 0 (clean)

**Build 11 / next session candidates:**
- Same-day memory filtering in triage (cross-reference gate gap — c3, c5 friction logs)
- feature_praise repurpose or scope reduction (dead weight at 27% corpus volume)
- Session notes pre-commit workflow (required before each Sunday GHA run)
- Substack RSS ingest (identify target feeds first)
- X/Twitter ingest (blocked — API access/cost unresolved)
- Evaluate moving raw_posts.json to project root to eliminate gitignore dependency


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

Do not make ar