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

Reddit ingest retired in Build 10 — no Reddit credentials required or used.

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
| HackerNews + dev.to | Yes | Yes |
| Trigger | Manual | Cron Sunday 14:00 UTC |
| Canonical digest | GHA is canonical — pull after run completes | Yes - primary production path |

**Rules:**

1. **Pull before editing `change_log.json` or `friction_log.txt`.** GHA commits
   both files back on every run. A local edit without a prior pull will
   conflict on push.

2. **Push `config.json` before Saturday.** GHA runs whatever `config.json` is on
   main at 14:00 UTC Sunday. A local edit that isn't pushed runs silently
   against last week's config with no warning.

3. **Push `session_notes.txt` before Sunday 14:00 UTC.** The CLAIRE-A scorer
   requires current content. Stale notes produce low-quality scorer output --
   not a pipeline failure, a signal quality failure.

---

## Directory Structure

```
CLAIRE\
├── claire_ingest.py          ✅ Build 13 — HN url set to permalink; external_url added; Build 10: Reddit retired, dev.to expanded
├── claire_triage.py          ✅ Build 2 — triage complete
├── claire_synthesize.py      ✅ Build 5 — fingerprints + change_target field added
├── claire_output.py          ✅ Build 8 — digest generation (PDF default fixed 2026-05-23; docx retained for local dev)
├── claire_a_assembler.py     ✅ Build 11 — load_dotenv fix (memory filter auth); Build 5 assembler base
├── claire_a_runner.py        ✅ Build 5 — decision engine runner (Opus)
├── claire_a_scorer.py        ✅ Build 5/6 — eval scoring layer (Sonnet)
├── claire_utils.py           ✅ Build 4 — shared compute_cost, append_cost_log
├── config.json               ✅ Build 10 — Reddit keys removed; dev.to tags expanded to 9
├── requirements.txt          ✅ requests, anthropic, python-dotenv
├── .env                      ✅ ANTHROPIC_API_KEY (never touch)
├── .gitignore                ✅ Secrets and data excluded
├── HANDOFF.md                ✅ This file
├── README.md                 ✅ Repo readme
├── change_log.json           ✅ CANONICAL — Applied changes + eval loop (v1.1 schema, Cycles 2-5)
├── friction_log.txt          ✅ CANONICAL — Weekly friction notes, human-maintained (Cycles 1-5)
├── claire_weekly.ps1         ✅ Build 6 — scheduled pipeline wrapper [local dev only — Task Scheduler entry retired]
├── claire_pull.ps1           ✅ Build 10 — Task Scheduler git pull (Sunday 09:30 local, pulls GHA digest)
├── claire_pull.xml           ✅ Build 10 — Task Scheduler import (schtasks /create /xml claire_pull.xml /tn "CLAIRE Digest Pull")
├── claire_notify.py          ✅ Build 8 — Pushover dispatch with PDF attachment
├── activate.bat              ✅ Venv activation shortcut
├── claire.bat                ✅ Pipeline launcher (CMD)
├── claire_runner.bat         ✅ Alternative pipeline runner
├── claire_scheduler.xml      ❌ Removed Build 10 — replaced by GHA in Build 8
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
    └── reddit_app_setup.md        ❌ Removed Build 10 — Reddit ingest retired
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
| 11 | `claire_a_assembler.py` | ✅ Complete | load_dotenv fix — memory filter auth error resolved; first suppression confirmed (c4-mem-006, score=0.850); Haiku pricing key verified |
| 11 | `claire_a_assembler.py` | ✅ Complete | memory filter extended to compare against change_log_entries at runtime (combined source); 9/12 suppressed on first combined run vs 1/12 snapshot-only |
| 10 | `claire_ingest.py` | ✅ Complete | Reddit ingest retired — all Reddit functions and constants removed; --source reddit exits with retirement message |
| 10 | `config.json` | ✅ Complete | Reddit config keys removed (subreddits_native/comparative, posts limits, keyword_searches); dev.to tags expanded: ai (25), chatgpt (10), productivity (10) |
| 12 | `claire_a_runner.py` | ✅ Complete | source field injected into each decision from input payload; ledger now keys by track (claire_synthesize:track_a, etc.) instead of "unknown" |
| 12 | `claire_a_scorer.py` | ✅ Complete | reliability ledger created manually (2026-06-02); 5 observations, score=0.700; 3 held + 2 partial across 4 eligible decision files |
| 12 | `claire_triage.py` | ✅ Complete | feature_praise+claude_native dropped to IGNORE at cross-reference gate; eliminates Track A pollution (16 posts / 37% corpus) |
| 12 | `config.json` | ✅ Complete | feature_praise keywords cleared from signal_keyword_map (praise/works/good/excellent were weak friction matches) |
| 12 | `claire_output.py` | ✅ Complete | Track C removed from main digest (PDF + docx); techniques PDF is sole Track C output |
| 12 | `CLAUDE.md` | ✅ Complete | load_dotenv rule added to silent failures table; stale Reddit row removed; version bumped to Build 12 |
| 13 | `claire_ingest.py` | ✅ Complete | HN citation URL fix -- `url` field set to HN permalink (`https://news.ycombinator.com/item?id={id}`); linked content preserved in new `external_url` field; `data/raw_posts.json` reset to empty corpus |

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
| Scheduling | GHA Sunday 14:00 UTC (all ingest sources) |
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
| Ingest sources | HackerNews + dev.to (GHA, Sunday 14:00 UTC) |
| dev.to tags | anthropic, claudeai, claude, llm, aitools, machinelearning, ai, chatgpt, productivity |
| dev.to min reactions | per-tag (5–25); see config.json devto.tags |
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
| GHA ingest sources | HN + dev.to (--source all) |

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
| git null-byte corruption | .git/config and .git/index had null-byte padding appended (62 and 130 bytes) — likely OneDrive FUSE mount. Strip with: `python -c "open('.git/config','wb').write(open('.git/config','rb').read().rstrip(b'\\x00'))"` Same fix applies to .git/index. Symptoms: 'bad config line' or 'index file corrupt'. |
| OneDrive FUSE mount write behavior | Silently truncates large file writes. Do not write config.json or other large files through Cowork file tools. Use Windows-side editor or bash heredoc. |
| Git index corruption (2026-05-23) | Null sha1 cache entry in .git/index — resolved by deleting index.lock and index, then running `git reset HEAD` to rebuild from HEAD before restaging. Root cause: FUSE mount null-byte padding. |
| claire_a_assembler.py mojibake | File contains cp1252 mojibake throughout (em-dashes, box-drawing chars). Caused string replacement failures during Build 11 edits. One-time cleanup: replace known sequences with clean UTF-8. No logic changes required. Low priority. |
| Assembler memory filter auth errors | All candidates pass through on error — Haiku dedup filter silently inactive on local runs. API key present (synthesis runs clean); assembler loads credentials via different path. Non-blocking. Build 11 fix. |
| Decision record source field missing | Fixed Build 12. Decisions written before 2026-06-02 have source="unknown" in ledger — historical entries cannot be retroactively attributed. Future runs will key correctly by track (claire_synthesize:track_a, etc.). |

