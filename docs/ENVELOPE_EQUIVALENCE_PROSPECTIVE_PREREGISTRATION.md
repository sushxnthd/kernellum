# Prospective envelope-only solver-equivalence certificate

**Frozen before outcome generation:** 15 October 2026  
**Classification:** prospective shifted-condition discrimination

## Active kernel

Can direct agreement of two independently implemented solver predictions certify
that their outputs are interchangeable on the requested inputs, without
requiring an identifiable cross-solver CV ordering or matching model identity?

This is a solver-invariance certificate, not a model-correctness certificate.

## Certificate fixed from opened development evidence

Fit the existing candidate and independent model banks. Let `c` and `i` be
their respective exact-LOO winners. On the union of all requested inside,
near-shell, and far-shell inputs, define:

```
prediction_rms = rms(pred_c - pred_i) / max(std(y_train), 1e-12)
prediction_max = max(abs(pred_c - pred_i)) / max(std(y_train), 1e-12)
```

Accept behavioral equivalence iff:

- `prediction_rms <= 0.5`;
- `prediction_max <= 4.0`.

No CV-margin, sign, or family-identity requirement is permitted. If accepted,
select the lower exact-LOO-CV solver. Otherwise abstain. Thresholds are inherited
unchanged from the opened stability-certificate study; no sweep is permitted.

## Untouched shifted factorial

Exactly 16 paths:

- functions: `anisotropic_laplace`, `rational_ridge`;
- dimensions: 2, 4;
- seeds: 4101, 4103;
- noise: `contaminated_gaussian`, `multiplicative_lognormal`.

Each path uses 24 maximin-selected training points from a 160-point uniform
pool. Requested inputs are 256 inside, 256 near-shell, and 256 far-shell points.

The functions, seeds, dimensions, noise mechanisms, pool size, training size,
and random-number derivation are new relative to the opened sign-anchor and
stability-certificate cohorts. No result from these paths may be inspected
before this protocol is committed.

## Frozen controls and labels

- always-candidate;
- always-independent;
- naive lower-CV arbitration;
- envelope-only equivalence plus abstention.

A naive lower-CV switch is **harmful** when independent is selected and is worse
than candidate by more than `ln(10)` in any requested domain.

## Preregistered gates

All must pass:

1. all 16 paths complete and certificate decisions are hashed before truth
   values are joined;
2. at least two harmful naive switches occur, making the safety test
   discriminating;
3. every harmful switch is rejected;
4. at least 8/16 paths are accepted;
5. no accepted selected output is worse than candidate by more than `ln(2)`
   in any domain;
6. on accepted paths, aggregate geometric NMSE is at most 1.10 times candidate
   in every domain;
7. two executions are byte-identical;
8. an independently written aggregation audit exactly reproduces every
   decision, count, ratio, and gate.

## Interpretation

- **PASS:** prospective evidence that prediction-envelope agreement is a useful,
  non-vacuous solver-interchangeability certificate on these shifted regimes.
  This licenses a Kernellum runtime receipt, not a claim of scientific model
  correctness or universal optimization reliability.
- **FAIL:** preserve the exact failure. Retire this pairwise-certificate kernel
  if safety or coverage fails; if only the harmful-opportunity gate fails, the
  result is inconclusive and requires a different untouched adversarial family,
  without reusing these paths as fresh evidence.

## Project consequence threshold

A pass must expose a concrete API result containing acceptance, normalized RMS
and max disagreement, selected solver, and an explicit statement that agreement
does not certify truth. A fail must prevent that interface from being promoted.

## Claim boundary

This protocol does not establish global optimality, correctness under model
misspecification, calibrated predictive uncertainty, or external-data
generalization. Historical novelty is not asserted.
