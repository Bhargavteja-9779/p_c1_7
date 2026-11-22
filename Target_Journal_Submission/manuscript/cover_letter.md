# Cover Letter

[Date]

To the Editors,
*Journal of Chemical Information and Modeling*

Dear Editor-in-Chief and Editorial Board,

We are pleased to submit our manuscript, **"Applicability-Domain Conditional Conformal Prediction: Distribution-Free Coverage over Chemical-Space Shifts without Density-Ratio Estimation,"** for consideration as an Article in the *Journal of Chemical Information and Modeling*.

**Problem.** Conformal prediction is now a leading way to attach a distribution-free applicability-domain statement to machine-learning predictions of molecular properties, and it appears frequently in this journal. Its guarantee assumes exchangeability — precisely what fails in prospective deployment, where the compounds to be scored are novel scaffolds or later-synthesized molecules (covariate shift). Coverage then fails selectively for the structurally novel compounds that drive decisions. Existing corrections either stratify the calibration set (and leave the most novel region under-covered) or reweight it by an *estimated* covariate density ratio that is unstable in high-dimensional chemical space and valid only if the estimate is correct.

**What is new.** We introduce **Applicability-Domain Conditional Conformal prediction (ADCC-CP)**, which calibrates with an augmented quantile regression over the class of piecewise-linear functions of a molecule's similarity to the training set. A single interval is then provably valid, *in finite samples and without estimating any density ratio*, (i) marginally, (ii) locally at every similarity level, and (iii) under **every** deployment shift whose density ratio along the applicability-domain axis lies in the class (Theorem 1). A companion bound (Proposition 2) states exactly how much coverage can be lost when the real shift is not applicability-domain–aligned — never more than for standard conformal prediction — giving practitioners a principled, label-free deployment diagnostic. To our knowledge this is the first molecular-property method to guarantee coverage over a whole family of chemical-space shifts without ratio estimation, and it adapts recent conditional-conformal theory (Gibbs, Cherian & Candès, *JRSSB* 2025) to chemistry for the first time. Because interval width depends on a compound only through its similarity score, ADCC-CP produces an interpretable applicability-domain calibration curve applicable to libraries of any size by lookup.

**Evidence.** On a pre-registered, held-out evaluation across **thirteen time-stamped ChEMBL targets from six protein families** under temporal shift (three chronological windows, two model families), ADCC-CP restores coverage in the most out-of-domain stratum far better than split, normalized, Mondrian and kernel-mean-matching conformal, improving over split conformal on every target, and it matches or exceeds the strongest estimated-weight method while carrying the finite-sample guarantee that method lacks and without collapsing the effective calibration size. Exchangeable and known-shift controls confirm the theory empirically. The function class was selected on separate MoleculeNet development data and then frozen, and all statistics are computed at the target level.

**Fit with JCIM.** The work is squarely within the journal's active stream on uncertainty quantification, applicability domain and trustworthy QSAR. All datasets used are public, and a complete, tested codebase reproduces every table and figure from a single command; the code will be made available by the authors upon reasonable request.

**Declarations.** This manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the submission and declare no competing financial interest. This research received no specific grant from any funding agency. No human or animal subjects were involved; the study uses only publicly available data. Generative AI tools were used only as a coding and drafting aid; all scientific claims, analyses and conclusions are the authors' own and are supported by the released code and public data.

We thank you for your consideration and look forward to the reviewers' feedback.

Sincerely,

[Corresponding Author Name], on behalf of all authors
[Affiliation] · [Email] · [ORCID]
