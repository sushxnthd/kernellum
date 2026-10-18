# Truth-blind adversarial basin-boundary protocol

**Frozen before manifest generation:** 16 October 2026  
**Classification:** prospective mechanism discrimination  
**Action class:** DISCRIMINATION

## Precise question

Can the fixed prediction-envelope certificate (normalized RMS `<= 0.5`,
normalized maximum `<= 4.0`) reject harmful candidate/independent solver
switches when cases are selected prospectively for solver-basin instability,
without using any extrapolation truth in case generation or ranking?

The certificate concerns solver interchangeability on an explicit request set.
It is not a model-correctness certificate.

## Mechanism and competing explanation

**Mechanism:** exact-LOO optimization has discontinuous winner surfaces. Small,
deterministic perturbations of the observed training response can cross those
surfaces. Near a cross-solver CV tie, the lower-CV solver can therefore change
while the two fitted response surfaces separate on requested inputs. If harmful
switches arise through that mechanism, direct prediction disagreement should
reject them.

**Strongest alternative:** CV winner flips are merely benign numerical
relabelings; even deliberately selected boundary cases will not yield harmful
extrapolation switches. If so, the previous zero-opportunity result reflects
rarity or absence of the proposed failure mode, not a weak random factorial.

## Frozen generator

Use four new base instances, Cartesian product of dimensions `3, 5` and seeds
`5101, 5107`. Each instance has:

- a 192-point uniform `[-1,1]^d` pool;
- 24 maximin-selected training inputs;
- an anisotropic signed rational peak with a weak sinusoidal ridge;
- Gaussian training noise fixed at 0.20 times the clean-response standard
  deviation;
- requested inputs fixed before fitting: 192 inside, 192 near-shell
  `(1,1.7]`, and 192 far-shell `(1.7,3.4]`.

For each base, form 97 deterministic response perturbations indexed
`j=-48,...,48`:

[
y_j = y_0 + (j/48)(0.45,s_y) v,
]

where `v` is the normalized, mean-zero first left singular vector of the
centered quadratic feature matrix
`[x_k, x_k x_l (k<=l)]`. Its sign is fixed by requiring its first nonzero
entry to be positive. This direction is derived only from training inputs.

For every perturbation, fit the existing candidate and independent banks over
both signs and both families. Record only training-derived CV values, winner
identity, failures, and predictions at the already-fixed requested inputs.
Extrapolation truth values MUST NOT be evaluated, serialized, logged, or made
available to the selection process.

## Truth-blind selection rule

A perturbation is eligible when the independent solver has lower exact-LOO CV.
For adjacent eligible perturbations, define a boundary event when either
solver's winning sign/family changes or the identity of the lower-CV solver
changes relative to the previous perturbation.

Rank eligible perturbations lexicographically by:

1. boundary event first;
2. smaller normalized CV gap
   `abs(cv_c-cv_i)/max(min(cv_c,cv_i),1e-12)`;
3. larger normalized prediction RMS disagreement;
4. larger normalized prediction maximum disagreement;
5. smaller `abs(j)`;
6. smaller signed `j`;
7. dimension, then seed.

Select the first 24 distinct perturbations, with at most six per base. If fewer
than 24 are eligible, preserve the exact count and classify the generator as
FAIL. The committed manifest must contain training inputs/responses, request
inputs, fitted winner metadata, envelope receipt, and SHA-256 digests, but no
requested-input truth.

## Two-stage integrity rule

1. Run the generator and commit the truth-free manifest.
2. Only in a later commit may an evaluator reconstruct the frozen functions,
   join requested-input truth, and label harm.

A manifest commit that contains requested truth is invalid. Any change to this
protocol, generator, thresholds, ranking, cap, seeds, or perturbation grid after
manifest generation creates a new study and cannot repair this one.

## Preregistered predictions and gates

All gates are required:

1. deterministic generation: two executions produce byte-identical manifests;
2. manifest integrity: exactly 24 selected cases, no truth fields, and all
   recorded features recompute independently;
3. discrimination: at least four selected cases are harmful naive switches,
   where independent is lower-CV and worse than candidate by `> ln(10)` in
   at least one requested domain;
4. safety: every harmful switch is rejected by the unchanged envelope;
5. non-vacuity: at least 8/24 cases are accepted;
6. accepted pointwise safety: no accepted selected output is worse than
   candidate by `> ln(2)` in any domain;
7. accepted aggregate performance: geometric NMSE is at most 1.10 times
   candidate in every domain;
8. independent evaluator reproduces all joins, labels, counts, ratios, and
   gates.

## Publishable success, consequence, and kill conditions

**Success condition:** all gates pass on the committed untouched manifest, a
clean independent evaluation agrees, and prior-art review finds no equivalent
prospective solver-interchangeability receipt.

**Project-relevance threshold:** a pass licenses an experimental Kernellum API
receipt returning acceptance, normalized RMS/max disagreement, chosen solver,
manifest provenance, and the explicit scope
`solver_invariance_not_model_correctness`.

**Kill condition:** any missed harmful switch, accepted degradation gate
failure, integrity failure, or a second truth-blind generator with fewer than
four harmful opportunities kills this pairwise-envelope kernel. Move to
globalized/ensemble selection or explicit abstention rather than retuning on
opened outcomes.

## Ledgers

### SCIENCE

- **KNOWN:** prior shifted coverage was 13/16, but safety was untested because
  harmful opportunities were 0/16.
- **BELIEVED:** harmful switches concentrate near discontinuous solver/CV
  boundary surfaces and direct prediction disagreement exposes them.
- **CONFLICTING:** opened development evidence rejected 3/3 known harmful
  switches, but prospective evidence has not exercised the mechanism.
- **FALSIFIED:** broad random shifted sampling is a discriminating safety test.
- **UNTESTED:** rejection of truth-blind prospectively generated harmful
  switches.

### CONSEQUENCE

Do not promote the receipt. This protocol creates the exact missing capability:
a provenance-checkable, truth-blind stress generator for solver-arbitration
mechanisms. The single next action is to implement the generator and commit its
truth-free manifest; evaluation must occur only afterward.
