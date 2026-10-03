# Affine-trend extrapolation result

3 October 2026. **The general improvement criterion failed.** This is
development evidence on the opened cohort; no field breakthrough or fresh
confirmation is established.

The candidate removes quadratic/cubic kernels inside logarithmic response
models and adds an unpenalized affine trend with an RBF correction. The
correction is bounded by the coefficient L1 norm. An exact power-law test
confirms that this structure preserves legitimate extrapolation without an
observed-response range clip. Universal kriging and transformed-input kriging
are established prior art, as cited in the frozen protocol.

All 39 functions, five seeds and both noise levels were retained: 390 shared
observation paths, 64 labels per path, and two predictors produce 780 outcomes.
The primary `trend_stack` results are geometric-mean NMSE ratios; lower is
better. Function wins average over all seeds and both noise levels.

| Control | Overall ratio | Clean ratio | Noisy ratio | Function wins |
| --- | ---: | ---: | ---: | ---: |
| Representation winner | 1.1502 | 1.3989 | 0.9457 | 26/39 |
| Original representation stack | 1.0611 | 1.4943 | 0.7535 | 21/39 |
| Raw winner | 0.3227 | 0.1492 | 0.6981 | 31/39 |
| Raw stack | 0.3166 | 0.1464 | 0.6846 | 28/39 |
| Weighted median stack | 1.1903 | 1.4083 | 1.0061 | 26/39 |
| Adaptive stack | 1.1963 | 1.4495 | 0.9873 | 23/39 |
| Nonlinear support stack | 0.9304 | 0.9160 | 0.9450 | 24/39 |
| Nested winner | 1.2186 | 1.5252 | 0.9736 | 24/39 |
| Noise-consistent winner | 1.1845 | 1.3649 | 1.0279 | 23/39 |

The secondary winner was also weaker: 1.1645 times the original stack error,
with 16/39 function wins. The candidate repaired the known noisy Genz Corner
Peak catastrophe to 0.0844 NMSE for the stack and 0.0985 for the winner, but
lost substantial clean-case accuracy. The primary arithmetic mean NMSE was
0.1524, and its worst case was 5.3847. These are stability diagnostics, not a
substitute for the failed matched-control comparisons.

The primary's ratio against the original stack ranges from 0.9977 to 1.2196
when each function is removed in turn. Removing Genz Corner Peak produces
the upper end: the apparent noisy-case benefit is strongly affected by that
single repaired failure. A retrospective check on the previous median result
also changes its 0.8914 ratio to 1.0181 when this function is removed. That
check is exploratory and was not part of the older median study's protocol.

The affine-trend hypothesis was frozen in commit
`470f6311f673ecf9e7343ecfe5f932d2e8c388c8` before its scores were read. The
first aggregate audit exposed a numerical bookkeeping problem: per-outcome
absolute tolerances do not imply the same relative tolerance for ratios of
very small errors. For McLainS2, prediction arithmetic differed by about
`1.2e-9` NMSE on one clean case. The auditor was corrected after that
discrepancy was observed; the predictor, selection rule, controls and
performance criterion were not changed. It now checks summary arithmetic
from exact recorded scores to `1e-12`, separately reports ratios from the
second implementation, and requires both implementations to agree on the
criterion decision. Individual prediction tolerance remains `rtol=2e-5`,
`atol=1e-7`; model-choice numerical ties are explicitly counted.

The corrected audit passed all 780 outcomes in CI run `37120720812` on commit
`0ae12dc141117f77e628f78630d64d4677904778`. It reported 49 selection numerical
ties, maximum scaled NMSE difference `4.949e-4` (the absolute tolerance matters
for tiny errors), maximum scaled CV difference `9.863e-9`, and maximum simplex
KKT violation `2.075e-9`. The largest function-comparison relative difference
was `4.223e-5`. Both the recorded and recomputed criterion decisions were false.
All ten repository workflows passed on that commit.

Compact evidence is in `results/trend_revision/development`. The full input
and truth archive is reproducible from the pinned benchmark source, seeds,
and archived nonuniform columns; its original SHA256 must match exactly.
To reproduce with NumPy 2.3.5, SciPy 1.17.0 and UQTestFuns 0.6.0:

```bash
mkdir -p build
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python scripts/rebuild_trend_inputs.py --folder results/trend_revision/development
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python scripts/audit_trend_revision.py --folder results/trend_revision/development --out build/trend-revision-audit.json
```

Run the rebuild only when that archive is absent. CI copies the compact
snapshot, reconstructs its exact arrays, runs the arithmetic audit, and
uploads the complete evidence with read-only repository permissions.
This is same-author verification, not external reproduction. No candidate
from this screen is promoted as a default.
