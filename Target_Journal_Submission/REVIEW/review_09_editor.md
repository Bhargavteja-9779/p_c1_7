# Review 9 — JCIM Associate Editor

**Perspective:** Scope fit, significance, completeness, reviewer risk.

## Assessment

**Scope:** Strong fit. Uncertainty quantification, applicability domain, conformal prediction, and benchmarking under data shift are an active JCIM stream (Parrondo-Pizarro 2026, Harris 2026, Li 2026, Li 2024). The paper is methodological with rigorous empirics and public data.

**Significance (post-KMM-CP reposition):** The contribution is now clearly delimited: first systematic *conditional* (AD-stratified) coverage study for molecular *regression* under covariate shift; a genuinely new *quantile-extrapolation* method (ADE-CP); *temporal*-shift evaluation absent from CoDrug/KMM-CP; and a label-free *pre-deployment diagnostic* with an honest impossibility characterization. This is sufficient novelty for JCIM provided the KMM-CP/CoDrug relationship is explicit (done) and the KMM baseline is included (done).

**[MAJOR → addressed] AE1.** Without the KMM-CP citation+baseline, desk-reject risk was high. Resolved.

**[MODERATE] AE2. Framing discipline.** The paper must lead with the *conditional-coverage* question and the *diagnostic*, not with "we fix covariate shift" (which CoDrug/KMM-CP already address for marginal/classification). The revised abstract/intro/contributions do this.

**[MODERATE] AE3. Author-guideline compliance.** Data & Software Availability present; ACS format; declarations present; SI present. Add a TOC/abstract graphic (noted as a submission to-do for the authors). 

**[MINOR] AE4.** Ensure every in-text number matches the tables (cross-checked in the consistency audit).

## Recommendation: MAJOR_REVISION → (after resolutions) borderline-accept / MINOR_REVISION. Survives peer review if the repositioning and KMM baseline hold up (they do in the re-run).
