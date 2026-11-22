"""Build submission DOCX files from the Markdown sources with pandoc, so that all
mathematics is rendered as native Word equations (OMML) rather than raw LaTeX.

  [[TABLE:name|caption]]   -> numbered table built from tables/<name>.csv (caption above)
  [[FIGURE:name|caption]]  -> numbered figure from figures/<name>.png (caption below)

Usage: python build_pandoc.py <input.md> <output.docx> [--author "Name"] [--title "Title"]
Requires pandoc >= 2.11 and python-docx.
"""
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"
FONT = "Times New Roman"


def make_reference_docx(path):
    data = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                          check=True, capture_output=True).stdout
    path.write_bytes(data)
    doc = Document(str(path))
    for st in doc.styles:
        try:
            f = st.font
        except AttributeError:
            continue
        if f is None:
            continue
        f.name = FONT
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(a), FONT)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rfonts.get(qn(a)) is not None:
                del rfonts.attrib[qn(a)]
        if st.name.startswith("Heading") or st.name == "Title":
            f.color.rgb = RGBColor(0, 0, 0); f.bold = True
    sizes = {"Normal": 12, "Body Text": 12, "First Paragraph": 12, "Compact": 10, "Title": 16,
             "Heading 1": 14, "Heading 2": 12, "Heading 3": 12, "Block Text": 12,
             "Image Caption": 10, "Table Caption": 10, "Author": 12}
    for name, sz in sizes.items():
        try:
            doc.styles[name].font.size = Pt(sz)
        except KeyError:
            pass
    for name in ("Body Text", "First Paragraph", "Block Text"):
        try:
            pf = doc.styles[name].paragraph_format
            pf.line_spacing = 1.5; pf.space_after = Pt(6)
        except KeyError:
            pass
    for name in ("Image Caption", "Table Caption"):
        try:
            doc.styles[name].font.italic = False
        except KeyError:
            pass
    doc.core_properties.author = ""
    doc.core_properties.comments = ""
    doc.save(str(path))


def csv_to_pipe(name):
    rows = list(csv.reader(open(TABLES / f"{name}.csv", encoding="utf-8")))
    n = max(len(r) for r in rows)
    rows = [[c.replace("|", "\\|").replace("*", "\\*") for c in r] + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * n) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def preprocess(md_text):
    lines = md_text.splitlines()
    title = None
    out, nt, nf = [], 0, 0
    for line in lines:
        s = line.strip()
        if title is None and s.startswith("# "):
            title = s[2:].strip(); continue
        mt = re.match(r"\[\[TABLE:([^|]+)\|(.+?)\]\]", s)
        mf = re.match(r"\[\[FIGURE:([^|]+)\|(.+?)\]\]", s)
        if mt:
            nt += 1
            out += ["", f"Table: **Table {nt}.** {mt.group(2).strip()}", ""]
            out += csv_to_pipe(mt.group(1).strip()) + [""]
            continue
        if mf:
            nf += 1
            png = FIGURES / f"{mf.group(1).strip()}.png"
            out += ["", f"![**Figure {nf}.** {mf.group(2).strip()}]({png}){{width=6.3in}}", ""]
            continue
        if s == "---":
            continue
        # a markdown pipe-table header must be preceded by a blank line for pandoc
        if s.startswith("|") and out and out[-1].strip() and not out[-1].strip().startswith("|"):
            out.append("")
        out.append(line)
    text = "\n".join(out) + "\n"
    # texmath does not accept the plain-TeX \rm switch; use \mathrm{...}
    text = re.sub(r"\{\\rm\s+([^{}]*)\}", lambda m: "{\\mathrm{" + m.group(1).strip() + "}}", text)
    return title, text


