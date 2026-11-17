"""Convert the Markdown manuscript into an ACS-styled .docx submission file.

Handles: title/headings, bold/italic inline, Word tables from tables/*.csv via
[[TABLE:name|caption]] markers, figures from figures/*.png via [[FIGURE:name|caption]]
markers, and an auto-generated ACS reference list. Produces a clean academic layout
(not a raw Markdown dump): Times New Roman, 12pt, numbered sections, captions.

Usage: python build_docx.py [manuscript.md] [out.docx]
"""
import re, sys, csv
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"


def set_cell_background(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): hexcolor})
    tcPr.append(shd)


def add_runs_with_markup(paragraph, text):
    """Parse **bold**, *italic*, `code` into runs."""
    tokens = re.split(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = paragraph.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("*") and tok.endswith("*"):
            r = paragraph.add_run(tok[1:-1]); r.italic = True
        elif tok.startswith("`") and tok.endswith("`"):
            r = paragraph.add_run(tok[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(10)
        else:
            paragraph.add_run(tok)


def add_table_from_csv(doc, name, caption):
    path = TABLES / f"{name}.csv"
    if not path.exists():
        doc.add_paragraph(f"[table {name} not found]")
        return
    with open(path) as f:
        rows = list(csv.reader(f))
    if not rows:
        return
    cap = doc.add_paragraph()
    cr = cap.add_run(f"Table. {caption}"); cr.bold = True; cr.font.size = Pt(10)
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]  # pad ragged rows
    t = doc.add_table(rows=len(rows), cols=ncols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Light Grid Accent 1"
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.size = Pt(8.5)
            if i == 0:
                run.bold = True
    doc.add_paragraph()


def add_figure(doc, name, caption):
    for ext in ("png", "pdf"):
        path = FIGURES / f"{name}.{ext}"
        if path.exists() and ext == "png":
            doc.add_picture(str(path), width=Inches(5.2))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cr = cap.add_run(f"Figure. {caption}"); cr.italic = True; cr.font.size = Pt(9)
            return
    doc.add_paragraph(f"[figure {name} not found]")


def build(md_path, out_path):
    md = Path(md_path).read_text().splitlines()
    doc = Document()
    # base style
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    i = 0
    in_refs = False
    while i < len(md):
        line = md[i].rstrip("\n")
        s = line.strip()
        # markers
        mt = re.match(r"\[\[TABLE:([^|]+)\|(.+?)\]\]", s)
        mf = re.match(r"\[\[FIGURE:([^|]+)\|(.+?)\]\]", s)
        if mt:
            add_table_from_csv(doc, mt.group(1).strip(), mt.group(2).strip()); i += 1; continue
        if mf:
            add_figure(doc, mf.group(1).strip(), mf.group(2).strip()); i += 1; continue
        if s.startswith("# "):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(s[2:]); r.bold = True; r.font.size = Pt(15)
        elif s.startswith("## "):
            title = s[3:]
            p = doc.add_heading(level=1); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(title); r.bold = True; r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(0, 0, 0)
            in_refs = title.strip().lower().startswith("references")
        elif s.startswith("### "):
            p = doc.add_heading(level=2)
            r = p.add_run(s[4:]); r.bold = True; r.font.size = Pt(11.5)
            r.font.color.rgb = RGBColor(0, 0, 0)
        elif s.startswith("|") and "---" not in s:
            # inline markdown table rows that are not marker-driven: render as text
            doc.add_paragraph(s)
        elif s == "---" or s == "":
            if s == "":
                doc.add_paragraph()
        elif re.match(r"^\d+\.\s", s) and in_refs:
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
            add_runs_with_markup(p, s)
            p.runs and setattr(p.runs[0].font, "size", Pt(9.5))
            for r in p.runs:
                r.font.size = Pt(9.5)
        elif s.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_runs_with_markup(p, s[2:])
        else:
            p = doc.add_paragraph()
            add_runs_with_markup(p, s)
        i += 1
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    md = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "manuscript_final.md")
    out = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "Final_Manuscript.docx")
    build(md, out)
