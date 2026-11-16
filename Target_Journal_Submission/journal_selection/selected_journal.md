# Selected Target Journal

**Decision date:** 2026-11-15 (Phase 0; fixed before the research topic was chosen)

| Field | Value | Verification status |
|---|---|---|
| TARGET JOURNAL | *Journal of Chemical Information and Modeling* (J. Chem. Inf. Model., JCIM) | — |
| PUBLISHER | American Chemical Society (ACS), Washington DC, USA | Crossref metadata; Wikipedia infobox |
| ISSN | 1549-9596 (print); 1549-960X (online) | Crossref / Peeref |
| JCR STATUS | Indexed in Science Citation Index Expanded; listed in JCR | Secondary sources (Wikipedia indexing list; Peeref; BioxBio). Clarivate JCR itself could not be accessed from this environment. |
| JCR QUARTILE | Q1 in *Chemistry, Medicinal*; Q1 in *Computer Science, Information Systems*; Q1 in *Computer Science, Interdisciplinary Applications*; Q2 in *Chemistry, Multidisciplinary* | Secondary source (Peeref, labelled "JCR 2026"). **Not checked against Clarivate directly.** |
| JOURNAL IMPACT FACTOR | 6.4 (JIF 2025, JCR release June 2026); 5.3 (2024); 5.6 (2023) | Three independent secondary sources agree (BioxBio, Wikipedia, journalmetrics.org). |
| RELEVANT JCR CATEGORY FOR THIS WORK | *Computer Science, Interdisciplinary Applications* (Q1) and *Chemistry, Medicinal* (Q1) | as above |
| VERIFIED REVIEW/DECISION TIMELINE | ACS does not publish a first-decision figure that could be retrieved here (publisher pages return HTTP 403 to automated access). **Not verified.** | — |
| VERIFIED ACCEPTANCE TIMELINE | **Median 84 days** from submission to acceptance (IQR 62–110 days); **65.9 % of papers accepted within 100 days**; 23.8 % within 60 days. Based on n = 390 JCIM research articles published 2025–2026 that carry both "received" and "accepted" dates in their PubMed history records. | **Measured here** from primary bibliographic metadata (NCBI E-utilities). Script: `evidence/pubmed_times.py`; raw records: `evidence/pubmed_J_Chem_Inf_Model.json`. |
| Caveats on the timeline | (i) Only accepted papers are counted (survivorship), so this is the time for papers that were eventually accepted, not a probability of acceptance. (ii) The clock starts at the first submission of the paper, revisions included. (iii) About one in three accepted papers took more than 100 days, so **a 100-day acceptance cannot be promised for any single manuscript.** | — |
| APC | Hybrid subscription journal: **no mandatory article charge** for standard publication. Open access is optional for a fee (ACS AuthorChoice / CC-BY); the current fee amount could not be checked here. | Partly verified (publishing model); fee amount **unverified** |
| SCOPE FIT | JCIM publishes new methods and important applications in chemical informatics and molecular modelling, including machine learning, QSAR and molecular property prediction, uncertainty and applicability-domain analysis, and benchmarking. | Paraphrased from the journal description and recent contents |
| RESEARCH FIT | Computational, CPU-feasible, data-driven methods on public molecular datasets with rigorous benchmarking are a core JCIM article type (for example the Chemprop papers, activity-cliff benchmarks, and uncertainty-quantification studies). | See `journal_verification.md` §3 |
| KEY AUTHOR GUIDELINES | ACS manuscript format (Abstract + TOC graphic; numbered ACS-style references; Data and Software Availability section). JCIM editorial policy since 1 Jan 2021 requires data and method sharing for reproducibility (Merz et al., *J. Chem. Inf. Model.* 2020, 60, 5868–5869, doi:10.1021/acs.jcim.0c01389). Benchmarking expectations set out in Ash et al., *J. Chem. Inf. Model.* 2025, 65, 9398–9411, doi:10.1021/acs.jcim.5c01609 (statistically rigorous method comparison). | DOIs checked on Crossref |
| KEY REJECTION RISKS | (1) Contribution seen as incremental ("another model on MoleculeNet"). (2) Weak or unfair baselines (Chemprop / RF-on-fingerprints are expected). (3) Random splits only, which overstate generalisation; scaffold, temporal or cluster splits are expected. (4) No repeated-split statistics. (5) No code or data. (6) Claims that rest on a single dataset. | Derived from the journal's editorial policy and recent papers |

## Why this journal (summary)
Among more than 70 candidate journals whose recent submission-to-acceptance times I measured from bibliographic metadata, JCIM is the reputable Q1 journal that best combines four things:
1. **Scientific fit** for a CPU-feasible computational machine-learning study.
2. **A high impact factor** for its field (6.4).
3. **A measured median acceptance time below 100 days** (84 days).
4. **A publisher of top reputation** (ACS).

Faster journals were rejected for poor scope fit. *J. Phys. Chem. Lett.*, *JACS Au*, *Anal. Chim. Acta*, *Eur. J. Med. Chem.* and *Bioorg. Chem.* are experimental or physical chemistry venues. *Chemical Science* and *ACS Central Science* require broad chemical significance that a methods paper rarely meets. Higher-impact computing journals (*Neural Networks*, *Brief. Bioinform.*, *Bioinformatics*, *Comput. Biol. Med.*, *npj Digit. Med.*, *Artif. Intell. Rev.*, *J. Big Data*) were rejected because their measured medians are 124–282 days. See `journal_comparison.md`.
