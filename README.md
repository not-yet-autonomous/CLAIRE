# CLAIRE
**Claude Learns and Improves Iteratively from Real Engagement**

A personal AI optimization pipeline. Mines community signal from Reddit,
HackerNews, and dev.to. Filters it against your behavioral friction patterns.
Synthesizes actionable configuration candidates for Claude memory edits,
profile diffs, and skill installs. Delivers a weekly PDF digest via GitHub
Actions with Pushover notification.

MIT licensed. Built for Claude power users who treat their AI configuration
as infrastructure.

---

## What It Does

Every week, CLAIRE:

1. Ingests posts from Reddit (local, unauthenticated), HackerNews API, and
   dev.to API
2. Classifies each post into Track A (memory/profile candidates), Track B
   (skill candidates), or Track C (technique candidates) using Haiku
3. Synthesizes configuration candidates across all three tracks in parallel
   using Sonnet
4. Runs the CLAIRE-A shadow pipeline — an autonomous decision engine (Opus)
   that evaluates every candidate and writes nothing to live config
5. Produces a six-section PDF digest covering candidates, CLAIRE-A shadow
   decisions, and the running eval loop
6. Commits the digest to the repo and sends a Pushover notification

You review the digest. You write hypotheses. You apply changes. Every applied
change is logged in `change_log.json` with its hypothesis and eval status.
CLAIRE-A exists to study what autonomous application would look like before
you decide whether to allow it.

---

## Architecture

```
Reddit public JSON (local, Monday)
HackerNews API (GHA, Sunday)      →  Ingest  →  raw_posts.json
dev.to API (GHA, Sunday)

raw_posts.json  →  Triage (Haiku)  →  Track A / B / C queues

Track A (memory/profile)  ─┐
Track B (skill candidates) ─┤  Synthesis (Sonnet, parallel)  →  candidates
Track C (technique)       ─┘

candidates  →  CLAIRE-A Assembler
            →  Decision Engine (Opus)     shadow decisions
            →  Eval Scorer (Sonnet)       reliability ledger

candidates + shadow decisions  →  Output (reportlab PDF)  →  output/

GHA commit-back + Pushover notification
```

**CLAIRE-A is shadow only.** It reads everything and authorizes nothing.
It writes shadow decisions to the digest so you can compare its calls against
yours over time. Graduation criteria before any live application: 80%
agreement rate over 6 consecutive runs, 10+ scored hypotheses in the
reliability ledger, zero escalations in the last 3 runs.

---

## Directory Structure

```
CLAIRE/
├── claire_ingest.py           # Reddit + HackerNews + dev.to ingest
├── claire_triage.py           # Haiku classification, three-track routing
├── claire_synthesize.py       # Sonnet synthesis, parallel tracks
├── claire_output.py           # reportlab PDF digest builder
├── claire_a_assembler.py      # CLAIRE-A input payload builder
├── claire_a_runner.py         # Opus decision engine
├── claire_a_scorer.py         # Sonnet eval scorer, reliability ledger
├── claire_utils.py            # Shared helpers (cost logging, etc.)
├── claire_weekly.ps1          # Local scheduled wrapper
├── config.json                # All locked pipeline decisions
├── requirements.txt
├── .env                       # ANTHROPIC_API_KEY (never commit)
├── change_log.json            # Applied changes + eval loop  ← YOU maintain
├── friction_log.txt           # Weekly behavioral observations  ← YOU maintain
├── data/
│   ├── raw_posts.json
│   ├── tagged_posts.json
│   ├── synthesis_queue_track_a.json
│   ├── synthesis_queue_track_b.json
│   ├── synthesis_queue_track_c.json
│   ├── archive.json
│   ├── memory_edits_snapshot.txt
│   ├── claire_a_input_[timestamp].json
│   ├── claire_a_decisions_[timestamp].json
│   ├── claire_a_reasoning_[timestamp].txt
│   ├── claire_a_source_reliability.json
│   └── claire_a_session_history.json
├── output/                    # Weekly PDF digests
├── skill_drafts/              # SKILL.md skeletons from Track B
├── prompts/
│   ├── triage_prompt.txt
│   ├── synthesis_prompts.py
│   └── profile_intent_summary.txt
└── docs/
    ├── claire_pipeline_flow.jsx
    └── reddit_app_setup.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- GitHub account with Actions enabled
- Anthropic API key (Haiku + Sonnet + Opus access)
- Pushover account (app token + user key)

### Clone and install
```bash
git clone https://github.com/shamblingshade/CLAIRE.git
cd CLAIRE
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
python -m pip install -r requirements.txt
```

### Configure `.env`
```
ANTHROPIC_API_KEY=your_key_here
```
This file is `.gitignore`d. Never commit it.

### GitHub Secrets
Four secrets required in your repo settings:

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Claude API access |
| `GH_PAT` | Commit-back (fine-grained PAT, Contents read+write) |
| `PUSHOVER_APP_TOKEN` | Pushover delivery |
| `PUSHOVER_USER_KEY` | Pushover delivery |

### Personalize before first run
CLAIRE synthesizes candidates against *your* configuration. Before running,
populate:

- `data/memory_edits_snapshot.txt` — paste your current Claude memory edits
- `prompts/profile_intent_summary.txt` — 200-400 word summary of your Claude
  profile goals and behavioral priorities
- `friction_log.txt` — at least one cycle of behavioral observations (format
  below)

The synthesis stage injects both files into Track A and B prompts. Without
them, candidates are generic community signal with no personal filtering.

---

## Weekly Ritual

Reddit blocks datacenter IPs, so ingest is split across two jobs:

**Monday 07:00 local** (automatic, Task Scheduler or launchd)
```
python claire_ingest.py --source reddit
git add data/raw_posts.json
git commit -m "ingest: reddit update $(date +%Y-%m-%d)"
git push
```

**Before Sunday** (manual, 5 minutes)

Update `friction_log.txt` with 2-4 behavioral observations from the past week.
Commit and push. This is the cross-reference gate's ground truth -- skip it
and all candidates score MEDIUM regardless of relevance.

**Sunday 14:00 UTC** (automatic, GitHub Actions)

GHA fires `.github/workflows/claire_weekly.yml`, runs HackerNews and dev.to
ingest, triage, synthesis, CLAIRE-A pipeline, digest generation, commit-back,
and Pushover notification.

**After digest review** (manual, 10-20 minutes)

For each candidate you decide to apply:
1. Write a hypothesis -- what you expect the change to do and why
2. Add an entry to `change_log.json` (schema below) before applying anything
3. Apply the change to your Claude configuration
4. Set `eval_status: "pending"` and the applicable eval window

---

## Maintenance Files

### `friction_log.txt`
Human-maintained. 2-4 entries per cycle minimum. Blank weeks force everything
to MEDIUM confidence next cycle -- the cross-reference gate loses precision.

```
# Format: YYYY-MM-DD | [context] | [component] | [severity: LOW/MEDIUM/HIGH]

