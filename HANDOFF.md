---
> Read this first. Every session. No exceptions.
> State as of 2026-07-20 documentation-reconciliation session (design mode, no runs).
> True cadence cycle 13 completed on the 2026-07-19 GHA run. Next live event:
> Sun 2026-07-26 14:00 UTC GHA run = cycle 14. NO manual cycle increment is owed
> anymore (Counter Fix A made cycle_state self-incrementing; see below).
>
> Verified against git this session: four commits above 4cae840 plus annotated tag
> v2.1.5. Anchors used throughout this file: 88a7808 (Counter Fix A), 1282c37
> (notify wire), 85d9444 (c8-process-003 entry), 8975444 (cycle-13 friction),
> 2d75cd3 (c8-process-003 code, shipped June). Repo convention is TAGS, not GitHub
> Releases: `git describe` is canonical; the Releases sidebar intentionally lags and
> is not drift.
>
> THREE prior HIGH/lead items are now CLOSED, not open:
>   (1) Frozen cycle counter -> FIXED (88a7808). config.pipeline.current_cycle
>       orphaned at 10, deliberate retire pending (single variable, next Code session).
>   (2) Notify path divergence -> RESOLVED (1282c37, wired to claire_notify.py).
>       Pending only cycle-14 runtime verification of applied-count surfacing.
>   (3) c8-process-003 -> SHIPPED and LOGGED (code 2d75cd3, entry 85d9444). Not staged.
>
> Discipline note (the whole reason this session exists): the prior root defect class
> was stale self-description trusted as truth. cycle_state.json was DOCUMENTED as an
> independent cycle owner while its write site copied config verbatim, so it inherited
> the freeze. A file is not an independent source of truth until you read its write
> site. Every line below traces to a commit, a tag, or a file read, not to recall.

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
| CI/CD | GitHub Actions, `.github/workflows/claire_weekly.yml` |
| GHA trigger | Cron `0 14 * * 0` (Sundays 14:00 UTC) + `workflow_dispatch` |
| GitHub repo | https://github.com/not-yet-autonomous/CLAIRE |
| Current tag | v2.1.5 (annotated). `git describe` canonical; Releases sidebar lags by convention. |

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

True cadence cycle is the authoritative cycle number (weekly cron, no skips from
06-14). The digest filename suffix is the artifact actually written to `output/`.
For 06-28 through 07-19 the suffix froze at `_c10` because the counter was frozen;
the true cadence cycle advanced underneath it. This split is the single most
important thing to understand in this log.

| Cadence cycle | GHA Run Date | Digest filename (actual) | Note |
|---------------|--------------|--------------------------|------|
| 1 | — | Pipeline validation only | |
| 2 | 2026-05-03 | Not tracked | |
| 3 | 2026-05-10 | Not tracked | |
| 4 | 2026-05-17 | Not tracked | |
| 5 | 2026-05-17 | claire_digest_2026-05-23.pdf (local rebuild) | |
| 6 | 2026-05-31 | claire_digest_2026-05-31.pdf | |
| 7 | 2026-06-07 | claire_digest_2026-06-07.pdf | |
| 8 | 2026-06-14 | claire_digest_2026-06-14_c8.pdf | run #29, verified |
| 9 | 2026-06-21 | claire_digest_2026-06-21_c8.pdf | MISLABELED c8: config never advanced to 9 pre-cron; recorded as cycle 9 by date-map |
| 10 | 2026-06-28 | claire_digest_2026-06-28_c10.pdf | config bumped 8->10 pre-run (commit 23a196f) |
| 11 | 2026-07-05 | claire_digest_2026-07-05_c10.pdf | FROZEN: counter stuck at 10 |
| 12 | 2026-07-12 | claire_digest_2026-07-12_c10.pdf | FROZEN: counter stuck at 10 |
| 13 | 2026-07-19 | claire_digest_2026-07-19_c10.pdf | FROZEN (4th `_c10`); freeze diagnosed this run; Counter Fix A applied, cycle_state corrected 10->13 |
| 14 | 2026-07-26 (next) | expect claire_digest_2026-07-26_c14.pdf | first run under Counter Fix A + notify wire; first correct auto-stamp |

