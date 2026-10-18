# Quantitative-premise boundary: frozen protocol

## Allocation and holdout status

KERNELLUM active kernel only. This run uses the already-opened 48-cell shifted
development cohort; no frozen or external holdout is opened. Multipliers are
fixed in advance at `1, 2, 5, 10`; none may be tuned after truth inspection.

## Precise question

Does the smallest transcript-compatible Lipschitz constant provide a sound and
useful prediction envelope at unseen requests, or must a Kernellum certificate
require an independently justified quantitative constant?

## Exact hypothesis

For finite observations `(x_i,y_i)`, the empirical constant

`L_T = max_{i != j} |y_i-y_j| / ||x_i-x_j||`

is only a lower bound on the Lipschitz constant of an unknown completion. For
every finite multiplier `c` and every unobserved request `x*`, there is a
completion that agrees with the transcript but lies outside the McShane interval
constructed with `c L_T`. Therefore neither `L_T` nor any fixed inflation of it
is a certificate without an external premise that the true response is
`L <= c L_T` Lipschitz.

Conditional on an externally verified global constant `L`, the exact feasible
pointwise interval is

`[max_i(y_i-L||x*-x_i||), min_i(y_i+L||x*-x_i||)]`.

## Best-known frontier and novelty boundary

McShane--Whitney Lipschitz extension theory already supplies the sharp
conditional interval, so that theorem is not claimed as historically novel.
The target result is the exact provenance boundary for a solver-stability
runtime, an exhaustive independent check, an opened-cohort collision for the
empirical shortcut, and an implemented fail-closed interface.

## Exact objective

1. Prove the fixed-inflation impossibility by indistinguishable completions.
2. Independently enumerate finite integer transcripts and verify interval
   sharpness against all bounded-grid Lipschitz completions.
3. On all 48 opened cells, report coverage and normalized width for the fixed
   multipliers `1, 2, 5, 10`, overall and by request domain; report catastrophic
   exact-LOO cells separately using the pre-existing `log_nmse > 5` definition.
4. Implement a certificate/refusal API that rejects a constant whose provenance
   is `estimated_from_same_transcript` and accepts only a verified external
   quantitative premise.

## Strongest alternative explanation

Although not certifying in principle, the empirical constant or a small fixed
inflation may cover every opened cell with a narrow interval, making the
provenance distinction operationally irrelevant for this benchmark.

## Cheapest decisive falsification

The exact claim is falsified by a proof that some finite multiplier of `L_T`
contains every unrestricted completion. The implementation is falsified by any
accepted certificate with transcript-derived constant provenance or any truth
inside the declared Lipschitz class but outside the emitted interval.

## Success, relevance, and kill conditions

- **Publishable success:** exact boundary, independent finite sharpness check,
  and reproducible matched cohort audit; historical novelty is not presumed.
- **Project relevance:** runtime distinguishes an external quantitative premise
  from an empirical lower bound and fails closed on the latter.
- **Kill:** counterexample to conditional interval sharpness, verifier false
  acceptance, or no measurable distinction between empirical and externally
  premised behavior.

## Fixed reporting rule

Opened-cohort coverage is diagnostic only. Even perfect coverage at multiplier
5 or 10 must not be called a certificate. The smallest claim must distinguish
the exact impossibility, the conditional classical law, and the empirical
development result.
