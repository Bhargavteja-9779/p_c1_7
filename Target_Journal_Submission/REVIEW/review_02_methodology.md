# Review 2 — Methodology Reviewer

**Perspective:** Mathematical correctness of the conformal methods and their stated guarantees.

## Findings

**[MAJOR → addressed] M1. ADE-CP coverage guarantee must not be overstated.**
ADE-CP conformalizes a quantile model (CQR-style), so its marginal coverage guarantee holds *under exchangeability*. Under covariate shift (the paper's setting) that guarantee is void, exactly as for split CP. The manuscript must present ADE-CP's shift behavior as an empirically validated *heuristic adaptation*, not a theorem. *Resolution:* §4 states the guarantee is "under exchangeability"; §3.4/§6 describe shift performance as empirical. Verified the text does not claim distribution-free conditional validity under shift.

**[MAJOR → addressed] M2. Weighted-CP validity requires the true density ratio.** The manuscript correctly notes (and a unit test confirms) that weighted CP restores coverage only with an accurate ratio; estimated ratios lose the finite-sample guarantee (cf. KMM-CP Remark 1). Ensure this caveat is explicit for ADR-CP as well. *Resolution:* stated in §3.5/§7.

**[MODERATE] M3. Interval clipping to the training label range** changes the formal object (a clipped conformal interval is conservative). This is standard but should be stated as a deliberate, reported choice with the saturated-fraction metric — which it is (§3.3). Acceptable.

**[MODERATE] M4. ADE-CP uses a linear quantile regression on [AD, sigma].** Linearity drives the extrapolation; if the error–novelty relationship is strongly nonlinear, extrapolation could mis-estimate (seen on ESOL where ADE-CP underperforms). *Resolution:* reported honestly as the severe-shift failure (§6.8); monotone/spline alternatives noted as future work.

**[MINOR] M5.** The normalized-CP local sigma (kNN mean absolute residual) is a reasonable model-agnostic scale; state k=10 and that it is fit on training residuals only (done, §S7).

## Verification against code
- `weighted_quantile_threshold` matches the Tibshirani normalized-mass construction (checked; unit tests pass, including infinite-threshold behavior).
- ADE-CP conformity correction uses the (n+1) quantile of E_i (checked in `methods.py::method_adecp`).
- No label leakage into weights (confirmed in `pipeline.py` and leakage audit).

## Recommendation: MINOR_REVISION. Methods are correct; only guarantee-scoping language needed tightening (done).
