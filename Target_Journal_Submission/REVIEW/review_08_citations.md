# Review 8 — Literature & Citation Reviewer

**Perspective:** Are all citations accurate and claims correctly attributed?

## Findings

**[MAJOR → addressed] B1. KMM-CP missing** (see Review 1). Added (ref 32, verified via arXiv).

**[MAJOR → addressed] B2. Venue error.** Hosni et al. "Explicit Applicability Domain Calculations..." was initially mis-attributed to JCIM; it is **ACS Omega** (DOI 10.1021/acsomega.5c11875). Corrected in all documents and the reference database.

**[MODERATE → addressed] B3. Venue checks.** Morger et al. 2022 = *Scientific Reports* (not J. Cheminform.); Oršolić & Šmuc dAD = *Bioinformatics*. Corrected. All 32 references verified against Crossref or arXiv (`verified_references.json`); DOIs, years, authors, venues checked programmatically.

**[MODERATE] B4. Claim attribution.** Verify: (a) "random splits overstate generalization" → MoleculeNet (ref 22) and Li 2026 partitioning (ref 21) support this; (b) impossibility of conditional coverage → Barber et al. 2021 (ref 16); (c) weighted CP marginal guarantee → Tibshirani 2019 (ref 13). All check out.

**[MINOR] B5.** arXiv-only items (CoDrug, KMM-CP, Tibshirani WCP, Romano CQR, Klarner) are cited with arXiv IDs and venue (NeurIPS/ICML) where applicable — acceptable for JCIM; update to DOIs if later published.

## Recommendation: MINOR_REVISION → ACCEPT after KMM-CP and venue fixes (done).
