"""
CLAIRE — Build 3b: Output Layer
Input:   data/candidates_track_a/b/c.json
Output:  output/CLAIRE_Weekly_Digest_YYYY-MM-DD.docx
         skill_drafts/*.md (Track B skill skeletons)

Run:     python claire_output.py
         python claire_output.py --date 2026-04-25  (override date)
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
OUTPUT_DIR      = BASE_DIR / "output"
SKILL_DRAFT_DIR = BASE_DIR / "skill_drafts"
LOGS_DIR        = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(exist_ok=True)
SKILL_DRAFT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

OUTPUT_LOG_PATH = LOGS_DIR / "output.log"

CANDIDATE_PATHS = {
    "a": DATA_DIR / "candidates_track_a.json",
    "b": DATA_DIR / "candidates_track_b.json",
    "c": DATA_DIR / "candidates_track_c.json",
}

TRIAGE_TAGGED_PATH = DATA_DIR / "tagged_posts.json"

# Waterton brand colors
NAVY        = RGBColor(0x1E, 0x3A, 0x5F)
GOLD        = RGBColor(0xC5, 0xA0, 0x30)
CHARCOAL    = RGBColor(0x3C, 0x3C, 0x3C)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = "F7F8FA"
BORDER_GRAY = "E2E8F0"
NAVY_HEX    = "1E3A5F"
GOLD_HEX    = "C5A030"
GREEN_HEX   = "2D6A4F"
AMBER_HEX   = "8B6914"

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(OUTPUT_LOG_PATH, encoding="utf-8"),
    ]
)
log = logging.getLogger("claire.output")

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT HELPERS — Waterton theme
# ─────────────────────────────────────────────────────────────────────────────

def init_document() -> Document:
    """Create and configure a Waterton-themed document."""
    doc = Document()

    # US Letter, 1" margins
    section = doc.sections[0]
    section.page_width    = Inches(8.5)
    section.page_height   = Inches(11)
    section.left_margin   = Inches(1)
    section.right_margin  = Inches(1)
    section.top_margin    = Inches(1)
    section.bottom_margin = Inches(1)

    # Normal style
    normal = doc.styles["Normal"]
    normal.font.name      = "Century Gothic"
    normal.font.size      = Pt(11)
    normal.font.color.rgb = CHARCOAL
    normal.paragraph_format.space_after  = Pt(6)

    # Heading styles
    def set_heading(style_name, size, color, before, after):
        s = doc.styles[style_name]
        s.font.name      = "Georgia"
        s.font.size      = Pt(size)
        s.font.bold      = True
        s.font.color.rgb = color
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after  = Pt(after)

    set_heading("Heading 1", 22, NAVY,  18, 6)
    set_heading("Heading 2", 16, GOLD,  12, 4)
    set_heading("Heading 3", 13, GOLD,  10, 3)

    # Strip bottom borders from Title and Heading styles in default template.
    # Word's default.dotx embeds a blue bottom border on the Title style
    # which renders as a line through large paragraph text.
    def clear_style_borders(style):
        pPr = style.element.find(qn("w:pPr"))
        if pPr is not None:
            for pBdr in pPr.findall(qn("w:pBdr")):
                pPr.remove(pBdr)

    for style_name in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
        try:
            clear_style_borders(doc.styles[style_name])
        except KeyError:
            pass

    return doc


def clear_paragraph_borders(para):
    """Explicitly remove all paragraph borders inherited from template."""
    pPr = para._p.get_or_add_pPr()
    for pBdr in pPr.findall(qn("w:pBdr")):
        pPr.remove(pBdr)
    pBdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right", "between"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        pBdr.append(el)
    pPr.append(pBdr)


def add_title_block(doc: Document, date_str: str):
    """Add CLAIRE document title block."""
    # Eyebrow
    eyebrow = doc.add_paragraph()
    run = eyebrow.add_run("Weekly Intelligence Digest")
    run.font.name      = "Georgia"
    run.font.size      = Pt(11)
    run.font.italic    = True
    run.font.color.rgb = GOLD
    eyebrow.paragraph_format.space_before = Pt(0)
    eyebrow.paragraph_format.space_after  = Pt(4)
    eyebrow.paragraph_format.line_spacing = None
    clear_paragraph_borders(eyebrow)

    # Title
    title_para = doc.add_paragraph()
    run = title_para.add_run("CLAIRE")
    run.font.name      = "Georgia"
    run.font.size      = Pt(28)
    run.font.bold      = True
    run.font.color.rgb = NAVY
    title_para.paragraph_format.space_before = Pt(6)
    title_para.paragraph_format.space_after  = Pt(6)
    title_para.paragraph_format.line_spacing = None
    clear_paragraph_borders(title_para)

    # Subtitle
    sub = doc.add_paragraph()
    run = sub.add_run(f"Claude Configuration Signal Report — {date_str}")
    run.font.name      = "Georgia"
    run.font.size      = Pt(14)
    run.font.bold      = True
    run.font.color.rgb = GOLD
    sub.paragraph_format.space_before = Pt(0)
    sub.paragraph_format.space_after  = Pt(28)
    sub.paragraph_format.line_spacing = None
    clear_paragraph_borders(sub)


def add_rule(doc: Document, color_hex: str = GOLD_HEX):
    """Add a horizontal rule."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "8")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def shade_cell(cell, fill_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  fill_hex)
    tcPr.append(shd)


