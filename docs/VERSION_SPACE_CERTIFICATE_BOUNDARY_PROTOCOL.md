# Version-space certificate boundary: frozen protocol

## Allocation and status

KERNELLUM active kernel only. This run uses the already-opened 48-cell shifted
cohort; no frozen or external holdout is opened. Preliminary exploratory work
showed that candidate-envelope width varies widely, so no empirical width
threshold may be tuned or presented as prospective evidence in this run.

## Precise question

Can a finite envelope computed only from training-compatible fitted candidates
be an unconditional prediction certificate at an unobserved request, or must a
sound Kernellum certificate carry an independently checkable hypothesis-class
provenance premise?

## Exact hypothesis

For an unrestricted response class, any deterministic finite-valued interval
computed from a finite training transcript is unsound at every unobserved
request: two response functions can agree on the complete transcript while one
places the requested value below and the other above the returned interval.

The runtime consequence is fail-closed: an envelope may be emitted as a
conditional certificate only when its model-class provenance premise is
explicit; otherwise the system must return a refusal object rather than a
numeric safety claim.

## Best-known frontier

Version spaces and robust optimization provide conditional bounds relative to a
specified hypothesis/uncertainty class. Distribution-free predictive inference
can provide probabilistic coverage under exchangeability, but neither empirical
fit nor disagreement among a finite list of fitted models establishes
unconditional out-of-support validity under unrestricted misspecification.

## Exact objective

1. Prove the indistinguishable-completions boundary for every finite transcript
   and every unobserved request.
2. Independently exhaust finite Boolean transcripts through at least six domain
   points, constructing both completions for every unobserved request.
3. Implement a machine-checkable certificate/refusal object whose verifier
   rejects missing provenance, malformed envelopes, uncovered predictions, and
   bounds above the user tolerance.
4. Audit the opened 48-cell cohort without threshold tuning: report how often
   the observed truth is outside the envelope of all successfully fitted
   candidate models, including any catastrophic cells.

## Strongest alternative explanation

The current finite candidate family may be diverse enough in practice that its
envelope contains the opened-cohort truth, making the provenance boundary
formally correct but operationally irrelevant.

## Cheapest decisive falsification

The theorem is falsified only by a finite training-only algorithm that returns a
finite interval at an unobserved request and contains every unrestricted
completion consistent with the transcript. The implementation is falsified by
any accepted object lacking the required premise or violating its stated bound.

## Success, relevance, and kill conditions

- **Publishable success condition:** exact theorem plus independent exhaustive
  certificate and a prior-art audit; historical novelty is not presumed.
- **Project-relevance threshold:** the production-facing API changes from a
  heuristic score to a verified conditional certificate or explicit refusal.
- **Kill condition:** a counterexample to the theorem, any verifier false
  acceptance, or an implementation that cannot expose the provenance premise.

## Fixed reporting rule

The smallest supported claim will distinguish: (a) the unconditional
impossibility boundary, (b) the conditional envelope guarantee under an explicit
premise, and (c) opened-cohort diagnostics. No empirical result from this run is
external validation.
