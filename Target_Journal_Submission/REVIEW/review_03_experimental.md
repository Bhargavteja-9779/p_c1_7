# Review 3 — Experimental-Design Reviewer

**Perspective:** Are comparisons fair and is the primary metric robust?

## Findings

**[MAJOR → addressed] E1. Worst-stratum coverage can be trivially maximized by widening/saturating intervals.** Localized CP and KDE-weighted CP reach ~0.95–0.99 worst-stratum coverage but at 48–95% saturation. Ranking by coverage alone would be misleading. *Resolution:* every coverage number is reported with mean width and saturated fraction; the headline comparison is a coverage–efficiency Pareto (Fig. 2); saturating methods are explicitly excluded from "restoration" claims.

**[MAJOR → addressed] E2. The most relevant weighting baseline (KMM-CP) was initially missing.** *Resolution:* `weighted_kmm` implemented (Huang et al. KMM QP, RBF on PCA features) and added to all tables/stats.

**[MODERATE] E3. Baseline fairness.** All methods wrap the identical fitted model and share preprocessing, calibration split, and AD score; weights use only unlabeled pool covariates. CoDrug-style logistic/KDE ratios and KMM use comparable inputs. Fair.

**[MODERATE] E4. Calibration size varies across scaffold seeds (esp. FreeSolv).** This inflates variance on the smallest dataset. *Resolution:* reported with per-dataset sd; FreeSolv flagged as small/high-variance (§S1, §7).

**[MINOR] E5.** Two nominal levels (0.9, 0.8) tested (§S2); results consistent.

## Recommendation: MINOR_REVISION (after KMM baseline added and Pareto framing confirmed).
