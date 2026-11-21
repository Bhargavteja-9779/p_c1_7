## 3. Method: Applicability-Domain Conditional Conformal Prediction (ADCC-CP)

### 3.1 Setting and the applicability-domain coordinate

A regressor $\hat f$ is trained on a training set $\mathcal D_{\rm tr}$. A labeled calibration set $\{(X_i,Y_i)\}_{i=1}^n$, independent of $\mathcal D_{\rm tr}$, is drawn from a law $P$, and predictions are required for an unlabeled deployment pool drawn from $P_{\rm test}$ with $P_{\rm test}(y\mid x)=P(y\mid x)$ (covariate shift). Nonconformity scores are absolute residuals $S_i=|Y_i-\hat f(X_i)|$. For a compound $x$ we use the applicability-domain (AD) coordinate $a(x)=\max_{x'\in\mathcal D_{\rm tr}}T(x,x')$, the maximum Tanimoto similarity of its ECFP4 fingerprint to the training set (low $a$ = structurally novel). Because $a$ is computed against the training set only, it is a fixed function once $\hat f$ is trained.

### 3.2 The estimator

Let $\kappa_1<\dots<\kappa_{K-1}$ be AD knots (here the calibration quartiles of $a$, $K=4$) and define the feature map
$$\phi(x)=\big(1,\ a(x),\ (a(x)-\kappa_1)_+,\ \dots,\ (a(x)-\kappa_{K-1})_+\big)\in\mathbb R^{d},\qquad d=K+1,$$
so that $\mathcal F_{\rm AD}=\{x\mapsto\phi(x)^\top\beta:\beta\in\mathbb R^d\}$ is the class of all continuous piecewise-linear functions of the AD coordinate with breakpoints at the knots. With $\tau=1-\alpha$ and the pinball loss $\rho_\tau(u)=u(\tau-\mathbb 1\{u<0\})$,³⁵ define for a test compound $x$ and an imputed score $s$ the *augmented* quantile regression
$$\hat\beta_s\in\arg\min_{\beta}\ \sum_{i=1}^{n}\rho_\tau\!\big(S_i-\phi(X_i)^\top\beta\big)+\rho_\tau\!\big(s-\phi(x)^\top\beta\big).$$
ADCC-CP outputs the interval $\hat C(x)=[\hat f(x)-\hat s(x),\ \hat f(x)+\hat s(x)]$ with
$$\hat s(x)=\sup\{s\ge 0:\ s\le\phi(x)^\top\hat\beta_s\},$$
i.e. the largest test score that the augmented $(1-\alpha)$-quantile regression would still place on or below its fitted quantile. This is the function-class conditional conformal construction of Gibbs, Cherian and Candès,³⁴ instantiated on an applicability-domain class; the choice of $\mathcal F_{\rm AD}$, its interpretation as a family of chemical-space shifts, and its evaluation under molecular temporal shift are the contributions here. No density ratio is estimated at any point.

### 3.3 Guarantees

> **Theorem 1 (simultaneous AD-shift coverage).** Suppose $(X_i,Y_i)_{i=1}^{n+1}$ are i.i.d. from $P$ and $\mathcal F_{\rm AD}$ is fixed given $\mathcal D_{\rm tr}$. Then for every $f\in\mathcal F_{\rm AD}$ with $f\ge 0$ and $\mathbb E_P f(X)>0$,
> $$\Pr_{P_f}\!\big(Y_{n+1}\in\hat C(X_{n+1})\big)\ \ge\ 1-\alpha,\qquad \text{where } \frac{{\rm d}P_f}{{\rm d}P}(x,y)=\frac{f(x)}{\mathbb E_P f(X)}.$$
> *Proof.* Gibbs et al.³⁴ (Theorem 2) show $\mathbb E_P[f(X_{n+1})(\mathbb 1\{Y_{n+1}\in\hat C(X_{n+1})\}-(1-\alpha))]\ge 0$ for every non-negative $f$ in a finite-dimensional class; dividing by $\mathbb E_Pf$ gives coverage under the tilted law $P_f$, which is a covariate shift because $f$ depends on $x$ only. $\square$

Theorem 1 holds **simultaneously for all non-negative members of $\mathcal F_{\rm AD}$**, which yields three chemically meaningful statements from one interval:

1. **Marginal validity** ($f\equiv 1$), as for split conformal.
2. **Localized AD coverage.** Each "hat" function $h_k(a)$ — piecewise-linear, equal to 1 at knot $\kappa_k$ and 0 at the neighbouring knots — belongs to $\mathcal F_{\rm AD}$. Coverage therefore holds on average over compounds *near every similarity level* $\kappa_k$, including the most out-of-domain level: a soft version of AD-stratified (Mondrian) coverage that does not fragment the calibration set.
3. **Coverage under AD-aligned covariate shift, without estimation.** If the deployment pool differs from calibration through a density ratio that is a non-negative continuous piecewise-linear function of $a(x)$ — e.g. the pool is enriched for novel chemistry at any rate — then coverage on the pool is $\ge 1-\alpha$, *whatever* that ratio is. Weighted conformal (ADR-CP, MW-CP, KMM- or CoDrug-style) must estimate the ratio and is valid only if the estimate is correct.

