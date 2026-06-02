# CLAIRE — Claude Code Context File

> Read this before touching anything. No exceptions.
> Last synced: Cycle 6 complete / Build 13 (2026-06-02)
> Also read: PROFILE.md -- behavioral rules for all work in this repo.

---

## What CLAIRE Is

CLAIRE (Claude Learns and Improves Iteratively from Real Engagement) is a weekly AI
optimization pipeline for a single operator at an SEC-registered RIA. It ingests
community signal from Reddit, HackerNews, and dev.to; filters it against the
operator's documented behavioral friction; synthesizes configuration candidates for
Claude memory edits, profile diffs, and skill installs; and delivers a PDF digest
via GitHub Actions with a Pushover notification.

This is infrastructure, not a tool. Every synthesis decision is filtered against the
operator's profile intent, live friction log, and active memory state. Output is
candidates for human review. Nothing is applied automatically.

CLAIRE-A, the shadow decision engine, evaluates candidates and produces what it would
do if authorized. It writes nothing to live config. Human authorization is required
for every applied change, no exceptions.

---

## Project Root

```
C:\DEV\CLAIRE
```

Note: Windows path. The project is PowerShell-native. If you are running in a
bash/WSL context, translate paths accordingly. All commands in this file are
PowerShell unless marked otherwise.

GitHub: https://github.com/not-yet-autonomous/CLAIRE
Branch: `main` — single working branch, no feature branch convention.
Visibility: Public. The `data/` directory is gitignored for this reason — it
contains scraped content and session state that must not be republished.

---

## Environment Setup

### Python Virtual Environment

The venv is intentionally separated from the project directory to avoid
OneDrive backup conflicts. Do not move it into the project directory.

```powershell
# Activate
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1

# Fallback (CMD)
C:\DEV\envs\CLAIRE\.venv\Scripts\activate.bat

# Verify
python -c "import anthropic, requests, reportlab, dotenv; print('Deps OK')"

# Install / repair
python -m pip install -r requirements.txt
```

**Always use `python -m pip`, not bare `pip`.**  
Python 3.11+ required.

### Dependencies (requirements.txt)

- `anthropic`
- `requests`
- `reportlab`
- `python-dotenv`

`python-dotenv` was added to requirements.txt in Build 8 after a GHA failure — it
was present in the local venv from a manual install but never declared. If it goes
missing, the failure won't surface until the first GHA run.

---

## Environment Variables

`.env` lives at project root. It is gitignored. Never commit it.

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | All Claude API calls: Haiku triage, Sonnet synthesis, Opus CLAIRE-A |

This is the only variable in `.env`. Pushover credentials are GitHub Secrets only
and are not needed for local runs. Local pipeline runs do not fire the notify step.

### GitHub Secrets (for GitHub Actions)

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Claude API access |
| `GH_PAT` | Commit-back push — fine-grained PAT, Contents read+write scope only |
| `PUSHOVER_APP_TOKEN` | Pushover CLAIRE app token |
| `PUSHOVER_USER_KEY` | Pushover account user key |

Four secrets. Not eight. Reddit credentials are not required — ingest uses
unauthenticated public JSON endpoints. Any documentation saying otherwise is stale.

---

## Pipeline Architecture

```
Reddit public JSON  (local manual run, before Sunday)
HackerNews API      (GHA, Sunday 14:00 UTC)           →  Ingest  →  raw_posts.json
dev.to API          (GHA, Sunday 14:00 UTC)
  - tags: anthropic, claudeai, claude, llm, aitools, machinelearning
  - per-tag thresholds configured in config.json

raw_posts.json  →  Triage (Haiku)  →  Track A / B / C queues

Track A (memory/profile)  ─┐
Track B (skill candidates) ─┤──  Synthesis (Sonnet, parallel ThreadPoolExecutor)
Track C (technique)        ─┘         ↓
                              candidates_track_*.json

candidates  →  CLAIRE-A Assembler
            →  Decision Engine (Opus)   [shadow decisions, writes nothing to live config]
            →  Eval Scorer (Sonnet)     [reliability ledger, hypothesis scoring]

candidates + shadow decisions  →  Output (reportlab PDF)  →  output/
GHA commit-back (data/, output/, logs/, change_log.json, friction_log.txt)
Pushover notification
```

### Model Assignments (locked — do not change without documented hypothesis and operator approval)

| Stage | Model |
|-------|-------|
| Triage | `claude-haiku-4-5-20251001` |
| Synthesis | `claude-sonnet-4-6` |
| CLAIRE-A decision engine | `claude-opus-4-5` |
| CLAIRE-A eval scorer | `claude-sonnet-4-6` |

