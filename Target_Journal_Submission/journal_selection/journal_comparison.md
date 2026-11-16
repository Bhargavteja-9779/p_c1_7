# Journal Comparison (Phase 0)

**Method.** For every candidate, the submission-to-acceptance time was **measured** from primary bibliographic metadata, not taken from marketing pages:

- **PubMed-indexed journals:** NCBI E-utilities history dates ("received" and "accepted"), journal research articles published 2025–2026, up to 400–600 most recent records per journal.
- **Springer Nature journals:** Crossref "ArticleHistory" assertions, articles published 2025-06-01 to 2026-11-15.
- **Reproducibility:** scripts are `evidence/pubmed_times.py` and `evidence/crossref_times.py`. All raw per-article records are in `evidence/*.json`, and the summary table is in `evidence/timeline_summary.md`.

Survivorship caveat: only accepted papers are observed.

Impact factors are JIF values from secondary sources, because Clarivate JCR could not be accessed from this environment. Values marked "≈" were not individually re-checked, since the journal was already eliminated on timeline or fit grounds.

## A. Shortlist (median ≤ 100 days, reputable publisher)

| # | Journal | Publisher | Median days (IQR) | % ≤100 d | JIF (approx.) | Scope fit for a CPU-feasible computational ML study | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **J. Chem. Inf. Model.** | ACS | **84 (62–110)** | 65.9 | **6.4 (2025)** | **Excellent**: ML, cheminformatics, QSAR, uncertainty, benchmarks are core | **SELECTED** |
| 2 | J. Chem. Theory Comput. | ACS | 77.5 (60–98) | 76.9 | ≈5.5 | Poor: electronic-structure and simulation theory | Rejected (fit) |
| 3 | ACS Central Science | ACS | 82 (64–104) | 74.2 | ≈10–12 | Weak: needs broad chemical significance; very selective | Rejected (fit / risk) |
| 4 | Chemical Science | RSC | 70 (48–100.5) | 75.1 | 7.4–8.1 (sources disagree) | Moderate: ML papers accepted only with broad chemical insight; high desk-rejection risk for methods/benchmark work | Rejected (risk) |
| 5 | JACS Au | ACS | 60 (45–79) | 88.2 | ≈8 | Weak: broad chemistry, mainly experimental | Rejected (fit) |
| 6 | Anal. Chim. Acta | Elsevier | 60 (43–80.75) | 90.5 | ≈6 | Moderate: chemometrics only; needs analytical-chemistry data | Rejected (fit) |
| 7 | Talanta | Elsevier | 70 (51–97.5) | 77.2 | ≈6 | As above | Rejected (fit) |
| 8 | Water Research | Elsevier | 84 (68–114) | 66.2 | ≈12 | Weak: needs water-science contribution and data | Rejected (fit) |
| 9 | J. King Saud Univ. – Comput. Inf. Sci. | Springer (for KSU) | 79 (59–105) | 71.9 | ≈6 | Good (general computing) but lower reputation than the society-published alternatives | Reserve |
| 10 | Int. J. Med. Inform. | Elsevier | 89 (56–151) | 55.5 | ≈4 | Needs credentialed clinical data (not available) | Rejected (data) |
| 11 | Comput. Struct. Biotechnol. J. | Elsevier/RNCSB | 91 (63–119) | 60.3 | ≈4–6 | Moderate | Rejected (lower JIF) |
| 12 | Anal. Chem. | ACS | 95 (73.75–130) | 54.0 | ≈7 | Analytical methods; computational-only papers rare | Rejected (fit) |
| 13 | J. Hazard. Mater. | Elsevier | 97 (75–125) | 53.2 | ≈11 | Environmental chemistry | Rejected (fit) |
| 14 | Methods; Comput. Biol. Chem.; J. Mol. Graph. Model. | Elsevier | 88.5–98.5 | 52–62 | ≈3–4 | Fit acceptable, but JIF / quartile lower | Rejected (JIF) |

## B. Eliminated on timeline (median > 100 days)

| Journal | Publisher | Median days | % ≤100 d |
|---|---|---|---|
| J. Med. Chem. | ACS | 104 | 45.8 |
| J. Comput.-Aided Mol. Des. | Springer | 102 | 48.7 |
| Environ. Sci. Technol. | ACS | 119 | 33.7 |
| JAMIA | Oxford UP | 120 | 35.1 |
| Digital Discovery | RSC | 123 | 33.0 |
| Briefings in Bioinformatics | Oxford UP | 124 | 30.7 |
| Nucleic Acids Research | Oxford UP | 124.5 | 43.4 |
| J. Cheminformatics | Springer/BMC | 134 | 19.9 |
| Scientific Reports | Springer Nature | 139 | 30.4 |
| Comput. Biol. Med. | Elsevier | 141 | 31.5 |
| J. Biomed. Inform. | Elsevier | 146 | 18.4 |
| Bioinformatics | Oxford UP | 147 | 22.2 |
| Complex & Intelligent Systems | Springer | 147 | 24.4 |
| Engineering with Computers | Springer | 147 | 25.8 |
| NAR Genom. Bioinform. | Oxford UP | 155 | 16.2 |
| J. Intell. Manuf. | Springer | 158.5 | 16.8 |
| Patterns | Cell Press | 166 | 8.8 |
| Comput. Methods Programs Biomed. | Elsevier | 170 | 12.3 |
| npj Digit. Med. | Springer Nature | 178.5 | 13.2 |
| GigaScience | Oxford UP | 182 | 15.1 |
| Artif. Intell. Rev. | Springer | 195 | 9.6 |
| Machine Learning | Springer | 201 | 12.4 |
| Neural Networks | Elsevier | 219 | 4.8 |
| J. Big Data | Springer | 232 | 5.6 |
| Medical Image Analysis | Elsevier | 236 | 3.2 |
| Applied Intelligence | Springer | 241 | 3.5 |
| Data Min. Knowl. Discov. | Springer | 258.5 | 11.6 |
| Neural Comput. Appl. | Springer | 264.5 | 4.1 |
| Cognitive Computation | Springer | 267 | 7.2 |
| Artif. Intell. Med. | Elsevier | 282 | 4.0 |
| Genomics Proteomics Bioinformatics | Oxford UP | 379 | 9.7 |

Applied Energy (Elsevier) is not PubMed-indexed. Third-party summaries of its publisher page give about 127–132 days to acceptance, so it was eliminated, but this is **not independently verified**.

## C. Could not be measured (timeline UNVERIFIED)
- **IEEE journals** (TNNLS, JBHI, TNSRE, TII, TIM, IoT-J): PubMed records carry no received/accepted dates, and IEEE Xplore blocks automated access.
- **Elsevier engineering/CS journals not indexed in PubMed** (ESWA, KBS, EAAI, Information Fusion, Information Sciences, Applied Soft Computing).
- **Oxford University Press engineering journals** (J. Comput. Des. Eng.), and **Wiley** (CACIE).

Following the user's rule, none of these was treated as meeting the 100-day requirement.

## D. Oxford University Press specifically
The user asked for journals "like Oxford". Every measurable OUP candidate had a median above 100 days:
- Briefings in Bioinformatics: 124 days
- JAMIA: 120 days
- Bioinformatics: 147 days
- NAR Genomics and Bioinformatics: 155 days
- GigaScience: 182 days
- Genomics, Proteomics & Bioinformatics: 379 days

OUP's J. Comput. Des. Eng. could not be measured. OUP was therefore not selected. ACS, a society publisher of comparable standing, offers the measured sub-100-day timeline.
