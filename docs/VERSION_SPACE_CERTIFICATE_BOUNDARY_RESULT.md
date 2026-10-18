# Version-space certificate boundary result

## Result

The original form of the active kernel is too strong. A finite envelope formed
from training-compatible fitted models is **not** an unconditional prediction
certificate at an unobserved request. It is sound only relative to an explicit
hypothesis-class or probabilistic premise.

### Exact boundary theorem

Let `T={(x_i,y_i)}` be any finite transcript, let `x*` be unobserved, and let a
deterministic training-only procedure return a finite interval `[L(T,x*),
U(T,x*)]`. Over the unrestricted real-valued response class, define two
completions that equal the transcript at every observed point and set

`f_minus(x*) = L(T,x*) - 1`, and `f_plus(x*) = U(T,x*) + 1`.

The procedure sees the identical transcript under both completions, so it
returns the same interval, yet that interval excludes both constructed request
values. Therefore no such finite interval is an unconditional certificate.

The finite Boolean analogue was independently exhausted through six domain
points: **2,005 indistinguishable completion pairs** and **8,201 exact checks**,
with zero failures.

### Conditional envelope law

For a selected prediction `p`, lower and upper envelope vectors `l,u`, and scale
`s>0`, if the explicit premise `l_i <= y_i <= u_i` holds for every request
point, then

`NRMSE(p,y) <= RMS(max(p-l,u-p))/s`.

This follows pointwise because `|p_i-y_i| <= max(p_i-l_i,u_i-p_i)` and then by
squaring and averaging. The implemented verifier computes exactly this bound.

## Opened-cohort adversarial audit

No threshold was tuned and no holdout was opened. The envelope included every
successfully fitted candidate model in the existing 48-cell shifted cohort.

| Diagnostic | Count |
|---|---:|
| Cells whose truth exits the fitted-candidate envelope | 31 / 48 |
| Cells whose truth is outside at every request point | 6 / 48 |
| Catastrophic exact-LOO cells | 11 / 48 |
| Catastrophic cells with some truth outside | 6 / 11 |
| Catastrophic cells with all truth outside | 3 / 11 |
| Runtime refusals without verified provenance | 48 / 48 |

This rejects the strongest alternative that the finite candidate bank is already
operationally broad enough. The audit does not say conditional envelopes are
useless: five catastrophic cells had truth inside the broad envelope, so width
can still expose some solver/model ambiguity. It says empirical candidate
diversity cannot itself establish coverage of the unknown response.

## Runtime consequence

`kernellum.discovery.version_space_certificate` now implements:

1. integrity checking of a hypothesis-class provenance manifest;
2. a mandatory external domain verifier for that scientific premise;
3. exact envelope and worst-case normalized-RMSE computation;
4. refusal for missing provenance, malformed/nonfinite predictions, an uncovered
   selected prediction, or a bound above user tolerance; and
5. a hash-bound conditional certificate that exposes its premise and scope.

The runtime never converts training compatibility into a realizability claim.

## Prior-art audit and novelty boundary

Mitchell's original version-space formulation already defines the space relative
to a specified rule language and consistency with observations:
https://www.ijcai.org/Proceedings/77-1/Papers/048.pdf. Conformal prediction gives
finite-sample probabilistic coverage under assumptions such as exchangeability,
and covariate-shift extensions require additional structure such as likelihood
ratios: https://jmlr.org/papers/volume9/shafer08a/shafer08a.pdf and
https://papers.nips.cc/paper/2019/file/8fb21ee7a2207526da55a679f0332de2-Paper.pdf.

Accordingly, the general impossibility observation and conditional version-space
idea are **not claimed as historically novel**. The defensible Kernellum result
is the exact interface boundary, opened-cohort collision, independently checked
finite certificate, and implemented fail-closed contract.

## Ledgers

### SCIENCE

- Exact indistinguishable-completions theorem: pass.
- Independent finite enumeration: 2,005 pairs / 8,201 checks, pass.
- Opened matched diagnostic: fitted-candidate envelope misses truth in 31/48
  cells and in 6/11 catastrophic cells.
- Smallest claim: training compatibility alone cannot turn a finite candidate
  envelope into an unconditional unobserved-response certificate.

### CONSEQUENCE

- Kernellum must refuse an envelope certificate without verified provenance.
- Every accepted object names the hypothesis class, request scope, conditional
  premise, exact bound, tolerance, and content hash.
- Exact-LOO scores and candidate disagreement remain diagnostics, not proof.
- Future prospective validation must choose a scientifically justified class or
  a probabilistic coverage contract before touching an external holdout.

## Active kernel after this result

The kernel is **refined, not killed**: construct useful proof-bearing envelopes
under explicit, independently checkable structural premises and measure their
coverage. The next decisive action is to identify the weakest premise that is
both externally defensible and operationally non-vacuous. Any claim without such
a premise is killed by this result.

## Limitations

The empirical audit is opened synthetic development evidence involving two
families, two signs, 16 paths, and three request domains. The theorem concerns
unrestricted deterministic response functions and finite-valued intervals; it
does not preclude conditional structural bounds, Bayesian credible intervals,
or probabilistic conformal coverage under their respective assumptions.