**Why these models:** Opus 4.7 produces verbose, hallucination-prone output on
planning and document tasks relative to 4.6. This is a documented regression with
multiple corroborating community reports, not a preference. For outputs entering
formal review in a regulated environment, silent quality regression is a
correctness risk. Do not substitute 4.7 for 4.6/4.5 anywhere in this pipeline
without explicit written approval.

---

## How to Run

### GitHub Actions (production — automated)

Trigger: cron `0 14 * * 0` (Sundays 14:00 UTC) + manual `workflow_dispatch`  
Monitor: https://github.com/not-yet-autonomous/CLAIRE/actions

GHA runs HN + dev.to ingest only (`--source forum`). Reddit signal comes from the
locally-committed `raw_posts.json`.

### Pre-run ritual (manual, before GHA fires each Sunday)

These steps are required. Skipping them degrades output quality or breaks the run.

```powershell
# 1. Reddit ingest (Monday, or any time before Sunday 14:00 UTC)
cd "C:\DEV\CLAIRE"
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1
python claire_ingest.py --source reddit
# raw_posts.json is gitignored — do not commit it

# 2. Update friction_log.txt with 2-4 behavioral observations from the past week
# Format: YYYY-MM-DD | [context] | [component] | [severity: LOW/MEDIUM/HIGH]
# Skipping this causes the cross-reference gate to score all candidates MEDIUM.

# 3. Update data/session_notes.txt with Claude session observations
# Skipping this causes the scorer to exit with error code 1 and fail the GHA run.

# 4. Commit and push
git add data/session_notes.txt friction_log.txt
git commit -m "pre-run cycle N"
git push
```

### Local full run

```powershell
cd "C:\DEV\CLAIRE"
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1
.\claire_weekly.ps1
```

---

## Pushover Integration

Configured in `claire_notify.py`. Standard Pushover API.

- **Endpoint:** `https://api.pushover.net/1/messages.json`
- **Auth:** `PUSHOVER_APP_TOKEN` + `PUSHOVER_USER_KEY` (GitHub Secrets only -- not in `.env`)
- **Attachment logic:** PDF < 2.5MB sends as attachment; oversized sends text-only
  notification with the GHA commit URL as fallback.
- **Trigger:** End of successful GHA run, after commit-back step.
- **Local runs:** The notify step does not run locally. Pushover delivery is
  GHA-only.

---



## Key Files

| File | Path | Notes |
|------|------|-------|
| `PROFILE.md` | project root | Operator behavioral rules. Read alongside this file. |
| `HANDOFF.md` | project root | Current state, build status, locked decisions. Read before any session. |
| `change_log.json` | **project root** | Applied changes + eval loop. v1.1 schema. NOT in `data/`. |
| `friction_log.txt` | **project root** | Weekly behavioral observations. Human-maintained. NOT in `data/`. |
| `config.json` | project root | Locked pipeline decisions. Do not modify without documented hypothesis. |
| `claire_ingest.py` | root | Reddit + HN + dev.to ingest |
| `claire_triage.py` | root | Haiku classification, three-track routing |
| `claire_synthesize.py` | root | Sonnet synthesis, parallel tracks via ThreadPoolExecutor |
| `claire_output.py` | root | reportlab PDF digest builder (--format pdf default) |
| `claire_a_assembler.py` | root | CLAIRE-A input payload builder; semantic memory filter (Haiku, 0.85 threshold) |
| `claire_a_runner.py` | root | Opus decision engine runner; session history writer |
| `claire_a_scorer.py` | root | Sonnet eval scorer; reliability ledger; requires --notes flag or stdin |
| `claire_utils.py` | root | compute_cost, append_cost_log — all cross-script helpers live here |
| `claire_notify.py` | root | Pushover dispatch with PDF attach or text fallback |
| `claire_weekly.ps1` | root | Local scheduled pipeline wrapper |
| `data/raw_posts.json` | data/ | Current ingest corpus (gitignored) |
| `data/session_notes.txt` | data/ | Weekly scorer input — manual update required before each run |
| `data/memory_edits_snapshot.txt` | data/ | Current Claude memory baseline — update when memory changes are applied |
| `data/claire_a_source_reliability.json` | data/ | Reliability ledger; created on first successful scorer run |
| `data/claire_a_session_history.json` | data/ | Cross-run fingerprint tracking for prior_appearances |
| `data/cost_log.json` | data/ | Per-run API cost tracking; upsert by YYYYMMDD run_id |
| `output/` | output/ | Weekly PDF digests — `claire_digest_YYYY-MM-DD.pdf` |
| `prompts/profile_intent_summary.txt` | prompts/ | 200-400 words injected into Track A + B synthesis |
| `.github/workflows/claire_weekly.yml` | .github/workflows/ | GHA workflow |
| `.git/hooks/pre-push` | .git/hooks/ | Blocks pushes with staged data/ files — do not remove |

