# Full independent additive-response audit: optimizer-dependent selection

## Decisive result

The clean implementation completed all 120 frozen positive/negative Gaussian
paths. It reproduces the candidate exponential-only winner on **116/120** paths,
including every 2-D path and all 40 clean paths. Four noisy 4-D paths disagree.
Those four are not harmless parameter variations: they create extreme changes
in leave-one-out selection and out-of-support prediction.

| Path | Candidate winner (LOO CV) | Independent winner (LOO CV) | Independent/candidate NMSE: inside / near / far |
|---|---|---|---:|
| Gaussian, seed 104203, noise .01 | concave + (0.000362) | affine + (1.060) | 1.25e4 / 1.59e6 / 1.47e13 |
| Gaussian, seed 104206, noise .1 | concave + (0.0402) | affine + (1.050) | 72.1 / 1.22e3 / 2.67e8 |
| Gaussian, seed 104209, noise .1 | affine + (1.512) | concave - (1.107) | 201 / 3.16e13 / 2.29e24 |
| Negative Gaussian, seed 104207, noise .1 | affine - (1.041) | concave - (0.2649) | 0.00985 / 0.000262 / 1.24e-8 |

Across all 120 paths, using the unchanged `1e-8` comparison floor, the clean
implementation's geometric NMSE ratio to the candidate is **1.293 inside**,
**1.628 near shell**, and **2.508 far shell**. The median log ratio is zero in
every domain: the aggregate degradation is entirely concentrated in rare,
severe disagreements.

## Mechanism diagnosis

The full-data nonlinear objective is not the main failure. On Gaussian seed
104203/noise .01, the independent concave fit reaches full-data objective
0.0194, yet its fold-specific refits produce LOO CV 115,154 instead of the
candidate's 0.000362. On seed 104206/noise .1, its concave full-data objective
is 0.2256 but fold refits inflate LOO CV to 3.147 instead of 0.0402.

Therefore the discrepancy is specifically **fold-optimizer basin instability**:
small training-set changes alter which nonlinear basin is reached, which then
changes model selection. The effect is bidirectional. Three disagreements make
the independent prediction much worse, while one finds a concave model the
candidate missed and improves far-shell NMSE by about 80 million-fold.

This also exposes a second failure mode: lower LOO CV does not ensure safe
extrapolation. On Gaussian seed 104209/noise .1, the independent negative
concave model has lower LOO CV than the candidate affine model but far-shell
NMSE is about 2.29e24 times larger.

## Smallest supported claim

The signed-Gaussian response-scale family is numerically reproducible in clean
and 2-D conditions, but the current exact-LOO nonlinear selection procedure is
not solver-invariant in noisy 4-D conditions. Rare fold-basin changes can cause
catastrophic extrapolation or conceal a strong fit. This is a high-value
negative/reliability result, not a new regression method or field breakthrough.

The earlier balanced 20-path partial PASS is superseded for broad replication:
it did not include the four discrepant paths. The frozen scoped candidate result
remains a valid result of its specified implementation, but a claim that the
effect is implementation-independent is **INCONCLUSIVE**.

## Provenance and next discrimination

- Candidate source/evidence commit: `949d69b1de5284a106d6ce99ab6bc95f71bb2ab6`.
- Independent implementation commit ancestry: `982080e330d62db48f7bc52f0147ceaf06669daf`.
- Complete records: `results/additive_response/independent_replication_full/records.json`.
- Six deterministic single-thread shards; wall-clock maximum 718.24 seconds.
- Candidate fitting functions and runner were not imported.

The cheapest next experiment is CAPABILITY-BUILDING/DISCRIMINATION: on opened
data, map deterministic multi-start basin occupancy for the four minimal
disagreements and test whether fold instability is predicted by dimension,
noise, curvature conditioning, or sign coverage. Then preregister a new shifted
study with a solver-invariance gate: the claimed mechanism must survive at least
two frozen independent fitting procedures and an extrapolation-tail constraint.

## Reproduction and independent aggregation audit

Install the declared research and test dependencies, run the focused shape
tests, then recompute the decisive aggregates without importing either fitter:

```bash
python -m pip install -e '.[test]'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python -m pytest -q tests/test_independent_additive_replication.py
python scripts/audit_independent_additive_replication.py
```

The audit also verifies the SHA-256 digests of the two immutable input files.
It must report `status: PASS`, 120 reproduced paths, 116 winner agreements,
40/40 clean inside-domain fits at the comparison floor, and geometric NMSE
ratios of 1.292638 / 1.627622 / 2.507709 (inside / near / far).

