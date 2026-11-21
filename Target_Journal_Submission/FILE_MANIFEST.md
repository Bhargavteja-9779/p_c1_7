# Final File Manifest (Round 6 — ADCC-CP)

Submission package for *Journal of Chemical Information and Modeling*. ADCC-CP (applicability-domain
conditional conformal). All results/tables/figures machine-generated from public data by released MIT code.

```
Target_Journal_Submission/
├── journal_selection/
│   ├── selected_journal.md         # target journal + verified metadata
│   ├── journal_comparison.md       # 70+ journals, measured acceptance timelines
│   ├── journal_verification.md     # legitimacy, scope, ≥20 comparable papers
│   └── evidence/                   # per-journal timeline JSONs + scripts + summary
├── manuscript/
│   ├── manuscript.md               # editable source (with table/figure markers)
│   ├── manuscript_final.md         # assembled source incl. formatted references
│   ├── Final_Manuscript.docx       # ACS-styled submission DOCX (tables+figures embedded)
│   ├── cover_letter.md             # cover letter
│   ├── references_acs.md           # ACS-formatted reference list
│   ├── make_references.py          # reference formatter (from verified DB)
│   └── build_docx.py               # Markdown -> DOCX converter
├── code/
│   ├── README.md                   # one-command reproduction instructions
│   ├── run_all.py                  # quick/full orchestrator
│   ├── requirements.txt, environment.yml
│   ├── config/default.yaml
│   ├── src/                        # data, preprocessing, models, conformal, evaluation, statistics, visualization
│   ├── experiments/                # run_experiments.py, leakage_audit.py
│   ├── tests/test_conformal.py     # unit tests (6, passing)
│   ├── results/                    # raw_results.csv, metrics.json, statistics.json, logs (also mirrored at top level)
│   ├── figures/ , tables/          # generated outputs (also mirrored at top level)
├── results/                        # raw_results.csv, metrics.json, statistics.json, leakage_audit.json, dataset_summaries.json, experiment_logs/
├── figures/                        # 9 figures (.png 600 dpi + .pdf vector)
├── tables/                         # 6 tables (.csv + .md)
├── supplementary/
│   ├── supplementary_information.md
│   ├── experimental_design.md      # pre-registered design
│   └── literature/                 # literature_matrix.md, gap_and_novelty.md, verified_references.json, PubMed search
├── REVIEW/
│   ├── review_workflow.js          # 10-reviewer adversarial workflow
│   ├── review_01.md … review_10.md # ten independent reviews
│   └── final_audit.md              # consolidated audit + adversarial round
├── PROJECT_STATE.md  EXPERIMENT_LOG.md  REVIEW_HISTORY.md  CHANGELOG.md
├── REPRODUCIBILITY_STATUS.md  REJECTION_RISK_REPORT.md  FINAL_DECISION.md
└── FILE_MANIFEST.md (this file)
```

Data files (`code/data/raw/`, `code/data/processed/`) are not committed — they are
downloaded automatically by `code/src/data/download.py` on first run.
