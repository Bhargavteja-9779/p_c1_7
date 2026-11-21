# Applicability-Domain Conditional Conformal Prediction: Distribution-Free Coverage over Chemical-Space Shifts without Density-Ratio Estimation

**Authors:** P. N. Bhargav Teja¹; [Second Author — Supervisor]¹,* (corresponding)

¹[Affiliation]

Corresponding author: [Second Author — Supervisor]; [email]

---

## Abstract

Conformal prediction gives molecular-property models distribution-free prediction intervals, but only under exchangeability — an assumption broken by the covariate shift of prospective screening, where coverage fails precisely for the structurally novel compounds that drive decisions. Existing corrections either stratify the calibration set, leaving the most novel region under-covered, or reweight it by an estimated covariate density ratio that is unstable in high-dimensional chemical space and valid only if the estimate is correct. We introduce **Applicability-Domain Conditional Conformal prediction (ADCC-CP)**, which calibrates with an augmented quantile regression over the class of piecewise-linear functions of a molecule's similarity to the training set. A single interval is then provably valid, in finite samples and **without estimating any density ratio**, (i) marginally, (ii) locally at every similarity level, and (iii) under *every* deployment shift whose density ratio along the applicability-domain axis lies in the class (Theorem 1); a companion bound (Proposition 2) shows the coverage lost to non-aligned shift is never greater than for standard conformal prediction. Because interval width depends on a compound only through its similarity score, ADCC-CP yields an interpretable applicability-domain calibration curve applicable to libraries of any size by lookup. On a pre-registered held-out evaluation across **thirteen time-stamped ChEMBL targets from six protein families** under temporal shift (three chronological windows, two model families), ADCC-CP raises worst-applicability-domain-stratum coverage from {{WSC_split}} (split conformal) to {{WSC_adcc}} at a 0.90 target, improving on every target over split conformal and matching or exceeding the best estimated-weight method while carrying a guarantee it lacks; exchangeable and known-shift controls confirm the theory. All data are public and all results are reproduced by released code.

**Keywords:** conformal prediction; conditional coverage; applicability domain; covariate shift; molecular property prediction; QSAR; prediction intervals; distribution-free inference
