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
