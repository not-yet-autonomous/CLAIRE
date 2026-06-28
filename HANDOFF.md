---
> Read this first. Every session. No exceptions.
> State as of 2026-06-28 post-verification-dispatch close (cycle 10).
> v2.1.4 tagged and pushed. HN ingest fix VERIFIED: fetched=150, new=62
> (commit 75fbb0f). raw_posts GHA cache operational (first save confirmed,
> key raw-posts-Linux-28331796118). Node 20 deprecation warning in
> actions/cache@v4 — LOW, not urgent.
>
> CYCLE-NUMBERING CORRECTION THIS SESSION: the 2026-06-21 run shipped MISLABELED
> as c8 because the increment to 9 was never on main before that cron.
> Decision: bump 8->10 (date-map). Quarantined to 06-21. See Known Issues.
>
> STILL OPEN, ranked: (1) notify path divergence HIGH — outranks switch-on.
> (2) c8-process-003 build authorization (assembler code uncommitted, own commit).
> (3) official-signal lane switch-on.
> Next live event: Sun 2026-07-05 14:00 UTC GHA run (cycle 11) —
> increment config.pipeline.current_cycle to 11 first.

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

No Reddit credentials required or used.

---

## Cycle Log

| Cycle | Review Date | GHA Run Date | Digest Filename |
|-------|-------------|--------------|-----------------|
| 1 | — | — | Pipeline validation only |
| 2 | 2026-05-05 | 2026-05-03 | Not tracked |
| 3 | 2026-05-10 | 2026-05-10 | Not tracked |
| 4 | 2026-05-19 | 2026-05-17 | Not tracked |
| 5 | 2026-05-21 / 2026-05-23 | 2026-05-17 | Not tracked (local rebuild: claire_digest_2026-05-23.pdf committed same day) |
| 6 | 2026-06-02 | 2026-05-31 | claire_digest_2026-05-31.pdf |
| 7 | 2026-06-08 | 2026-06-07 | claire_digest_2026-06-07.pdf |
| 8 | run verified 2026-06-14 | 2026-06-14 ✅ run #29 | claire_digest_2026-06-14_c8.pdf |
| 9 | — | 2026-06-21 | claire_digest_2026-06-21_c8.pdf (MISLABELED — increment to 9 missed before cron; see Known Issues "06-21 cycle mislabel") |
| 10 | — | 2026-06-28 | claire_digest_2026-06-28_c10.pdf (config bumped 8→10 pre-run, commit 23a196f) |
| 11 | — | 2026-07-05 | claire_digest_2026-07-05_c11.pdf |
| 12 | — | 2026-07-12 | claire_digest_2026-07-12_c12.pdf |
| 13 | — | 2026-07-19 | claire_digest_2026-07-19_c13.pdf |

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
> 1. Increment `config.pipeline.current_cycle` (nested, NOT flat config.current_cycle).
>    Currently 10 (on main for the June 28 run); bump to 11 before the July 5 run, +1 each week.
>    THIS IS THE LOAD-BEARING KEYSTROKE — the 06-21 mislabel happened because it was skipped.
>    If config's cycle is not advanced on main before the cron, claire_output stamps last week's
>    number and the digest mislabels silently. Push to main, do not just edit locally.
>    Commit with session notes in the same commit:
>    `git commit -m "pre-run cycle N: session notes + cycle increment"`
> 2. Update `data/session_notes.txt` with behavioral observations from the week
> 3. Commit and push both together

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
Expected: `data/raw_posts.json`, `data/profile_snapshot.txt`, `data/session_notes.txt`, plus the CLAIRE-A state files committed back by GHA since Build 14 (`claire_a_decisions_*.json`, `claire_a_session_history.json`, `claire_a_source_reliability.json`, `cost_log.json`, `suppressed_candidates_*.json`). Any other filename = a tracked data file that should not be in the index — run `git rm --cached <file>` before pushing.

**Pre-push hook scope (Build 14):** The hook at `.git/hooks/pre-push` blocks local pushes with staged `data/` files. It is local-only — git hooks are not versioned, so it does not exist on the GHA runner and does not block the GHA commit-back of the state files listed above. Locally it will also block staged changes to the now-tracked state files; this is intentional — state files are written by the pipeline and committed back by GHA, not edited and pushed by hand. If a local pipeline run legitimately updates them, let the next GHA run commit the fresh versions rather than pushing local copies.

**index.lock — CONDITIONAL, do not run blind (2026-06-13/14 harness-guard finding):**
The documented `Remove-Item .git\index.lock -ErrorAction SilentlyContinue` session-start
prefix aborted the first commit attempt on the execution harness path guard — twice now.
Run it conditionally, never unconditionally:
```powershell
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -ErrorAction SilentlyContinue }
```
Or assume the harness manages the lock and skip the prefix entirely. The unconditional prefix
is the documented step that now conflicts with this environment.

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

11. Memory edits are scoped to this project only. Behavioral changes intended to apply globally must be profile diffs. Use data/profile_snapshot.txt as the global config baseline for synthesis cross-reference.

