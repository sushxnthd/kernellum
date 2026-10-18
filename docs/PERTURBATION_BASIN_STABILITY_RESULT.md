# Perturbation-basin selector: prospective result

## Decision

**KILL.** The frozen selector failed its prospective success condition and must not be threshold-tuned on this cohort.

The selector emitted **0 overrides on 16 untouched paths**. Therefore it could neither halve catastrophic tails in either domain nor improve the far-regime tail ratio. The failure is decisive for this fixed conjunction of occupancy, dispersion, separation, and in-sample-fit gates.

## Frozen evidence

- Pull-request workflow: [39118332354](https://github.com/sushxnthd/kernellum/actions/runs/39118332354)
- Artifact: [12134225315](https://github.com/sushxnthd/kernellum/actions/runs/39118332354/artifacts/12134225315)
- Artifact ZIP SHA-256: `f03f5d03f9b12a392d594b5a372421a5f1ca54681ebafdca3dedb5cc0167c4c5`
- Result canonical SHA-256: `395711c42ca8d11405b6387d588f5f2559e4c7fe17888bd2b2ef6729238d0553`
- Independent-audit canonical SHA-256: `71057713ed0117a8c9319bc39f1e665feffbe4f869589a3bea2f88166337cd8e`
- Determinism: two complete evaluations were byte-identical.
- Independent audit: **PASS**, 207 checks, 0 failures.

## Gate table

| Frozen gate | Outcome |
|---|---:|
| Complete cohort | PASS |
| At least 2 overrides | **FAIL (0)** |
| No excess catastrophes | PASS (vacuous: no interventions) |
| Halve catastrophes in one domain | **FAIL** |
| Inside-regime noninferiority, ratio ≤ 1.05 | PASS (1.00) |
| Far-regime improvement, ratio ≤ 0.90 | **FAIL (1.00)** |
| Override precision ≥ 0.75 | **FAIL (undefined operationally; reported 0.00)** |

## Mechanistic falsification

The proposed conjunction does not identify actionable alternative basins on the prospective distribution.

- In low-dimensional paths, the perturbation ensemble was often unanimous or nearly unanimous, but its medoid stayed close to the candidate (distance 0.021–0.070 on the listed tight paths), so the separation gate rejected every intervention.
- In high-dimensional paths, large candidate distance appeared only when cluster occupancy was too low (for example distance 1.235 at occupancy 0.167), while high occupancy generally coincided with negligible distance.
- Several high-dimensional paths also produced extreme full-training residual ratios, correctly blocked by the fit gate.

Thus the failure is not merely “threshold too strict.” The prospective observations expose an antagonism between **consensus** and **actionable separation**: when perturbations agree, they usually agree near the incumbent; when they move far, they fragment or lose fit. That destroys the mechanism's intended operating region.

## SCIENCE ledger

Smallest supported claim:

> On the frozen 16-path two-family prospective cohort, a 12-member controlled-perturbation selector requiring a large tight cluster, material separation from the incumbent, and preserved full-training fit produced zero actionable overrides. Its proposed positive mechanism is falsified on this cohort.

This does **not** show that perturbation stability is universally useless. It rules out this predeclared selector and its claim of prospective tail suppression.

## CONSEQUENCE ledger

- Do not deploy this perturbation-cluster conjunction in Kernellum's evaluator.
- Do not tune its thresholds against these opened paths.
- Preserve the cohort as opened/falsification evidence; it is no longer eligible as a holdout.
- The next active positive-mechanism kernel should model **basin transitions**, not static cluster consensus: a prospective homotopy/continuation diagnostic must predict a solver-family switch before outcome truth and must be evaluated on a new frozen cohort.

## Prior-art boundary

The negative result is consistent with classical distinctions between algorithmic stability and actionable model-selection reliability: stability can control sensitivity without guaranteeing that a stable alternative is better. It also avoids claiming novelty for generic resampling consensus or ensemble disagreement. The publishable object here is only the sharply frozen falsification, not a new general theorem.
