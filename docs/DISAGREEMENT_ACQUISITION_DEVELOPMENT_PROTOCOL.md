# One-point disagreement acquisition: frozen development protocol

**Frozen:** 16 October 2026  
**Classification:** opened-cohort mechanism discrimination  
**Active KERNELLUM kernel:** intervention after fixed support-distance abstention failed

## Precise question

Can one response measurement, selected prospectively from the actual requested
batch by disagreement among the frozen sign × model-family candidates, reduce
catastrophic exact-LOO model-selection error more reliably than no acquisition,
deterministic random acquisition, nearest-support acquisition, and
farthest-support acquisition?

This test uses the permanently opened 16-path shifted synthetic cohort. It can
kill or refine the intervention mechanism, but cannot validate a publishable
generalization claim.

## Frozen unit, candidate models, and truth barrier

The unit is one `(path, request_domain)` cell: 16 paths crossed with `inside`,
`near_shell`, and `far_shell`, for 48 cells. Each cell has 256 candidate query
points. Before the response at any candidate point is read, the runner must:

1. fit the four existing single-start candidates from sign in `{+1,-1}` and
   family in `{exp_affine,exp_concave}` on the original 20 observations;
2. write the selected point index for every acquisition method and cell;
3. bind all decisions in a canonical SHA-256 artifact containing no candidate
   truth or post-acquisition score.

Only after that artifact is written may the synthetic oracle supply the one
selected response, the support set grow from 20 to 21 points, and exact LOO
model selection be rerun.

## Frozen acquisition rules

For candidate point `z`, let `p_m(z)` be the prediction from original-data
candidate `m`, and let `s_y=max(std(y_train),1e-12)`.

1. **Disagreement:** maximize
   `median(|p_m(z)-median_m p_m(z)|)/s_y`; break ties by lowest point index.
2. **Deterministic random:** choose the index from the first eight bytes of
   SHA-256 of the canonical cell key, modulo 256.
3. **Nearest support:** minimize Euclidean distance from `z` to the original
   training set; break ties by lowest index.
4. **Farthest support:** maximize the same distance; break ties by lowest index.
5. **No acquisition:** preserve the original exact-LOO winner and prediction.

Each acquisition method receives exactly one noiseless synthetic response at
its selected point. The response is a measurement of the latent function, not
the originally sampled observation noise. All methods then use the identical
single-start exact-LOO selection code and the same four sign/family candidates.

## Exact objective and gates

A cell is catastrophic iff log-NMSE is greater than 5, matching the predecessor
studies. Disagreement acquisition advances only if every gate holds:

1. exactly 48 decisions per acquisition rule are written and hashed before the
   outcome join;
2. all methods complete all 48 post-acquisition fits, with failures preserved;
3. disagreement removes at least half of no-acquisition catastrophes;
4. disagreement leaves at least two fewer catastrophes than each matched
   acquisition control;
5. disagreement has no more catastrophes than no acquisition in any of the
   three domains;
6. disagreement inside-domain geometric NMSE is at most 1.10 times the
   no-acquisition value;
7. disagreement near- and far-shell geometric NMSE are each at most 0.90 times
   the best matched acquisition control;
8. a separately implemented audit reproduces the decision hash, selected
   indices, scores, catastrophe counts, geometric means, and gates.

No threshold, candidate pool, score normalization, solver, or tie rule may be
changed after the outcome join.

## Strongest alternative explanation

Any improvement may come merely from adding one noiseless observation or from
geometric expansion of support, not model disagreement. Random acquisition
tests the generic-data explanation; nearest and farthest support test local
density and extrapolation-geometry explanations. The same refit and selection
code is used after every acquisition.

## Publishable success condition

Passing this opened screen licenses one untouched prospective cohort with new
function families, support geometries, dimensions, noise processes, and a
frozen noisy-measurement model. Publishable success requires the same
catastrophe and matched-control gates prospectively, plus an external dataset or
physical/simulation oracle. This run alone cannot support a flagship claim.

## Project-relevance threshold

A pass must produce an experimental Kernellum action that returns a concrete
measurement location and a machine-readable reason/receipt, rather than only a
risk score. A fail forbids shipping one-point disagreement acquisition and
forces either multi-point experimental design or model-class revision.

## Kill condition

Failure of any terminal gate kills this exact one-point rule. Three total
non-discriminating intervention runs kill the broader acquisition kernel.

## Ledgers at freeze

### SCIENCE

- **KNOWN:** optimizer rescue and fixed nearest-support abstention failed.
- **QUESTION:** does intervening at maximal model-class disagreement change the
  selected model and its catastrophic tail?
- **ALTERNATIVE:** any extra point or support expansion explains improvement.

### CONSEQUENCE

- **PASS:** add an experimental measurement-request planner and freeze one new
  prospective cohort.
- **FAIL:** do not expose one-point disagreement acquisition as a safety action;
  reformulate toward batch design or model revision.

## Controlled serendipity

The farthest-support control doubles as the isolated wildcard probe: a purely
geometric intervention may unexpectedly dominate disagreement. If it does, the
result is preserved but does not replace the active kernel without a new frozen
protocol.
