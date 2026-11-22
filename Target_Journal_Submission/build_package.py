"""Build the JCIM submission package (SUBMISSION_PACKAGE/ and JCIM_Submission_Package.zip)
from the Markdown sources, figures, tables and code. Requires pandoc, node + playwright
(Chromium) and KATEX_DIR pointing at a KaTeX dist/ folder for the PDF renders."""
import shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "SUBMISSION_PACKAGE"
AUTHOR = "P. N. Bhargav Teja"
B = [sys.executable, str(ROOT / "manuscript" / "build_pandoc.py")]


def run(*args):
    subprocess.run(list(args), check=True)


def main():
    if PKG.exists():
        shutil.rmtree(PKG)
    d = {k: PKG / k for k in ["01_Cover_Letter", "02_Manuscript", "03_Supporting_Information",
                              "04_Figures", "05_Graphical_TOC", "06_Code_Archive", "07_Source_Data_Tables"]}
    for p in d.values():
        p.mkdir(parents=True)
    ms, si, cl = ROOT / "manuscript/manuscript_final.md", ROOT / "supplementary/supplementary_information.md", ROOT / "manuscript/cover_letter.md"
    for src, dst in [(ms, d["02_Manuscript"] / "Manuscript"), (si, d["03_Supporting_Information"] / "Supporting_Information"),
                     (cl, d["01_Cover_Letter"] / "Cover_Letter")]:
        run(*B, str(src), f"{dst}.docx", "--author", AUTHOR)
        run(*B, str(src), f"{dst}.pdf", "--author", AUTHOR)
    for i, name in enumerate(["fig_adcc_panel", "fig_adcc_curve"], 1):
        for ext in ("pdf", "png"):
            shutil.copy(ROOT / "figures" / f"{name}.{ext}", d["04_Figures"] / f"Figure_{i}.{ext}")
    for ext in ("pdf", "png"):
        shutil.copy(ROOT / "figures" / f"TOC_graphic.{ext}", d["05_Graphical_TOC"] / f"TOC_graphic.{ext}")
    tabs = {"table_jcim_positioning": "Table_1_positioning", "table_adcc_pooled": "Table_2_pooled_coverage",
            "table_adcc_stats": "Table_3_paired_stats", "table_adcc_per_target": "Table_S_per_target",
            "table_adcc_validity": "Table_S_validity", "table_ad_representation": "Table_S_AD_coordinate"}
    for k, v in tabs.items():
        shutil.copy(ROOT / "tables" / f"{k}.csv", d["07_Source_Data_Tables"] / f"{v}.csv")
    # code archive (no caches, data downloads, logs or legacy figures)
    code = ROOT / "code"
    skip_dirs = {"__pycache__", "experiment_logs", "logs_tmp", ".pytest_cache"}
    skip_top = {"data", "figures"}
    with zipfile.ZipFile(d["06_Code_Archive"] / "ADCC-CP_code.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(code.rglob("*")):
            rel = f.relative_to(code)
            if f.is_dir() or rel.parts[0] in skip_top or any(part in skip_dirs for part in rel.parts) or f.suffix == ".pyc":
                continue
            z.write(f, Path("ADCC-CP_code") / rel)
    shutil.copy(ROOT / "SUBMISSION_GUIDE.md", PKG / "SUBMISSION_GUIDE.md")
    out = ROOT / "JCIM_Submission_Package.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PKG.rglob("*")):
            if f.is_file():
                z.write(f, Path("JCIM_Submission_Package") / f.relative_to(PKG))
    print("wrote", out)


if __name__ == "__main__":
    main()