> **Proposition 2 (graceful degradation under misspecified shift).** Let the deployment pool satisfy $P_{\rm test}(y\mid x)=P(y\mid x)$ with an *arbitrary* density ratio $w={\rm d}P_{\rm test}/{\rm d}P$. Then
> $$\Pr_{P_{\rm test}}\big(Y\in\hat C(X)\big)\ \ge\ 1-\alpha-\delta_{\mathcal F},\qquad \delta_{\mathcal F}=\tfrac12\inf_{f\in\mathcal F_{\rm AD},\,f\ge0,\,\mathbb E_Pf=1}\mathbb E_P|w(X)-f(X)|.$$
> *Proof.* Let $c(x,y)=\mathbb 1\{y\in\hat C(x)\}$. For any admissible $f$, $\mathbb E_P[wc]=\mathbb E_P[fc]+\mathbb E_P[(w-f)c]\ge(1-\alpha)-\mathbb E_P[(f-w)_+]$ by Theorem 1, and $\mathbb E_P[(f-w)_+]=\tfrac12\mathbb E_P|w-f|$ because $\mathbb E_Pw=\mathbb E_Pf=1$. Take the infimum. $\square$

Proposition 2 makes precise *when* an AD-only correction suffices: the shortfall is at most the total-variation distance between the true shift and its best AD-piecewise-linear approximation. Because constants belong to $\mathcal F_{\rm AD}$, $\delta_{\mathcal F}\le\delta_0=\tfrac12\mathbb E_P|w-1|$ — the corresponding bound for split conformal — so ADCC-CP's worst-case guarantee is never weaker than that of standard conformal prediction, and strictly stronger whenever any part of the shift is aligned with the AD axis. Exact pointwise conditional coverage remains impossible distribution-free;¹⁶ Theorem 1 replaces it with the strongest finite-dimensional surrogate that is attainable.

**Over-coverage.** The same construction cannot be arbitrarily conservative: Gibbs et al. bound the excess coverage under each $P_f$ by $O(d/n)$,³⁴ which is small here ($d=5$, $n\approx 200$–$500$). Test compounds whose AD value lies outside the calibration range can receive very wide (or unbounded, then clipped) intervals because their feature vector has high leverage; we report this saturated fraction for every method.

**Remark (knots).** Theorem 1 requires $\mathcal F_{\rm AD}$ to be fixed independently of the calibration data. We place knots at calibration quantiles of $a$, a mild covariate-only dependence; the exchangeable random-split controls (Section 5.1) show no detectable loss of validity, and knots fixed in advance (e.g. Tanimoto 0.3/0.4/0.5) or taken from an independent split remove the dependence entirely.

### 3.4 Computation

Following Gibbs et al.,³⁴ membership $s\le\phi(x)^\top\hat\beta_s$ is decided from the dual of the augmented quantile regression,
$$\max_{\eta\in\mathbb R^{n+1}}\ \sum_{i=1}^{n}\eta_iS_i+\eta_{n+1}s\quad\text{s.t.}\quad \sum_{i=1}^{n+1}\eta_i\phi(X_i)=0,\ \ \eta_i\in[-\alpha,\,1-\alpha],$$
with $X_{n+1}=x$: the test point is covered iff $\eta_{n+1}<1-\alpha$, and $\eta_{n+1}$ is non-decreasing in $s$. We therefore find $\hat s(x)$ by bisection over $s$, each step one small linear program ($n+1$ variables, $d$ constraints; HiGHS). Because $\phi$ depends on $x$ only through $a(x)$, rounded to 0.01, **$\hat s$ is a function of a single number and at most 101 thresholds are needed per calibration set, independent of the size of the screening library**; the result is an *AD calibration curve* $a\mapsto\hat s(a)$ that can be tabulated once and applied to ultra-large libraries by lookup (Figure 4). A full run (all thresholds) takes seconds to a few minutes on one CPU core.

**Algorithm 1 (ADCC-CP).** *Input:* calibration scores $S_{1:n}$, AD values $a_{1:n}$, level $1-\alpha$, test AD value $a$. (1) Knots $\kappa$ = calibration quartiles of $a$; build $\phi$. (2) Bracket $[0,\,2\max_iS_i]$; if $\eta_{n+1}(2\max S)<1-\alpha$, return $+\infty$. (3) Bisect on $s$ until the bracket is below tolerance, testing $\eta_{n+1}(s)<1-\alpha$ by the dual LP. (4) Return $\hat f(x)\pm\hat s$. Cache by rounded $a$.

### 3.5 Variants, baselines and their relation to ADCC-CP

The function class is the only design choice. We pre-specified four classes (Section 4.2): **indicator** (AD-stratum indicators — this recovers Mondrian-AD conformal as a special case of the same framework), **piecewise-linear** (indicators plus a within-stratum linear tilt; $d=8$), the **continuous linear spline** (primary; $d=5$), and the spline with a **normalized score** $|r|/\hat\sigma(x)$ (local difficulty from the $k$ nearest training neighbours). Baselines are split conformal;² normalized conformal;⁵,⁶ Mondrian-AD conformal;³ ADR-CP — weighted conformal¹³ with an *estimated* one-dimensional density ratio along $a$ (logistic, calibration-vs-pool), the strongest method in our earlier benchmark; MW-CP — within-stratum estimated weights; and KMM-weighted conformal following KMM-CP²⁹ (kernel mean matching on PCA-reduced fingerprints). ADR-CP and MW-CP target the same AD-aligned shifts as ADCC-CP but *estimate* the ratio and plug it in as importance weights; ADCC-CP instead enforces coverage for every ratio in the class at once.