Filename caveat: the four `_c10` suffixes (06-28, 07-05, 07-12, 07-19) trace to the
friction 2026-07-19 "_c10 x4" observation plus the run dates. The exact date portions
for 07-05 and 07-12 are reconstructed from cadence, not read off `output/` this
session. Confirm against `output/` glob on the next Code session if precision matters.

---

## Session Start Checklist

**GitHub Actions runs require no manual start.** The pipeline triggers on the Sunday
14:00 UTC cron or via `workflow_dispatch` in the Actions UI. Monitor at the repo's
Actions tab.

**Pre-Sunday ritual (manual, before cron fires) - UPDATED after Counter Fix A:**
1. NO cycle increment. `config.pipeline.current_cycle` is orphaned at 10 and is no
   longer read for cycle identity. Do not touch it. cycle_state.json now self-increments
   the cycle on the output path (Counter Fix A, 88a7808). The "load-bearing keystroke"
   that caused the 06-21 mislabel and the four-week freeze no longer exists.
2. Update `data/session_notes.txt` with the week's behavioral observations. Still
   required: the CLAIRE-A scorer reads it. Stale notes are a signal-quality failure,
   not a pipeline failure.
3. Commit and push session notes before the cron.

For local Cowork sessions, before doing anything else:

```powershell
cd "C:\DEV\CLAIRE"
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1
python -c "import anthropic, requests; print('Deps OK')"
```

Expected: `(.venv)` in prompt + `Deps OK`. If venv fails, use `.\.venv\Scripts\activate.bat`.
If deps fail, `python -m pip install -r requirements.txt`.

**Pre-push verification (before any commit touching data/ or git state):**
```powershell
git ls-files data/
```
Expected: `data/raw_posts.json`, `data/profile_snapshot.txt`, `data/session_notes.txt`,
plus the CLAIRE-A state files committed back by GHA since Build 14
(`claire_a_decisions_*.json`, `claire_a_session_history.json`,
`claire_a_source_reliability.json`, `cost_log.json`, `suppressed_candidates_*.json`).
Any other filename is a tracked data file that should not be in the index. Run
`git rm --cached <file>` before pushing.

**Pre-push hook scope (Build 14):** the hook at `.git/hooks/pre-push` blocks local
pushes with staged `data/` files. Local-only (hooks are not versioned), so it does not
exist on the GHA runner and does not block the GHA commit-back. It will also block
staged changes to the now-tracked state files locally, which is intentional: those are
written by the pipeline and committed back by GHA, not edited by hand.

**index.lock, CONDITIONAL, do not run blind (harness-guard finding):**
```powershell
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -ErrorAction SilentlyContinue }
```
The unconditional `Remove-Item .git\index.lock` prefix aborted commits twice on the
execution harness path guard. Run it conditionally, or assume the harness manages the
lock and skip it.

