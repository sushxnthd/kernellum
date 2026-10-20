# Four-basin transfer: coverage advantage falsified

## Decision

**Kill the claim that algebraically synthesized starts provide a catastrophic-
basin-coverage advantage over optimized maximin starts.**

The frozen second external transfer used the classical Himmelblau nonlinear
least-squares residual system

\[
r_1(x,y)=x^2+y-11,\qquad r_2(x,y)=x+y^2-7,
\]

whose squared-residual objective has four zero-valued minima. Eliminating the
variable that is affine in `r1` produces

\[
y=11-x^2,\qquad x^4-22x^2+x+114=0.
\]

All four real roots lifted to distinct zero-residual points with nonsingular
residual Jacobians and positive-definite least-squares Hessians. This algebraic
certificate passed, but the claimed coverage advantage did not.

## Frozen outcome

| Equal four-start method | Trials | Full four-basin coverage | Catastrophes | Mean evaluations |
|---|---:|---:|---:|---:|
| Eliminant roots | 9 | 9 | 0 | 5.89 |
| Exact corner maximin | 9 | 9 | 0 | 26.00 |
| Dense-grid greedy maximin | 9 | 9 | 0 | 26.00 |
| Latin hypercube | 576 | 357 | 219 | 26.30 |
| Uniform random | 576 | 36 | 540 | 26.31 |

The structured starts remained complete under the identity system and eight
unopened affine coordinate metamorphs. Both strongest simple controls did too.
The preregistered kill condition therefore fired unchanged:
`KILL_MAXIMIN_MATCHES_COVERAGE`.

Eliminant starts required 77.4% fewer solver evaluations than either maximin
control. That is a useful certified efficiency result, but it is not evidence
of superior catastrophic-tail suppression.

## Adversarial validation

- 1,179 matched trials and 4,716 local solves.
- Four algebraic candidates independently checked for residual zero,
  distinctness, full-rank Jacobian, and positive-definite Hessian.
- Independent audit passed 12/12.
- Duplicate primary executions were byte-identical.
- Focused tests passed 2/2.
- Full Python suite passed 184 tests plus 36 subtests.

## Priority boundary

Himmelblau's function, polynomial substitution/elimination, numerical root
finding, multistart least squares, and maximin space-filling designs are
classical. The benchmark is attributed to Himmelblau's *Applied Nonlinear
Programming* (1972); a later benchmark survey is Jamil and Yang (2013), DOI
`10.1504/IJMMNO.2013.055204`. No mathematical novelty is claimed.

## Smallest supported claim

For the certified Himmelblau residual form, eliminant-root starts recover all
four global minima across nine coordinate regimes with 77.4% fewer local-solver
evaluations than maximin starts. They do **not** reduce basin-coverage failures
relative to either optimized maximin control.

## Project consequence and pivot

Two consecutive external transfers now show the same boundary: algebraic starts
can be substantially cheaper, but low-dimensional maximin designs already
match their complete basin coverage. KERNELLUM must stop treating structural
root synthesis as a general catastrophic-tail mechanism on such benchmarks.

The next KERNELLUM kernel must be deliberately positive: build a fail-closed
certificate-conditioned selector that invokes algebraic elimination only when
its structural certificate holds and test whether it reduces evaluation cost
across a heterogeneous external residual suite without any coverage or
ordinary-performance loss. Coverage superiority is no longer its objective.

## Limitations

- The four classical minima are public; only the affine confirmations and
  solver/control outcomes were prospective.
- The benchmark is two-dimensional and polynomial.
- Exact algebraic candidates start extremely near solutions, so evaluation
  efficiency is an expected consequence rather than a surprising law.
- This is internally reproduced and CI-gated, not third-party replication.