12. Hypothesis prompts for pending entries live in the hypothesis_prompt field of each change_log.json entry. If the field is absent, the prompt is lost — add it at entry creation time, not after.

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
├── change_log.json           ✅ CANONICAL — Applied changes + eval loop (v1.2 schema w/ scope field, Cycles 2-8; 59 entries)
├── friction_log.txt          ✅ CANONICAL — Weekly friction notes, human-maintained (Cycles 1-8)
├── claire_weekly.ps1         ✅ Build 6 — scheduled pipeline wrapper [local dev only — Task Scheduler entry retired]
├── claire_pull.ps1           ✅ Build 10 — Task Scheduler git pull (Sunday 09:30 local, pulls GHA digest)
├── claire_pull.xml           ✅ Build 10 — Task Scheduler import (schtasks /create /xml claire_pull.xml /tn "CLAIRE Digest Pull")
├── claire_notify.py          ✅ Build 8 — Pushover dispatch with PDF attachment; v2.1.2 — cycle identity from config.pipeline.current_cycle, applied-count scoped
├── claire_official_signal.py ✅ Build 14 (DORMANT) — official-signal lane; Haiku on release-notes prose + regex on deprecations table; block-level gate; enabled:false
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
│   ├── claire_session_context.txt  ✅ Claude memory snapshot (CLAIRE session scope only — renamed from memory_edits_snapshot.txt 2026-06-02)
│   ├── profile_snapshot.txt        ✅ Profile v12 canonical snapshot — injected into Track A cross-reference gate alongside claire_session_context.txt; human-maintained
│   ├── cost_log.json         ✅ Build 4 — per-run API cost tracking
│   ├── ingest_run_log.json   ✅ Ingest run history — source counts per run
│   ├── claire_a_input_[timestamp].json     ✅ Build 5 — assembler output, engine input payload
│   ├── claire_a_decisions_[timestamp].json ✅ Build 5 — shadow decision record (Opus output)
│   ├── claire_a_reasoning_[timestamp].txt  ✅ Build 5 — auditable reasoning scratchpad
│   ├── claire_a_source_reliability.json    ⬜ Build 6 — expected; created on first scorer run (not yet present)
│   ├── claire_a_session_history.json       ✅ Build 6 — cross-run fingerprint tracking for prior_appearances
│   ├── change_log_v1_legacy.json           ✅ v1.0 schema archive — superseded by root change_log.json
│   ├── cycle_state.json        ✅ v2.1.3 — machine-written: last_completed_cycle, last_completed_at, digest. Persisted via enumerated GHA commit-back. NOT config.json.
│   ├── official_signal_seen.json ✅ Build 14 — official-signal dedup memory (model,sign,date). Seeded empty; grows once lane is enabled. Enumerated commit-back.
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
├── tests\                    ✅ Build 14 — test_official_signal.py (30 assertions: gate block-level, tag, dedup, live Haiku extraction, fabrication check) + fixture_official_signal.json
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
| 13 | README.md | ✅ Complete | v2.0.0 output scope architecture, profile diff primacy, ritual update |
| 13 | release v2.0.0 | ✅ Complete | Tagged — global optimization architecture |
| 14 | `claire_utils.py` | ✅ Complete | atomic_write_json helper (temp file + os.replace); adopted by every JSON writer in the pipeline — closes the truncated-write corruption class |
| 14 | `claire_a_assembler.py` | ✅ Complete | JSONDecodeError handling in _load_track — corrupt candidates file now fails with a repair message instead of a traceback |
| 14 | `claire_triage.py` | ✅ Complete | archive.json deduped by post_id on write — stops duplicate accumulation from full-cache re-routing |
| 14 | `.github/workflows/claire_weekly.yml` | ✅ Complete | commit-back extended to CLAIRE-A state files (decisions, session history, reliability ledger, cost log, suppressed candidates) + logs/ — enumerated adds, no blanket data/ |
| 14 | `claire_weekly.ps1` | ✅ Complete | --notes data/session_notes.txt passed to scorer — unattended local runs no longer fail at the scorer step |
| 14 | `claire_ingest.py` | ✅ Complete | per-source HTTPError handling — a 403 from one API logs and skips that source instead of aborting the run |
| 14 | `claire_a_scorer.py` | ✅ Complete | missing --notes file path now errors out instead of being silently treated as inline notes text |
| 14 | `claire_official_signal.py` | ✅ Built (dormant) | Official-signal lane (Proposal 1, capability-delta). Haiku for release-notes prose (ADD + prose-WITHDRAW); regex for the deprecations table; block-level gate anchored to change_log c8-prof-001; dedup via official_signal_seen.json. Ships enabled:false; switch-on logs c8-process-002. 30 tests + live extraction + fabrication check pass. |
| 14 | `claire_output.py` | ✅ Complete | Capability-delta digest section -- own labeled section, WITHDRAW first, coverage-boundary line every run, non-fatal unavailable/disabled/not-run states |
| 14 | `config.json` | ✅ Complete | official_signal block (enabled:false, source URLs, seen filename, token caps) -- additive top-level key, no existing config touched |
| 14 | `.github/workflows/claire_weekly.yml` | ✅ Complete | Official-signal lane step before digest (non-fatal, || true); official_signal_seen.json added to enumerated commit-back (no blanket data/) |
| 14 | `claire_weekly.ps1` | ✅ Complete | Official-signal lane step before digest, self-gating on enabled, non-fatal |

