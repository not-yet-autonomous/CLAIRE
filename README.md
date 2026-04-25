# CLAIRE
### Claude Loop for Adaptive Intelligence from Reddit Evidence

Personal AI configuration improvement pipeline. Mines Reddit signal,
filters it against your actual friction patterns, synthesizes actionable
candidates for memory edits, skill builds, and profile refinements.

---

## Directory Structure

```
claire/
├── config.json                    # All locked pipeline decisions
├── data/
│   ├── friction_log.txt           # Weekly friction notes (YOU maintain this)
│   ├── change_log.json            # Applied changes + eval loop (YOU maintain this)
│   ├── memory_edits_snapshot.txt  # Copy of current memory edits before each run
│   ├── raw_posts.json             # Build 1 output — ingested Reddit posts
│   ├── tagged_posts.json          # Build 2 output — triage-classified posts
│   ├── synthesis_queue_*.json     # Build 2 output — routed by track and confidence
│   └── archive.json               # LOW confidence items — quarterly review
├── output/                        # Weekly digest .docx files
├── skill_drafts/                  # SKILL.md skeletons from Track B
├── archive/                       # Low-confidence signal archive
└── prompts/
    ├── profile_intent_summary.txt # Injected into Track A and B synthesis
    ├── triage_prompt.txt          # Haiku triage system prompt
    └── synthesis_prompts.py       # All three Sonnet synthesis prompts
```

---

## Build Sequence

| Build | File | Description | Est. Time |
|-------|------|-------------|-----------|
| 0 | *(this setup)* | Eval infrastructure, config, prompts | ✅ Done |
| 1 | `claire_ingest.py` | PRAW ingestion + raw_posts.json cache | ~2 hrs |
| 2 | `claire_triage.py` | Haiku classification + cross-reference gate | ~2 hrs |
| 3 | `claire_synthesize.py` | Sonnet synthesis, three tracks | ~3 hrs |
| 3 | `claire_output.py` | Weekly digest .docx via docx-env skill | ~1 hr |

---

## Weekly Maintenance (YOU — 10 minutes)

1. **Sunday evening** — add 2-4 entries to `friction_log.txt`
2. **After review** — for any candidate you apply, add entry to `change_log.json`
   with your hypothesis before applying the change
3. **After sessions** where a changed behavior was relevant — add eval note
   to that change's `eval_notes` array

## Quarterly Maintenance (YOU + Claude — 30 minutes)

Feed `change_log.json` + `friction_log.txt` to Claude.
Ask for eval report: what held, what didn't, what to revert.
Update `quarterly_evals` array in change_log.json with findings.

---

## Locked Decisions

| Decision | Value |
|----------|-------|
| Config injection depth | Partial (intent summary + memory list) |
| Developer persona | Filter out |
| Hypothesis authorship | Human-written |
| Evidence threshold | 3 corroborating posts minimum |
| Triage model | claude-haiku-4-5-20251001 |
| Synthesis model | claude-sonnet-4-6 |
| Noise prefilter | score < 5 AND comments < 2 → drop |
| Scheduling | Windows Task Scheduler, weekly Sunday |

---

## Critical: What Degrades Without Maintenance

**friction_log.txt** — if you stop updating this, the cross-reference gate
has no ground truth. All signal scores MEDIUM regardless of relevance.
CLAIRE becomes a Reddit-to-config pipeline with no personal filtering.
The whole bias-correction layer collapses.

**change_log.json hypotheses** — if you apply changes without writing
hypotheses, the quarterly eval has nothing to measure against.
You lose the eval loop entirely.

---

## Reddit App Prerequisites (Build 1)

See reddit_app_setup.md for registration steps.
Credentials go in environment variables — never hardcoded.

Required env vars:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT (format: "CLAIRE/0.1 by /u/YOUR_USERNAME")