def set_cell_borders(cell, color: str = BORDER_GRAY):
    tcPr  = cell._tc.get_or_add_tcPr()
    tcBdr = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    "4")
        el.set(qn("w:color"), color)
        tcBdr.append(el)
    tcPr.append(tcBdr)


def header_cell(cell, text: str):
    shade_cell(cell, NAVY_HEX)
    set_cell_borders(cell)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    run = cell.paragraphs[0].add_run(text)
    run.font.name      = "Century Gothic"
    run.font.size      = Pt(10)
    run.font.bold      = True
    run.font.color.rgb = WHITE


def body_cell(cell, text: str, even: bool = True):
    shade_cell(cell, "FFFFFF" if even else LIGHT_GRAY)
    set_cell_borders(cell)
    run = cell.paragraphs[0].add_run(str(text))
    run.font.name      = "Century Gothic"
    run.font.size      = Pt(10)
    run.font.color.rgb = CHARCOAL


def add_confidence_badge(para, confidence: str):
    """Inline confidence indicator."""
    run = para.add_run(f" [{confidence}]")
    run.font.name = "Century Gothic"
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = NAVY if confidence == "HIGH" else GOLD


def add_callout(doc: Document, text: str):
    """Light gray callout box with gold left border — for hypothesis prompt."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"),   "single")
    left.set(qn("w:sz"),    "12")
    left.set(qn("w:color"), GOLD_HEX)
    left.set(qn("w:space"), "20")
    pBdr.append(left)
    pPr.append(pBdr)
    # Background
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  LIGHT_GRAY)
    pPr.append(shd)
    run = p.add_run(text)
    run.font.name      = "Century Gothic"
    run.font.size      = Pt(10)
    run.font.italic    = True
    run.font.color.rgb = CHARCOAL


# ─────────────────────────────────────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_signal_summary(doc: Document, triage_data: dict):
    """Section 1 — Signal Summary."""
    doc.add_heading("Signal Summary", level=1)

    meta  = triage_data.get("meta", {})
    stats = meta.get("stats", {})

    # Run metadata
    run_at = meta.get("run_at", "unknown")
    total  = meta.get("total", 0)

    para = doc.add_paragraph()
    para.add_run(f"Run date: ").bold = True
    para.add_run(run_at[:10])
    para2 = doc.add_paragraph()
    para2.add_run("Posts scanned: ").bold = True
    para2.add_run(str(total))

    doc.add_heading("Signal Breakdown", level=2)

    # Signal type table
    by_signal  = stats.get("by_signal", {})
    by_persona = stats.get("by_persona", {})
    by_source  = stats.get("by_source", {})

    headers = ["Category", "Count"]
    rows = [
        ["behavior_complaint", str(by_signal.get("behavior_complaint", 0))],
        ["workflow_gap",       str(by_signal.get("workflow_gap", 0))],
        ["feature_praise",     str(by_signal.get("feature_praise", 0))],
        ["competitor_gap",     str(by_signal.get("competitor_gap", 0))],
        ["cross_platform",     str(by_signal.get("cross_platform_workflow", 0))],
        ["noise (dropped)",    str(by_signal.get("noise", 0))],
    ]

    table = doc.add_table(rows=1 + len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    col_widths = [6240, 3120]
    for i, col in enumerate(table.columns):
        col.width = col_widths[i]

    for i, h in enumerate(headers):
        header_cell(table.rows[0].cells[i], h)
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            body_cell(table.rows[r_idx + 1].cells[c_idx], val, even=(r_idx % 2 == 0))

    doc.add_paragraph()
    doc.add_heading("Developer Signal Disposition", level=2)
    dev_count = by_persona.get("developer", 0)
    p = doc.add_paragraph()
    p.add_run(f"{dev_count} developer-persona posts filtered at cross-reference gate "
              f"per locked pipeline configuration (filter_out).")

    add_rule(doc)


def build_track_a_section(doc: Document, candidates: dict):
    """Section 2 — Memory Edit Candidates and Profile Diffs."""
    doc.add_heading("Track A — Claude Native Signal", level=1)

    memory_edits  = candidates.get("memory_edit_candidates", [])
    profile_diffs = candidates.get("profile_diff_candidates", [])
    watch_list    = candidates.get("behavior_watch", [])

    # Memory edit candidates
    doc.add_heading("Memory Edit Candidates", level=2)
    if not memory_edits:
        doc.add_paragraph("No memory edit candidates this cycle. "
                          "Signal below evidence threshold or no patterns identified.")
    else:
        for i, candidate in enumerate(memory_edits, 1):
            para = doc.add_paragraph()
            run = para.add_run(f"{i}. {candidate.get('control', '')}")
            run.font.bold      = True
            run.font.name      = "Century Gothic"
            run.font.color.rgb = NAVY
            add_confidence_badge(para, candidate.get("confidence", "MEDIUM"))

            doc.add_paragraph(candidate.get("rationale", "")).style = doc.styles["Normal"]

            # Ready-to-apply command
            add_callout(doc,
                f"Apply command: memory_user_edits → add → \"{candidate.get('control', '')}\"\n"
                f"Write your hypothesis before applying.")

            # Source links
            sources = candidate.get("source_posts", [])
            if sources:
                src_para = doc.add_paragraph()
                src_para.add_run("Sources: ").bold = True
                src_para.add_run(" · ".join(
                    f"reddit.com{p}" if p.startswith("/r/") else p
                    for p in sources[:5]
                ))
                src_para.runs[-1].font.size = Pt(9)

            if i < len(memory_edits):
                doc.add_paragraph()

    add_rule(doc)

    # Profile diff candidates
    doc.add_heading("Profile Diff Candidates", level=2)
    if not profile_diffs:
        doc.add_paragraph("No profile diff candidates this cycle.")
    else:
        for i, candidate in enumerate(profile_diffs, 1):
            para = doc.add_paragraph()
            run = para.add_run(
                f"{i}. Target section: {candidate.get('target_section', '')}")
            run.font.bold      = True
            run.font.name      = "Century Gothic"
            run.font.color.rgb = NAVY
            add_confidence_badge(para, candidate.get("confidence", "MEDIUM"))

            doc.add_paragraph(
                f"Proposed change: {candidate.get('proposed_change', '')}"
            ).style = doc.styles["Normal"]
            doc.add_paragraph(candidate.get("rationale", "")).style = doc.styles["Normal"]

            add_callout(doc, "Review proposed change against current profile section "
                            "before applying. Write hypothesis first.")

            sources = candidate.get("source_posts", [])
            if sources:
                src_para = doc.add_paragraph()
                src_para.add_run("Sources: ").bold = True
                src_para.add_run(" · ".join(sources[:5]))
                src_para.runs[-1].font.size = Pt(9)

    add_rule(doc)

    # Behavior watch list
    doc.add_heading("Behavior Watch List", level=2)
    doc.add_paragraph(
        "Patterns flagged for monitoring — not yet actionable. "
        "Check against personal session notes before next cycle."
    )
    if not watch_list:
        doc.add_paragraph("Nothing on watch list this cycle.")
    else:
        for item in watch_list:
            para = doc.add_paragraph(style="List Bullet")
            para.add_run(item.get("pattern", "")).bold = True
            doc.add_paragraph(
                f"Why not actioned: {item.get('why_not_actioned', '')}"
            ).style = doc.styles["Normal"]

    add_rule(doc)


def build_track_b_section(doc: Document, candidates: dict):
    """Section 3 — Competitor Gap Signal."""
    doc.add_heading("Track B — Competitor Gap Signal", level=1)

    skill_drafts     = candidates.get("skill_draft_candidates", [])
    profile_additions = candidates.get("profile_addition_candidates", [])

    doc.add_heading("Skill Draft Candidates", level=2)
    if not skill_drafts:
        doc.add_paragraph(
            "No skill draft candidates this cycle. "
            "Competitor gap signal below evidence threshold of 3 corroborating posts. "
            "This is expected in early cycles — pattern builds over weekly runs."
        )
    else:
        for i, candidate in enumerate(skill_drafts, 1):
            para = doc.add_paragraph()
            run = para.add_run(f"{i}. {candidate.get('skill_name', '')}")
            run.font.bold      = True
            run.font.color.rgb = NAVY
            run.font.name      = "Century Gothic"
            add_confidence_badge(para, candidate.get("confidence", "MEDIUM"))

            doc.add_paragraph(
                f"Gap: {candidate.get('gap_description', '')}"
            ).style = doc.styles["Normal"]
            doc.add_paragraph(
                f"Trigger: {candidate.get('trigger_description', '')}"
            ).style = doc.styles["Normal"]
            doc.add_paragraph(
                f"Estimated effort: {candidate.get('estimated_build_effort', '')}"
            ).style = doc.styles["Normal"]

            add_callout(doc,
                f"SKILL.md skeleton saved to skill_drafts/{candidate.get('skill_name', 'skill').replace(' ', '_')}.md")

    add_rule(doc)

    doc.add_heading("Profile Addition Candidates", level=2)
    if not profile_additions:
        doc.add_paragraph("No profile addition candidates this cycle.")
    else:
        for i, candidate in enumerate(profile_additions, 1):
            para = doc.add_paragraph()
            run = para.add_run(f"{i}. Section: {candidate.get('target_section', '')}")
            run.font.bold      = True
            run.font.color.rgb = NAVY
            run.font.name      = "Century Gothic"
            add_confidence_badge(para, candidate.get("confidence", "MEDIUM"))

            doc.add_paragraph(candidate.get("proposed_text", "")).style = doc.styles["Normal"]
            doc.add_paragraph(candidate.get("rationale", "")).style = doc.styles["Normal"]

    add_rule(doc)


def build_track_c_section(doc: Document, candidates: dict):
    """Section 4 — Cross-Platform Workflow Techniques."""
    doc.add_heading("Track C — Cross-Platform Workflow Techniques", level=1)
    doc.add_paragraph(
        "Portable techniques to test manually before any configuration change is considered."
    )

    techniques = candidates.get("technique_candidates", [])

    if not techniques:
        doc.add_paragraph("No technique candidates this cycle.")
    else:
        for i, technique in enumerate(techniques, 1):
            para = doc.add_paragraph()
            run = para.add_run(f"{i}. {technique.get('technique_name', '')}")
            run.font.bold      = True
            run.font.color.rgb = NAVY
            run.font.name      = "Century Gothic"
            add_confidence_badge(para, technique.get("confidence", "MEDIUM"))

            doc.add_paragraph(technique.get("description", "")).style = doc.styles["Normal"]
            add_callout(doc, f"Test: {technique.get('test_suggestion', '')}")

    add_rule(doc)


def build_eval_section(doc: Document, date_str: str):
    """Section 5 — Eval Status."""
    doc.add_heading("Eval Loop Status", level=1)

    doc.add_heading("Applied Changes Pending Eval", level=2)
    doc.add_paragraph(
        "Review change_log.json for changes applied since last digest. "
        "For each change where a relevant session has occurred, add an eval note:"
    )
    add_callout(doc,
        f"{date_str} | [session context] | held/partial/no | [one sentence notes]")

    doc.add_heading("Friction Log Reminder", level=2)
    doc.add_paragraph(
        "Update data/friction_log.txt this week. "
        "2-4 entries. Specific behaviors in specific contexts. "
        "Blank weeks score everything MEDIUM next cycle — the cross-reference gate loses precision."
    )

    doc.add_heading("Quarterly Eval", level=2)
    doc.add_paragraph(
        "If quarterly eval is due: feed change_log.json and friction_log.txt to Claude. "
        "Request eval report. Revert changes that did not hold. "
        "Flag source signal from reverted changes as low-quality in archive."
    )


# ─────────────────────────────────────────────────────────────────────────────
# SKILL DRAFT FILE WRITER
# ─────────────────────────────────────────────────────────────────────────────

def write_skill_drafts(candidates_b: dict) -> int:
    """Write SKILL.md skeleton files for Track B skill candidates."""
    skill_drafts = candidates_b.get("skill_draft_candidates", [])
    written = 0

    for candidate in skill_drafts:
        name     = candidate.get("skill_name", "unnamed_skill")
        skeleton = candidate.get("skill_md_skeleton", "")
        filename = name.lower().replace(" ", "_").replace("/", "_") + ".md"
        path     = SKILL_DRAFT_DIR / filename

        content = f"""---
