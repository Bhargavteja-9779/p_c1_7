# PROJECT_STATE — recovery checkpoint

_Update after every significant stage (GU8). If execution halts, resume from "NEXT STEP"._

## Target journal (Phase 0 — DONE)
**Journal of Chemical Information and Modeling (JCIM)**, ACS. JIF 6.4 (2025, secondary); Q1 in *Computer Science, Interdisciplinary Applications* and *Chemistry, Medicinal* (secondary). Measured median submission→acceptance = 84 days (n=390, PubMed history). Details: `journal_selection/`.

## Topic (Phases 1–5 — DONE, locked)
Applicability-domain–conditional conformal prediction for molecular property **regression** under covariate shift. Does correcting covariate shift (via a model-agnostic, unlabeled-pool fingerprint-discriminator density-ratio) restore **conditional** (AD-stratified) coverage, or only marginal? Proposed method: **Mondrian-Weighted Conformal Prediction (ADW-CP)**. Central falsifiable hypothesis H1 + H2–H4. Full rationale: `supplementary/literature/gap_and_novelty.md`, `supplementary/experimental_design.md`.

## Key prior art (differentiated)
CoDrug 2023 (classification, marginal, GNN+KDE) · Tibshirani 2019 (WCP marginal) · Guo 2027 (regression conditional failure, no shift correction) · Hosni 2026 (AD flags only) · Harris 2026 (domain-classifier filter, classification) · Klarner 2023 (Bayesian, not CP). None cover: regression + conditional coverage + model-agnostic pool-based weighting.

## Environment
CPU-only (4 cores, 15 GB). Installed: numpy 2.5, pandas 3.0, scikit-learn, scipy, rdkit 2026.09.2, lightgbm 4.7, python-docx 1.2. No GPU → no GNN training at scale (Chemprop noted as related/limitation; DL baseline = fingerprint MLP). Data reachable: MoleculeNet CSVs (deepchem S3), ChEMBL API (document_year available).

## Progress log
- [x] Phase 0 journal selection + verification (+ measured timelines for 70+ journals) → `journal_selection/`
- [x] Phases 1–4 topic discovery, stress test, literature matrix, novelty defense → `supplementary/literature/`
- [x] Phases 5–6/8 experimental design + leakage plan (pre-registered) → `supplementary/experimental_design.md`
- [ ] Phase 7/9 data download + preprocessing + feature/scaffold/AD code
- [ ] Phase 9/10 full pipeline + run_all.py (quick/full) + tests + seeds
- [ ] Phases 11–13 baselines + main experiments + seeds
- [ ] Phases 14–19 ablation, robustness, generalization, statistics, error analysis, iteration
- [ ] Phase 20 figures/tables (auto-generated)
- [ ] Phase 21–23 manuscript + claim-evidence + citation audit
- [ ] Phases 24–33 / GU5–6 ten-reviewer cycles
- [ ] Phases 34–42 audits, DOCX, cover letter, package, risk report, decision

## Status 2026-11-16 (checkpoint)
- Full pipeline built, tested (6 unit tests pass), leakage audit passes.
- Proposed methods: **ADR-CP** (`weighted_ad`) + **ADE-CP** (`adecp`). Thesis: align conformal
  correction with the applicability-domain axis; weighting-in-high-dim fails (negative result);
  diagnostic = train-vs-pool discriminator AUC. All evidence-based, honest.
- Full experiments running in background (lgbm primary + rf/ridge/mlp ablation + temporal + sweep);
  resumable via run_meta.jsonl. ~2500 scaffold rows done; temporal + sweep pending.
- References: 31 verified via Crossref/arXiv (`supplementary/literature/verified_references.json`),
  ACS-formatted (`manuscript/references_acs.md`). Hosni corrected to ACS Omega (not JCIM).
- Manuscript stable sections drafted (`manuscript/manuscript.md`); Results/Abstract numbers pending.
- DOCX builder (`manuscript/build_docx.py`) validated; cover letter drafted.

## STATUS: COMPLETE (2026-11-17) — READY FOR SUBMISSION
All 42 phases + global updates executed. Final decision: READY FOR SUBMISSION with disclosed
novelty risk (see FINAL_DECISION.md, REJECTION_RISK_REPORT.md).
- Experiments: 4,652 result rows (6 datasets, 4 models, 12 conformal methods incl. KMM baseline).
- Adversarial review (10 perspectives + 2 AI agents) caught + fixed missing prior art (KMM-CP, Lee);
  implemented KMM baseline; repositioned contributions honestly; 11/11 consistency checks pass.
- Deliverables: Final_Manuscript.docx, cover_letter.docx, 9 figures, 6 tables, full code, 33 verified refs.
- Headline result: AD-aligned conformal (ADR-CP/ADE-CP) restores conditional coverage under temporal
  shift (0.88 vs split 0.70, Holm p<0.001) where KMM/CoDrug-style weighting does not; diagnostic predicts regime.
