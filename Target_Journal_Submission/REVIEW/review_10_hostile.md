# Review 10 — Hostile Competing Researcher (final adversarial)

**Perspective:** Find the single most damaging valid criticism; show the work is incremental or wrongly evaluated.

## Attacks and outcomes

**A1. "KMM-CP already solved conformal under covariate shift for molecules."**
Rebuttal (holds): KMM-CP is classification, marginal/class-Mondrian coverage, fingerprint split, KMM weighting. This paper is regression, AD-conditional coverage, temporal shift, and a different mechanism (quantile extrapolation). Empirically, KMM weighting does **not** restore conditional coverage on temporal shift (worst-stratum 0.70, ≈ split), whereas ADR-CP reaches 0.88 — so KMM-CP does not subsume this work; it is a baseline this work beats on its target endpoint.

**A2. "Your win is a width/saturation artifact."**
Partially valid and must be disclosed: ADR-CP is ~45% wider than split, and the surprise-rate metric is width-sensitive (Review 7 C2). Rebuttal: ADR-CP is non-saturating (0% vs KDE 95%), beats Mondrian (a non-wider AD baseline) significantly on temporal worst-stratum coverage (0.88 vs 0.80, Holm p<0.001), and the Pareto view shows it dominates the coverage/width frontier among deployable methods. The width caveat is now stated.

**A3. "Mondrian (old) nearly matches you on mild scaffold shift."**
Valid and disclosed: on lipophilicity Mondrian (+0.050) ≈ ADE-CP (+0.052). The paper does not claim ADE-CP dominates Mondrian on scaffold; the differentiator is temporal shift (ADR-CP ≫ Mondrian) and the unified AD-axis framing + diagnostic. Honest.

**A4. "The negative result (weighting degenerates) is not yours."**
Valid: credited to CoDrug/KMM-CP; reframed as confirmation/extension to regression+conditional (Review 1).

**A5. "Only 2 temporal targets; small scaffold sets."**
Valid limitation; bounded claims + controlled sweep + per-target reporting mitigate; more targets = future work.

## Most damaging valid criticism (surviving):
The paper's novelty is **incremental relative to the CoDrug→KMM-CP line** on the *weighting* axis; its defensible originality rests on (i) the conditional-coverage-for-regression lens, (ii) ADE-CP, (iii) temporal evaluation, and (iv) the diagnostic. If a reviewer weights "new algorithm" heavily over "rigorous characterization + simple deployable tools + honest limits," they may still rate it MAJOR_REVISION. Mitigation: lead with the characterization/diagnostic value and the temporal result, which are genuinely new and practically important.

## Recommendation: MAJOR_REVISION (honest); defensible for acceptance after the repositioning, with residual novelty risk disclosed in the rejection-risk report.
