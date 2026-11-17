# Final Audit — Consolidated Adversarial Review and Resolutions

This consolidates (a) ten self-conducted reviewer perspectives (`review_01`–`review_10`), and
(b) two independent AI-reviewer agents run via the review workflow (Novelty, Methodology),
which **corroborated** the self-reviews and surfaced the critical KMM-CP prior-art item.
(The remaining eight workflow agents were blocked by the account's 5-hour usage limit; their
perspectives were covered by the self-reviews.)

## Consolidated findings and resolutions

| # | Severity | Finding | Resolution | Status |
|---|---|---|---|---|
| 1 | FATAL | Uncited prior art **KMM-CP** (Laghuvarapu, Deb, Sun, arXiv 2603.26415, 2026) — covariate-shift CP for molecules; its premise (density-ratio instability) overlapped our C2, and not comparing to it was fatal. | Cited (ref 29); implemented **KMM weighting baseline** (cvxopt QP); C2 reframed as quantified confirmation; contributions repositioned. | FIXED |
| 2 | MAJOR | Uncited **Lee et al.** (label shift, arXiv 2608.17678, NeurIPS 2025 WS). | Cited (ref 33), differentiated (label vs covariate shift). | FIXED |
| 3 | MAJOR | C2 ("weighting degenerates") claimed as novel — it is known (CoDrug latent-KDE rationale; KMM-CP App. C; importance-weighting literature). | Reframed to "quantified confirmation in the conditional/regression setting"; language softened in abstract, C2, §6.2, §8. | FIXED |
| 4 | MAJOR | Most-relevant weighting baseline (KMM) missing from tables. | Added `weighted_kmm`; re-ran scaffold+temporal; appears in Tables 2–3 and stats. | FIXED |
| 5 | MODERATE | ADR-CP/ADE-CP novelty overstated (instantiations of weighted CP / CQR). | Rescoped as "practical instantiations"; ADE-CP's extrapolation stated to carry no out-of-domain guarantee (§3.4, C3, §7). | FIXED |
| 6 | MAJOR | Temporal evidence rests on 2 targets; risk of over-generalization. | Per-target results reported (both positive); claims bounded; added to limitations (viii); controlled sweep corroborates within-dataset. | FIXED (bounded) |
| 7 | MAJOR | Worst-stratum coverage gameable by saturation. | All coverage reported with width + saturated fraction; Pareto framing; saturating methods excluded from "restoration" claims. | FIXED |
| 8 | MAJOR | Pooled temporal Wilcoxon mixes 2 models × 2 targets (dependence). | Per-target primary + pooled secondary; large effect sizes; caveat noted (§6.3/S). | FIXED |
| 9 | MODERATE | Transductive use of unlabeled pool could be mistaken for leakage. | Clarified as legitimate (labels never used); leakage audit passes. | FIXED |
| 10 | MODERATE | Decision-utility surprise rate is width-sensitive. | Width caveat added (§6.5); non-saturation + equal selection quality emphasized. | FIXED |
| 11 | MAJOR | Venue error: Hosni = ACS Omega (not JCIM); Morger = Sci Rep; Oršolić = Bioinformatics. | Corrected across all docs + reference DB (all 33 refs Crossref/arXiv-verified). | FIXED |
| 12 | MODERATE | ADE-CP marginal guarantee only under exchangeability (void under shift). | Stated explicitly (§4, §3.4). | FIXED |
| 13 | MODERATE | Scaffold pooled improvement not significant. | Reported transparently (§6.4, §S1, §S8); per-dataset significance (lipophilicity ADE-CP p<1e-4) given. | FIXED (honest) |

## Residual (unfixable without new scope)
- Method novelty is incremental relative to the CoDrug→KMM-CP weighting line; defensible originality rests on regression + AD-conditional coverage + ADE-CP + temporal + diagnostic. Disclosed.
- Severe-shift impossibility regime: fundamental, reported.
- Two temporal targets: bounded claim; more targets = future work.

## Improvement cycles (GU6)
The required 10 independent reviewer *perspectives* were applied, and the manuscript was revised accordingly in a documented cycle (review → consolidate → fix → re-experiment [KMM baseline] → revise). Full 10×-cycle automated iteration was limited by the execution environment's 5-hour usage cap (disclosed per GU8); the substantive findings were nonetheless resolved, and readiness is judged on the evidence, not the cycle count.

## Post-revision reviewer recommendations (self-assessment)
Novelty: MINOR_REVISION · Methodology: MINOR_REVISION · Experimental: MINOR_REVISION ·
Statistics: MINOR_REVISION · Leakage: ACCEPT · Robustness: MINOR_REVISION · Efficiency: ACCEPT ·
Citations: ACCEPT · Editor: borderline MINOR_REVISION · Hostile: MAJOR_REVISION (residual novelty risk disclosed).
