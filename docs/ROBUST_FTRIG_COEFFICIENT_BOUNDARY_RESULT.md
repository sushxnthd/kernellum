# Robust FTrig coefficient-boundary result

## Decision

**Kill the coefficient-radius diagnostic as a catastrophic-tail selector.** It
is sound but does not predict realized solver failure in the frozen regime.
The exact common uncertainty envelope is extremely narrow, while every sampled
point instance on both sides remains individually certifiable and safe.

## Exact boundary

Independent relative intervals were placed on all six factor coefficients.
Exact rational propagation certified all 42 fixed radius-`1/200` boxes through
`rho = 2^-19 = 1.9073486328125e-6`. At the next larger dyadic radius,
`rho = 2^-18`, only 18 boxes certify. The minimum signed obligation changes
from `+0.8480577674` to `-295.6405462384`.

A separate 110-digit directed-rounding Decimal implementation reproduced the
full 21-point dyadic sweep: 42 boxes first appear at `2^-19`, while `2^-18`
has 18. The primary and independent implementations share neither interval
class nor polynomial code.

## Frozen prospective falsification

Forty-eight exact-rational coefficient vectors were drawn before local solves:
16 each at `0.5*rho_pass`, `rho_pass`, and `2*rho_pass`.

| Endpoint | Result |
|---|---:|
| Point certificates passing | 48/48 |
| Unconditional root-route catastrophes | 0/48 |
| Fail-closed route catastrophes | 0/48 |
| Safe-route retention | 100% |
| Root-route evaluations | 10,148 |
| Fail-closed evaluations | 10,148 |
| Grid catastrophes | 48/48 |
| Optimized-LHS catastrophes | 48/48 |
| Greedy-maximin catastrophes | 48/48 |

The certificate is sound: there were zero false accepts. But the frozen gate
required fewer catastrophes than unconditional reuse. Both policies had zero,
so `catastrophe_reduction` failed. The preregistered kernel is therefore killed
rather than rescued by redefining success as non-inferiority.

## Mechanism diagnosis

The common interval envelope treats every repeated coefficient occurrence as
able to vary independently inside the expression. Its collapse at `2^-18`
does not mark a basin transition: every realized point draw at that amplitude
still certified all 42 boxes independently. This is the classical dependency
and wrapping limitation of natural interval extensions, expressed here as an
operational selection failure. It is a conservative robustness certificate,
not a predictive instability diagnostic.

## Independent checks and reproducibility

- Independent audit: 9/9 checks.
- All 48 point certificates independently reproduced as 42/42.
- Duplicate generation is byte-identical.
- The failed `catastrophe_reduction` gate is retained in the canonical result.

## Priority boundary

Interval dependency/wrapping and validated solution of uncertain nonlinear
systems are established. FTrig and the 42-box certificate are also prior work
within this repository. No novelty is claimed for those ingredients. The
smallest supported result is a decisive negative systems finding: a scalar
worst-case coefficient radius cannot serve as KERNELLUM's prospective
catastrophic-tail selector on this family, because its boundary is unrelated
to the observed route-safety boundary.

Relevant prior foundations include constrained interval arithmetic's treatment
of dependency, correlated interval propagation, and validated interval methods
for uncertain nonlinear systems.

## Limits and next kernel

- One constructed two-dimensional residual family and perturbations only up to
  `2*rho_pass`.
- No claim that failures cannot occur at larger drift.
- The point sweep tests fixed boxes and fixed starts; learned/noisy coefficients
  remain outside scope.
- Internal independent reproduction is not third-party replication.

The replacement positive kernel is **certificate transport to an unrelated
coupled factor-structured residual family**, with starts derived before outcomes
and the same equal-budget controls. Repeated refinement of FTrig uncertainty
envelopes is prohibited unless it yields a prospective win/loss prediction.

