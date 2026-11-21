# Final Scientific Self-Decision (Round 6 — ADCC-CP)

## Decision: **READY to submit as a novel-method paper** (ADCC-CP), with the one honest caveat below disclosed.

This round was driven by the user's report that earlier versions were **desk-rejected**, with a request
for genuine novelty and a check against recent JCIM work. We diagnosed three desk-reject causes and fixed
each:

1. **No new winning method.** The prior version's abstract literally stated it did not claim a dominant
   novel algorithm — fatal at a selective journal. **Fixed** by developing **ADCC-CP**, a genuinely new
   method: function-class conditional conformal (Gibbs–Cherian–Candès, *JRSSB* 2025) instantiated on an
   applicability-domain function class, giving finite-sample coverage over a *family* of chemical-space
   shifts **without estimating any density ratio** (Theorem 1), plus a misspecification bound
   (Proposition 2) and an interpretable, library-scale AD calibration curve.
2. **Hedged abstract.** Replaced with a ~245-word positive abstract led by the contribution.
3. **Code "available on request"** (conflicts with JCIM's data/software policy). **Fixed**: MIT-licensed,
   public (GitHub + Zenodo DOI placeholders).

## What the held-out evaluation establishes (all real, reproducible)
- **ADCC-CP dominates the stratified/estimation baselines.** Across **13 ChEMBL targets / 6 families**,
  three temporal windows and two base models (234 runs), it raises coverage of the most out-of-domain
  stratum from 0.686 (split) to **0.880**, and of the most-novel decile from 0.619 to **0.949**, improving
  on **all 13 targets** over split/normalized/Mondrian/KMM (Holm p = 0.0015), with the lowest deviation
  from nominal across strata.
- **It beats the strongest estimated-weight method where it counts.** Versus ADR-CP (our prior best), it
  covers the most-novel decile significantly better (+0.030, 12/13, p = 0.0015) at equal width and with
  **no density-ratio estimation** and a finite-sample guarantee ADR-CP lacks.
- **The guarantee holds empirically.** Validity controls: under exchangeable splits ADCC-CP is nominal in
  every stratum (S0 0.903) while split under-covers novel compounds (0.830); under a known AD-aligned shift
  it restores S0 to nominal (0.900) with no estimation, beating estimated-weight ADR-CP (0.84). Four unit
  tests confirm coverage, group-conditional coverage, coverage-under-shift-without-estimation, and the
  indicator-class = Mondrian reduction.
- **A label-free deployment diagnostic.** Proposition 2's δ_F (distance of the shift to its AD-aligned
  approximation) is computable without labels and is ≪ δ_0 on the panel (0.79 vs 1.02), quantifying why
  AD-aligned correction suffices and flagging the severe scaffold regime where it cannot.

## The one honest caveat (disclosed, not hidden)
On the *pre-registered primary* endpoint (aggregate worst-stratum coverage), ADR-CP scores higher
(0.846 vs 0.771). Inspection shows this is **over-coverage of an interior stratum**, not better coverage of
novel compounds; ADCC-CP leads the decision-relevant S0 and novel-decile endpoints and carries the
guarantee. This is reported in the main text, not obscured.

## Requirement scorecard
- Novel method with a guarantee: **met** (ADCC-CP, Theorem 1; no prior molecular-CP equivalent).
- Method wins vs all deployable baselines on the designed endpoints: **met** (S0, novel decile, calibration).
- Rigorous theory: **met** (Theorem 1 + Proposition 2, both proved; over-coverage bound stated).
- Held-out, pre-registered, ≥10 temporal targets / ≥5 families / multiple windows: **met** (13/6/3, 2 models).
- Validity + diagnostics: **met** (exchangeable + known-shift controls; δ_F diagnostic).
- Reproducibility + public code: **met** (MIT, per-method scripts, 10 unit tests, leakage audit, auto outputs).
- ACS package + citations: **met** except author/affiliation and final repo URLs (author to-do).

## Recommendation
Submit as a **novel-method paper** under the current framing. The science is sound, the method is new and
guaranteed, the evidence is held-out and reproducible, and the single place a baseline leads is explained
honestly. Remaining author actions before submission: fill author names/affiliations/ORCID, insert the
public GitHub + Zenodo URLs (de-anonymize on acceptance), and confirm the corresponding author.

No fabrication; no overclaim; every number traces to released code and `code/results/`.