---

## Current Session Task

Build 12 complete (2026-06-02).

**Build 11 applied:**
- claire_a_assembler.py: load_dotenv fix (memory filter auth). Combined source filter: change_log_entries injected at runtime alongside memory_edits_snapshot.txt. filter_source field added to suppressed entries. First combined run: 9/12 suppressed (source=combined), 3 passed. Suppression rate 8% -> 75%. Haiku pricing key verified.
- Memory filter JSON parse fix: code-fence stripping added; raise on empty response with stop_reason/output_tokens in error message.

**Claude Code migration (2026-06-02):**
- CLAUDE.md added to project root
- PROFILE.md added to project root (behavioral rules for all Claude Code work)
- MIGRATION_CHECKLIST.md produced (browser session) -- not yet committed

**CLAIRE-A graduation criteria (6 of 6 runs complete -- graduation in progress):**
- Consecutive eval runs logged: 6 of 6 -- criterion met
- Reliability ledger: CREATED 2026-06-02. 5 observations, score=0.700. Scorer run manually against 4 eligible decision files (April 26 x2, May 19, May 21). 3 held + 2 partial outcomes contributed; remainder insufficient_data (no null scores in ledger).
- Escalations in last 3 runs: not yet assessable -- ledger source field is "unknown" on all entries (decisions files lack source field; see known issue below). Escalation check requires source-attributed entries.
- Remaining 3 decision files (May 23, 28, 31) within eval window. Pass window June 6/11/14. GHA scorer will pick up naturally. 10-observation threshold expected by June 14.
- Next action: pull after June 14 GHA run; verify ledger reaches 10+ observations; graduation decision follows.

**Build 12 items (priority order):**
- DONE: Verify claire_a_source_reliability.json writes -- ledger created, mechanism verified
- DONE: Eyeball suppressed_candidates_20260531_185610.json -- 9 suppressions confirmed legitimate (0.92-0.95 clear duplicates; two at 0.85 threshold match combined source)
- DONE: source field missing on decision records -- fixed in claire_a_runner.py (Build 12); future decisions will key by track
- DONE: feature_praise scope reduction -- drop feature_praise+claude_native to IGNORE at gate (16 Track A polluters eliminated); feature_praise keywords removed from signal_keyword_map (weak matches: praise/works/good/excellent); cross_platform feature_praise retained as technique signal; actual corpus volume was 37% not 27%
- DONE: Technique candidates separate output stream -- Track C removed from main digest (PDF + docx); techniques PDF is now sole output for Track C
- DONE: load_dotenv presence check added to CLAUDE.md silent failures table

**Build 13 candidates (priority order):**
- DONE: HN citation URL fix -- `url` field set to HN permalink; `external_url` field added; `data/raw_posts.json` corpus reset (commit 210ae16)
- PRIORITY 1: CLAIRE-A graduation decision -- pull after June 14 GHA run; verify ledger reaches 10+ observations with source-attributed entries; evaluate all three criteria; document outcome in change_log.json
- PRIORITY 2: GHA commit-back scope gap -- workflow only commits PDFs; data/, logs/, change_log.json, friction_log.txt not committed back despite HANDOFF stating they are; CLAIRE-A decision files, cost logs, session history not persisting between runs; affects ledger continuity
- .claude/ directory untracked -- showing in git status; needs gitignore entry or explicit decision to track
- Assembler mojibake cleanup -- claire_a_assembler.py contains cp1252 encoding throughout (em-dashes, box-drawing chars); one-time cleanup, no logic changes; low priority
