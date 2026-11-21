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

## ROUND-6 NOVELTY UPGRADE (started 2026-11-21) — goal: avoid desk rejection
User report: submissions were desk-rejected; wants more novelty + level-check vs recent JCIM papers.
Diagnosis (desk-reject drivers): (1) no new method that wins — abstract says so explicitly;
(2) 600-word hedged abstract, "we do not claim" framing; (3) code "available on request" conflicts
with JCIM 2021 data/software policy (doi 10.1021/acs.jcim.0c01389) -> must be public (GitHub+Zenodo);
(4) author/affiliation placeholders.
Plan:
 1. NEW METHOD ADCC-CP = function-class conditional conformal (Gibbs-Cherian-Candes JRSSB 2025)
    on an applicability-domain function class F_AD (stratum indicators + within-stratum linear tilt
    in a(x)). Finite-sample guarantee simultaneously for every AD stratum AND every covariate shift
    whose density ratio (as function of a) lies in F_AD — no density-ratio estimation. Lit search
    (2026-11-21): not yet applied to molecules/AD (gap open). Code: src/conformal/methods.py (adcc*).
 2. Dev selection of variant on MoleculeNet scaffold ONLY (experiments/dev_adcc.py ->
    results/dev_adcc_rows.jsonl); ChEMBL panel held out. Lock variant in supplementary/adcc_preregistration.md.
 3. Panel run (13 targets x 3 windows x lgbm,rf x 3 seeds) with split,mondrian,weighted_ad,mwcp,adcc
    -> experiments/run_panel_adcc.py -> results/panel_adcc_rows.jsonl. Target-clustered stats.
 4. Rewrite manuscript around ADCC-CP (short abstract <=250 words, positive framing), rebuild DOCX/PDF/ZIP.
NEXT STEP: (update as you go)
 - [x] step 2 dev selection (spline locked; supplementary/adcc_preregistration.md)
 - [x] ADCC dev selection done; drafts: manuscript/draft_v6_intro.md, draft_v6_methods.md (related-work section still to write)
 - [x] panel done (234 runs); validity+misspec done; manuscript v6 assembled; DOCX/PDF/ZIP rebuilt
 - [x] ROUND 6 COMPLETE: ADCC-CP novel method; 10 unit tests + leakage audit pass; manuscript+SI+cover+ZIP rebuilt; decision/risk/history updated. Author fields + repo URLs are the only author to-dos.

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

## STATUS: ROUND-5 — professor review #4 addressed with 3 new real experiments (2026-11-19)
- **Experiment A (AD-representation robustness, MUST):** `experiments/ad_representation.py`; added
  `ad_variant` to `run_single`. ADR-CP under 4 pre-defined AD coordinates (13 targets, w30, 3 seeds):
  max-ECFP 0.843 (+0.194, 13/13), mean-top5-ECFP 0.811 (+0.162, 13/13), max-FCFP 0.841 (+0.196,
  13/13), physchem-distance 0.689 (+0.045, 11/13). Robust across structural coordinates; physchem
  weaker. Table S-adrep; §6.2.
- **Experiment C (target-clustered stats, MUST):** `experiments/clustered_stats.py`. Target-level
  (n=13, not 117 runs) cluster bootstrap: ADR-CP vs split +0.169 CI[+0.138,+0.200]; CI excludes 0 vs
  all deployable baselines. Table S-clust; §6.2.
- **Experiment B/E (screening + chemical space):** `experiments/screening_chem.py`. Budgets 5/10/20/30%
  + width-among-selected (surprise ~0.15 ADR vs ~0.29 split; width 2.2→3.2); uncertainty-aware
  decision rule (calib-set thresholds; high-tier err 0.90 vs 0.51, split cov 0.68 vs 0.89); coverage
  across 6 descriptors (MW/logP/TPSA/HBD/HBA/RotB) all restored. Tables S-screen-decision, S-rule,
  S-desc(extended); §6.5.
- **Text:** retitled "...under Scaffold and Temporal Chemical-Space Shift"; abstract notes residual
  gap (0.84 vs 0.90) + 55% width cost + AD-robustness; §6.5 reframed retrospective simulation;
  "When to use what" guidance in §8; ESS reported; code stays "on request" (no conflict).
- Rebuilt DOCX+PDF; package 36 files. All numbers verified; committed + pushed.

