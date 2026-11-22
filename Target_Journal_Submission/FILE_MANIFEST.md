# File Manifest

```
Target_Journal_Submission/
├── JCIM_Submission_Package.zip     # final upload bundle (built by build_package.py)
├── SUBMISSION_PACKAGE/             # unzipped contents of the bundle
├── SUBMISSION_GUIDE.md             # what to upload where; fields still to fill in
├── build_package.py                # rebuilds SUBMISSION_PACKAGE/ and the ZIP
├── manuscript/
│   ├── draft_v6_*.md               # manuscript sections (source)
│   ├── assemble_v6.py              # fills numbers from results, orders references -> manuscript_final.md
│   ├── manuscript_final.md         # assembled manuscript
│   ├── build_pandoc.py             # Markdown -> DOCX (Word equations) and PDF (KaTeX + Chromium)
│   ├── cover_letter.md
│   └── references_acs.md, references_order.json, make_references.py
├── supplementary/
│   ├── build_si_v6.py              # generates supplementary_information.md from results
│   ├── supplementary_information.md
│   ├── adcc_preregistration.md     # function-class selection record
│   └── literature/                 # verified reference metadata and literature search
├── figures/                        # Figure 1 (panel), Figure 2 (AD calibration curve), TOC graphic
├── tables/                         # CSV tables used in the manuscript and SI
├── code/                           # full implementation, experiments, tests, results (MIT)
├── results/                        # earlier benchmark outputs
├── EXPERIMENT_LOG.md, CHANGELOG.md, REPRODUCIBILITY_STATUS.md
```
