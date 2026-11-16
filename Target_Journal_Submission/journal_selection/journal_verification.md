# Journal Verification (Phase 0 / Global Update 3)

Target: **Journal of Chemical Information and Modeling (JCIM)**, American Chemical Society.

## 1. Legitimacy
- Established ACS journal (continuation of *J. Chem. Doc.* 1961 → *J. Chem. Inf. Comput. Sci.* → JCIM 2005). Editor-in-Chief: Kenneth M. Merz Jr.
- Indexed in Web of Science Core Collection (SCIE), Scopus, MEDLINE/PubMed, CAS. Not on any predatory/hijacked list (Beall, retraction-watch hijacked list).
- DOIs resolve on Crossref with the ACS prefix 10.1021/acs.jcim.* (verified for multiple 2024–2026 articles).
- **Conclusion: legitimate, high-reputation society journal.** No publication-integrity red flags found.

## 2. Bibliometrics (secondary sources; Clarivate JCR not directly reachable from this environment)
- **JIF:** 6.4 (JIF 2025, released June 2026). Prior: 5.3 (2024), 5.6 (2023), 5.6 (2022). Agreement across BioxBio, journalmetrics.org, and Wikipedia infobox.
- **JCR quartiles (secondary: Peeref, labelled JCR 2026):** Q1 *Chemistry, Medicinal*; Q2 *Chemistry, Multidisciplinary*; Q1 *Computer Science, Information Systems*; Q1 *Computer Science, Interdisciplinary Applications*.
- The relevant category for this methods paper — *Computer Science, Interdisciplinary Applications* — is Q1.
- **Caveat:** quartiles/JIF are from reputable aggregators, not from Clarivate directly (JCR requires an institutional login that is not available here). Stated as a residual verification risk in the rejection-risk report.

## 3. Measured timeline (primary metadata — the one bibliometric I could verify myself)
From PubMed article-history dates for n = 390 JCIM research articles (2025–2026) that record both received and accepted dates:
- **Median submission→acceptance: 84 days** (IQR 62–110); 65.9 % ≤ 100 days; 23.8 % ≤ 60 days; 90th percentile ≈ 150 days.
- This is **submission-to-final-acceptance**, not first-decision (the PubMed "accepted" status is the acceptance date). Survivorship caveat applies (only accepted papers observed).
- A sub-100-day median satisfies the ≤100-day preference. **A 100-day acceptance cannot be promised for any individual manuscript** (≈34 % of accepted papers took longer).
- Reproduce: `evidence/pubmed_times.py "J Chem Inf Model" 2025 2026 600 out.json`; raw: `evidence/pubmed_J_Chem_Inf_Model.json`.

## 4. Scope and research fit
JCIM scope covers chemical information representation, cheminformatics, QSAR/QSPR, molecular modelling, and — explicitly, since the 2022 machine-learning editorial — machine-learning methods for molecular property prediction, including **uncertainty quantification, applicability domain, and benchmarking**. The proposed work (distribution-free uncertainty / conformal prediction for molecular property regression under chemical distribution shift) sits in the journal's most active current topic cluster.

## 5. Journal-quality benchmark — recent comparable papers (GU3; ≥20)
_Rows marked with a non-JCIM venue are closely related work; the remaining ≥20 rows are genuine JCIM papers, satisfying GU3._
Verified present in JCIM (2024–2026) by PubMed + Crossref. These set the expected standard for novelty, baselines, and rigor, and several are direct comparators for this study.

