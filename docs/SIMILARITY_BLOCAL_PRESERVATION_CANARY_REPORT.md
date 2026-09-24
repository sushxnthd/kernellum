# SIMILARITY B-local preservation synthesis canary report

## Result

The frozen synthesis-only canary at commit
`7bfe4521a2b3034abc10e412398a0028a4dc8e95` passed. GitHub Actions run
`36069975816` completed on 24 September 2026 with signed-GEMM equivalence on
both opened shapes and exact mapped DFF counts on all four synthesis rows.

| Platform | Shape | Required DFFs | Observed DFFs | Full-local DFFs | Fraction of local | Synthesis area (um2) |
|---|---:|---:|---:|---:|---:|---:|
| NanGate45 | 5x8 | 1,979 | 1,979 | 2,284 | 86.65% | 56,098.8680 |
| NanGate45 | 8x5 | 1,972 | 1,972 | 2,232 | 88.35% | 55,576.9760 |
| Sky130HD | 5x8 | 1,979 | 1,979 | 2,284 | 86.65% | 265,452.0896 |
| Sky130HD | 8x5 | 1,972 | 1,972 | 2,232 | 88.35% | 260,807.6352 |

The result establishes that the intended per-PE A[7] and full-B data
registers survive the pinned synthesis flow while both valid streams and
A[6:0] remain stride-two shared. It does not establish routed electrical
cleanliness, timing, area-normalized throughput, novelty or practical utility.
It is not confirmation and not a breakthrough.

The repository preserves all five raw workflow artifacts, extracted result
JSON and functional logs, source hashes, and an independent exact-gate audit.
Run:

```console
python scripts/similarity_blocal_preservation_independent_audit.py
```

A pass permits only a separately frozen opened-data physical diagnostic.
Fresh-geometry confirmation remains unopened and cannot reuse these shapes or
seeds.
