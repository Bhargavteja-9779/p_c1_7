# EXPERIMENT_LOG

Chronological log of experiments and design updates. Dev-set = scaffold splits of
ESOL, FreeSolv, Lipophilicity, BACE (used to develop/choose methods). Held-out
confirmation = temporal ChEMBL datasets + full 20-seed runs + controlled shift sweep.

## 2026-11-15 — Pipeline bring-up (dev-set, RF, α=0.1)
- Verified scaffold-disjoint splits (0 overlap), InChIKey dedup, ECFP4 features, AD score.
- **Finding 1 (degenerate weights):** raw 2048-bit fingerprint discriminators separate
  train/test almost perfectly (AUC≈1.0), making density-ratio weights explode and
  weighted-CP intervals infinite. Fix: PCA-reduce (32-d) + strong L2 (C=0.1) + clip.
  This is the "data-efficient likelihood ratio" issue CoDrug (2023) flagged.
- **Finding 2 (coverage inflation):** infinite/degenerate intervals trivially "cover".
  Fix: clip intervals to the training label range and report `saturated_fraction`
  as an efficiency penalty (a saturated interval is uninformative).
- **Finding 3 (localized kernel):** exp(sim/h) lets the test atom dominate → all-infinite.
  Fix: bounded kernel exp(-(1-sim)/h), self-weight = 1.

## 2026-11-15 — Method screening (dev-set, 3–5 seeds, α=0.1)
Observed (worst-stratum coverage vs nominal 0.90; mean width; saturated %):
- Covariate-shift **weighting** (discriminator / 1-D AD / CoDrug-style logistic,KDE) does
  **not** reliably restore *conditional* coverage for regression; KDE and calib-vs-test
  logistic saturate badly. → **extends CoDrug's marginal/classification result: weighting
  is not sufficient for conditional coverage in regression (negative result).**
- **Mondrian (AD-stratified, unweighted)** improves worst-stratum coverage at ~no width
  cost under mild/moderate shift (lipophilicity, bace) but under-covers under extreme
  shift (esol).
- **Design update:** added **ADE-CP** (applicability-domain conformal extrapolation):
  model the conformal residual quantile as a monotone function of the AD coordinate and
  extrapolate beyond the calibrated range (CQR-style correction). Added the 1-D AD
  density-ratio weight (`weighted_ad`) as a robust, non-degenerate weighting baseline.
- **Finding 4 (regime law):** achievable conditional coverage decreases monotonically
  with shift magnitude (train-vs-pool discriminator AUC): lipophilicity AUC≈0.62 →
  worst≈0.88; bace≈0.80 → ≈0.86; esol≈0.97 → ≈0.71 (best finite-width method).
  Under extreme shift, only (near-)trivial intervals reach nominal conditional coverage
  — consistent with Barber (2021) impossibility. → motivates the **discriminator-AUC
  deployment diagnostic**.

## Pending (full run)
- All datasets × models {ridge,rf,lgbm,mlp} × seeds 0–19 × α∈{0.1,0.2}, scaffold.
- Temporal ChEMBL (VEGFR2, COX-2): chronological split (held-out confirmation).
- Controlled similarity-shift sweep (diagnostic law).
- Ablations, decision-utility, statistics (Wilcoxon + Holm + bootstrap CIs), figures/tables.

## 2026-11-17/18 — Expanded validation (13 ChEMBL targets, 6 families)
HONEST, consequential findings from the expanded validation:
- Pooled worst-stratum coverage (temporal, 13 targets, lgbm, target 0.90):
  Split 0.670 | KMM 0.715 | Mondrian 0.732 | ADE-CP 0.742 | MW-CP 0.755 | ADR-CP 0.839 |
  Localized 0.852 (15% saturated) | KDE 0.965 (96% saturated).
- **ADR-CP (simple global 1-D AD reweighting) is the best DEPLOYABLE method**, significantly
  beating MW-CP (median Δ +0.073, Holm p<0.001), Mondrian, KMM, ADE-CP, with low saturation (6%).
- **MW-CP (the group-conditional-GUARANTEED method) underperforms ADR-CP** (stratification
  fragments calibration). It beats split/KMM/Mondrian-on-rank but not ADR-CP.
- **Diagnostic FAILS target-level validation**: Spearman(AUC, achievable worst-cov) rho=-0.016,
  p=0.96 across 13 targets; LOTO false-safe 0.54. The earlier split-level rho=-0.56 was inflated
  by non-independent repeated splits . The universal-AUC-
  threshold deployment rule is NOT supported across targets and is withdrawn.
Implication: the novel method does not dominate the simple baseline, and the diagnostic does not
generalize. This materially weakens the intended contributions and must drive an honest decision.
