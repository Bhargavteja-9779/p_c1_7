# Review 7 — Computational-Efficiency Reviewer

**Perspective:** Is the method cheap, and is its cost honestly reported?

## Findings

**[MODERATE → addressed] C1. Width cost.** ADR-CP intervals are ~45% wider than split (3.31 vs 2.28 pChEMBL) and ADE-CP ~30% wider. This is the price of honest coverage and must be reported alongside coverage. *Resolution:* every table reports mean width; the Pareto figure makes the trade-off explicit; ADR-CP/ADE-CP are far narrower than the saturating methods (KMM-KDE 6.09).

**[MODERATE → addressed] C2. The surprise-rate decision metric is width-sensitive.** Wider intervals mechanically lower surprise rate. ADR-CP's lower surprise (0.063 vs 0.136) partly reflects its greater width. *Resolution:* report width alongside surprise; note the caveat; the key point is that ADR-CP achieves this without saturation and at equal selection quality (hit rate 0.372). (Add caveat sentence to §6.5.)

**[PASS] C3. Compute.** All methods are CPU-only; the KMM QP (RBF on PCA-32, source cap 900) and the 1-D AD fit add <1 s/run. Full study (~400 runs) ≈ 50 min on 4 cores. Honestly reported.

## Recommendation: ACCEPT with the width caveat added to the decision-utility section.