### Path rule: two canonical files at root

`change_log.json` and `friction_log.txt` live at project root. The `data/`
directory does not contain canonical versions of either. `data/change_log_v1_legacy.json`
is a read-only v1.0 archive.

---

## Git Rules

**Every git operation in any session or script must begin with:**

```powershell
Remove-Item .git\index.lock -ErrorAction SilentlyContinue
```

This is not optional. The OneDrive FUSE mount and VS Code frequently leave
`index.lock` held between sessions.

**Before every push:**

```powershell
git ls-files data/
```

The `.gitignore` rule for `data/` does not evict already-tracked files. If a
data file appears in this output that should not be committed (scraped content,
session state, test artifacts), remove it with `git rm --cached <file>` before
pushing. The pre-push hook at `.git/hooks/pre-push` is a backstop, not a
substitute for this check.

---

## Session Start Checklist (local dev)

Run these before doing anything else:

```powershell
# 1. Kill any held lock
Remove-Item .git\index.lock -ErrorAction SilentlyContinue

# 2. Navigate and activate
cd "C:\DEV\CLAIRE"
C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1

# 3. Verify deps
python -c "import anthropic, requests, reportlab, dotenv; print('Deps OK')"

# 4. Strip FUSE null-byte corruption
python -c "
for f in ['HANDOFF.md', 'change_log.json', 'friction_log.txt', '.git/config', '.git/index']:
    try:
        data = open(f, 'rb').read().rstrip(b'\x00')
        open(f, 'wb').write(data)
    except FileNotFoundError:
        pass
print('Null-byte check OK')
"

# 5. Check for unintended tracked files before any git operation
git ls-files data/
```

Expected: `(.venv)` in prompt + `Deps OK` + `Null-byte check OK`

---

## Known Gotchas and Fragile Areas

### Things that will silently break the pipeline

| Issue | Symptom | Fix |
|-------|---------|-----|
| `data/session_notes.txt` blank | Scorer exits code 1, GHA fails | Update before Sunday push |
| `friction_log.txt` not updated | All candidates score MEDIUM | Update 2-4 entries per cycle |
| `load_dotenv()` missing from new script | Anthropic client auth fails silently -- all candidates pass filter unscored | Any script calling `anthropic.Anthropic()` must call `load_dotenv()` before instantiation. Check on every new script. |
| Conflict markers in scripts | Script may fail or produce wrong output silently | `grep -n "<<<" *.ps1 *.py` before push |
| `--format pdf` missing | Digest is .docx, Pushover notify looks for .pdf | Verify `claire_weekly.ps1` and GHA workflow have flag |

### OneDrive FUSE mount

The project directory syncs through OneDrive. The FUSE mount silently truncates
large file writes and appends null bytes to files including `.git/config` and
`.git/index`. Run the null-byte strip at every session start (see checklist above).

**Do not write `config.json` or other large files through Claude Code file tools
on this mount.** Use the Windows-side editor or a bash heredoc. Symptoms of FUSE
corruption: JSON parse errors on previously-valid files, `bad config line` in git,
`index file corrupt`.

### Git sandbox isolation

Never attempt `.git` operations in a sandbox or scratch environment against the
live working repo. On 2026-05-22, partial ref writes from a Cowork sandbox
corrupted the live repo HEAD. The working tree was deleted during recovery.
Recovered from a sanitized clone in the sandbox (65 commits). If you need to
test git operations, clone to a separate directory first.

### Reddit ingest

Reddit returns 403 from GHA datacenter IPs. Empty RSS feeds from GHA IPs despite
working locally. **This is permanent architecture, not a bug to fix.** Manual
ingest is the design. Do not attempt to re-automate Reddit ingest through GHA
without evaluating a residential proxy solution first and documenting the approach.

### claire_a_scorer.py stdin

Reads session notes interactively via stdin when `--notes` is not provided. This
breaks unattended GHA execution. The workflow passes `--notes data/session_notes.txt`.
If you modify the scorer, preserve this behavior.

### Confidence scores (Cycles 2-4)