### Official-signal lane -- switch-on pending

Built and committed dormant (enabled:false). Switch-on is operator-gated and requires:
1. Flip `config.official_signal.enabled` to true.
2. Provide the ratified c8-process-002 hypothesis (operator-authored; held from the 2026-06-13 design session).
On switch-on, log together: c8-process-002 change_log entry (date = switch-on; type pipeline_change; scope process;
eval_status pending; eval_window per-model-event); extend change_log _meta.notes eval_window definition to
duration-or-cadence; friction_log "lane live, baseline 0/3" note.
Carried Forward (not chased this session): audit any consumer doing date math on eval_window to branch on the
cadence token (cf. cycle-5 "eval window elapsed"); refresh data/profile_snapshot.txt to carry the MODEL ROUTING
block (still stale at the retired "Opus 4.6 > 4.7" preference -- standing debt, gate does not depend on it).

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
| Cost log entries | Single upsert per run keyed by YYYYMMDD - triage + synthesis + assembler accumulated. ⚠ DIVERGENT as of run #29 (2026-06-14): writes three separate rows per run keyed to the same date instead of one accumulated row; total correct, shape wrong, total_runs miscounts. See Known Issues. |
| Opus exclusion | exclude_keywords in config.json — config-driven |
| Shared utilities | claire_utils.py — home for all cross-script helpers |
| Track A batching | Signal cluster by signal_type, max 50 posts per call |
| track_a_max_batch | 50 — tunable in config.json under "synthesis" |
| CLAIRE-A mode | Shadow only — reads everything, writes nothing to live config |
| Decision engine model | claude-opus-4-5 |
| Eval scoring model | claude-sonnet-4-6 |
| Batch size ceiling | 15 candidates per decision engine run |
| CLAIRE-A graduation criteria | 10 consecutive eval runs — clock resets 2026-06-14 (first post-change run after c7-config-001) |
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
| Pushover oversize fallback | PDF > 2,500,000 bytes → text-only notification with commit URL; no attachment. ⚠ Lives in claire_notify.py, which the GHA path does NOT invoke (run #29 finding). NOT active in production. See Known Issues "notify path divergence". |
| State persistence | Commit-back — data files committed to repo at end of each GHA run |
| Digest format (production) | reportlab PDF — docx retained for local dev only |
| Pushover oversize fallback | Summary notification + repo commit if PDF > 2.5MB |
| GHA ingest sources | HN + dev.to (--source all) |
| Profile snapshot injection | data/profile_snapshot.txt injected into Track A cross-reference gate; gitignored — GHA writes placeholder if missing; gate logs warning when running on placeholder |
| Cycle identity source | `config.pipeline.current_cycle` (nested) is authoritative for cycle identity (v2.1.2). claire_notify.py reads it directly — BUT claire_notify.py is NOT invoked by the GHA workflow (run #29 finding); GHA notifies via an inline curl with a hardcoded cycle-less title. The cycle-identity fix proves out ON-PATH only through cycle_state.json (written by claire_output.py at generate_pdf), verified == 8 on run #29. Applied-count (the other v2.1.2 behavior) is unobservable on GHA until the workflow is wired to the script. Never derive identity from change_log. |
| cycle_state.json | Machine-written runtime state (last_completed_cycle, last_completed_at, digest). Written at successful generate_pdf() via atomic_write_json. Separate from config.json by design — human-incremented config must not mix with pipeline-written state. Persisted via enumerated GHA commit-back. |
| Official-signal lane | Built dormant (enabled:false). Capability-delta candidate type. Block-level touch-test gate anchored to change_log c8-prof-001. No 3-post threshold (authoritative n=1). Haiku on release-notes prose (ADD + prose-WITHDRAW), regex on deprecations table. WITHDRAW covered via release notes + deprecations table; uncovered only when announced solely by email/status page with no published entry. Switch-on is operator-gated. |

---

## Known Issues

| Issue | Detail |
|-------|--------|
| Opus filter log count | Reports against full corpus not just new posts — misleading log line, triage behavior correct |
| change_log.json corruption | Root file truncated mid-write on 2026-05-10 (ends with dangling `{` after c3-prof-003). Repaired 2026-05-19 — trailing `{` removed, JSON closed. Cycle 4 entries appended in same session. 21 entries total. |
| Cycle 2-4 confidence scores understated | `FRICTION_LOG_PATH` in `claire_triage.py` pointed to `data/friction_log.txt` (original April template) instead of root `friction_log.txt` (live log). Cross-reference gate ran against example data for all three live cycles. Signals matching documented friction scored MEDIUM instead of HIGH. Fix applied 2026-05-19 — takes effect Cycle 5. Historical scores not retroactively adjusted; directionally correct but not corroboration-weighted. |
| claire_a_source_reliability.json missing | Expected by Build 6 scorer but never written. Created on first successful scorer run — not a bug, just never run to completion with scorer active. |
| git null-byte corruption | .git/config and .git/index had null-byte padding appended (62 and 130 bytes) — likely OneDrive FUSE mount. Strip with: `python -c "open('.git/config','wb').write(open('.git/config','rb').read().rstrip(b'\\x00'))"` Same fix applies to .git/index. Symptoms: 'bad config line' or 'index file corrupt'. |
| OneDrive FUSE mount write behavior | Silently truncates large file writes. Do not write config.json or other large files through Cowork file tools. Use Windows-side editor or bash heredoc. |
| Git index corruption (2026-05-23) | Null sha1 cache entry in .git/index — resolved by deleting index.lock and index, then running `git reset HEAD` to rebuild from HEAD before restaging. Root cause: FUSE mount null-byte padding. |
| claire_a_assembler.py mojibake | File contains cp1252 mojibake throughout (em-dashes, box-drawing chars). Caused string replacement failures during Build 11 edits. One-time cleanup: replace known sequences with clean UTF-8. No logic changes required. Low priority. |
| Assembler memory filter auth errors | All candidates pass through on error — Haiku dedup filter silently inactive on local runs. API key present (synthesis runs clean); assembler loads credentials via different path. Non-blocking. Build 11 fix. |
| Decision record source field missing | Fixed Build 12. Decisions written before 2026-06-02 have source="unknown" in ledger — historical entries cannot be retroactively attributed. Future runs will key correctly by track (claire_synthesize:track_a, etc.). |
| profile_snapshot.txt GHA degradation | File is gitignored — GHA runs use a placeholder; cross-reference gate runs without profile context on automated runs. Update locally after each profile revision and push to restore full precision. Not a pipeline failure — a signal quality degradation. |
| CLAIRE-A ledger pre-Build 12 | All 8 existing decision files predate Build 12 source field injection. Ledger keys everything as "unknown" until first post-Build 12 GHA run. Not a bug — expected aggregation of pre-attribution observations. Source-attributed entries begin after June 15 GHA run. |
| read_cycle_number cycle lag (RESOLVED ON-PATH 2026-06-13, v2.1.2/v2.1.3; notify-path UNREACHED) | Was: notify's `read_cycle_number()` derived cycle from `max(int(c['cycle']))` across ALL change_log entries (max-of-all, not action-filtered), lagging config for any cycle with no applied entry. Fixed v2.1.2 (74af5ef): identity from `config.pipeline.current_cycle` (confirmed nested), SystemExit(1) on missing key, applied-count scoped to current_cycle with zero allowed; last_completed_cycle to data/cycle_state.json at digest completion. v2.1.3 (38abf20): cycle_state.json persisted via enumerated GHA commit-back. CORRECTION after run #29: the fix lives in claire_notify.py, which the GHA path does NOT call. It proved out only via cycle_state.json (claire_output.py, on-path) == 8, persisted. The notify-side behavior (cycle in alert, applied-count surfacing) never runs on GHA. June 14 mistitle risk was real but masked this once (three cycle-8 entries forced max==8). See "notify path divergence" below. |
| notify path divergence (run #29, 2026-06-14) - HIGH, OPEN | GHA "Notify via Pushover" step is an inline curl: hardcoded `title=CLAIRE`, `message="CLAIRE digest ready -- <date>"`, PDF attached. `claire_notify.py` is invoked by ZERO workflow steps (confirmed against full claire_weekly.yml). All claire_notify.py features - cycle in notification, applied-count surfacing, 2.5MB oversize text-only fallback - never run on the production path and presumably never have; all past alerts were cycle-less. HANDOFF locked decisions + directory tree document claire_notify.py as the dispatcher; production uses the inline curl. A twice-tagged (v2.1.2/v2.1.3) capability that has never run in production. DECISION OWED (ranked above switch-on): wire the workflow to claire_notify.py, OR accept the inline curl and stop documenting the script as the dispatcher. Applied-count verification stays impossible until resolved. |
| 06-21 cycle mislabel (cycle 9 shipped as c8) - RESOLVED 2026-06-28 | The 2026-06-21 run shipped as claire_digest_2026-06-21_c8.pdf instead of c9. Mechanism: config.pipeline.current_cycle was never advanced to 9 on main before the 06-21 14:00 UTC cron, so claire_output read 8 and stamped c8. Human-side ritual gap (Local-vs-GHA rule 2: an unpushed/skipped config edit runs silently against last week's value with no warning), NOT a code defect — v2.1.2 reported config faithfully; the digest cover subtitle (claire_output.py, on-path) rendered exactly what config held. This is the downstream consequence of the same config-as-single-source design the notify fix introduced: correct mechanism, stale input. Detected 2026-06-28 by the cycle-label collision (06-21 PDF self-labeled c8 while the cycle log expected c9). Correction: config bumped 8→10 pre-run (commit 23a196f), a DATE-MAP decision — 06-21 recorded as "cycle 9, mislabeled c8", 06-28 = cycle 10 per the cycle log, no forward renumber. Quarantined to 06-21. Graduation clock unaffected (counts qualifying runs from the 06-14 reset, not labels). Standing exposure: the increment is a manual weekly keystroke with no guard; a skipped or unpushed bump repeats this silently. Candidate hardening (not built): a pre-run check that refuses to run if config.current_cycle equals the last digest's cycle — with a manual-backfill escape, since a legitimate re-run would trip it. |
| cost_log upsert not merging (run #29, 2026-06-14) - MEDIUM, OPEN | cost_log.json wrote three separate rows for the single run #29, all keyed `_match_key 20260614` (timestamps within 20s). Locked decision specifies one upsert per run by date key. Each stage appends its own row instead of accumulating. Cost total correct (0.1257 = sum, matches cumulative); shape wrong; `total_runs` reads 3 for one weekly run because it counts rows. Build 14 atomic_write_json fixed corruption but the upsert-merge-by-key is unimplemented or regressed. Verify against claire_utils append_cost_log / upsert path. |
| verification-spec fabrication (run #29, 2026-06-14) - MEDIUM, process | The June 14 verification checklist (authored in-session) asserted a Pushover title "reads CLAIRE Cycle 8" as a pass condition, then located applied-count successively in a notification body and in claire_notify.py output. None existed: title hardcoded CLAIRE, no body (title + timestamp + PDF thumbnail only), script not on GHA path. Three assertions about where a value lived, each corrected only by reading raw output. Same defect class hallucination-guard targets, originating in the verification spec not the pipeline. Lesson: verification conditions must be read from the code/output they assert, not specified from recall. Logged to friction 2026-06-14 under Claude error. |
| CLAUDE.md enum drift (RESOLVED 2026-06-13) | Schema doc lagged live enum values: action missing modify/retire, type missing pipeline_change, scope missing process. Reconciled (commit 0d0fc96) by reading live distinct values, not recalled ones. The first sync pass this session was itself incomplete — caught on a second pass. Lesson recorded: doc reconciliation must read live values. |
| memory summary fabrication | Generated Claude memory summary recorded an NVDA Jan 2027 $185 put as a live holding (full entry price + thesis, formatted identically to real positions). Operator confirmed the position was never held — a worked analytical example promoted to a recorded holding during summarization. Structured memory edits were clean; fabrication lived only in the generated summary layer. Guarded by memory edit 20 (narrow: excludes NVDA holdings, preserves NVDA as analytical subject). Implication for CLAIRE: any stage ingesting memory state as ground truth (assembler memory snapshot, cross-reference gate) inherits summary-layer fabrications. Treat memory-snapshot inputs as operator-confirmable, not authoritative. |
| index.lock prefix vs harness guard (2026-06-13) | The `Remove-Item .git\index.lock` session-start prefix aborted the first commit attempt this session — hit a path guard in the execution harness. Commit succeeded once the prefix was dropped. The documented session-start step now conflicts with this environment. Next session will hit it cold. Candidate fix: make the prefix conditional, or note that the harness manages the lock. Logged to friction 2026-06-13. |
| actions/cache Node 20 deprecation (LOW, open) | actions/cache@v4 uses Node 20; GHA runs Node 24. Warning on every run, not a failure. Fix: bump to actions/cache@v5 in claire_weekly.yml. |

---

## June 14 Run Verification - CLOSED 2026-06-14

Run #29 (Sunday 14:00 UTC, cycle 8) is complete and verified. Below is the verification
result. The two deliverables it was verifying (notify cycle-identity fix, official-signal
lane dormant-ship) shipped in the PRIOR 2026-06-13 wrap session and are summarized after
this block for provenance.

**VERIFICATION RESULT - run healthy, three findings, one HIGH.**

Five-point checklist outcome:
1. Pushover title "CLAIRE Cycle 8" - STRUCK, never a valid check. Title is hardcoded
   `CLAIRE`; the cycle was never in it. The claire_notify.py cycle-aware title is not on
   the GHA path (see finding A).
2. Applied-count == 3 - UNOBSERVABLE on GHA. The only code that computes/surfaces it is
   claire_notify.py, which the workflow does not invoke. Not failed; unreachable. The
   ledger supports 3 (c8-prof-001 add + c8-mem-001/002 retires); the runtime value is not
   emitted anywhere on the GHA path.
3. cycle_state.json == 8, persisted - PASS. Read off run #29 commit-back:
   `last_completed_cycle: 8`, `last_completed_at: 2026-06-14T15:52:19Z`,
   `digest: claire_digest_2026-06-14_c8.pdf`. This is written by claire_output.py at
   generate_pdf (on-path) and is the ONLY artifact proving any cycle-identity work reached
   production. Confirm the file's latest change on main is the run #29 bot commit, not frozen.
4. cost_log no lane cost - PASS. Run #29: triage 0.0951 + synthesis 0.0306 + assembler 0.0
   = 0.1257. No official-signal/Haiku lane line. enabled:false gate HELD. (Side-finding:
   three rows per run, see finding B.)
5. Digest disabled capability-delta line - PASS (confirmed in the digest PDF).

**Findings (all logged to friction 2026-06-14):**
- A. notify path divergence - HIGH. GHA notifies via inline curl; claire_notify.py runs
  nowhere in the workflow. The v2.1.2/v2.1.3 notification features never reach production.
  RANKED NEXT-SESSION LEAD, above switch-on. See Known Issues.
- B. cost_log upsert not merging - MEDIUM. Three rows per run; total correct, shape wrong.
- C. verification-spec fabrication (Claude) - MEDIUM. The checklist asserted a title format
  and value locations that did not exist; caught only by reading raw output. Logged under
  Claude error.

**On the merits, switch-on is UNBLOCKED:** run clean, lane dark, cycle identity correct
on-path, costs normal. The notify-verification gate turned out unobservable, not failed.
Switch-on remains a deliberate operator action (own commit, c8-process-002 logging) and
should be sequenced AFTER the notify-divergence decision, which now outranks it.

**Staged / held, untouched by this session's friction commit:**
- c8-process-003 in change_log: source-URL suppression flag. Hypothesis APPROVED (operator,
  in-session). Entry PENDING-AUTHORIZATION, not yet in the ledger. Claude Code task spec
  written. Build is a separate single-variable commit when authorized.
- claire_a_assembler.py: source-URL suppression code BUILT, verified offline, UNCOMMITTED
  in the working tree. Held so it ships as the next single variable after the notify run
  proved clean.
- config.json official-signal lane: enabled:false. Switch-on pending.

**Friction log: brought to LIVE MATCH 2026-06-14** (five entries, two dated blocks):
06-13 owed writes (index.lock harness-guard MEDIUM; read_cycle_number pre-fix confirmation
LOW) + 06-14 verification (notify path divergence HIGH; cost_log upsert MEDIUM;
verification-spec fabrication MEDIUM).

**change_log entry count: 59 - UNCHANGED through run #29.** Next ledger write is whichever
lands first: c8-process-003 at build authorization, or c8-process-002 at lane switch-on.

---

## Prior Session - Cycle 8 Wrap (2026-06-13) - deliverables verified by run #29

**Deliverable 1 - notify cycle-identity fix. SHIPPED, tagged. PROVED OUT ON-PATH ONLY.**
- v2.1.2 (commit 74af5ef): read_cycle_number() reads `config.pipeline.current_cycle`
  (nested), SystemExit(1) on missing key, no change_log fallback. Applied-count queries
  change_log scoped to current_cycle, APPLIED_ACTIONS = {add, apply, modify, retire},
  queued excluded, zero allowed; cycle 8 yields applied = 3. last_completed_cycle written
  to data/cycle_state.json at generate_pdf via atomic_write_json.
- v2.1.3 (commit 38abf20): cycle_state.json added to GHA enumerated commit-back.
- RUN #29 OUTCOME: the cycle_state.json write is on the GHA path and verified (== 8). The
  rest of the fix lives in claire_notify.py, which the GHA workflow does NOT call - so the
  notification-facing behavior never ran. Fix is correct and, for notification, unreached.
  See finding A / Known Issues "notify path divergence".

**Deliverable 2 - official-signal lane (Proposal 1). BUILT DORMANT, on main, UNTAGGED.**
- Commit 9ce68da. enabled:false. Run #29 confirmed the gate held (no lane cost, finding 4).
- See "Official-signal lane - switch-on pending" under Build Status for the switch-on
  procedure and deferred-logging list. Do not re-derive; it is recorded.
- WITHDRAW scope note (provenance): Fable June 12 is a TRUE POSITIVE / covered case via
  release-notes prose. The uncovered gap is narrower: withdrawals announced ONLY by
  email/status page with no published release-note or deprecations-table entry.

---

## Prior Session — Cycle 8 Design (2026-06-13, earliest)

Kept for provenance. Focus: model-routing de-rot, doc-schema reconciliation,
memory-fabrication catch.

- c8-prof-001 (commit 7e69481): MODEL ROUTING block. Replaced per-version model
  preferences with one dated, self-maintaining rule. Browser profile, scope global.
  Governs browser profile routing ONLY; does not touch config.json pipeline-stage models.
- c8-mem-001 / c8-mem-002 (commit f6afcb7): retired c2-mem-002 (4.7 flag) and
  c4-mem-002 (4.6 preference). Both superseded by c8-prof-001. Removed from live memory.
- Doc reconciliation to live v1.2 schema: CLAUDE.md (schema/scope/eval_window/enums,
  commits 1635229, 0d0fc96), README.md (version 1.1→1.2), change_log _meta.notes.
- Memory edit 20: holds no NVDA position; prior summary NVDA detail (Jan 2027 $185 put)
  was analytical, not a holding; NVDA still permitted as analytical subject.
- Schema enum reality (live-audited): action add|apply|queued|modify|retire;
  type memory_edit|profile_diff|skill_install|pipeline_change; scope global|project|process;
  eval_status pending|held|partial|no|queued|n/a (held+partial UNUSED across all entries —
  quarterly question).

---

## Open Proposals (scoping started 2026-06-13)

1. **Official-signal ingest lane (Proposal 1) — BUILT DORMANT 2026-06-13, gate VERIFIED
   HELD by run #29. Now a switch-on decision, sequenced behind the notify-divergence call.**
   Authoritative Anthropic release-notes + deprecations-table source, capability-delta
   candidate type, block-level touch-test gate anchored to change_log c8-prof-001, no
   3-post threshold. Shipped enabled:false, untagged (commit 9ce68da). Run #29 confirmed no
   lane cost — gate held. Switch-on UNBLOCKED on the merits but should follow the HIGH
   notify-divergence decision. The ratified operator hypothesis is held for c8-process-002
   and must be supplied at switch-on (operator-authored; Code cannot write it). See
   "Official-signal lane — switch-on pending" under Build Status. REMAINING WORK is
   switch-on, not build.

2. **Model-routing enforcement (Proposal 2 — cheap once Proposal 1 is live).**
   Launch-triggered review that flags the MODEL ROUTING block stale on any model event.
   The staleness rule is in the profile (c8-prof-001) but nothing in CLAIRE enforces it;
   reconciliation is manual. Shares the model-event signal with the now-built Proposal 1
   lane — natural next build once the lane is switched on and producing capability-deltas.
   STILL OPEN.

3. **Skill-marketplace monitoring (Proposal 3 — lowest urgency).** Discovery via
   first-party Anthropic directory (claude.com/connectors) + Agent Skills standard.
   Third-party aggregators are vet-only LEADS, never install sources (supply-chain +
   injection risk). Trigger for when an attached skill is superseded by a first-party
   equivalent. Do NOT auto-ingest third-party skills. STILL OPEN.

---

## Carried Forward — Still Open

**NEXT SESSION (cycle 11 prep + lead items):**
- LEAD (HIGH, outranks switch-on): resolve the notify path divergence. Decide whether to
  wire claire_weekly.yml's notification to claire_notify.py (restoring cycle-in-alert,
  applied-count surfacing, 2.5MB oversize fallback) OR accept the inline curl and strip
  claire_notify.py from the documented dispatcher role. Until resolved, applied-count
  (v2.1.2) is unverifiable and a twice-tagged capability sits unused. See Known Issues.
- PIPELINE-HEALTH READS (owed, first actions next session): two frozen-artifact signals
  surfaced 2026-06-28 that need confirmation, not assumption:
  - ingest_run_log.json: CONFIRMED. Verification dispatch 2026-06-28 shows
    HN was returning 0 posts due to numericFilters 400 (fixed 75fbb0f).
    Cycles 9-10 ran on dev.to only. Not a Reddit/archive dedup artifact —
    a code bug. Next cycle 11 run should show full dual-source corpus.
  - CLAIRE-A ledger (claire_a_source_reliability.json): frozen at 5 observations, all keyed
    `unknown`, last_updated 2026-06-02. No growth across 06-14 or 06-21 GHA runs despite the
    Build 14 commit-back fix meant to enable it. Cause unconfirmed (no scorable candidates on
    thin corpus vs. commit-back not landing vs. windows not elapsed). Graduation clock is
    advancing over a ledger that hasn't moved in weeks — a run that scores zero observations
    may not be substantively qualifying. Verify against GHA run logs.
- c8-process-003 build authorization (source-URL suppression). Hypothesis approved; code
  staged+verified offline in claire_a_assembler.py (still UNCOMMITTED in the working tree);
  task spec written. Authorize → Code commits it as the NEXT single variable (its own commit,
  separate from notify-divergence work and from switch-on). On commit: flip entry date off
  PENDING-AUTHORIZATION, add to ledger, eval_window cadence "per source-duplicate occurrence;
  first assessment at first flag fire" (NOT a 14/21d duration - same cadence-token class as
  c8-process-002).
- Official-signal lane SWITCH-ON (operator decision, sequenced AFTER the notify-divergence
  call): flip config.official_signal.enabled to true; supply the ratified c8-process-002
  hypothesis (operator-authored, held from design - paste, do not re-derive); Code then
  writes c8-process-002 + the eval_window _meta.notes duration-or-cadence extension + the
  friction "lane live, baseline 0/3" note together, and tags release v2.2.0.
- README + version pass (pairs with switch-on): reflect Reddit retirement (still describes
  Reddit as a live source - stale since Build 10), document the official-signal lane,
  reconcile the version string. RESOLVE the README-"release"-string-vs-tags discrepancy
  (repo tags at v2.1.3; README lags - confirm canonical before bumping to v2.2.0).
- Cycle 11 pre-run ritual before Sunday 2026-07-05 14:00 UTC: increment
  config.pipeline.current_cycle to 11 (nested), update data/session_notes.txt, commit+push
  both before cron. THE LOAD-BEARING KEYSTROKE — skipping it is exactly the 06-21 mislabel.

**DONE this session (2026-06-28 cycle-10 pre-run, no longer carried):**
- Cycle-numbering correction - COMPLETE. 06-21 mislabel diagnosed (config never advanced to
  9 before the 06-21 cron, confirmed by direct config read == 8). Decision: bump 8→10
  (date-map). config bumped, cycle-10 session_notes written with both file-backed numbers
  read from disk (cost_log 6 rows/2 runs/+4 overcount; ledger 5 obs frozen at 06-02), gate
  pushed before 14:00 UTC (commit 23a196f). HANDOFF cycle log + Known Issue updated.
- Cycle 9 pre-run ritual - SUPERSEDED, not done as such. The 06-21 run already fired against
  config=8; the missed increment is recorded as the mislabel, not re-run.

**DONE prior session (2026-06-14, no longer carried):**
- June 14 run verification - COMPLETE. Run healthy; three findings logged. See the
  verification-closed block above.
- Friction writes - DONE through 2026-06-14. NOTE: this session (06-28) owes three more
  friction entries not yet written at HANDOFF-update time — 06-21 mislabel mechanism, plus
  the two carried from 06-13 (index.lock harness-guard, notify pre-fix max-of-all masked-once).
  Pull-first; friction_log is in GHA commit-back. Write before the project-knowledge refresh.

**Switch-on deferred-logging conditions (from the lane build):**
- eval_window date-math consumer audit: any consumer doing date math on eval_window must
  branch on a cadence token rather than parse it as a duration (cf. cycle-5 "eval window
  elapsed"). NOW APPLIES TO TWO entries: c8-process-002 (per-model-event) and c8-process-003
  (per source-duplicate occurrence). Fold into one audit pass.
- _meta.notes eval_window definition extension to duration-or-cadence: owed at the FIRST
  cadence-window ledger write (whichever of c8-process-002 / c8-process-003 lands first),
  not just at switch-on.
- profile_snapshot.txt refresh: still stale at the retired "Opus 4.6 > 4.7" preference;
  carry the MODEL ROUTING block instead. Gate does not depend on it — standing debt, but
  any other stage reading the snapshot as truth inherits stale routing guidance.

**Pending — human action (from Build 13 / v2.0.0):**
- Write hypotheses for c6-prof-006 through c6-prof-012, c6-skill-001, c6-skill-002
  (hypothesis_prompt field in each change_log entry carries the prompt).

**Longer tail:**
- CLAIRE-A graduation timeline — two checkpoints:
  - June 22 = first post-fix run review: pipeline health, ledger growth, first
    qualifying run scored correctly. NOT a graduation decision.
  - Graduation review = after 10 consecutive qualifying runs from June 14 reset.
    Weekly cadence puts earliest graduation late October.
- c6-skill-001: business-case-builder — BAA/FedRAMP blocking disqualifier addition.
- c6-skill-002: internal-comms — doc-generation-theme + docx-env co-trigger.
- autocrlf awareness note: repo has LF/CRLF normalization; harmless until a
  normalization churn is mistaken for a real diff.
- held/partial eval_status quarterly question: unused across 59 entries — either
  the eval loop never reaches them or the rubric is wrong.
- .claude/ directory untracked — gitignore entry or explicit decision to track.
- Assembler mojibake cleanup — cp1252 encoding in claire_a_assembler.py.
- Skills audit sessions 3+ — remaining installed skills not yet audited against Profile v13.
- Memory-fabrication follow-up: scan remaining summary portfolio claims (SCHD/SCHG
  barbell, options positions) against actual book; assembler memory snapshot input
  should be treated as operator-confirmable, not authoritative.

---

## Session Close — Project Knowledge Refresh

Refresh change_log.json, friction_log.txt, and this HANDOFF.md into Project knowledge so
the next session (cycle 11 prep) starts from 2026-06-28 cycle-10 pre-run truth: config at 10
on main (commit 23a196f), 06-21 mislabel diagnosed and quarantined (date-map bump 8→10),
cycle-10 session_notes written from disk-read numbers, gate pushed before the 14:00 UTC cron.
Root canonical files ONLY — not data/ artifacts, not the profile.

SEQUENCING (do not refresh early): the project-knowledge refresh is the LAST act, AFTER the
three owed friction writes (06-21 mislabel mechanism + the two carried from 06-13) land in
friction_log.txt. Refreshing before those writes bakes a half-done state into project
knowledge that reads as authoritative — the same stale-but-trusted shape that caused the
06-21 mislabel. config.json also belongs in the refreshed set now (carries current_cycle);
a stale project copy re-inherits the exact confusion this session resolved.
Post-verification: HN fix confirmed (fetched=150, new=62). v2.1.4 tagged.
raw_posts cache operational. friction_log at live match through 2026-06-28
verification dispatch.

Open work into cycle 11: notify-divergence decision (HIGH lead), the two pipeline-health
reads (ingest_run_log.json source counts, frozen CLAIRE-A ledger), c8-process-003 build
authorization, lane switch-on, README/version pass. change_log unchanged at 59 entries (a
cycle bump is operational state, not a logged change); its next write is whichever lands
first — c8-process-003 at build authorization or c8-process-002 at switch-on.

POST-RUN VERIFY (after today's cron, read from artifacts NOT a pre-written checklist — the
finding-C lesson): open the actual claire_digest_2026-06-28_c10.pdf cover subtitle (reads
"Cycle 10"), read cycle_state.json off the run's bot commit-back (last_completed_cycle == 10),
read cost_log rows for the run. Drop the Pushover-title and applied-count checks entirely —
not observable on the GHA path (notify divergence). What the artifacts say is what happened;
what you expected them to say is not evidence.