name: {name}
description: {candidate.get('trigger_description', '')}
status: DRAFT — generated by CLAIRE, requires human review and implementation
generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
confidence: {candidate.get('confidence', 'MEDIUM')}
estimated_effort: {candidate.get('estimated_build_effort', 'unknown')}
source_signal: {', '.join(candidate.get('source_posts', [])[:3])}
---

# {name}

## Gap Description
{candidate.get('gap_description', '')}

## Trigger
{candidate.get('trigger_description', '')}

## Skeleton
{skeleton}

## Implementation Notes
(Complete this section before installing the skill)

## Review Status
- [ ] Gap confirmed from personal session experience
- [ ] Hypothesis written
- [ ] Implementation complete
- [ ] Tested in session
- [ ] Installed
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        log.info(f"Skill draft written → {filename}")
        written += 1

    return written


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLAIRE output layer")
    parser.add_argument("--date", help="Override digest date (YYYY-MM-DD)")
    args = parser.parse_args()

    date_str  = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_start = datetime.now(timezone.utc)

    log.info(f"CLAIRE output started — date={date_str}")

    # Load candidate files
    candidates = {}
    for track, path in CANDIDATE_PATHS.items():
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            candidates[track] = data.get("candidates", {})
            log.info(f"Track {track.upper()} candidates loaded from {path.name}")
        else:
            log.warning(f"Candidate file missing: {path.name} — section will show empty")
            candidates[track] = {}

    # Load triage metadata for signal summary
    triage_data = {}
    if TRIAGE_TAGGED_PATH.exists():
        with open(TRIAGE_TAGGED_PATH, encoding="utf-8") as f:
            triage_data = json.load(f)

    # Build document
    doc = init_document()
    add_title_block(doc, date_str)

    build_signal_summary(doc, triage_data)
    build_track_a_section(doc, candidates.get("a", {}))
    build_track_b_section(doc, candidates.get("b", {}))
    build_track_c_section(doc, candidates.get("c", {}))
    build_eval_section(doc, date_str)

    # Save document
    filename = f"CLAIRE_Weekly_Digest_{date_str}.docx"
    output_path = OUTPUT_DIR / filename
    try:
        doc.save(str(output_path))
        log.info(f"Digest saved → {output_path}")
    except PermissionError:
        locked_path = OUTPUT_DIR / f"CLAIRE_Weekly_Digest_{date_str}_locked.docx"
        doc.save(str(locked_path))
        log.warning(f"Output file was locked — saved to fallback: {locked_path.name}")
    except Exception as e:
        log.error(f"Failed to save digest: {e}")
        sys.exit(1)

    # Write skill drafts
    skill_count = write_skill_drafts(candidates.get("b", {}))
    log.info(f"Skill drafts written: {skill_count}")

    log.info("═" * 60)
    log.info("CLAIRE output complete.")
    log.info(f"Digest: {output_path}")
    log.info(f"Skill drafts: {skill_count} files in skill_drafts/")
    log.info("Review the digest. Apply candidates manually with hypotheses.")


if __name__ == "__main__":
    main()
get("b", {}))
    log.info(f"Skill drafts written: {skill_count}")

    log.info("=" * 60)
    log.info("CLAIRE output complete.")
    log.info(f"Digest: {output_path}")
    log.info(f"Skill drafts: {skill_count} files in skill_drafts/")
    log.info("Review the digest. Apply candidates manually with hypotheses.")


if __name__ == "__main__":
    main()
)
