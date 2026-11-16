export const meta = {
  name: 'ten-reviewer-adversarial',
  description: 'Ten independent adversarial reviewers critique the manuscript+code, each a distinct JCIM-reviewer perspective; verify and consolidate findings.',
  phases: [
    { title: 'Review', detail: 'ten independent reviewer perspectives' },
    { title: 'Verify', detail: 'adversarially check each major/fatal finding against the code and results' },
  ],
}

const MS = 'Target_Journal_Submission/manuscript/manuscript.md'
const CODE = 'Target_Journal_Submission/code'
const RESULTS = 'Target_Journal_Submission/code/results'

const COMMON = `You are an expert, adversarial-but-fair peer reviewer for the Journal of Chemical Information and Modeling (JCIM, ACS).
The manuscript is at ${MS}. Its code is at ${CODE}/ (src/, experiments/, run_all.py), machine-readable results at ${RESULTS}/ (raw_results.csv, metrics.json, statistics.json, leakage_audit.json), tables at Target_Journal_Submission/tables/, figures at Target_Journal_Submission/figures/, verified references at Target_Journal_Submission/supplementary/literature/verified_references.json.
READ the manuscript and the specific files your role targets. Check claims AGAINST the code and result files — do not trust prose alone. The paper's thesis: standard/weighted conformal under-cover out-of-domain compounds under chemical covariate shift; naive high-dim fingerprint weighting degenerates; AD-axis methods (ADR-CP, ADE-CP) restore conditional coverage in the recoverable regime (esp. temporal); a discriminator-AUC diagnostic predicts the regime; under severe shift nothing deployable works (honest negative).
Be genuinely critical: try to find NEW, specific, defensible problems. Do not invent problems to hit a count. For each finding give: severity (FATAL|MAJOR|MODERATE|MINOR), the exact location/claim, why it is wrong or unsupported, and a concrete fix (and whether it needs a new experiment). End with a recommendation: ACCEPT | MINOR_REVISION | MAJOR_REVISION | REJECT.`

const ROLES = [
  { key: 'novelty',     prompt: `ROLE: Novelty & prior-art reviewer. Focus: is the contribution genuinely distinct from CoDrug (2023), Tibshirani weighted CP, Guo (2027), Hosni, Harris, Klarner? Search for closer prior art. Is ADR-CP/ADE-CP's novelty overstated? Is the "negative result" already known?` },
  { key: 'methodology', prompt: `ROLE: Methodology reviewer. Focus: mathematical correctness of weighted conformal, CQR-style ADE-CP validity, the 1-D density-ratio, clipping/capping, the saturation handling. Are the guarantees stated correctly? Any incorrect claim of validity under shift?` },
  { key: 'experimental', prompt: `ROLE: Experimental-design reviewer. Focus: fairness of baselines, hyperparameters, calibration sizes, number of splits, whether comparisons are apples-to-apples, whether the primary metric (worst-stratum coverage) can be gamed by saturation (check the saturated_fraction handling).` },
  { key: 'statistics',  prompt: `ROLE: Statistical reviewer. Focus: paired Wilcoxon + Holm correctness, unit of analysis, multiple-comparison family, bootstrap CIs, effect sizes, whether significance claims match statistics.json, seed handling, whether 20 seeds / 5 temporal draws suffice.` },
  { key: 'leakage',     prompt: `ROLE: Dataset & leakage reviewer. Focus: InChIKey dedup, scaffold-disjointness, temporal monotonicity, that the unlabeled pool uses no labels, AD to train only. Verify leakage_audit.json and the code actually enforce these. Any contamination between calibration and test?` },
  { key: 'robustness',  prompt: `ROLE: Robustness & generalization reviewer. Try to invalidate the central claim: do the temporal wins generalize (only 2 targets)? Is the scaffold "impossibility" an artifact of tiny datasets (FreeSolv n=642)? Does the diagnostic law hold within-dataset (the sweep) as well as across?` },
  { key: 'efficiency',  prompt: `ROLE: Computational-efficiency reviewer. Focus: is the width cost of ADR-CP/ADE-CP justified? Are the methods actually cheap as claimed? Is the efficiency (width, effective sample size, saturation) honestly reported alongside coverage?` },
  { key: 'citations',   prompt: `ROLE: Literature & citation reviewer. Verify every citation in the manuscript resolves to verified_references.json with correct venue/year (note: Hosni is ACS Omega, not JCIM). Flag any claim attributed to a paper that the paper may not support, and any missing key competing work.` },
  { key: 'editor',      prompt: `ROLE: JCIM Associate Editor. Evaluate scope fit, novelty sufficiency for JCIM, clarity, completeness, reproducibility, author-guideline compliance (Data & Software Availability, ACS format), and overall reviewer risk. Would this survive peer review here?` },
  { key: 'hostile',     prompt: `ROLE: Hostile competing researcher. Try to show the work is incremental, that a simpler method (e.g., just Mondrian, or just widening intervals) matches it, that the improvement is a saturation/width artifact, or that the baseline comparison is unfair. Find the single most damaging valid criticism.` },
  { key: 'writing',     prompt: `ROLE: Scientific-writing & consistency reviewer. Focus: unsupported or over-strong claims, number/consistency between abstract, results text, tables and figures, undefined terms, logical gaps, and whether limitations are honestly stated. Check that every number in the text matches the tables.` },
]

const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    role: { type: 'string' },
    recommendation: { type: 'string', enum: ['ACCEPT', 'MINOR_REVISION', 'MAJOR_REVISION', 'REJECT'] },
    summary: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['FATAL', 'MAJOR', 'MODERATE', 'MINOR'] },
          location: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
          needs_experiment: { type: 'boolean' },
        },
        required: ['severity', 'problem', 'fix'],
      },
    },
  },
  required: ['role', 'recommendation', 'findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['CONFIRMED', 'PARTIAL', 'REFUTED'] },
    reasoning: { type: 'string' },
    recommended_action: { type: 'string' },
  },
  required: ['verdict', 'reasoning'],
}

phase('Review')
const reviews = await parallel(ROLES.map(r => () =>
  agent(`${COMMON}\n\n${r.prompt}`, { label: `review:${r.key}`, phase: 'Review', schema: FINDING_SCHEMA })
))

const valid = reviews.filter(Boolean)
// collect MAJOR/FATAL findings for adversarial verification
const major = []
for (const rv of valid) for (const f of (rv.findings || []))
  if (f.severity === 'FATAL' || f.severity === 'MAJOR') major.push({ ...f, role: rv.role })

phase('Verify')
const verified = await parallel(major.map(f => () =>
  agent(`${COMMON}\n\nA reviewer (${f.role}) raised this ${f.severity} issue:\nPROBLEM: ${f.problem}\nPROPOSED FIX: ${f.fix}\n\nAdversarially verify it AGAINST the code and result files. Is it real, and is the severity right? Default to REFUTED if the manuscript or code already addresses it.`,
    { label: `verify:${f.role}`, phase: 'Verify', schema: VERDICT_SCHEMA })
    .then(v => ({ ...f, ...v }))
))

const confirmed = verified.filter(Boolean).filter(v => v.verdict === 'CONFIRMED' || v.verdict === 'PARTIAL')
return {
  recommendations: valid.map(r => ({ role: r.role, rec: r.recommendation })),
  n_reviews: valid.length,
  n_major_raised: major.length,
  confirmed_major: confirmed,
  all_reviews: valid,
}