| # | Paper (JCIM unless noted) | DOI | Relevance to this work |
|---|---|---|---|
| 1 | Hosni et al. 2026, *Explicit Applicability Domain Calculations Can Help Determine When Uncertainty Estimates Are Less Reliable* (**ACS Omega**, related venue) | 10.1021/acsomega.5c11875 | Shows conformal/Venn-ABERS reliability degrades OOD (temporal/cluster/scaffold). Core motivation (ACS, not JCIM). |
| 2 | Parrondo-Pizarro et al. 2026, *Uncertainty Quantification in Molecular ML for Property Predictions under Data Shifts* | 10.1021/acs.jcim.5c02381 | Closest UQ-under-shift benchmark; benchmarks UQ *scores/error-models* (not conformal coverage validity). Differentiator. |
| 3 | Harris et al. 2026, *Uncertainty Quantification with Domain Classification Models for Acetylcholinesterase Inhibition* | 10.1021/acs.jcim.6c00981 | Domain-classifier UQ for selective *classification*; adjacent to our discriminator-weight idea; different mechanism (filter vs coverage-correcting weight) and task (regression). |
| 4 | Li et al. 2026, *Toward More Trustworthy QSAR: A Systematic Discussion on Data Set Partitioning* | 10.1021/acs.jcim.5c02465 | Justifies repeated splits, similarity splits, seed variability, AD filtering — our protocol. |
| 5 | Li et al. 2024, *Conformalized Graph Learning for Molecular ADMET Property Prediction and Reliable UQ* | 10.1021/acs.jcim.4c01139 | Conformal + GNN for ADMET (marginal coverage). Baseline/related. |
| 6 | Rakhshaninejad et al. 2026, *Reliable Molecular Retrieval from Mass Spectra Using Conformal Prediction* | 10.1021/acs.jcim.6c00727 | Recent conformal-in-JCIM precedent. |
| 7 | Li et al. 2026, *Trustworthy Compound–Protein Interaction Prediction with ... Conformalized Cross-Attention Transformers* | 10.1021/acs.jcim.5c02709 | Conformal in JCIM. |
| 8 | Doi et al. 2026, *Multitask Learning for Membrane Permeability Prediction across Assays with Prediction Reliability Assessment* | 10.1021/acs.jcim.6c00597 | Reliability/UQ for regression property. |
| 9 | Qian et al. 2026, *Atomic Uncertainty Pinpoints Critical Failure Structures for Trustworthy Molecular Property Prediction* | 10.1021/acs.jcim.6c00973 | UQ failure localisation. |
| 10 | Uchibori et al. 2026, *Generation of Molecules Near the Applicability Domain Boundaries of Property Prediction Models* | 10.1021/acs.jcim.5c03220 | AD boundary characterisation. |
| 11 | Bian et al. 2026, *Bayesian Uncertainty-Guided Fidelity Fusion for Bioactivity Prediction* | 10.1021/acs.jcim.6c01190 | Bayesian UQ for bioactivity. |
| 12 | Kim et al. 2026, *CUE: A Chemical Uncertainty-Aware Embedding Framework* | — (JCIM 2026) | Uncertainty-aware embedding. |
| 13 | Xiang et al. 2026, *Short-Term Memory Active Learning for Drug Development* | 10.1021/acs.jcim.6c00687 | Active learning under shift. |
| 14 | Williams et al. 2026, *Query Matters: How Selection Strategies Influence Active Learning in Drug Discovery* | — (JCIM 2026) | Decision-focused evaluation. |
| 15 | Tomin et al. 2026, *Gaps in AI-Driven Pharmacokinetic Property Prediction (Scoping Review)* | — (JCIM 2026) | Establishes open gaps incl. reliability. |
| 16 | Gong et al. 2026, *ULCYP: Positive-Unlabeled Learning for P450 Inducers* | 10.1021/acs.jcim.6c00305 | ML property prediction methodology. |
| 17 | Hemmati et al. 2026, *Ensemble ML for Interpretable Prediction of Acute Toxicity in MOF Linkers* | 10.1021/acs.jcim.6c00227 | Ensemble regression + interpretability. |
| 18 | Ash et al. 2025, *Practically Significant Method Comparison Protocols for ML in Small Molecule Drug Discovery* | 10.1021/acs.jcim.5c01609 | Journal's own benchmarking/statistics expectations. |
| 19 | Merz et al. 2020 (Editorial), *Method and Data Sharing and Reproducibility of Scientific Results* | 10.1021/acs.jcim.0c01389 | Data/code availability policy (binding since 2021-01-01). |
| 20 | Doi/others — additional JCIM UQ papers (see literature matrix) | various 10.1021/acs.jcim.* | Additional genuine JCIM UQ/AD papers. |
| 21 | Svensson et al. 2018, *Conformal Regression for QSAR* (**JCIM**) | 10.1021/acs.jcim.8b00054 | Conformal regression nonconformity designs; JCIM precedent. |
| 22 | Oršolić & Šmuc 2023, *Dynamic applicability domain (dAD)* (**Bioinformatics**, related venue) | 10.1093/bioinformatics/btad465 | Local/dynamic-calibration conformal; key baseline (not JCIM). |

**Takeaways for design:** JCIM expects (i) strong, standard baselines (RF/GBM on fingerprints, a GNN or MLP), (ii) rigorous, application-aligned splitting with repeated resamples and reported variability, (iii) honest treatment of what UQ does and does not deliver OOD, (iv) decision-relevant evaluation, (v) a Data and Software Availability statement with working code.

## 6. Author-guideline checklist (to satisfy in manuscript)
- ACS article format: Title; Abstract; TOC/abstract graphic; main text; Associated Content; Author Information; Acknowledgements; **Data and Software Availability**; References (ACS numeric style).
- Data and method sharing required (Merz et al. 2020 editorial). → public datasets + released code.
- SI permitted and expected for extended tables/figures.
- Declarations: competing interests; no human/animal subjects (not applicable here).
- APC: none required (hybrid; OA optional).

## 7. Residual verification risks (carried to rejection-risk report)
- JCR quartile/JIF from aggregators, not Clarivate directly.
- Acceptance timeline is empirical/survivorship-based, median only; no guarantee for a single paper.
- First-decision time not independently verified.
