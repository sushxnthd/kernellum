# Experiment selection under model error: completed result

29 September 2026. Program: **Scientific Discovery / Machine Reasoning**.

**No breakthrough is established.** The frozen candidate improved on several
baselines but failed to beat space-filling sampling. Two subsequent development
variants did not reach the original improvement target either. All results,
including the failed gates, are retained.

This work gives Kernellum a working non-hardware experiment-selection component
and an external-formula evaluation harness. It does not establish autonomous
scientific discovery, a novel physical law, or superiority to current research.

## Frozen experiment

Protocol and implementation were committed before comparative execution at
[`3d580a2`](https://github.com/sushxnthd/kernellum/commit/3d580a2a890790418a5b3a3ed34069042afd9428).
See [the protocol](DISCOVERY_DESIGN_PROTOCOL.md) for the source, methods, gates,
prior-art screen, and exact data-access boundary.

All **2,496 / 2,496** runs completed: 52 published Feynman equation rows, three
seeds, two noise conditions, and eight methods. Each method used 40 measurements
including the common 12-point start. Inputs and labels were simulated from the
published formulas and bounds, not collected from physical experiments. These
are repeat trials on 52 equations; several equations are algebraically related.

Primary metric: ratio of geometric mean normalized test MSE at 40 measurements,
with a floor of 1e-8 before taking log ratios. Lower than 1 favors the candidate.
Every included baseline had to be beaten by at least 20%, with a majority of
equation wins and no aggregate regression within either noise condition.

| Comparator | Candidate/comparator error | Error reduction | Equation wins |
|---|---:|---:|---:|
| Uniform random | 0.84246 | 15.75% | 44/52 |
| Space-filling / maximin | 1.00026 | -0.03% | 28/52 |
| Pointwise variance | 0.82874 | 17.13% | 46/52 |
| Integrated variance reduction | 0.88940 | 11.06% | 41/52 |
| RBF committee disagreement | 0.86055 | 13.94% | 45/52 |
| Improved greedy sampling | 0.91160 | 8.84% | 40/52 |

**Frozen gate: FAIL.** The candidate is 2.04% worse than maximin in the noisy
condition and 1.95% better in the clean condition. The gain against random is
insufficient evidence of a research advantage when a simple stronger control ties
it overall. No confidence interval or population-wide significance is claimed.

The entire simulated comparison took about 29 seconds on the recorded CPU
runtime. This is not evidence that real scientific measurements take that time.
Median end-to-end per-run times were approximately 16.8 ms for the candidate and
6.6 ms for maximin, including post-run evaluation. Timings are environment-specific.

## Diagnostic and two further attempts

These analyses happened **after opening the frozen results** and are development
work. They cannot be presented as held-out confirmation.

1. A privileged fit used *all clean test answers* to calculate the quadratic
   model class's error floor. Among the 47 equations with floor NMSE above 1e-6,
   that floor was 80.75% of maximin error in the clean condition and 80.08% in the
   noisy condition, on a geometric-mean basis. This suggests limited room for
   query selection alone before improving the model class. The floor is a
   diagnostic bound on this finite test set, not an eligible budgeted algorithm.
2. Two new variants made each teacher a quadratic trend plus an RBF model of
   observed residuals. The mean-risk variant achieved an exploratory error ratio
   of **0.94956** versus maximin, a **5.04%** reduction. The conservative variant,
   requiring improvement across teacher hypotheses, achieved **1.00489**, a
   **0.49% regression**. Together these added 624 development runs.

We do not tune and relabel these opened results as validation. Across the initial
candidate and the two revisions, **3,120 runs** are preserved. Further same-cohort
sampling-rule sweeps are not justified by the present evidence. A subsequent
research protocol should test model-class revision and falsification against
existing methods, with a fresh confirmation cohort and an explicit novelty case.
That work has **not** been executed or scheduled by this report.

## What can be used now

The measurement loop is usable on a supplied finite experimental pool. It accepts
actual observations and recommends one next point. The default is **maximin**,
selected after this experiment; its general superiority is not claimed.
`teacher_risk` remains an explicitly experimental option, marked as having failed
the frozen gate. The tool does not generate or pretend to execute measurements.

```bash
python -m kernellum.discovery \
  --pool examples/discovery_design/pool.json \
  --observations examples/discovery_design/observations.json \
  --out next-experiment.json
```

`pool.json` contains `points`, `lower`, and `upper`; observations contain integer
`index` and finite `value` fields. At least two distinct observations are required.
The pool must contain at least one unmeasured point. Run the proposed measurement,
append its actual response to the observations, and call again using a new output
path. Input hashes accompany each decision. The example values are synthetic.

Developers can connect an actual measurement function to
`kernellum.discovery.design.investigate(x, query, ...)`; the selector receives
only the measured responses, not an array of unqueried answers. For that API,
normalize input dimensions to [-1,1] consistently before use. This is a software
API boundary, not a security sandbox against hostile in-process code.

## Evidence and verification

- [Original summary](../results/discovery_design/frozen_run/summary.json)
- [Original compressed query traces](../results/discovery_design/frozen_run/traces.jsonl.gz)
- [Frozen source and output hashes](../results/discovery_design/frozen_run/manifest.json)
- [Separate arithmetic audit](../results/discovery_design/audit.json)
- [Post-hoc floor diagnostic](../results/discovery_design/posthoc_floor.json)
- [Development traces](../results/discovery_design/development.jsonl.gz)

The raw JSONL bytes are losslessly gzip-compressed; their original decompressed
hashes remain in the original manifest. The audit understands both plain and
compressed traces. Archives are committed with the code, not solely retained as
temporary workflow artifacts. A separate provenance manifest identifies the
post-hoc files; it is not a preregistration of those analyses.

The separate audit imports no Kernellum or runner implementation. It reconstructs
all outputs, checks the exact cohort and measurement accounting, and recomputes
**7,488 checkpoint errors** using augmented least squares instead of the original
inverse-based fit. Maximum absolute discrepancy: **4.89e-12**. All six comparison
aggregates and the failed verdict agree. This is a second implementation by the
same author, **not independent external scientific reproduction**.

Eight focused tests check the acquisition formula against explicit refits,
measurement budgets, label-access boundaries, malicious formula syntax, invalid
inputs, and the recommendation interface. GitHub's dedicated evidence workflow
also reruns the frozen experiment and compares all six primary aggregates.

The [prior-art screen](DISCOVERY_DESIGN_PROTOCOL.md#prior-art-screen-and-claim-boundary)
identifies substantial existing work. IDEAL, EMCM and R-IDeA are not fully
implemented in this comparison. No state-of-the-art, patentability, physical
validation, customer traction, or investor-readiness claim follows from this work.
