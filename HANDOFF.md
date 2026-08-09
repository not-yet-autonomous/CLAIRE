---
> Read this first. Every session. No exceptions.
> State as of the 2026-07-26 cycle-14 review session (design + Code, seven local
> commits plus a merge, pushed).
> Cycle 14 completed on the 2026-07-26 GHA run. Next live event:
> Sun 2026-08-02 14:00 UTC GHA run = cycle 15.
>
> Verified against git and artifacts this session: a974b74 (retire current_cycle),
> b84287b (cycle-14 friction block), f26c81b (feature_praise triage fix +
> c14-process-001), 268ecd4 (untrack profile_snapshot), d927dd4 (friction encoding
> repair + duplicate removal), 089bd76 (ledger + routing findings), 5df35e3 (merge
> of bot commit 8d9f51a). origin/main == 5df35e3. Tag unchanged at v2.1.5; seven
> commits now sit above it. `git describe` remains canonical; the Releases sidebar
> lags by convention and is not drift.
>
> COUNTER FIX A IS VERIFIED IN PRODUCTION. cycle_state.json read off the bot
> commit-back: last_completed_cycle 14, last_completed_at 2026-07-26T15:00:56Z,
> digest claire_digest_2026-07-26_c14.pdf. Filename auto-stamped correctly for the
> first time since 06-21. The four-week _c10 freeze is closed and the manual
> pre-Sunday increment is permanently gone.
>
> Discipline note (this session's lesson, and it is a new one): the prior root
> defect class was stale self-description trusted as truth. The class found today is
> narrower and worse. A config-state change is logged as applied at the moment of the
> edit and never checked against the next output, so an applied entry is a claim
> about intent rather than a measurement of effect. Two instances, both live for
> weeks: c7-config-001 retired feature_praise by clearing a keyword map the triage
> model does not read, and claire_weekly.yml line 91 has force-added a file that has
> never existed on the runner, with `|| true` converting the failure into a green
> check. This project verifies code by absence-grep and runs by artifact-read. It has
> no verification step for config state at all.

---

## Machine Context

| Item | Value |
|------|-------|
| Project root | `C:\DEV\CLAIRE` |
| Python | `python` (via .venv) [local dev only] |
| Pip | `python -m pip` |
| Venv activate (PowerShell) | `C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1` [local dev only] |
| Venv activate (CMD/bat) | `.\.venv\Scripts\activate.bat` [local dev only] |
| Git | initialized, remote on GitHub, origin/main == 5df35e3 |
| Execution policy | RemoteSigned (already set) [local dev only] |
| CI/CD | GitHub Actions, `.github/workflows/claire_weekly.yml` |
| GHA trigger | Cron `0 14 * * 0` (Sundays 14:00 UTC) + `workflow_dispatch` |
| GitHub repo | https://github.com/not-yet-autonomous/CLAIRE (PUBLIC) |
| Current tag | v2.1.5 (annotated), seven commits behind HEAD. Next tag is v2.2.0 at official-signal switch-on. |
| Shell convention | PowerShell for all git and file operations. bash heredoc only for large writes on the FUSE mount. Confirm shell before running anything. |

---

## GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | All Claude API calls |
| `GH_PAT` | Commit-back push (Contents read+write, fine-grained PAT) |
| `PUSHOVER_APP_TOKEN` | Pushover CLAIRE app token |
| `PUSHOVER_USER_KEY` | Pushover account user key |

No Reddit credentials required or used. Reddit ingest was retired permanently in
Build 10 and must not reappear in any checklist, task spec, or doc.

---

## Cycle Log

True cadence cycle is authoritative (weekly cron, no skips from 06-14). Cycles
10 through 13 shipped stamped `_c10` because the counter was frozen; the cadence
cycle advanced underneath the filename. Cycle 14 is the first correct auto-stamp.

| Cadence cycle | GHA Run Date | Digest filename (actual) | Note |
|---------------|--------------|--------------------------|------|
| 1 | - | Pipeline validation only | |
| 2 | 2026-05-03 | Not tracked | |
| 3 | 2026-05-10 | Not tracked | |
| 4 | 2026-05-17 | Not tracked | |
| 5 | 2026-05-17 | claire_digest_2026-05-23.pdf (local rebuild) | |
| 6 | 2026-05-31 | claire_digest_2026-05-31.pdf | |
| 7 | 2026-06-07 | claire_digest_2026-06-07.pdf | |
| 8 | 2026-06-14 | claire_digest_2026-06-14_c8.pdf | run #29, verified |
| 9 | 2026-06-21 | claire_digest_2026-06-21_c8.pdf | MISLABELED c8: config never advanced to 9 pre-cron |
| 10 | 2026-06-28 | claire_digest_2026-06-28_c10.pdf | config bumped 8->10 pre-run (23a196f) |
| 11 | 2026-07-05 | claire_digest_2026-07-05_c10.pdf | FROZEN |
| 12 | 2026-07-12 | claire_digest_2026-07-12_c10.pdf | FROZEN |
| 13 | 2026-07-19 | claire_digest_2026-07-19_c10.pdf | FROZEN (4th `_c10`); freeze diagnosed; Counter Fix A applied |
| 14 | 2026-07-26 | claire_digest_2026-07-26_c14.pdf | VERIFIED. First correct auto-stamp. cycle_state 14, committed back at 15:00:56Z. |
| 15 | 2026-08-02 (next) | expect claire_digest_2026-08-02_c15.pdf | Falsification run for c14-process-001 |
| 16 | 2026-08-09 | claire_digest_2026-08-09_c16.pdf | Counter Fix A third consecutive correct auto-stamp. |

Cycle 14 digest contents, read from the PDF: 57 posts scanned; behavior_complaint
10, workflow_gap 8, feature_praise 14, competitor_gap 0, cross_platform 0, noise
dropped 25; 34 developer-persona posts filtered; zero Track A, Track B, and
CLAIRE-A candidates; official-signal section printed the disabled notice.

---

## Session Start Checklist

**GHA runs require no manual start.** Cron at Sunday 14:00 UTC, or `workflow_dispatch`
in the Actions UI.

**PULL FIRST. This is rule 1 and the 2026-07-26 session broke it.** GHA commits
`data/`, `logs/`, `output/`, `change_log.json`, and `friction_log.txt` back on every
run. Six local commits accumulated after the cycle-14 cron without a prior pull and
the push was rejected non-fast-forward. It resolved cleanly only because an empty
digest wrote nothing to change_log. A cycle with applied entries would have
conflicted on the file the session spends the most time editing.

```powershell
git fetch origin
git log --oneline HEAD..origin/main
git diff --name-only HEAD...origin/main
```

**Pre-Sunday ritual (manual, before cron fires):**
1. NO cycle increment. `config.pipeline.current_cycle` is retired (a974b74,
   tombstone left). cycle_state.json self-increments on the output path.
2. Update `data/session_notes.txt` with the week's behavioral observations, then
   COMMIT AND PUSH. The scorer reads it. A local edit does not reach the runner.
3. Confirm `data/profile_snapshot.txt` reflects the current profile. It is now
   untracked (268ecd4), so nothing versions it and nothing warns when it rots.

**Pre-push verification (before any commit touching data/ or git state):**
```powershell
git ls-files data/
```
Expected 22 files as of 2026-07-26: `raw_posts.json`, `session_notes.txt`,
`cycle_state.json`, `official_signal_seen.json`, `cost_log.json`,
`claire_a_session_history.json`, eight `claire_a_decisions_*.json`, eight
`suppressed_candidates_*.json`. `profile_snapshot.txt` must NOT appear.
`claire_a_source_reliability.json` does NOT appear and never has; see Known Issues.

**index.lock, CONDITIONAL, do not run blind:**
```powershell
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -ErrorAction SilentlyContinue }
```
The unconditional form aborted commits twice on the execution harness path guard.

**Strip null bytes before working** on HANDOFF.md, change_log.json,
friction_log.txt, .git/config, .git/index. OneDrive FUSE appends null padding.

**Multi-line `python -c` blocks fragment on this console.** Three pastes broke
mid-block on 2026-07-26, one of them a verification script. Write verification
one-liners with semicolons, or use a script file.

---

## Local vs. GHA, Operational Discipline

1. **Pull before editing `change_log.json` or `friction_log.txt`.** See above.
2. **Push `config.json` before Saturday.** Applies to ingest terms, thresholds, and
   the official_signal block. `current_cycle` no longer exists.
3. **Push `session_notes.txt` before Sunday 14:00 UTC.**
4. Memory edits are project-scoped. Global behavioral changes must be profile diffs.
5. Hypothesis prompts for pending entries live in the `hypothesis_prompt` field.
   Add at entry-creation time or the prompt is lost.
6. **Hypothesis authorship is human, non-negotiable.** Claude may draft starters and
   sharpen language. Approval is not authorship. A Claude-drafted hypothesis with
   operator sign-off is not equivalent to the "recovered ratified hypothesis" pattern
   used on c8-process-003, where recovery restored operator-written text from a prior
   transcript. Do not let that label drift.
7. **Single-variable commits.** d927dd4 carried two friction entries its message did
   not name. Stage deliberately.

---

## Directory Structure (delta-noted)

```
CLAIRE\
├── claire_output.py          ✅ Counter Fix A VERIFIED IN PRODUCTION (88a7808). cycle_state is the sole self-incrementing output-path cycle owner. Cycle 14 auto-stamped correctly.
├── claire_notify.py          ✅ WIRED (1282c37). Cycle read points at cycle_state; digest located by glob. Applied-count surfacing STILL UNVERIFIED: not visible in the PDF, requires reading the actual Pushover alert.
├── claire_a_assembler.py     ⚠ Self-reports v2.0.0 against repo tag v2.1.5 (seen in cycle-14 digest). Likely hardcoded version string. c8-process-003 suppression present (2d75cd3) but HAS NEVER FIRED.
├── claire_triage.py          ⚠ Dead feature_praise+claude_native special-case left in place deliberately at f26c81b (single-variable). Cleanup owed.
├── prompts\triage_prompt.txt ✅ feature_praise definition block and signal_type enum value REMOVED (f26c81b). This is the actual taxonomy source; the keyword map is not.
├── config.json               ✅ current_cycle RETIRED with tombstone (a974b74). Empty feature_praise keyword entry left in place (cleanup owed). official_signal enabled:false.
├── change_log.json           ✅ CANONICAL, root. v1.2 schema, Cycles 2-14, 61 entries (c14-process-001 last). Second cadence-token eval_window; no _meta.notes extension owed.
├── friction_log.txt          ✅ CANONICAL, root. Cycles 1-14. Encoding repaired and duplicate cycle-5 block removed (d927dd4). Six cycle-14 entries.
├── .github\workflows\claire_weekly.yml ⚠ Line 91 force-adds claire_a_source_reliability.json with `|| true`. Has never produced a commit. See Known Issues.
├── data\
│   ├── cycle_state.json                    ✅ AUTHORITATIVE. last_completed_cycle 14, 2026-07-26T15:00:56Z, digest claire_digest_2026-07-26_c14.pdf.
│   ├── claire_a_source_reliability.json    ⚠ NEVER COMMITTED, not once, in any cycle. Local copy dates to 2026-06-02 (Build 12), 5 observations all keyed `unknown`. Blocks CLAIRE-A graduation.
│   ├── suppressed_candidates_*.json         ⚠ Cycle 14 file is an empty array. c8-process-003 has never fired. Read these; nobody has.
│   ├── profile_snapshot.txt                ✅ UNTRACKED (268ecd4), gitignore:26 now binds, working copy refreshed to full profile v14. ⚠ ALREADY STALE: Opus 5 launched 2026-07-24, profile v14 reconciled 2026-07-23.
│   └── official_signal_seen.json           ✅ Dedup memory; empty until lane enabled.
└── (all other files unchanged)
```

**Path rule:** `change_log.json` and `friction_log.txt` live at project root.
`data/change_log_v1_legacy.json` is a read-only v1.0 archive.

---

## Locked Pipeline Decisions

| Decision | Value |
|----------|-------|
| Config injection | Partial (intent summary + memory list) |
| Developer persona | Filter out entirely |
| Hypothesis authorship (applied changes) | Human-written. Approval is not authorship. |
| Evidence threshold | 3 corroborating posts minimum (Track A) |
| Triage model | claude-haiku-4-5-20251001 |
| Synthesis model | claude-sonnet-4-6 |
| Noise prefilter | score < 5 AND comments < 2 -> drop |
| Scheduling | GHA Sunday 14:00 UTC (all ingest sources) |
| **Cycle identity source** | **cycle_state.last_completed_cycle + 1, owned and self-incremented by claire_output.py at generate_pdf. VERIFIED IN PRODUCTION on the cycle-14 run. config.pipeline.current_cycle no longer exists. Never derive identity from change_log.** |
| Notify dispatch | claire_weekly.yml calls claire_notify.py (1282c37). Applied-count surfacing remains unverified; read the Pushover alert, not the PDF. |
| Cost log entries | Single upsert per run keyed by YYYYMMDD. ⚠ DIVERGENT: one row per stage, `total_runs` overcounts. OPEN. |
| Opus exclusion | exclude_keywords in config.json |
| Shared utilities | claire_utils.py |
| Track A batching | Signal cluster by signal_type, max 50 posts per call |
| CLAIRE-A mode | Shadow only, writes nothing to live config |
| Decision engine model | claude-opus-4-5 |
| Eval scoring model | claude-sonnet-4-6 |
| Batch size ceiling | 15 candidates per decision engine run |
| CLAIRE-A graduation criteria | 10 consecutive qualifying eval runs, clock reset 2026-06-14. ⚠ MEANINGLESS: the reliability ledger has never been written to the repo. |
| Eval window | 14d (format/behavior), 21d (memory/behavioral), OR a cadence token. Cadence uses: c8-process-003, c14-process-001. |
| Ingest sources | HackerNews + dev.to (GHA, Sunday 14:00 UTC) |
| dev.to tags | anthropic, claudeai, claude, llm, aitools, machinelearning, ai, chatgpt, productivity |
| PDF output | reportlab, six-section digest; `claire_digest_YYYY-MM-DD_cNN.pdf` |
| Memory filter threshold | 0.85 semantic similarity (Haiku, assembler) |
| Commit-back strategy | GHA commits data/, output/, logs/, change_log.json, friction_log.txt each run. Does NOT include profile_snapshot.txt, and has never included claire_a_source_reliability.json. |
| Official-signal lane | Built dormant (enabled:false). Switch-on operator-gated. Model-event detection baseline now 0/4. |

---

## Known Issues

| Issue | Status / Detail |
|-------|-----------------|
| **Frozen cycle counter** | **CLOSED AND VERIFIED.** Cycle 14 auto-stamped from cycle_state; value read off the bot commit-back, not local state. |
| **CLAIRE-A reliability ledger dead** | **OPEN, HIGH, root cause narrowed.** `git log -- data/claire_a_source_reliability.json` returns empty: the file has never been committed in any cycle. Workflow line 91 force-adds it with `|| true`, which returns success when the path is absent on the runner. The commit-back branch of the diagnosis is eliminated; there was never anything to commit back. Remaining question is why the scorer produces no file on GHA when the same invocation produces one locally. Cycle 14 confirmed it again: the incoming bot diff carried decisions, suppressed candidates, cost log, and cycle state, and no ledger. |
| **`\|\| true` on persistence steps** | **OPEN, structural.** Converts hard failure into invisible failure. Other force-adds on the same line share the pattern and are masked because those files do land. Grep every `\|\| true` in the workflow. |
| **CLAIRE-A confabulation** | **STANDING, six cycles deep.** 2026-06-02 ALREADY_APPLIED over-generalization; 2026-06-28 invented schema defect + 73-vs-59 miscount; 2026-07-19 cited nonexistent c7-prof-001; 2026-07-26 cited nonexistent c9-pipe-001, reported 73 applied changes against canonical 60, and recommended scraper-health verification contradicted by its own digest; 2026-08-09 (cycle 16) cited c9-pipe-001 again, verbatim rather than drifted — a second stable fabricated constant alongside the 73 count. Treat every engine self-referential claim as unverified. |
| **Engine has no view of live profile state** | **OPEN.** The cycle-14 engine flagged the MODEL ROUTING block stale by dating it from the c8-prof-001 change_log entry (2026-06-13). Its reasoning is invalid; it cannot read the profile. Its conclusion happened to be correct because Opus 5 launched 2026-07-24, two days before the run. Right conclusion, wrong basis. Structural fix is Open Proposal 2. |
| **MODEL ROUTING block exists in exactly one place** | **OPEN, MEDIUM.** Search across change_log.json, claire_official_signal.py, friction_log.txt, and profile_snapshot.txt found four pointers and zero copies of the content. `ROUTING_ANCHOR = "c8-prof-001"` anchors gate logic to an entry whose prose the pipeline has never held. Canonical text lives only in the claude.ai Settings profile field. No backup, no version history the repo can read. |
| **Model-event detection 0/4** | **OPEN.** Missed: Opus 4.8 launch, Fable 5 launch, Fable 5 suspension, Opus 5 launch (2026-07-24). Opus 5 was detected by the operator noticing which model a session was running on. The official-signal lane was built for exactly this class and has now sat dormant through one more instance. |
| **c8-process-003 has never fired** | **OPEN.** Cycle-14 `suppressed_candidates_20260726_150026.json` is an empty array. The eval_window is a cadence token requiring a first flag fire, so the entry is unevaluated and cannot be evaluated on any calendar. Do not treat it as validated by age. The cycle-14 empty batch traces to thin signal at the cross-reference gate, not to suppression and not to intake. |
| **feature_praise** | **FIX VERIFIED, two consecutive zeros.** f26c81b removed it from the triage prompt definition block and signal_type enum. Cycle 15 and cycle 16 both report feature_praise 0. c14-process-001 held, not closed: the signal_type enum value was removed, so a zero count cannot distinguish a genuine corpus shift from a label-layer impossibility. |
| **c5-prof-003 observation gate** | **OVERDUE, four cycles.** The 3-cycle staleness rule (c7-process-001) required retire-or-apply at cycle 13. It was already flagged as hitting the limit in the cycle-10 session notes. The rule fired, was recorded, and nothing acted on it. Decision owed, not investigation. |
| cost_log upsert not merging | OPEN, MEDIUM. One row per stage; cost total correct, `total_runs` overcounts. Verify claire_utils append_cost_log. |
| within-cycle dedup failure | OPEN, MEDIUM. 07-19 case. c8-process-003 addresses the cross-cycle case at the assembler; the within-cycle case may need suppression at synthesis. |
| Developer-filter denominator unlabeled | OPEN, LOW. Cycle-14 digest reports 34 filtered against 57 scanned with 25 dropped as noise. 34 cannot be a subset of the 32 survivors. The digest does not state which stage each count is measured at. |
| Assembler version self-report | OPEN, LOW. Reports v2.0.0 against tag v2.1.5. |
| actions/cache Node 20 deprecation | OPEN, LOW. Bump to actions/cache@v5. |
| profile_snapshot GHA degradation | OPEN. GHA substitutes a placeholder, so the cross-reference gate runs without profile context on automated runs. The local refresh addresses design sessions only. |
| memory summary fabrication | Guarded by memory edit 20. Treat memory-snapshot inputs as operator-confirmable. |
| OneDrive FUSE / null-byte / index corruption | Standing local-env hazards. Also: multi-line console pastes fragment. |
| claire_a_assembler.py mojibake | cp1252 mojibake throughout. Low priority. |
| friction_log cycles 9-12 header gap | OPEN, cosmetic-adjacent. Cycle 10 has six entries under no header; cycles 9, 11, 12 have none at all. Three blank weeks is itself a finding under the file's own header rule. Editorial, wording is the operator's. |

---

## Carried Forward, Still Open

**Ranked leads for the next session:**

1. **Scorer-write investigation.** Now narrow. Open with one Actions log read of the
   scorer step's actual stdout from a recent run, not its exit code. Then check
   whether the scorer step also carries `|| true`. Then grep every `|| true` in
   claire_weekly.yml. The ledger has never existed on the repo, so graduation is
   measuring nothing and has been since the clock reset on 06-14.

2. **Semantic-dedup GHA starvation (Proposal 5).** Two consecutive cycles (15, 16)
   let a HIGH duplicate of c6-prof-014 reach the digest because profile_snapshot_input
   is placeholder-substituted on GHA, starving the 0.85 semantic filter of real profile
   content to compare against. The filter is enabled, not broken — it has nothing to
   compare. Needs a hypothesis before build.

3. **c5-prof-003 retire-or-apply.** Four cycles past the staleness threshold this
   project wrote for itself. A decision, not an investigation. Make it and log it.

4. **MODEL ROUTING reconciliation.** Opus 5 launched 2026-07-24 at $5/$25 per Mtok,
   default on Claude Max, positioned near Fable 5 at half the price, with a May 2026
   training cutoff against January 2026 for Fable 5 and Opus 4.8. The block is stale
   by its own staleness rule. Reconcile in Settings, re-stamp, then re-paste the
   snapshot. COI rule applies: a model under evaluation may confirm its own
   availability but not its own placement in a routing lane. Launch coverage is
   evidence the model exists and is default, not evidence it is better on the
   doc-quality axis. That axis stays provisional until community signal arrives.

5. **Official-signal lane switch-on.** No blocker remains except sequencing; flip on
   a clean week. At switch-on: paste the ratified c8-process-002 hypothesis
   (operator-authored, held from the 2026-06-13 design session, do not re-derive),
   write the c8-process-002 entry (pipeline_change, scope process, eval_window
   per-model-event), write the friction note with the baseline now 0/4 rather than
   0/3, tag v2.2.0, and document the lane in the README at switch-on.

**Owed writes:**
- Two friction entries drafted 2026-07-26 and not written: the push-rejected
  working-ahead-of-commit-back entry, and a note that d927dd4 carried two entries its
  commit message did not name.
- `data/session_notes.txt` for cycle 14 must be committed and pushed before
  2026-08-02 14:00 UTC. A local edit does not reach the runner.

**Deferred cleanup (deliberately not bundled at f26c81b):**
- Dead `feature_praise+claude_native` special-case in claire_triage.py.
- Empty `feature_praise` keyword entry in config.json.

**Longer tail:**
- eval_window date-math consumer audit. Any consumer doing date math must branch on
  a cadence token rather than parse it as a duration. Now covers c8-process-003 and
  c14-process-001; c8-process-002 joins at switch-on. One pass covers all three.
- Hypotheses owed for c6-prof-006 through c6-prof-012, c6-skill-001, c6-skill-002.
  Each entry's `hypothesis_prompt` carries the prompt.
- README: arrow mojibake near line 297; reconcile version string against
  `git describe`; remember the tags-not-Releases convention.
- held/partial eval_status unused across all 61 entries. Quarterly question: dead
  branch or wrong rubric.
- .claude/ directory untracked. Gitignore or an explicit decision to track.
- Skills audit sessions 3+, now against profile v14.
- Memory-fabrication follow-up: scan remaining summary portfolio claims against the
  actual book.

---

## Open Proposals

1. **Official-signal ingest lane (Proposal 1).** BUILT DORMANT, gate verified held.
   Remaining work is switch-on. Now carries four missed model events as evidence.
2. **Model-routing enforcement (Proposal 2).** Launch-triggered review that flags the
   MODEL ROUTING block stale on any model event. Cycle 14 produced the first concrete
   false positive from the pipeline's blindness to live profile state, so this is no
   longer theoretical. Cheap once Proposal 1 is live.
3. **Config-state verification (Proposal 4, NEW).** Every applied change with a config
   target is currently a claim about intent with no check against the next output.
   c7-config-001 and workflow line 91 are two instances that ran for weeks. Candidates
   with an observable digest signature, checkable in one pass: `exclude_keywords`, the
   noise prefilter thresholds, the dev.to tag list. Needs a hypothesis before build.
4. **Semantic-dedup GHA starvation (Proposal 5, NEEDS HYPOTHESIS).**
   assembler.memory_filter_enabled is true, but profile_snapshot_input is
   placeholder-substituted on GHA, so the 0.85 semantic filter runs with no real
   profile content to compare against. Two consecutive cycles (15, 16) let a HIGH
   duplicate of c6-prof-014 reach the digest as a result. Cycle 16 engine notes
   compounded the gap by asserting dedup is not performed at all — false; the
   correct diagnosis is starvation, not absence. Needs a hypothesis before build.
5. **Skill-marketplace monitoring (Proposal 3, lowest urgency).** First-party Anthropic
   directory only. Third-party aggregators are vet-only leads, never install sources.

---

## Unverified At Write Time

Everything above traces to a commit, an artifact read, or a command output pasted
into the 2026-07-26 session, except the following. Confirm before relying on them.

- friction_log.txt entry count. 78 is arithmetic (76 confirmed after d927dd4, plus
  two entries in 089bd76), not a read. Confirm with a count if precision matters.
- Tag state. No new tag was cut on 2026-07-26, so v2.1.5 stands and seven commits sit
  above it. `git describe` was not run this session.
- `data/session_notes.txt` cycle-14 content was written but no commit was observed.
- Notify applied-count surfacing. Not visible in the PDF. Requires reading the actual
  Pushover alert for the cycle-14 run.
- Cycle 14 dual-source confirmation. The digest reports 57 posts scanned but does not
  break down HN against dev.to.

---

## Provenance (compressed; superseded detail lives in git history)

- **Cycle 14 session (2026-07-26, this state):** a974b74 retire current_cycle;
  b84287b cycle-14 friction block; f26c81b feature_praise triage fix and
  c14-process-001; 268ecd4 untrack profile_snapshot; d927dd4 friction encoding repair
  and duplicate cycle-5 block removal; 089bd76 ledger and routing-block findings;
  5df35e3 merge of bot commit 8d9f51a. Counter Fix A verified in production. Ledger
  root cause narrowed. Opus 5 launch identified as the fourth missed model event.
- **v2.1.5 session (2026-07-19/20):** Counter Fix A (88a7808), notify wire (1282c37),
  c8-process-003 entry (85d9444), cycle-13 friction (8975444).
- **Cycle 8 (2026-06-13/14):** notify cycle-identity fix v2.1.2/v2.1.3. Official-signal
  lane built dormant (9ce68da). c8-prof-001 MODEL ROUTING block; retired c2-mem-002 and
  c4-mem-002. Memory edit 20 (NVDA fabrication guard).
- **Build 14:** atomic_write_json; CLAIRE-A state-file commit-back; archive dedup.
- **Build 10:** Reddit ingest retired permanently; dev.to tag expansion.

---

## Session Close, Project Knowledge Refresh

Root canonical files only: HANDOFF.md, change_log.json, friction_log.txt. Not data/
artifacts, not the profile. All three are at git-canonical state and pushed as of
5df35e3, except this HANDOFF, which is the file being brought current. Commit it as
its own single-variable change, confirm HEAD moved, then re-upload all three to the
project Files section, replacing the stale snapshots.

Read live, write once, point everything at the canonical source.
