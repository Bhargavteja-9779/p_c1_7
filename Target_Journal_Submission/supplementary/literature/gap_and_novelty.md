# Gap Analysis & Novelty Defense (Phases 2–5)

## Topic (locked)
**Applicability-domain–conditional conformal prediction for molecular property *regression* under covariate shift: does correcting the shift restore *conditional* coverage, and can it be done model-agnostically from the unlabeled deployment pool?**

Working title (manuscript): *When Does Correcting Covariate Shift Fix Conformal Coverage for Molecules? Applicability-Domain–Conditional Prediction Intervals for Molecular Property Regression.*

## Research problem (why it matters)
Conformal prediction (CP) gives distribution-free prediction intervals with a finite-sample **marginal** coverage guarantee under exchangeability. In molecular property prediction it is the leading way to attach an applicability domain / reliability statement to any model. But real deployment is a **covariate shift**: the compounds we must score (new scaffolds, prospective/temporal series) are not exchangeable with the historical training/calibration compounds. Under shift, CP's guarantee is void, and recent work shows coverage collapses exactly where decisions are made — on novel, low-similarity, high-activity compounds (Morger 2022; Hosni 2026; Guo 2027). The decision-relevant quantity is therefore **conditional** coverage: the coverage *given* that a compound lies in a particular region of chemical space (e.g., far from training). A 90 % interval that covers 90 % on average but 78 % on the novel compounds you actually act on is dangerous.

## What exists (precise)
1. CP for QSAR UQ/AD: standard, marginal only.
2. Documented failure under scaffold/temporal shift: Morger 2022, Hosni 2026, Guo 2027.
3. Covariate-shift **correction** via weighting: CoDrug (NeurIPS 2023) — **classification only**, **marginal/per-label coverage only**, GNN+energy-regularization+external-OOD+latent-KDE pipeline. Tibshirani 2019 — general theory, marginal only.
4. Regression finding (Guo 2027): marginal repair ≠ conditional repair; similarity-binned/normalized CP insufficient; **no covariate-shift weighting attempted**.
5. Domain classifiers as OOD signals: Harris 2026 — used as selective-classification filter, not coverage-correcting weights.

## The gap (three linked holes)
- **G1 (regression).** Covariate-shift–corrected conformal has only been demonstrated for molecular **classification**. Regression — the native setting for potency (pIC50/pKi), solubility, lipophilicity, ADME — is explicitly listed as future work by CoDrug.
- **G2 (conditional coverage).** Existing shift corrections target and report **marginal** coverage. Whether weighting restores **conditional (AD-stratified)** coverage is **uncharacterized**, and the one regression study that measured conditional coverage (Guo 2027) used **no** shift correction and found practical CP variants fail conditionally.
- **G3 (deployability / model-agnosticism).** The only molecular shift-correction (CoDrug) requires training a specific GNN with energy regularization against an external OOD library and KDE in a latent space. A **model-agnostic** correction that wraps any regressor and estimates the shift from only the **unlabeled deployment pool** (always available in a prospective screen) using cheap fingerprint features is missing — and is precisely the "more data-efficient likelihood ratio" direction CoDrug flagged.

## Novelty map
| Prior work | Its contribution | Its boundary |
|---|---|---|
| Tibshirani 2019 (WCP) | Weighted CP restores *marginal* coverage under covariate shift | general; weights assumed given; not molecular; not conditional |
| CoDrug 2023 | Density-ratio weighted CP for molecular **classification**; restores marginal/per-label coverage | classification; marginal; GNN+KDE+external-OOD; no conditional/AD-stratified analysis |
| Klarner 2023 (Q-SAVI) | Bayesian prior for extrapolative bioactivity; better accuracy+ECE | not conformal; no coverage guarantee |
| Guo 2027 | Benchmarks CP variants under scaffold shift; shows conditional failure | **no shift correction**; single ChEMBL source; regression |
| Hosni 2026 | kNN-AD flags unreliable CP OOD | diagnoses, does not correct |
| Harris 2026 | Domain classifier as selective-classification filter | classification; filter not weight; no interval coverage |
| **This work** | **(a)** covariate-shift–weighted conformal for molecular **regression**, model-agnostic, using **only the unlabeled deployment pool** via a calibrated fingerprint discriminator; **(b)** an **AD-stratified (Mondrian) weighted** variant that targets **conditional** coverage; **(c)** the first systematic answer to *marginal-vs-conditional* repair under scaffold **and** temporal shift across multiple datasets with repeated-split statistics; **(d)** a deployment diagnostic linking the discriminator weight to coverage degradation. | approximate conditional coverage only (exact is impossible, Barber 2021); weights estimated, not known; CPU-scale models. Honestly stated. |

## Why it is not incremental
The *vehicle* (combine Mondrian stratification with Tibshirani weighting, estimate weights by a train-vs-pool classifier) uses known ingredients; the **research** is the **falsifiable scientific question** the field has left open and whose answer is non-obvious:

