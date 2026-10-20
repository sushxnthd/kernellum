# Profile-critical-root external transfer result

## Decision

**Kill the claimed basin-coverage advantage.** The structural certificate
transferred to the classical Freudenstein--Roth problem, but the strongest
matched simple control recovered the same two basins in every regime. The
precommitted failure gate therefore fires without threshold changes.

## Frozen result

The shared-affine-variable diagnostic eliminated `x`, enumerated the real roots
of the derivative of the resulting univariate profile, rejected negative
profile curvature, and emitted exactly two candidates before local-solver
outcomes were observed.

| Equal two-start method | Trials | Both minima | Catastrophes | Mean coverage | Mean evaluations |
|---|---:|---:|---:|---:|---:|
| Profile critical roots | 9 | 9 | 0 | 100.0% | 22.67 |
| Fixed maximin corners | 9 | 9 | 0 | 100.0% | 40.33 |
| Latin hypercube | 576 | 368 | 208 | 81.9% | 51.65 |
| Uniform random | 576 | 249 | 327 | 71.6% | 52.28 |

The structured starts retained the zero-residual global solution in 9/9
regimes and both candidates had independently positive-definite Hessians. But
the maximin control also retained the global solution and both basins in 9/9,
so the structure did not reduce catastrophic coverage tails against the
strongest simple baseline. Its 43.8% evaluation reduction is useful but does
not satisfy the parent mechanism claim.

The identity benchmark and eight fixed affine coordinate metamorphs were used.
The latter test coordinate robustness, not independent scientific systems.

## SCIENCE ledger

**Supported:** exact conditional elimination plus univariate critical-root
classification is a sufficient two-start certificate for both strict minima
of Freudenstein--Roth. It transfers a structural-start capability beyond the
FTrig factor lattice and reduces local-solver work.

**Falsified:** on this external system the certificate does not uniquely solve
the basin-coverage problem. A fixed domain-corner maximin design is equally
reliable at the same start budget. The FTrig coverage advantage therefore does
not yet generalize.

**Priority boundary:** eliminating linear parameters is classical variable
projection, originating with Golub and Pereyra (1973), and Freudenstein--Roth
is a classical test problem catalogued by More, Garbow, and Hillstrom (1981).
No novelty is claimed for either ingredient or for polynomial root
enumeration.

## CONSEQUENCE ledger

Do not promote profile-root synthesis as KERNELLUM's positive flagship
coverage mechanism. It may be retained as a certified efficiency optimization
inside a solver portfolio, but the active positive search must move to a
higher-basin external problem where a matched space-filling/maximin design
cannot trivially span all basins.

The next external gate must require at least four documented minima and compare
against optimized maximin starts, not only random, LHS, or an axis grid.

## Reproducibility and limitations

- Protocol commit precedes the result artifact.
- The runner uses 1,170 frozen trials and 2,340 local solves.
- The independent checker re-evaluates both candidate Hessians without
  importing the runner and audits the precommitted kill condition.
- The first local focused-test collection failed because the dynamic test
  loader did not register its module before evaluating a `dataclass`; the
  harness was corrected without changing the protocol, runner, raw result, or
  scientific gate.
- An initial isolated-environment full-suite invocation omitted the repository
  root from `PYTHONPATH` and failed collection for legacy `scripts` and
  `experiments` imports. This environment-only failure is preserved here; the
  corrected full-suite command sets `PYTHONPATH=.` and changes no science.
- Results concern a two-dimensional polynomial benchmark; they do not imply
  behavior under noise, approximate separability, high dimension, or model
  selection.

## Primary references

- J. J. More, B. S. Garbow, and K. E. Hillstrom, “Testing Unconstrained
  Optimization Software,” *ACM TOMS* 7(1), 1981. DOI: 10.1145/355934.355936.
- G. H. Golub and V. Pereyra, “The Differentiation of Pseudo-Inverses and
  Nonlinear Least Squares Problems Whose Variables Separate,” *SIAM J. Numer.
  Anal.* 10(2), 1973. DOI: 10.1137/0710036.