## STATUS: ROUND-4 — professor review #3 addressed (2026-11-18)
Addressed the detailed JCIM-style review #3 with real analysis (no fabrication):
- **W1 (Critical) — ADR-CP 1-D justification.** New `experiments/residual_analysis.py` + three SI
  tables: within-AD-stratum calib-vs-test discriminator AUC stays ~0.78–0.84 (vs 0.86 global) →
  a(x) is NOT a sufficient statistic; ADR-CP stated as an empirically effective approximation. But
  coverage is restored UNIFORMLY across all MW/logP quartiles (0.66–0.71→0.81–0.84, Table S-desc)
  and all six families (Table S-fam), and the 1-D ratio is stable where KMM/KDE degenerate. Explicit
  assumption added in §4.
- **W2 — MW-CP.** Abstract + §6.3 now separate (i) Theorem (exact weights), (ii) implemented
  estimated-weight method (no unconditional guarantee), (iii) measured empirical coverage; removed
  "certified deployment" language.
- **W3 — screening.** §6.5 reframed as risk-aware screening (not better hits); states 14.8% still
  > 10% nominal and the 55% width cost (3.30 vs 2.13).
- **W4 — novelty.** C2 marked the central contribution; theorem supports, not carries, it.
- **W5 — temporal.** Family-coverage result in §6.6; §7 expanded on document-year proxy, assay-source
  control, and 3-window cutoff sensitivity.
- **Blockers.** Fixed code-availability conflict (abstract/SI/cover letter now "available on request",
  consistent); ref 29 → UAI 2026 (verified via web; no fabricated pages); created `figures/TOC_graphic`
  (data-driven ACS graphical TOC); added ASSOCIATED CONTENT/SI section. Author placeholder kept per
  user. Rebuilt all DOCX+PDF; package now 32 files incl. TOC + 3 new SI tables.

## STATUS: ROUND-3 — professor review #2 addressed + submission ZIP built (2026-11-18)
Responded to external JCIM review #2 and user's finalization instructions:
- **Retitled** to "Applicability-Domain–Aligned Conformal Prediction for Reliable Molecular Property
  Prediction under Chemical-Space Shift" (R2 preferred title).
- **Theorem clarity (R2):** added Remark 1 — implemented estimated-weight MW-CP is an empirically
  evaluated approximation; Theorem 1 is the exact-weight idealized target. Abstract softened to match.
- **Dataset consistency (R3):** all descriptions unified to the 13-target panel; table/figure
  cross-references renumbered and made internally consistent (Tables 1–5, Figures 1–2); build_docx now
  auto-numbers tables/figures and renders markdown pipe-tables (SI) as real tables.
- **Screening case study (R4), §6.5 + Table 5 + SI S-screen:** prospective selection across budgets
  (top 5/10/20 %), pooled over 13 targets × 3 windows × 2 base models × 3 seeds, from real
  `panel_decision.jsonl`. Hit/enrichment identical across CP methods (shared ranking); ADR-CP roughly
  halves split CP's surprise rate at every budget (0.152/0.148/0.139 vs 0.254/0.262/0.266).
- **Honesty fix:** removed overclaim that the panel ran α∈{0.90,0.80,0.95}; panel is 90 % only
  (α=0.10), 80 % is on scaffold/earlier-temporal data (SI S2). 95 % and the AD-definition sensitivity
  (max-Tanimoto vs mean-top-k) were NOT run — now stated as limitations/future work, not claimed.
- **Author/availability/declarations (user):** P. N. Bhargav Teja first author; corresponding/second
  author left as placeholder; Data Availability = real public links + 13 ChEMBL IDs; Code = available
  on request; CRediT (Teja = most roles, co-author = supervision); funding = none; competing = none.
- **Deliverable:** `SUBMISSION_PACKAGE/` + `JCIM_Submission_Package.zip` (cover letter, manuscript, SI,
  figures, source-data tables; DOCX + PDF). All headline numbers re-verified against results/.

## STATUS: ROUND-2 REDEVELOPMENT COMPLETE (2026-11-18) — finalized as rigorous benchmark
Responded to external do-not-submit verdict. Key honest outcomes:
- ADR-CP (1-D AD reweighting) is the best deployable method: beats split/Mondrian/KMM/MW-CP, 13/13 targets (Holm p<0.001).
- MW-CP: new method WITH a finite-sample group-conditional guarantee (Theorem 1), but does NOT beat ADR-CP (efficiency cost) — reported honestly.
- Diagnostic REFUTED at target level (rho~0/+0.65); withdrawn as a universal rule.
- 13 ChEMBL targets/6 families/3 windows/4 models+GNN; FCFP ablation; all audits pass; 6/6 number consistency.
- Decision (authors' choice): READY to submit as a benchmark+guarantee+cautionary-diagnostic paper; novelty risk disclosed (FINAL_DECISION.md, REJECTION_RISK_REPORT.md).
