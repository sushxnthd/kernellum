# Basin-transition continuation: prospective result

## Decision

**PROMISING BUT NOT A FROZEN-GATE PASS.** Keep the mechanism active for one
larger, untouched confirmatory cohort. Do not tune thresholds on these opened
paths.

The frozen selector passed six of seven scientific gates. It failed only
`halves_one_domain_catastrophes`, because the protocol required at least two
candidate catastrophes in a domain and this cohort contained only one. The
selector eliminated that one catastrophe, but the predeclared count condition
correctly prevents calling the complete gate passed.

## Frozen result

- 16/16 untouched paths completed.
- 4 routes fired.
- Route precision: 3/4 = 0.75.
- Far-shell geometric NMSE: 3.5778 candidate, 2.1139 selected; ratio **0.5908**.
- Inside geometric NMSE: 0.5169 candidate, 0.4285 selected; ratio **0.8290**.
- Near-shell geometric NMSE: 1.1204 candidate, 0.8095 selected; ratio **0.7225**.
- Catastrophes: far shell 1 -> 0; inside and near shell 0 -> 0.
- Duplicate executions were byte-identical.
- Independent audit: **PASS**, 503 checks, 0 failures.

Result canonical SHA-256:
`fee774eb7b02c5db35940a4b5f148037dda165238e076329ca8aeeb15475ad3c`

Audit canonical SHA-256:
`d243a914df9725fc5af72b3d34d0857d48af3bf6e5e3d9568c60563500176eb3`

## Gate table

| Frozen gate | Outcome |
|---|---:|
| Complete cohort | PASS |
| At least two routes | PASS (4) |
| No excess catastrophe | PASS |
| Halve catastrophes where candidate count >=2 | **FAIL: only one candidate catastrophe existed** |
| Inside noninferiority <=1.05 | PASS (0.8290) |
| Far improvement <=0.90 | PASS (0.5908) |
| Route precision >=0.75 | PASS (0.75) |

## Routed-path audit

| Path | Candidate far log-NMSE | Selected far log-NMSE | Better? |
|---|---:|---:|---:|
| oscillatory_cauchy, d=8, seed=8123, leverage | 1.0187 | 1.1977 | no |
| warped_laplace, d=4, seed=8129, symmetric-t | 6.9861 | -0.6015 | yes; catastrophe removed |
| warped_laplace, d=8, seed=8123, leverage | 1.5236 | 1.4765 | yes |
| warped_laplace, d=8, seed=8129, leverage | 1.6369 | 0.6732 | yes |

## SCIENCE ledger

Smallest supported claim:

> On a frozen 16-path, two-family prospective cohort, a truth-blind diagnostic
> based on repeated early continuation transitions routed 4 cases to an
> existing globalized solver, improved 3 of 4 routed far-shell outcomes,
> reduced aggregate far-shell geometric NMSE by 40.9%, and introduced no
> catastrophes. The predeclared overall success gate nevertheless failed
> because only one baseline catastrophe was available for the required
> halving test.

This is evidence for predictive signal, not yet a flagship law. The result does
not establish calibration, generality beyond the two synthetic families, or
historical novelty.

## Mechanism interpretation

The earlier static-consensus mechanisms produced no interventions. The
continuation diagnostic is nonvacuous because it detects *where a fitted branch
changes under increasing controlled perturbation*, rather than demanding a
distant stable endpoint cloud. Three of four early-transition signatures
correctly identified cases where globalization improved extrapolation.

The strongest surviving alternative is family confounding: three routed wins
occurred in `warped_laplace`, and the sole routed loss occurred in
`oscillatory_cauchy`. A new confirmatory cohort must therefore balance
additional unseen families and test family-stratified calibration.

## CONSEQUENCE ledger

- Do not deploy yet.
- Preserve thresholds unchanged.
- Advance this kernel to exactly one confirmatory test with more independent
  families and enough paths to make catastrophic-tail reduction measurable.
- Require family-stratified route precision plus the existing aggregate safety
  gates.
- Kill if the prospective advantage collapses outside `warped_laplace`.

## Prior-art boundary

Continuation/path-following, stability selection, and nonconvex homotopy
optimization are established. The potentially new object is the specific
pre-outcome transition-amplitude diagnostic as a routing signal for
solver-dependent model-selection tails. That priority claim remains unmade
until confirmatory evidence and a deeper literature audit are complete.
