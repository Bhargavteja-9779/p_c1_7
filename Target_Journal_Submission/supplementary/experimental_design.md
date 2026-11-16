# Pre-registered Experimental Design (Phases 5–8)

Fixed **before** looking at any results. Seeds pre-declared: {0,1,…,19}. Nominal miscoverage α ∈ {0.1, 0.2} (primary 0.1 → 90% intervals).

## Research questions → experiments → hypotheses
- **RQ1 / Exp. Main+1 → H1.** Under scaffold & temporal shift, does covariate-shift weighting restore *marginal* coverage, and does it restore *conditional* (AD-stratified) coverage? Compare marginal vs worst-stratum coverage across methods.
- **RQ2 / Exp. Ablation → H1.** Which component matters — the weighting, the AD-stratification, or both? Ablate: Split → +Normalized → +Weighted(marginal) → +Mondrian(unweighted) → +Mondrian-Weighted (full, ADW-CP).
- **RQ3 / Exp. Weight-estimator → H2.** Does a model-agnostic fingerprint-discriminator density-ratio (from the *unlabeled pool*) restore coverage as well as model-internal density estimates (CoDrug-style logistic/KDE)? Compare weight estimators.
- **RQ4 / Exp. Robustness/shift-sweep → H4.** How do methods behave as shift magnitude and calibration size vary? Controlled similarity-split sweep; calibration-size sweep.
- **RQ5 / Exp. Generalization → H1.** Does the finding hold across datasets, models (Ridge/RF/LightGBM/MLP), and both shift types (scaffold and temporal)?
- **RQ6 / Exp. Decision utility → H3.** Does better conditional coverage yield safer risk-controlled selection (lower surprise rate among selected compounds at equal selection size)?
- **RQ7 / Exp. Efficiency → H4.** What is the cost: interval width, effective sample size, wall-clock/memory?

## Datasets
Scaffold-shift (MoleculeNet, public):
1. **ESOL/Delaney** — aqueous solubility logS (n≈1128).
2. **FreeSolv/SAMPL** — hydration free energy (n≈642).
3. **Lipophilicity** — logD7.4 (n≈4200).
4. **BACE** — pIC50 regression (n≈1513).

Temporal-shift (ChEMBL, public API; also scaffold-splittable):
5. **CHEMBL279 (VEGFR2/KDR)** — pChEMBL (IC50).
6. **One additional high-count target** (selected by record count & year spread; candidates CHEMBL230/CHEMBL203/CHEMBL244) — pChEMBL.

Preprocessing (identical pipeline): RDKit parse → remove salts/standardize (largest fragment, neutralize) → canonical SMILES → InChIKey. Deduplicate by InChIKey; for ChEMBL aggregate replicate measurements by median pChEMBL and keep earliest document_year. Drop records failing RDKit or lacking endpoint.

Features: ECFP4 (Morgan radius 2, 2048-bit binary). Similarity = Tanimoto. (RDKit 2D descriptors computed for a secondary robustness check only.)

## Splits (covariate shift)
- **Scaffold-disjoint:** Bemis–Murcko generic scaffolds; assign whole scaffolds to train/calib/test so no scaffold crosses sets. 20 independent randomized scaffold partitions (seeds 0–19). Proportions train:calib:test = 60:20:20 of molecules (scaffold-grouped).
- **Temporal:** sort by document_year; train+calib = earliest ≈70% (calib = latest 20% of the early block, still before cutoff), test = latest ≈30% (strictly later years). One chronological split per target; bootstrap over test for CIs.
- **Controlled similarity sweep:** rank molecules by similarity to a seed cluster; move the test set progressively farther (quantile knob) to vary shift magnitude; measure the discriminator AUC(train vs test) as the empirical shift strength.
- **Unlabeled deployment pool** = test-set descriptors **without labels** (legitimately available when choosing what to screen). Weights estimated from (train X) vs (pool X) only.

## Methods (all wrap the same trained regressor; α fixed)
B0 **Raw ensemble interval** (RF std × z) — non-conformal reference.
B1 **Split-CP** (|y−ŷ|).
B2 **Normalized split-CP** (|y−ŷ|/σ̂(x), σ̂ = RF tree std or kNN local error).
B3 **Mondrian-AD CP** (stratify calib by AD-similarity bins; per-bin quantile) — unweighted conditional.
B4 **Localized CP** (Tanimoto-kernel-weighted calibration per test point; dAD/Guan-style).
B5 **Weighted-CP (marginal, ours-base)** — Tibshirani weighting; weights = clipped density-ratio from fingerprint discriminator on unlabeled pool.
B5′ **Weighted-CP (CoDrug-style comparators)** — logistic density-ratio; KDE density-ratio (on PCA-reduced FP) — reimplementation of CoDrug weighting for regression.
**M1 Mondrian-Weighted CP (ADW-CP, proposed)** — within each AD-similarity stratum, apply weighted conformal with pool-based density-ratio weights.
B6 **Calibration-update CP (Morger, reference upper bound)** — adds labeled near-test points to calibration (uses labels → not deployment-feasible; reported as a reference).

Weight estimator detail: probabilistic classifier d(x)=P(pool | x) trained on train(0) vs pool(1), balanced; w(x) = [d/(1−d)] × (n_train/n_pool), clipped to [1/C, C] with the Tibshirani probability clip (p∈[0.01,0.99]); isotonic/Platt calibration of d. Weighted quantile per Tibshirani 2019.

## Metrics (all computed from machine-readable outputs; no hand-entry)
Coverage: marginal coverage; **per-AD-stratum coverage** (quartile bins by similarity-to-train); **worst-stratum coverage** and **max |stratum coverage − (1−α)|** (primary conditional metric); coverage per predicted-value quartile (activity strata, per Guo). Efficiency: mean/median interval width; normalized width. Calibration: coverage-vs-stratum curve; conditional-coverage SSC (size-stratified coverage). Decision (H3): at matched selection size k, surprise rate = fraction of selected with y outside interval; enrichment = hit-rate among selected vs base rate. Cost: effective sample size n_eff = (Σw)²/Σw²; wall-clock; peak memory; FLOPS proxy (model size/trees).

## Statistics (Phase 17)
Unit = independent scaffold split (n=20) for scaffold datasets; bootstrap (n=2000) over test compounds for temporal. Primary test: **Wilcoxon signed-rank**, paired across splits, ADW-CP (M1) vs each baseline, on the primary conditional metric (max stratum coverage gap) and on marginal coverage gap and width. **Holm–Bonferroni** across the comparison family. Report **median paired difference + 95% bootstrap CI** and **rank-biserial effect size**. Significance claimed only when corrected p<0.05 AND CI excludes 0. Pre-registered: we expect H1 (weighting fixes marginal not conditional) — recorded now so a null/opposite result is reported honestly.

## Leakage audit (Phase 8) — checklist to execute in code
InChIKey dedup across all sets; scaffold-disjoint verified (0 shared scaffolds); temporal monotonicity verified (max train year < min test year after dedup); labels never used by discriminator or AD score; AD similarity to **train only**; calibration labels never in test; pool = test **X only**. Unit tests assert each.

## Quick vs full
`--mode quick`: datasets {ESOL, FreeSolv}, model RF, seeds {0,1,2}, α=0.1, 2 strata — pipeline smoke test (<~10 min).
`--mode full`: all datasets, models {Ridge,RF,LightGBM,MLP} (RF primary for main tables; others for model-agnosticism), seeds 0–19, α∈{0.1,0.2}.
