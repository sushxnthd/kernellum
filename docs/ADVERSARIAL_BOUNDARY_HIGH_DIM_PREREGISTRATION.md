# High-dimensional truth-blind boundary replication

**Frozen before implementation or manifest generation:** 16 October 2026  
**Classification:** prospective mechanism discrimination; second and final opportunity generator  
**Action class:** DISCRIMINATION

## Precise question

Does the eligible independent-lower-CV boundary regime observed in the first
generator persist at dimensions 5 and 7 strongly enough to create a complete
24-case truth-blind manifest, and does the unchanged prediction-envelope
certificate reject harmful solver switches without sacrificing ordinary cases?

The certificate remains a solver-interchangeability test on an explicit request
set, not a certificate that either model is correct.

## Prior evidence and mechanism-derived prediction

The first frozen generator produced 0/194 eligible perturbations in dimension 3
and 86/194 (44.33%) in dimension 5. That study failed its 24-case selection gate
before requested-input truth was opened. The dimensional split is descriptive,
not itself confirmatory.

**Prediction:** with new bases at dimensions 5 and 7, the independent-lower-CV
frequency will be high enough that every base contributes its cap of six cases,
yielding exactly 24 selected cases. The mechanism is that the enlarged feature
geometry creates more distinct nonconvex solver basins and winner surfaces.

**Strongest alternative:** the first split was seed-specific or a numerical
artifact. New high-dimensional bases will not reproduce a complete manifest, or
the selected cases will contain fewer than four harmful switches after the
truth join.

## Frozen factorial and generator

Use four new bases: dimensions `5, 7` crossed with seeds `6101, 6107`.
For each base:

- draw a 192-point uniform `[-1,1]^d` pool and select 24 maximin training
  inputs;
- use the same anisotropic signed rational peak with weak sinusoidal ridge;
- add Gaussian training noise at 0.20 times clean-response standard deviation;
- freeze 192 inside, 192 near-shell `(1,1.7]`, and 192 far-shell
  `(1.7,3.4]` requested inputs;
- use RNG seed `seed + 100*dimension + 60000`.

Generate 97 perturbations indexed `j=-48,...,48`:

[
y_j=y_0+(j/48)(0.45s_y)v,
]

where `v` is the normalized mean-zero first left singular vector of the
centered linear-plus-quadratic training-input feature matrix, with deterministic
sign. Fit the existing candidate and independent banks over both response signs
and both model families.

Requested-input truth MUST NOT be evaluated, serialized, logged, or available
to selection. The implementation must run twice byte-identically and must
upload every per-base manifest even when its scientific gate fails.

## Frozen selection and certificate

Eligibility, ordering, and cap are unchanged:

1. independent solver has lower exact-LOO CV;
2. boundary event first;
3. smaller normalized CV gap;
4. larger normalized prediction RMS disagreement;
5. larger normalized prediction maximum disagreement;
6. smaller `abs(j)`, then smaller signed `j`;
7. dimension, then seed.

Select at most six cases per base. The generator passes only if every base
selects six, for exactly 24 cases total. The certificate thresholds remain
normalized RMS `<=0.5` and normalized maximum `<=4.0`.

## Integrity barrier and later truth join

The truth-free per-base manifests must be committed or preserved as immutable
workflow artifacts before any outcome evaluator is committed or run. A manifest
containing requested truth is invalid. Changing dimensions, seeds, RNG offset,
grid, ranking, cap, bank, or thresholds creates a different study.

Only after manifest preservation may a separately committed evaluator
reconstruct the frozen functions and join requested truth.

## Outcome gates

All gates are required:

1. exactly 24 selected truth-blind cases, six per base;
2. at least four harmful naive switches, defined as independent lower-CV and
   worse than candidate by `>ln(10)` in at least one request domain;
3. every harmful switch rejected by the unchanged envelope;
4. at least 8/24 selected cases accepted;
5. no accepted case worse than candidate by `>ln(2)` in any domain;
6. accepted aggregate geometric NMSE at most 1.10 times candidate in every
   domain;
7. an independent evaluator reproduces joins, labels, counts, ratios, and gates.

## Publishable success, consequence, and kill rule

**Success:** all generator, outcome, and independent-replication gates pass,
followed by a primary-literature audit finding no equivalent prospective
solver-interchangeability receipt.

**Consequence:** a pass licenses an experimental runtime receipt carrying
acceptance, disagreement statistics, selected solver, provenance, and scope
`solver_invariance_not_model_correctness`.

**Kill rule:** if the generator cannot freeze 24 cases, or the later untouched
truth join yields fewer than four harmful opportunities, retire this pairwise
envelope kernel. Any missed harmful switch or accepted degradation gate failure
also kills it. Do not retune on opened outcomes; move to globalized/ensemble
selection or explicit abstention.

## Ledgers

### SCIENCE

- **KNOWN:** the first frozen generator had a sharp 3-D/5-D eligibility split
  but failed before outcome truth.
- **BELIEVED:** higher-dimensional feature geometry creates more solver winner
  boundaries.
- **ALTERNATIVE:** the split was seed-specific rather than dimensional.
- **UNTESTED:** whether new 5-D/7-D bases create at least four harmful
  opportunities and whether the envelope rejects them safely.

### CONSEQUENCE

This is the second and final opportunity generator for the active pairwise
envelope kernel. It either earns one untouched safety evaluation and possible
runtime integration, or retires the mechanism in favor of a robust alternative.
