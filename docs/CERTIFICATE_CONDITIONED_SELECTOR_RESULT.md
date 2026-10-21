# Certificate-conditioned selector: fleet-level savings gate falsified

## Decision

**Kill the claim that the current fail-closed structural-start selector provides
a material aggregate evaluation reduction across a heterogeneous residual
portfolio.**

The selector behaved safely: it activated only on the two polynomial families
with machine-checkable completeness certificates, abstained on FTrig, and
introduced zero basin-coverage or best-objective losses. But the expensive
FTrig fallback dominated total cost, leaving only a **7.87%** aggregate
evaluation reduction, far below the frozen 25% gate and the predicted 35%.

## Frozen prospective outcome

| External family | Route | Trials | Selector evaluations | Baseline evaluations | Reduction |
|---|---|---:|---:|---:|---:|
| Freudenstein--Roth | profile-complete | 12 | 259 | 488 | 46.93% |
| Himmelblau | zero-set-complete | 12 | 68 | 312 | 78.21% |
| FTrig | fail-closed fallback | 12 | 5,213 | 5,213 | 0% |
| **Aggregate** | mixed | **36** | **5,540** | **6,013** | **7.87%** |

Across the 12 previously unopened affine transforms per family, the selector
had zero coverage losses and zero best-objective losses against always-maximin.
The frozen scientific gate is `KILL_AGGREGATE_SAVINGS`.

## Mechanism diagnosis

Certificate conditioning prevents unsupported structural extrapolation, but
abstention is not free. The single uncertified 42-start FTrig family accounted
for 86.7% of baseline evaluations. Large within-family savings on both eligible
systems therefore could not create a portfolio-level win. This is a useful
boundary: a safe router becomes consequential only if certificate coverage is
high on the workloads that dominate cost, not merely if conditional savings
are large.

## Adversarial checks

- 36 prospective transformed problems; 1,008 local solves across selector and
  matched baselines.
- Routing used residual algebra only, before any local-solver outcome.
- Freudenstein--Roth enumerated all five complex/real critical roots and retained
  both real positive-curvature profile minima.
- Himmelblau enumerated all four real eliminant roots and checked zero residual,
  distinctness, and nonsingular Jacobians.
- FTrig correctly failed the zero-residual completeness certificate and used
  the frozen grid fallback.
- Duplicate generation was byte-identical; an independent artifact audit
  recomputed routes, losses, totals, reduction, digest, and the failed gate.

### Preserved checker correction

The first execution incorrectly required every Freudenstein--Roth critical root
to be real, rather than enumerating every real root as specified in the frozen
protocol. That implementation defect produced `KILL_ROUTE_MISMATCH`. The check
was corrected literally, without changing data, routes, transforms, thresholds,
or outcomes. The corrected run then exposed the actual preregistered failure:
insufficient aggregate savings.

## Priority boundary

Freudenstein--Roth, Himmelblau, FTrig, variable/profile elimination, polynomial
root enumeration, multistart least squares, maximin designs, and selective
algorithm portfolios are established. No novelty is claimed for those pieces.
The supported result is the negative KERNELLUM system boundary above.

## Smallest supported claim

On three external residual families and 36 frozen affine transforms, the
certificate-conditioned selector was performance-safe and saved 46.9% and
78.2% evaluations when eligible, but only 7.87% in aggregate because its
uncertified high-cost fallback dominated the portfolio.

## Project consequence and next kernel

Keep the fail-closed routing invariant, but do not ship the current selector as
an efficiency mechanism. The next positive kernel must target certificate
acquisition on the cost-dominant FTrig-like family, or a cheaper fallback with
a coverage certificate. Reweighting families or lowering the 25% gate after
seeing this result is prohibited.

## Limits

- The eligible family landscapes were previously known; only the new affine
  transforms and router-level aggregate were prospective.
- The suite contains three two-dimensional residual systems.
- Affine metamorphs test coordinate robustness, not unrelated landscape
  transfer.
- This is internally reproduced and CI-gated, not third-party replication.
