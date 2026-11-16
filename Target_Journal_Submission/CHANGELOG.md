# CHANGELOG

## 2026-11-15/16 — Build and experiments
- Journal selection (JCIM) with measured acceptance timelines for 70+ journals.
- Topic locked: AD-conditional conformal regression under covariate shift.
- Implemented full pipeline (data, features, splits, models, 11 conformal methods, metrics, stats).
- Fixes during bring-up: PCA+regularized discriminator (degenerate high-dim weights);
  interval clipping + saturated-fraction (coverage inflation by infinite intervals);
  bounded localized kernel; vectorized Tanimoto + feature caching (speed);
  balanced scaffold assignment; LightGBM primary model.
- Added proposed methods ADR-CP (weighted_ad) and ADE-CP (adecp) after dev-set screening.
- Unit tests + leakage audit passing.