> **H1 (central).** Under chemical covariate shift, covariate-shift weighting restores *marginal* coverage but **not** *conditional* coverage across the applicability-domain spectrum; restoring conditional coverage additionally requires AD-stratified calibration.

H1 can be **falsified** (maybe weighting alone fixes both; maybe nothing fixes the extreme-OOD stratum). Either outcome is a genuine, publishable scientific result, and the negative parts will be reported, not hidden (RULE 3, 18).

Secondary, each tied to an experiment:
- **H2 (deployability).** A model-agnostic fingerprint-discriminator density-ratio (clipped), estimated from the *unlabeled* deployment pool, restores coverage at least as well as model-internal density estimates (CoDrug-style logistic/KDE), at a fraction of the engineering and compute.
- **H3 (decision utility).** Improved conditional coverage yields safer risk-controlled screening: among compounds *selected* by a lower-bound rule, fewer have true values outside their predicted interval ("surprises"), and selection quality (enrichment) is not degraded.
- **H4 (cost/regime).** Weighting reduces effective calibration size; we quantify the efficiency (interval-width) cost and identify the shift-magnitude / calibration-size regime where the method helps vs. hurts (there will be a regime where it hurts — reported).

## Stress-test (Phase 2) — skeptical JCIM editor, answered
- *Incremental?* No — central falsifiable hypothesis + mechanism + honest negatives; see above.
- *Already solved (CoDrug)?* No — classification vs regression; marginal vs conditional; GNN+KDE vs model-agnostic+pool+fingerprint. CoDrug reimplemented as a baseline.
- *Simpler method suffices?* Directly tested: split CP, normalized CP, Mondrian-AD CP (unweighted), calibration-update CP (Morger), localized CP (dAD-style) are all baselines.
- *Artificial gap?* No — the gap is stated by the prior work itself (CoDrug future work; Guo conditional failure; Hosni flag-only).
- *One dataset / leakage?* 6 public regression datasets + ≥2 temporal ChEMBL targets; scaffold-disjoint and temporal splits; InChIKey dedup; group-aware CV; repeated splits + CIs; explicit leakage audit (Phase 8).
- *Weak baselines?* Baselines are the actual practical SOTA CP variants and CoDrug-style weighting, on strong models (RF, LightGBM, fingerprint-MLP).
- *Engineering not research?* The deliverable is a scientific characterization (H1–H4), not a tool.

## Decision: PROCEED with this topic.

---
## Design update after preliminary dev-set runs (transparency note)
The hypotheses above were pre-registered **before** any results. Preliminary runs on the
scaffold dev-set (ESOL, FreeSolv, Lipophilicity, BACE; RF; 3–5 seeds) tested them and
**refined** the framing (documented in `EXPERIMENT_LOG.md`). We keep the pre-registered
hypotheses and report their outcomes honestly:

- **H1 outcome (partially falsified / refined):** Covariate-shift weighting does *not*
  reliably restore even *marginal* coverage under strong shift (weights become degenerate
  in high-dimensional fingerprint space), and it does *not* restore *conditional* coverage
  in regression. Simple AD-stratification (Mondrian) helps conditional coverage under
  mild/moderate shift but not under extreme shift. No deployable finite-width method
  restores conditional coverage under extreme shift — consistent with the distribution-free
  impossibility of exact conditional coverage (Barber 2021) and the need for non-degenerate
  importance weights (Tibshirani 2019).
- **New contribution added (method):** **ADE-CP** — applicability-domain conformal
  extrapolation — models the conformal residual quantile along the AD coordinate and
  extrapolates it, giving the best conditional-coverage/efficiency trade-off among
  finite-width methods under mild/moderate shift, and degrading gracefully.
- **New contribution (diagnostic), promoted to headline:** achievable conditional coverage
  is governed by shift magnitude, estimable label-free by the **train-vs-pool discriminator
  AUC**; we give a practical decision rule for when conformal intervals can be trusted in
  prospective screening.

### Final contributions (evidence-based)
- **C1.** First systematic evaluation of *conditional* (AD- and activity-stratified)
  coverage of conformal **regression** under scaffold **and** temporal shift across 6 public
  datasets, including covariate-shift–**weighted** variants (extends CoDrug 2023, which is
  classification + marginal only) with repeated-split statistics.
- **C2 (negative/characterization).** Covariate-shift weighting is insufficient for
  conditional coverage in molecular regression; high-dimensional/KDE weight estimators
  degenerate into trivial intervals — a cautionary, actionable result.
- **C3 (method).** ADE-CP: a model-agnostic, deployable novelty-extrapolation conformal
  method; best finite-width conditional coverage under mild/moderate shift.
- **C4 (diagnostic).** The discriminator-AUC shift-magnitude law and a deployment decision
  rule for trusting conformal intervals.
- **C5 (reproducibility).** Public data + released code + automated results/figures/tables.

### Held-out confirmation (not used for method development)
Temporal ChEMBL datasets (VEGFR2, COX-2), the full 20-seed scaffold runs, and the
controlled similarity-shift sweep serve as confirmation of C1–C4.