`FRICTION_LOG_PATH` in `claire_triage.py` pointed to `data/friction_log.txt` (the
original April template) instead of the root `friction_log.txt` for Cycles 2-4.
All Cycle 2-4 confidence scores are understated. Fix applied Build 9 (2026-05-19).
Historical scores are not retroactively adjusted — they are directionally correct
but not corroboration-weighted.

---

## Things You Must Not Change Without Asking

| Item | Reason |
|------|--------|
| Model assignments in `config.json` | Version-specific quality behavior; 4.7 regressions documented |
| CLAIRE-A output wiring | Shadow only — never wire to live config application |
| `change_log.json` `eval_status` enum | Values are: `pending`, `held`, `partial`, `no`, `queued`, `n/a` — do not add |
| `friction_log.txt` format | The cross-reference gate parses this file; format change breaks scoring |
| Hypothesis authorship | For applied changes, hypotheses must be human-written. Do not generate them. |
| Pre-push hook at `.git/hooks/pre-push` | Blocks accidental data/ commits to public repo |
| `data/` gitignore rules | Reddit ToS prohibits republishing scraped content |
| CLAIRE-A graduation criteria | Current thresholds are part of the audit trail design |

---

## CLAIRE-A Shadow Pipeline

CLAIRE-A reads all candidates and records what it would decide. It writes nothing
to live config. This is not a technical limitation — it is an intentional
architectural constraint for a regulated environment.

**Graduation criteria before any live application authority:**
- 80% agreement rate with human decisions over 6 consecutive eval runs
- 10+ scored hypotheses in `data/claire_a_source_reliability.json`
- 0 escalations in last 3 runs

Current status: [verify count against live HANDOFF.md -- memory indicates 3 of 6
runs complete as of Cycle 6; uploaded HANDOFF.md (Cycle 5) shows 2 of 6]

**Never wire CLAIRE-A output to live config application, conditionally or otherwise,
without explicit written authorization from the operator in this session.**

---

## Maintenance Files (human-maintained, not generated)

These files require the operator's input. Do not auto-generate content for them.

| File | Minimum cadence | Format / rules |
|------|----------------|----------------|
| `friction_log.txt` | 2-4 entries per cycle | `YYYY-MM-DD \| [context] \| [component] \| [severity: LOW/MEDIUM/HIGH]` |
| `change_log.json` | One entry per applied change | Hypothesis required before change is applied; `eval_status: pending` on entry |
| `data/session_notes.txt` | Before each Sunday GHA run | Free-form behavioral observations; blank content causes scorer failure |
| `data/memory_edits_snapshot.txt` | When memory changes are applied | Paste of current Claude memory state |
| `prompts/profile_intent_summary.txt` | When profile changes | 200-400 word summary of Claude profile goals |

---

## change_log.json Schema (v1.1)

```json
{
  "id": "cN-type-NNN",
  "date": "YYYY-MM-DD",
  "cycle": N,
  "type": "memory_edit | profile_diff | skill_install",
  "action": "add | apply | queued",
  "target": "Human-readable description of what is being changed",
  "summary": "One sentence. What the change does.",
  "hypothesis": "What the operator expects this change to do and why. Operator's words.",
  "source_signal": "Track and source posts that motivated this candidate.",
  "eval_status": "pending | held | partial | no | queued | n/a",
  "eval_notes": ""
}
```

Eval windows: 14d for format/behavior changes, 21d for memory/behavioral changes.

---

## Cost Profile

~$0.70-1.00 per weekly run at normal corpus size:

| Stage | Typical cost |
|-------|-------------|
| Haiku triage | ~$0.25 |
| Sonnet synthesis | ~$0.45 |
| Opus CLAIRE-A | ~$0.20 |

Track A cost alert fires at $0.65 synthesis threshold (configured in
`claire_weekly.ps1`). Large ingest weeks can push synthesis to $0.70+ on
its own. Monitor `data/cost_log.json`.

---

## Design Principles (Non-Negotiable)

1. **Human-in-the-loop.** Every applied change requires a human-written hypothesis.
   CLAIRE generates candidates. The operator decides.

2. **Audit trail.** `change_log.json` records every applied change with its
   hypothesis, source signal, and eval status. No hypothesis, no application.

3. **Evidence threshold.** 3 corroborating posts minimum for Track A candidates.
   One enthusiastic post does not make a configuration change.

4. **CLAIRE-A is shadow only.** Reads everything, authorizes nothing.

5. **Surgical edits.** When editing any existing file or document, touch only the
   specified section. Full-document regeneration on a partial edit is a workflow
   failure.

6. **Hypothesis authorship integrity.** Never generate a hypothesis on the
   operator's behalf for an applied change. This is an audit trail integrity
   requirement, not a formatting preference.
