# Quantitative-premise boundary result

## Decisive result

The refined kernel has a sharp boundary: the smallest Lipschitz constant
compatible with the training transcript is an empirical **lower bound**, not a
prediction certificate. No fixed finite inflation repairs this distinction.

For a finite transcript `T`, let `L_T` be its largest observed secant slope.
Given any fixed multiplier `c` and unobserved request `x*`, an interval computed
with `c L_T` has a finite upper endpoint. Preserve every observed value and set
the request value above that endpoint. This completion is indistinguishable on
`T` and has a larger finite Lipschitz constant on the augmented finite domain.
Thus the proposed interval is unsound unless `L <= c L_T` is itself an external
premise.

Conditional on an independently verified global constant `L`, the exact
pointwise feasible interval is the classical McShane--Whitney interval

`[max_i(y_i-L d(x*,x_i)), min_i(y_i+L d(x*,x_i))]`.

An exhaustive bounded-grid check covered **2,774 transcript/request pairs** and
**27,974 completion checks** through five domain points with zero failures.

## Opened-cohort collision

The fixed screen used all 48 previously opened cells and did not touch a frozen
or external holdout.

| Multiplier of empirical `L_T` | Cells with any miss | Catastrophic cells with any miss | Mean width / training SD |
|---:|---:|---:|---:|
| 1x | 30 / 48 | 4 / 11 | 8.12 |
| 2x | 6 / 48 | 1 / 11 | 17.85 |
| 5x | 0 / 48 | 0 / 11 | 45.61 |
| 10x | 0 / 48 | 0 / 11 | 91.49 |

The strongest alternative fails. The raw empirical constant misses in 30
cells, and even a preregistered 2x inflation misses in six. Fivefold inflation
covers this opened cohort, but its mean width is 45.6 training standard
deviations (83.0 on the far shell), so it is both non-certifying and operationally
weak. Perfect opened coverage is not upgraded into a guarantee.

## Runtime consequence

`kernellum.discovery.quantitative_premise` now separates:

1. `empirical_lipschitz_lower_bound`, explicitly diagnostic only;
2. the exact conditional interval under a supplied global constant; and
3. a fail-closed issuer that rejects `estimated_from_same_transcript` provenance
   even if a caller-provided verifier returns true.

Accepted envelopes require an independently verified premise naming the global
Lipschitz class, request scope, constant, and source, and are hash-bound to that
premise.

## Prior-art and novelty boundary

McShane's 1934 extension theorem and Whitney's 1934 extension work already
establish constant-preserving Lipschitz extension constructions. Modern work
still refers to this as the classical McShane--Whitney theorem. Therefore the
conditional interval is **not claimed as historically novel**. Primary/near-primary
references audited:

- E. J. McShane, *Extension of range of functions*, Bull. AMS 40 (1934),
  837--842.
- H. Whitney, *Analytic extensions of differentiable functions defined in
  closed sets*, Trans. AMS 36 (1934), 63--89:
  https://www.math.ucdavis.edu/~saito/data/high-dimensions/whitney2.pdf
- V. Gutev, *Extension of Lipschitz Functions Revisited* (2024), which explicitly
  characterizes the result as classical: https://arxiv.org/abs/2411.17825

The defensible Kernellum contribution is narrower: an exact provenance boundary,
a matched empirical collision, an independently audited finite sharpness check,
and a production-facing refusal contract specialized to solver/model-selection
diagnostics.

## Ledgers

### SCIENCE

- Exact fixed-inflation impossibility: pass.
- Finite sharpness audit: 2,774 transcript/request pairs and 27,974 checks, pass.
- Opened diagnostic: 1x misses 30/48 cells; 2x misses 6/48.
- Smallest claim: a transcript-derived constant cannot certify its own unseen
  extrapolation; the sharp interval is valid only under an external quantitative
  premise.

### CONSEQUENCE

- Kill transcript-derived or fixed-inflation Lipschitz envelopes as certificates.
- Treat learned constants as diagnostics only.
- Require externally sourced quantitative limits (physical specification,
  verified simulator bound, or separately validated contract) before emission.
- If no such premise exists, return refusal rather than a numeric safety claim.

## Active kernel after this result

The empirical-premise route is **killed**. The KERNELLUM kernel advances to the
weakest externally sourced quantitative premise that is scientifically credible
and produces a non-vacuous interval on a prospective untouched cohort. A premise
that merely scales `L_T` is excluded regardless of development coverage.

## Limitations

The cohort is opened synthetic development evidence involving two families,
two dimensions, two seeds, two noise laws, and three domains. The exact
impossibility concerns deterministic certification from the same finite
transcript; it does not rule out probabilistic coverage under explicit sampling
assumptions or separately validated learned bounds.