def style_tables(doc):
    for t in doc.tables:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "bottom", "insideH"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4"); el.set(qn("w:color"), "000000")
            borders.append(el)
        old = tblPr.find(qn("w:tblBorders"))
        if old is not None:
            tblPr.remove(old)
        tblPr.append(borders)
        for i, row in enumerate(t.rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_after = Pt(0)
                    for r in p.runs:
                        r.font.size = Pt(9); r.font.name = FONT
                        if i == 0:
                            r.bold = True


def build(md_path, out_path, author="", title_override=None):
    title, body = preprocess(Path(md_path).read_text(encoding="utf-8"))
    title = title_override or title or ""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ref = td / "reference.docx"; make_reference_docx(ref)
        src = td / "in.md"; src.write_text(body, encoding="utf-8")
        cmd = ["pandoc", str(src), "-f", "markdown+tex_math_dollars+pipe_tables+implicit_figures",
               "-t", "docx", "--reference-doc", str(ref), "-o", str(out_path),
               "--resource-path", str(ROOT)]
        if title:
            cmd += ["-M", f"title={title}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(r.stderr)
        if r.stderr.strip():
            print(r.stderr.strip(), file=sys.stderr)
    doc = Document(str(out_path))
    style_tables(doc)
    cp = doc.core_properties
    cp.author = author; cp.last_modified_by = author; cp.title = title
    cp.comments = ""; cp.subject = ""; cp.keywords = ""; cp.category = ""; cp.revision = 1
    doc.save(str(out_path))
    print(f"Wrote {out_path}")




# ---------------------------------------------------------------------------
# PDF output: pandoc -> standalone HTML (KaTeX-rendered math) -> Chromium print.
# LibreOffice's headless converter does not render Word (OMML) equations, so the
# PDF is produced from the same Markdown source through a browser instead.
CSS = """
@page { size: A4; margin: 2.3cm 2.2cm 2.3cm 2.2cm; }
body { font-family: 'Times New Roman', 'Liberation Serif', serif; font-size: 11.5pt; line-height: 1.5;
       color: #000; max-width: none; margin: 0; }
header#title-block-header h1.title { font-size: 16pt; text-align: center; line-height: 1.3; margin: 0 0 14pt; }
h2 { font-size: 13.5pt; margin: 16pt 0 6pt; } h3 { font-size: 12pt; margin: 12pt 0 4pt; }
p { margin: 0 0 7pt; text-align: justify; }
blockquote { margin: 8pt 0 8pt 1.2em; padding: 0 0 0 0.8em; border-left: 2px solid #999; }
table { border-collapse: collapse; margin: 6pt auto 12pt; font-size: 8.6pt; line-height: 1.25;
        border-top: 1.2px solid #000; border-bottom: 1.2px solid #000; page-break-inside: avoid; }
thead tr { border-bottom: 0.8px solid #000; } th, td { padding: 2.5pt 5pt; text-align: left; vertical-align: top; }
caption { caption-side: top; text-align: left; font-size: 10pt; margin-bottom: 4pt; }
figure { margin: 10pt 0; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; } figcaption { font-size: 10pt; text-align: left; margin-top: 4pt; }
ol li, ul li { margin-bottom: 3pt; } code { font-size: 9.5pt; }
.katex { font-size: 1.05em; } .katex-display { margin: 8pt 0; overflow: hidden; }
"""

PRINT_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [,, html, pdf] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + html, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  await page.pdf({ path: pdf, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8pt;width:100%;text-align:center;font-family:serif"><span class="pageNumber"></span></div>' });
  await browser.close();
})();
"""


def build_pdf(md_path, pdf_path, author="", title_override=None, katex_dir=None):
    import os
    katex_dir = Path(katex_dir or os.environ.get("KATEX_DIR", ""))
    if not (katex_dir / "katex.min.js").exists():
        sys.exit("Set KATEX_DIR to a KaTeX dist/ folder (npm pack katex).")
    title, body = preprocess(Path(md_path).read_text(encoding="utf-8"))
    title = title_override or title or ""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "style.css").write_text(CSS)
        src = td / "in.md"; src.write_text(body, encoding="utf-8")
        html = td / "out.html"
        cmd = ["pandoc", str(src), "-f", "markdown+tex_math_dollars+pipe_tables+implicit_figures",
               "-t", "html5", "-s", "--katex=" + katex_dir.as_uri() + "/", "--css", "style.css",
               "-o", str(html), "--resource-path", str(ROOT), "-M", f"pagetitle={title}"]
        if title:
            cmd += ["-M", f"title={title}"]
        if author:
            cmd += ["-M", f"author-meta={author}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(r.stderr)
        js = td / "print.js"; js.write_text(PRINT_JS)
        subprocess.run(["node", str(js), str(html), str(Path(pdf_path).resolve())], check=True)
    # clean PDF metadata
    from pypdf import PdfReader, PdfWriter
    rd = PdfReader(pdf_path); wr = PdfWriter(clone_from=rd)
    wr.metadata = None
    wr.add_metadata({"/Title": title, "/Author": author, "/Creator": "", "/Producer": ""})
    with open(pdf_path, "wb") as f:
        wr.write(f)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    author = ""; title = None
    if "--author" in args:
        i = args.index("--author"); author = args[i + 1]; del args[i:i + 2]
    if "--title" in args:
        i = args.index("--title"); title = args[i + 1]; del args[i:i + 2]
    if args[1].lower().endswith(".pdf"):
        build_pdf(args[0], args[1], author, title)
    else:
        build(args[0], args[1], author, title)
