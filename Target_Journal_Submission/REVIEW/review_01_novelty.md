# Review 1 — Novelty & Prior-Art Reviewer

**Perspective:** Is the contribution genuinely distinct from existing covariate-shift conformal work in molecular ML?

## Findings

**[FATAL → now addressed] F1. Uncited, highly relevant prior art: KMM-CP (Laghuvarapu, Deb & Sun, arXiv:2603.26415, Mar 2026).**
This paper does conformal prediction under covariate shift for molecular property prediction, and its central motivation — "accurate density-ratio estimation becomes unstable when training and test distributions exhibit limited support overlap" — is exactly the "naive weighting degenerates" observation the manuscript framed as its own novel negative result (contribution C2). Omitting it, and not comparing to it, would be fatal.
- *Resolution:* KMM-CP is now cited; a KMM-weighting baseline (`weighted_kmm`) is implemented and added to all comparisons; contribution C2 is reframed to *confirm and extend* the CoDrug/KMM-CP observation to regression and conditional coverage, not to claim it as novel.
- *What remains genuinely novel after KMM-CP:* KMM-CP is (i) **classification only** (Tox21/AMES/hERG/BBB/HIV), (ii) evaluates **marginal + class-label-Mondrian coverage**, not applicability-domain/region-conditional coverage, (iii) uses a **fingerprint-distance split only** (no temporal), and (iv) proposes **KMM weighting, not quantile extrapolation**. Our distinct contributions — regression + AD-conditional coverage, the ADE-CP extrapolation mechanism, temporal-shift evaluation, and the label-free pre-deployment diagnostic — survive.

**[MAJOR → addressed] F2. CoDrug overlap.** CoDrug (NeurIPS 2023, same group) already does density-ratio weighted conformal for molecular classification (marginal). The manuscript must not imply weighted conformal for molecules is new. *Resolution:* CoDrug cited as the origin of the approach; our scope explicitly disjoint (regression, conditional, extrapolation, temporal).

**[MODERATE] F3. ADR-CP novelty is modest.** ADR-CP is weighted split conformal (Tibshirani 2019) with a one-dimensional applicability-domain feature. Its novelty is the *choice of the AD coordinate* for a non-degenerate weight, not a new estimator. *Recommendation:* present ADR-CP as a simple, robust instantiation, and let ADE-CP (genuinely new mechanism) and the conditional-coverage analysis carry the novelty weight. (Reflected in the revised framing.)

**[MINOR] F4.** The diagnostic (discriminator AUC) is conceptually related to KMM-CP's MMD+1/ESS proxy; cite and differentiate (ours is label-free, pre-deployment, and tied to *conditional* coverage and an impossibility regime). *Addressed.*

## Recommendation: MAJOR_REVISION → (after resolutions) MINOR_REVISION.
The core contributions are defensible once KMM-CP/CoDrug are cited, the KMM baseline is added, and claims are repositioned around regression + conditional coverage + ADE-CP + temporal + diagnostic.
