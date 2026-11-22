# Applicability-Domain Conditional Conformal Prediction: Distribution-Free Coverage over Chemical-Space Shifts without Density-Ratio Estimation

**Authors:** P. N. Bhargav Teja¹; [Second Author — Supervisor]¹,* (corresponding)

¹[Affiliation]

Corresponding author: [Second Author — Supervisor]; [email]

---

## Abstract

Conformal prediction gives molecular-property models distribution-free prediction intervals, but only under exchangeability, an assumption broken by the covariate shift of prospective screening: coverage fails precisely for the structurally novel compounds that drive decisions. Existing corrections either stratify the calibration set, leaving the most novel region under-covered, or reweight it by an estimated density ratio that is unstable in high-dimensional chemical space. We introduce **Applicability-Domain Conditional Conformal prediction (ADCC-CP)**, which calibrates with an augmented quantile regression over piecewise-linear functions of a molecule's similarity to the training set. The resulting intervals are provably valid in finite samples, **without estimating any density ratio**, marginally, locally at every similarity level, and under every deployment shift whose density ratio along the applicability-domain axis lies in this class; a companion bound shows that coverage lost to non-aligned shift never exceeds that of standard conformal prediction. Interval width depends on a compound only through its similarity score, giving an interpretable applicability-domain calibration curve that applies to libraries of any size by lookup, and the method extends to several novelty axes. In a pre-registered held-out evaluation on **thirteen time-stamped ChEMBL targets from six protein families** under temporal shift, ADCC-CP raises coverage of the most out-of-domain compounds from 0.686 (split conformal) to 0.880 at a 0.90 target, improving on all thirteen targets over split, normalized, Mondrian and kernel-mean-matching conformal, and covers the most-novel decile better than the strongest estimated-weight method at equal width. All data are public and all results are reproduced by the accompanying code.

**Keywords:** conformal prediction; conditional coverage; applicability domain; covariate shift; molecular property prediction; QSAR; prediction intervals; distribution-free inference