**Strip FUSE null-byte corruption before working:**
```powershell
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

---

## Local vs. GHA, Operational Discipline

Two environments run the same pipeline. GHA is the canonical production path; pull
after each run completes.

1. **Pull before editing `change_log.json` or `friction_log.txt`.** GHA commits both
   back on every run. A local edit without a prior pull conflicts on push.
2. **Push `config.json` before Saturday.** GHA runs whatever `config.json` is on main
   at 14:00 UTC Sunday. Note: `current_cycle` is now orphaned, so this rule now matters
   only for the non-cycle config keys (ingest terms, thresholds, official_signal block).
3. **Push `session_notes.txt` before Sunday 14:00 UTC.** The scorer requires current
   content.
4. Memory edits are scoped to this project only. Global behavioral changes must be
   profile diffs. Use `data/profile_snapshot.txt` as the global baseline for synthesis
   cross-reference (note: snapshot is stale, see Carried Forward).
5. Hypothesis prompts for pending entries live in the `hypothesis_prompt` field of each
   change_log entry. If absent, the prompt is lost. Add at entry-creation time.

---

## Directory Structure (delta-noted; unchanged files omitted for brevity)

```
CLAIRE\
├── claire_output.py          ✅ Counter Fix A (88a7808): run cycle = cycle_state.last_completed_cycle + 1; cycle_state is the SOLE output-path cycle owner and self-increments; one-time 10->13. cycle_state is no longer a config mirror.
├── claire_notify.py          ✅ WIRED (1282c37): now invoked by claire_weekly.yml (was inline curl). Cycle read repointed config -> cycle_state. Digest located by glob, not filename reconstruction. v2.1.2 applied-count logic reaches production first on the cycle-14 run.
├── claire_a_assembler.py     ✅ c8-process-003 source-URL suppression COMMITTED (code 2d75cd3, June; entry 85d9444, cycle 13). Build 11 load_dotenv fix; Build 5 base.
├── config.json               ✅ config.pipeline.current_cycle ORPHANED at 10 (no longer read; retire pending). official_signal block enabled:false.
├── change_log.json           ✅ CANONICAL, root. v1.2 schema, Cycles 2-13, 60 entries (c8-process-003 added cycle 13). _meta.notes carries the cadence eval_window extension (first cadence use).
├── friction_log.txt          ✅ CANONICAL, root. Cycles 1-13. Cycle-13 block (8975444): frozen counter HIGH; within-cycle dedup + c7-prof-001 confabulation MEDIUM.
├── .github\workflows\claire_weekly.yml ✅ Notify step now calls claire_notify.py (1282c37). Official-signal lane step present, self-gating on enabled:false.
├── data\
│   ├── cycle_state.json                    ✅ Now the INDEPENDENT self-incrementing cycle owner (last_completed_cycle, last_completed_at, digest). Corrected to 13. No longer mirrors config. Enumerated GHA commit-back.
│   ├── claire_a_source_reliability.json    ⚠ PRESENT but DEAD since 2026-06-02: 5 observations, all keyed `unknown`, no growth across any GHA run since. Scorer not writing. See Known Issues + Carried Forward.
│   ├── profile_snapshot.txt                ⚠ STALE at retired "Opus 4.6 > 4.7". Should carry the MODEL ROUTING block. Standing debt; gate does not depend on it.
│   └── official_signal_seen.json           ✅ Dedup memory; empty until lane enabled.
└── (all other files unchanged from Build 14 state)
```

**Path rule:** `change_log.json` and `friction_log.txt` live at project root. `data/`
holds no canonical copy of either. `data/change_log_v1_legacy.json` is a read-only v1.0
archive.

---

## Locked Pipeline Decisions (updated rows in bold-context)

| Decision | Value |
|----------|-------|
| Config injection | Partial (intent summary + memory list) |
| Developer persona | Filter out entirely |
| Hypothesis authorship (applied changes) | Human-written |
| Evidence threshold | 3 corroborating posts minimum (Track A) |
| Triage model | claude-haiku-4-5-20251001 |
| Synthesis model | claude-sonnet-4-6 |
| Noise prefilter | score < 5 AND comments < 2 -> drop |
| Scheduling | GHA Sunday 14:00 UTC (all ingest sources) |
| **Cycle identity source** | **cycle_state.last_completed_cycle + 1, owned and self-incremented by claire_output.py at generate_pdf (Counter Fix A, 88a7808). cycle_state.json is the sole output-path cycle owner and is independent of config. claire_notify.py reads cycle from cycle_state (1282c37). config.pipeline.current_cycle is ORPHANED at 10, retire pending. Never derive identity from change_log.** |
| **cycle_state.json** | **Machine-written, self-incrementing runtime state. Was a config mirror (root cause of the freeze); is now genuinely independent. Enumerated GHA commit-back.** |
| **Notify dispatch** | **claire_weekly.yml calls claire_notify.py (1282c37). Cycle-in-alert, applied-count surfacing, and 2.5MB oversize text-only fallback are now on the production path. Applied-count surfacing is verifiable first on the cycle-14 run.** |
| Cost log entries | Single upsert per run keyed by YYYYMMDD. ⚠ DIVERGENT since run #29: writes one row per pipeline stage (~3 rows/run); total correct, `total_runs` overcounts. OPEN. See Known Issues. |
| Opus exclusion | exclude_keywords in config.json |
| Shared utilities | claire_utils.py |
| Track A batching | Signal cluster by signal_type, max 50 posts per call |
| CLAIRE-A mode | Shadow only, writes nothing to live config |
| Decision engine model | claude-opus-4-5 |
| Eval scoring model | claude-sonnet-4-6 |
| Batch size ceiling | 15 candidates per decision engine run |
| CLAIRE-A graduation criteria | 10 consecutive qualifying eval runs, clock reset 2026-06-14. ⚠ MOOT until the scorer writes again (reliability ledger dead since 06-02). |
| Eval window | 14d (format/behavior), 21d (memory/behavioral), OR a cadence token (first cadence use: c8-process-003, per source-duplicate occurrence). |
| Ingest sources | HackerNews + dev.to (GHA, Sunday 14:00 UTC) |
| dev.to tags | anthropic, claudeai, claude, llm, aitools, machinelearning, ai, chatgpt, productivity |
| PDF output | reportlab, six-section digest; filename `claire_digest_YYYY-MM-DD_cNN.pdf` |
| Memory filter threshold | 0.85 semantic similarity (Haiku, assembler) |
| Commit-back strategy | GHA commits data/, output/, logs/, change_log.json, friction_log.txt each run |
| Official-signal lane | Built dormant (enabled:false). Capability-delta type. Block-level gate anchored to change_log c8-prof-001. Switch-on operator-gated; documented in README only at switch-on with the v2.2.0 tag. |

---

## Known Issues (resolved items retained for provenance)

| Issue | Status / Detail |
|-------|-----------------|
| **Frozen cycle counter (four-week freeze, 06-28..07-19)** | **RESOLVED, Counter Fix A (88a7808).** current_cycle stuck at 10 across four runs; all four digests stamped `_c10`. Root cause: cycle_state.json `last_completed_cycle` was a config mirror (claire_output wrote current_cycle verbatim), so the intended independent witness inherited the freeze, and the comment block above the write site documented a separation-of-concerns safeguard the code did not implement. Fix: claire_output derives cycle from cycle_state.last_completed_cycle + 1; cycle_state is now the self-incrementing sole owner; one-time correction 10->13. config.pipeline.current_cycle orphaned at 10, retire pending. |
| **06-21 cycle mislabel (cycle 9 shipped as c8)** | **RESOLVED as a class by Counter Fix A.** Was a manual-keystroke gap (config not advanced before cron). The manual increment no longer exists, so the exposure is gone. Historical: recorded as cycle 9 by date-map; config bumped 8->10 at 06-28 (commit 23a196f). |
| **Notify path divergence** | **RESOLVED, notify wire (1282c37).** claire_weekly.yml now calls claire_notify.py; the inline curl is retired. Cycle-in-alert / applied-count / oversize fallback are on the production path. Pending only cycle-14 runtime verification that applied-count surfaces in the actual alert. |
| **c8-process-003 (source-URL suppression)** | **SHIPPED and LOGGED.** Code committed 2d75cd3 (June); change_log entry 85d9444 (cycle 13) with the recovered ratified hypothesis. Not staged, not held. eval_window is a cadence token (per source-duplicate occurrence; first assessment at first flag fire). Within-cycle dedup case (below) may still need the same suppression at synthesis, not just assembler. |
| read_cycle_number cycle lag | RESOLVED. Superseded by the cycle_state ownership model. |
| cost_log upsert not merging | OPEN, MEDIUM. One row per pipeline stage (~3/run); cost total correct, `total_runs` overcounts by ~2/run. Build 14 atomic_write_json fixed corruption but not the upsert-merge-by-key. Verify against claire_utils append_cost_log / upsert path. |
| **CLAIRE-A reliability ledger dead** | OPEN, blocks graduation. `claire_a_source_reliability.json` frozen since 2026-06-02: 5 observations, one `unknown` key, no growth across any GHA run despite the Build 14 commit-back fix. Diagnosed, not fixed. Diagnostic commands exist from the prior session. Graduation is meaningless until the scorer writes again. |
| **CLAIRE-A confabulation pattern** | STANDING CAVEAT, three cycles deep (2026-06-02 ALREADY_APPLIED over-generalization; 2026-06-28 invented schema defect + miscounted entries 73 vs 59; 2026-07-19 cited nonexistent c7-prof-001 as harm-threshold basis, when live change_log has only c7-process-001 and the harm-threshold language is c6-prof-003). The engine fabricates plausible-but-false self-referential artifacts (citations, schema claims, counts), worst on empty/thin candidate batches. Treat any engine self-referential claim as unverified until checked against the live file. |
| within-cycle dedup failure (07-19) | OPEN, MEDIUM. The 07-19 digest promoted three HIGH profile candidates from five source posts; HN 48875494 was load-bearing in all three, and three of five posts were recycled from 07-05/07-12 already-dispositioned cycles, yet all CLAIRE-A candidates were tagged SOURCE_NEW. The raw_posts / actions/cache dedup soft spot now fires inside one digest, not just across weeks. c8-process-003 addresses the cross-cycle case at the assembler; the within-cycle case may need suppression applied at synthesis. |
| HN ingest zero-posts | RESOLVED (v2.1.4, commit 75fbb0f). numericFilters 400 fixed; fetched=150, new=62 confirmed. Cycles 9-10 had run dev.to-only; dual-source expected from cycle 11 onward (not independently re-verified in this doc session). |
| actions/cache Node 20 deprecation | LOW, open. Warning each run, not a failure. Bump to actions/cache@v5. |
| profile_snapshot.txt GHA degradation | Gitignored; GHA uses a placeholder; cross-reference gate runs without profile context on automated runs. Also stale at "Opus 4.6 > 4.7". Refresh to carry MODEL ROUTING block. |
| memory summary fabrication | Guarded by memory edit 20 (no NVDA holding; NVDA analytical-subject only). Any stage ingesting memory state as ground truth inherits summary-layer fabrications; treat memory-snapshot inputs as operator-confirmable. |
| OneDrive FUSE / null-byte / index corruption | Standing local-env hazards. Strip null bytes at session start; do not write large files through Cowork file tools; use bash heredoc or a Windows-side editor. |
| claire_a_assembler.py mojibake | cp1252 mojibake throughout. One-time UTF-8 cleanup, no logic change. Low priority. |

---

## Carried Forward, Still Open

**Ranked leads for the next session:**

1. Retire `config.pipeline.current_cycle` (orphaned at 10). Deliberate single-variable
   change in the next Code session: remove it as a cycle source, leave a tombstone
   comment pointing at cycle_state as the owner. It is already unread after Counter Fix
   A; this closes the loop and removes the trap of someone re-incrementing a dead field.

2. Scorer-write investigation. The reliability ledger has been dead since 2026-06-02
   (5 observations, one `unknown` key). Diagnosed, unfixed. This moots CLAIRE-A
   graduation entirely: a clock that advances over a ledger that never grows is not
   measuring anything. Diagnostic commands exist from the prior session. Determine
   whether the cause is no-scorable-candidates on thin corpus, commit-back not landing,
   or eval windows not elapsing, then fix the writer.

3. c13-prof-001 (refusal / insertion / moralizing profile diff). HELD. Do NOT author it
   from corpus. It is unwitnessed in operator context; the only source signal is HN
   bio/geopolitical over-refusal, which does not establish the behavior in this user's
   sessions. The correct trigger is a real query: it writes itself the first time
   over-refusal is observed live. Until then it stays a named placeholder, not a candidate.

4. Official-signal lane switch-on. Still dormant (config.official_signal.enabled:false).
   When switched on: supply the ratified c8-process-002 hypothesis (operator-authored,
   held from the 2026-06-13 design session, paste do not re-derive); Code writes the
   c8-process-002 entry (type pipeline_change, scope process, eval_window per-model-event)
   plus the friction "lane live, baseline 0/3" note; tag v2.2.0. Document the lane in the
   README AT switch-on paired with the v2.2.0 tag, not before.

**README pass (cosmetic + accuracy):**
- Arrow mojibake at approximately line 297 (a `->` rendered as cp1252-mangled unicode).
  Sweep in the next README pass. Cosmetic.
- Do NOT re-add the "Reddit as a live source" correction: the README already scrubbed
  Reddit. That prior HANDOFF note was itself stale and is dropped here.
- Reconcile the version string against `git describe` (v2.1.5) when the README is next
  touched, and remember the tags-not-Releases convention so the sidebar lag is not
  investigated as drift.

**Deferred logging (partially discharged):**
- `_meta.notes` eval_window duration-or-cadence extension: DONE. Discharged at the
  c8-process-003 write (85d9444), the first cadence use. Confirmed present in the live
  change_log `_meta.notes`.
- eval_window date-math consumer audit: STILL OPEN. Any consumer doing date math on
  eval_window must branch on a cadence token rather than parse it as a duration (cf.
  cycle-5 "eval window elapsed"). Now applies to c8-process-003 today and c8-process-002
  at switch-on. One audit pass covers both.

**Pending, human action (from Build 13 / v2.0.0):**
- Write hypotheses for c6-prof-006 through c6-prof-012, c6-skill-001, c6-skill-002. Each
  entry's `hypothesis_prompt` carries the prompt.

**Longer tail:**
- profile_snapshot.txt refresh to carry the MODEL ROUTING block (still stale).
- held/partial eval_status unused across all 60 entries. Quarterly question: dead branch
  or wrong rubric.
- .claude/ directory untracked. Gitignore or an explicit decision to track.
- Skills audit sessions 3+ against Profile v13.
- Memory-fabrication follow-up: scan remaining summary portfolio claims (SCHD/SCHG
  barbell, options) against the actual book.
- autocrlf awareness: repo has LF/CRLF normalization; harmless until a normalization
  churn is mistaken for a real diff.

---

## Open Proposals

1. **Official-signal ingest lane (Proposal 1).** BUILT DORMANT, gate verified held.
   Remaining work is switch-on, not build. See lead 4 above.
2. **Model-routing enforcement (Proposal 2).** Launch-triggered review that flags the
   MODEL ROUTING block stale on any model event. Cheap once Proposal 1 is live (shares
   the model-event signal). STILL OPEN.
3. **Skill-marketplace monitoring (Proposal 3, lowest urgency).** Discovery via
   first-party Anthropic directory only. Third-party aggregators are vet-only leads,
   never install sources. Do NOT auto-ingest third-party skills. STILL OPEN.

---

## Provenance (compressed; superseded detail lives in git history)

- **v2.1.5 session (prior):** four commits above 4cae840, annotated tag v2.1.5.
  Counter Fix A (88a7808), notify wire (1282c37), c8-process-003 entry (85d9444),
  cycle-13 friction (8975444). This is the state this HANDOFF documents.
- **Cycle 8 (2026-06-13/14):** notify cycle-identity fix v2.1.2/v2.1.3 (proved out
  on-path only via cycle_state at the time; now fully on-path after the notify wire).
  Official-signal lane built dormant (9ce68da). c8-prof-001 MODEL ROUTING block; retired
  c2-mem-002 and c4-mem-002. Memory edit 20 (NVDA fabrication guard).
- **Build 14:** atomic_write_json (closes truncated-write corruption class); CLAIRE-A
  state-file commit-back; archive dedup.
- **Build 10:** Reddit ingest retired permanently; dev.to tag expansion.

---

## Session Close, Project Knowledge Refresh

This session is the refresh. Goal: project-knowledge copies == git canonical == reality,
in one reconciliation. Root canonical files ONLY (HANDOFF.md, change_log.json,
friction_log.txt); not data/ artifacts, not the profile. change_log (60) and friction
(cycle 13) are already at git-canonical state and carry the four commits; this HANDOFF
is the one file being brought current. Commit this HANDOFF as its own single-variable
change, confirm all three match origin, then re-upload all three to the project Files
section, replacing the stale snapshots. Read live, write once, point everything at the
canonical source.
