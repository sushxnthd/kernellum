# Frozen NIST StRD safety-constrained multistart protocol

## Active KERNELLUM kernel

- **Question:** On an external nonlinear least-squares benchmark, can disagreement between the two NIST-supplied starting fits prospectively identify solver-basin risk, and can a safety-constrained multistart intervention reduce certified-solution failures without worsening ordinary cases?
- **Frontier:** Multistart, trust-region least squares, residual-based selection, and NIST StRD solver benchmarking are established. The research question is the prospective diagnostic-to-intervention bridge and its direct system gate, not novelty of these ingredients.
- **Objective:** reduce certified-parameter failures on a frozen, unopened NIST confirmation set while never accepting a fit with worse residual sum of squares or non-finite/out-of-envelope predictions.
- **Strongest alternative:** any gain is generic multistart benefit; the disagreement diagnostic has no predictive value.
- **Cheapest falsification:** the fixed diagnostic routes no confirmation problem, has precision below 75%, or the intervention fails to remove at least half of routed certified failures.
- **Project consequence threshold:** a passing rule becomes a fail-safe in Kernellum's nonlinear discovery evaluator; a failure kills start-disagreement routing.

## Provenance and split

Source is the NIST Statistical Reference Datasets mirror pinned at lmfit/lmfit-py commit `e270500e3efb4ff9cce91416b3f55678d6271811`. Dataset files retain NIST descriptions, formulas, supplied starts, certified parameters, and certified residual sums of squares.

Development files (may set no thresholds): `Misra1a`, `Misra1b`, `Misra1c`, `Rat43`, `Lanczos1`, `Lanczos3`, `MGH09`, `MGH10`.

**Unopened confirmation files frozen now:** `Lanczos2`, `MGH17`, `Misra1d`, `Rat42`. These files must not be fetched or inspected until implementation and all decision rules are committed.

## Fixed solvers

All fits use `scipy.optimize.least_squares`, `method="trf"`, numerical Jacobian, identical tolerances and evaluation budget.

1. incumbent: NIST Start 1;
2. start-2 control: NIST Start 2;
3. two-start control: lower-RSS result of Starts 1 and 2;
4. intervention: Starts 1 and 2 plus 32 seed-bound multiplicative/additive perturbations, selecting the lowest-RSS safe fit.

A fit is safe only if parameters and residuals are finite and its predictions on observed x lie within `[min(y)-2*range(y), max(y)+2*range(y)]`. The intervention may override the incumbent only when safe and its RSS is lower by at least `1e-10` relative. The incumbent is included, so accepted training RSS cannot worsen.

## Frozen prospective diagnostic

Before reading certified parameters, compute the two supplied-start fits. Route iff either fit fails, or

`D = max_i |theta1_i-theta2_i| / max(1, |theta1_i|, |theta2_i|) > 0.25`.

Prediction: routed cases contain certified-parameter failures disproportionately; the constrained intervention removes at least half of those failures. No threshold may be tuned.

A certified-parameter failure is maximum componentwise relative error above `1e-3`, using denominator `max(1, |theta_cert|)`.

## Confirmation gates

All four confirmation files must complete.

1. at least one and at most three cases route;
2. routed diagnostic precision at least 75%;
3. intervention removes at least half of routed incumbent failures;
4. no intervention case has worse RSS than incumbent;
5. no non-routed case is modified;
6. maximum certified-parameter error across intervention outputs is no worse than incumbent;
7. independent checker reproduces routing, selections, metrics, and file hashes;
8. duplicate execution is byte-identical.

Passing supports only this pinned NIST family and direct safety rule. It is not evidence of global optimality, all nonlinear least-squares tasks, or external independent reproduction.