2026-05-10 | digest review session | memory persistence | MEDIUM
Em dash suppression applied as memory edit. Training weight appears to
override preference-level instructions for this pattern. Holding to observe
before escalating to profile-level hard rule.
```

### `change_log.json`
One entry per applied change. Schema version 1.1.

```json
{
  "id": "c5-mem-001",
  "date": "2026-05-19",
  "cycle": 5,
  "type": "memory_edit",
  "action": "add",
  "target": "Memory — [description]",
  "summary": "One sentence. What the memory says.",
  "hypothesis": "What you expect this change to do and why. Your words.",
  "source_signal": "Track and source posts that motivated this candidate.",
  "eval_status": "pending",
  "eval_notes": ""
}
```

`type` values: `memory_edit`, `profile_diff`, `skill_install`
`eval_status` values: `pending`, `held`, `partial`, `no`, `queued`, `n/a`

**Every applied change requires a human-written hypothesis before application.
This is not optional.** The eval loop has nothing to measure against without it.

---

## Locked Pipeline Decisions

| Decision | Value |
|----------|-------|
| Triage model | `claude-haiku-4-5-20251001` |
| Synthesis model | `claude-sonnet-4-6` |
| Decision engine model | `claude-opus-4-5` (CLAIRE-A) |
| Eval scoring model | `claude-sonnet-4-6` (CLAIRE-A) |
| Evidence threshold | 3 corroborating posts minimum |
| Noise prefilter | score < 5 AND comments < 2 → drop |
| Track A batch ceiling | 50 posts per synthesis call |
| CLAIRE-A batch ceiling | 15 candidates per decision engine run |
| Hypothesis authorship | Human-written for applied changes; Opus-written for shadow decisions |
| CLAIRE-A mode | Shadow only -- reads everything, writes nothing to live config |
| Reddit ingest | Unauthenticated public JSON -- no OAuth credentials required |
| HackerNews + dev.to | GitHub Actions, Sunday 14:00 UTC |
| Reddit | Local scheduled task, Monday 07:00 |

Changes to locked decisions require a hypothesis and explicit session approval.
Do not modify `config.json` items without documenting the rationale.

---

## What Degrades Without Maintenance

`friction_log.txt` -- if you stop updating it, the cross-reference gate has no
ground truth. Signal scores MEDIUM across the board. Candidates stop being
filtered against your actual friction patterns. CLAIRE becomes a Reddit-to-
config pipeline with no personal calibration.

`change_log.json` hypotheses -- if you apply changes without hypotheses, the
quarterly eval has nothing to measure against. You lose the eval loop entirely.
CLAIRE-A's agreement rate becomes meaningless because there is no human
decision record to compare against.

Neither file is optional infrastructure.

---

## Quarterly Review

Feed `change_log.json` + `friction_log.txt` to Claude. Ask for an eval report:
what held, what didn't, what to revert, where CLAIRE-A agreement rate stands.
Update `eval_notes` on each entry with findings. Revert changes that failed
their hypothesis. 30 minutes, four times a year.

---

## CLAIRE-A Graduation Criteria

CLAIRE-A operates in shadow mode indefinitely until you decide it has earned
trust. The criteria for considering live application:

- 80% agreement rate with your decisions over 6 consecutive eval runs
- 10+ scored hypotheses in the reliability ledger
- Zero escalations in the last 3 runs

Meeting these criteria does not automatically change anything. It means the
data supports a conversation about what, if anything, to hand over. The human
authorizes every applied change until you explicitly decide otherwise.

---

## Design Principles

CLAIRE is built on three constraints that are not negotiable:

**Human-in-the-loop.** Every applied change requires a human-written hypothesis
before application. CLAIRE generates candidates. You decide.

**Audit trail.** `change_log.json` records every applied change with its
hypothesis, source signal, and eval status. If you can't explain why a change
was made, it shouldn't be in the log.

**Evidence threshold.** Three corroborating posts minimum for Track A
candidates. One enthusiastic post does not make a configuration change.

These are not preferences. They are the difference between an optimization
system and a pipeline that randomly edits your AI configuration based on
whatever Reddit was complaining about this week.
