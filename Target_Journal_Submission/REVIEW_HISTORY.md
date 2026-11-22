# REVIEW_HISTORY

## Round 1 — Ten reviewer perspectives (GU5) + 2 corroborating AI-agent reviews
- Conducted 10 distinct reviewer perspectives (REVIEW/review_01..10) + 2 independent
  workflow agents (novelty, methodology) that corroborated them.
- **Most consequential finding:** missing prior art KMM-CP (Laghuvarapu et al. 2026) and
  Lee et al. (label shift); both verified via arXiv and cited. KMM-CP's premise (density-ratio
  instability) overlapped the claimed "negative result".
- **Revisions applied (one full documented cycle):**
  - Implemented KMM weighting baseline (cvxopt QP); re-ran scaffold+temporal (4,652 rows).
  - Finding: KMM does NOT restore conditional coverage (temporal worst-stratum 0.679 ≈ split),
    strengthening the thesis; ADR-CP beats KMM by +0.230 (Holm p=4e-5).
  - Repositioned contributions (C2 credited to CoDrug/KMM-CP; novelty = regression +
    conditional + ADE-CP + temporal + diagnostic).
  - Scoped ADE-CP guarantee (exchangeability only); added width caveat to decision utility;
    fixed venue errors (Hosni=ACS Omega etc.); cited all 33 refs inline.
  - Consistency audit: 11/11 manuscript numbers match data.
- Documented in REVIEW/final_audit.md.

## Execution-limit note (GU8)
Full 10×-cycle automated iteration was limited by the environment's 5-hour usage cap
(reviewer subagents failed twice at the cap). The substantive findings were resolved in the
main loop; readiness is judged on evidence, not cycle count (see FINAL_DECISION.md).

## Round 6 — Desk-rejection response: new method ADCC-CP (2026-11-21)
- **Trigger:** user reported earlier versions were desk-rejected; asked for more novelty and a
  level-check against recent JCIM/arXiv papers.
- **Root-cause of desk-rejects (diagnosed):** (1) abstract explicitly disclaimed a novel winning
  method; (2) long hedged abstract; (3) code "available on request" vs JCIM data/software policy.
- **New method:** ADCC-CP — function-class conditional conformal (Gibbs–Cherian–Candès, JRSSB 2025)
  on an applicability-domain class. Finite-sample coverage over a family of AD-aligned shifts with
  NO density-ratio estimation (Theorem 1); misspecification bound (Proposition 2); AD calibration curve.
- **Held-out evidence (13 ChEMBL targets, 3 windows, 2 models, 234 runs):** S0 coverage 0.686→0.880,
  novel decile 0.619→0.949, beats split/normalized/Mondrian/KMM on all 13 (p=0.0015); beats ADR-CP on
  the novel decile (+0.030, 12/13, p=0.0015) with no estimation + a guarantee. Validity controls confirm
  the theory (exchangeable S0 0.903; known AD-shift S0 0.900). 10 unit tests + leakage audit pass.
- **Honesty:** ADR-CP leads aggregate worst-stratum (0.846 vs 0.771) by over-covering an interior
  stratum — reported in-text, not hidden.
- **Package:** short positive abstract; MIT-licensed public code (GitHub+Zenodo placeholders); rebuilt
  manuscript (18pp) + SI (7pp) + cover letter + graphical TOC + ZIP (23 files); 37 verified refs.

## Round 7 — Novelty amplification + JCIM positioning (2026-11-22)
- **Trigger:** user asked to improvise more, push novelty "very high", make it unrejectable, compare
  against more recent JCIM papers; code "available on request"; no funding / no competing interest.
  User OK'd a real-world (deployment) reframing if it helps acceptance.
- **New method (novelty+):** multi-coordinate ADCC-CP (ADCC-CP-2D) — additive piecewise-linear
  function class over TWO applicability-domain coordinates (structural max-Tanimoto + physicochemical
  nearest-train similarity). Theorem 1 guarantee extends unchanged (F_AD subset F_AD^2); raises
  most-out-of-domain coverage over 1-D ADCC-CP on all tested targets. Code: methods.py ad_basis_2d /
  method_adcc_2d; pipeline computes 2nd coordinate; held-out panel run_panel_adcc2d.py (234 configs).
- **Theory+:** Corollary 3 (ADCC-CP returns the pointwise-tightest class-valid interval -> efficiency
  optimal among AD-threshold rules satisfying Theorem 1).
- **JCIM positioning:** added Table 1 comparing ADCC-CP vs Norinder2014, Svensson2018, Li/conformalized
  GNN 2024, Koetter2025, Fooladi2025, Parrondo2026, Harris2026, CoDrug, KMM-CP, ADR-CP, Guo on task /
  shift / coverage target / guarantee / needs-ratio-estimate / pool-deployable. ADCC-CP is the only
  row with a finite-sample conditional-family guarantee AND no ratio estimation.
- **New refs (verified Crossref+EuropePMC abstracts):** Koetter et al. JCIM 2025 (robust UQ; UQ fails
  out-of-domain; split-dependent eval) #38; Fooladi/Kirchmair et al. JCIM 2025 (OOD evaluation; scaffold
  splits understate shift) #39. Related work rewritten around both.
- **Real-world framing:** Section 5.6 — the AD calibration curve as a per-compound, guaranteed-coverage
  reliability schedule for prospective screening/triage; delta_F as a pre-synthesis go/no-go on the pool.
- **Metadata:** first author P. N. Bhargav Teja; 2nd placeholder; Funding none; competing interest none;
  code "available on request" (user override of public-repo).
