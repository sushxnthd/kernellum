# Transition-constrained batch acquisition: frozen development protocol

**Frozen:** 17 October 2026  
**Classification:** opened-cohort causal mechanism discrimination  
**Active KERNELLUM kernel:** safe intervention after one-point disagreement acquisition failed

## Precise question

Does catastrophic post-acquisition exact-LOO failure arise primarily from sparse
measurement coverage or from a discontinuous jump in sign/model family? Compare
a three-point disagreement-diversity batch with the identical batch while locking
the pre-acquisition winning sign and family, against no acquisition, the frozen
one-point disagreement rule, and a three-point farthest-support control.

## Frontier and exact objective

On the permanently opened 48-cell shifted cohort, one-point maximum disagreement
reduced total catastrophes from 11 to 9 but increased far-shell catastrophes
from 7 to 8. Optimizer rescue, fixed support abstention, and one-point acquisition
are already killed. The objective is total cells with log-NMSE greater than 5,
with far-shell catastrophe count and geometric NMSE as hard secondary gates.

## Truth barrier and frozen batch rules

Each `(path, request_domain)` cell has 256 candidate query points. Before any
candidate response is read, write and hash all selected indices from the original
20 observations and the four frozen sign × family candidate fits.

Let `d(z)` be normalized median absolute model disagreement, and let `r(z,S)` be
the Euclidean distance from candidate `z` to its nearest point in set `S`.

1. **No acquisition:** original exact-LOO winner.
2. **One-point disagreement:** the previously frozen maximum-`d` rule.
3. **Batch disagreement-diversity:** greedily choose three distinct points. The
   first maximizes `d`; each later point maximizes
   `d(z) * r(z, training union selected) / max_z r(z, training)`. Lowest index
   breaks ties.
4. **Batch farthest support:** greedily choose three distinct points maximizing
   `r(z, training union selected)`. Lowest index breaks ties.
5. **Transition-locked batch:** use the exact indices from arm 3, append their
   noiseless latent responses, and refit only the pre-acquisition exact-LOO
   winner's sign and family. Parameters may change; sign/family may not.

The unrestricted batch arms refit all four candidates and select the lowest
exact-LOO score. Acquired points are excluded from the evaluation score. Failed
fits and incomplete arms count as catastrophes and are preserved.

## Measurable gates

The transition-locked batch advances only if every gate holds:

1. 48 truth-blind decision rows are written and SHA-256 bound before outcome join;
2. all five arms complete all 48 cells;
3. total catastrophes are at most 5 (halving the 11-cell baseline);
4. total catastrophes are at least two fewer than each acquisition control;
5. no domain has more catastrophes than no acquisition;
6. far-shell catastrophes are at most 3 (halving the seven-cell baseline);
7. inside geometric NMSE is at most 1.10 times no acquisition;
8. near- and far-shell geometric NMSE are each no worse than the best acquisition
   control;
9. an independently written audit reproduces decisions, fits, scores, metrics,
   gates, and canonical digest.

No score, threshold, candidate set, batch size, solver, or tie rule may change
after joining responses.

## Strongest alternative explanation

Any gain may be explained by three-point geometric coverage rather than transition
locking. The unrestricted disagreement-diversity and farthest-support arms isolate
that explanation. Conversely, a locked-arm failure would show that discontinuous
class transitions are not the sole cause.

## Cheapest decisive falsification

Run all arms on the already opened cohort and inspect the terminal gates. Any
failed gate kills this exact locked-batch rule. No untouched holdout is opened.

## Publishable success condition

Passing this screen only licenses a pre-registered prospective cohort. A flagship
claim additionally requires the same gates on untouched regimes and external or
physical/simulation-oracle data, plus a primary-literature audit and independent
replication.

## Project-relevance threshold

A pass must ship as a machine-readable measurement plan containing selected
locations, frozen model identity, transition policy, and evidence receipt. A fail
forbids presenting transition locking as a safety mechanism and forces model-class
revision or explicit abstention outside certified support.

## Kill condition

Failure of any terminal gate kills this rule. Because fixed abstention and
one-point disagreement already failed, failure here is the third discriminating
failure of the broader intervention line and kills/reformulates that kernel.

## Ledgers at freeze

### SCIENCE

- **Known:** maximizing disagreement can induce a worse exact-LOO class transition.
- **Unknown:** whether holding sign/family fixed converts acquisition into tail-safe
  parameter refinement.
- **Alternative:** batch coverage, not transition locking, explains any benefit.

### CONSEQUENCE

- **Pass:** expose a transition-locked batch planner, then spend one new holdout.
- **Fail:** retire this acquisition/abstention line and move to model-class revision
  or certified-support refusal.

## Controlled serendipity

The unrestricted disagreement-diversity and farthest-support batches are the
wildcard probes. If either dominates the locked arm while passing every gate, it
may replace the kernel only under a separately frozen prospective protocol.
