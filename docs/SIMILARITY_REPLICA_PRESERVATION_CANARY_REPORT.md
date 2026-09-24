# SIMILARITY replica-preservation synthesis canary report

## Result

The frozen synthesis-only canary at commit
`8935555a38fc3892810f7b33d00f9ed07a6bebed` passed. GitHub Actions run
`36061292676` completed on 24 September 2026 with all five jobs successful.
Both opened geometries passed the signed-GEMM simulation, and all four mapped
rows contained exactly the preregistered number of DFFs.

This establishes only that lane-diverse invalid reset states prevented the
pinned synthesis flow from collapsing the intended selective A[7] and
B[2:0] replicas. It does not establish routed timing, electrical cleanliness,
area-normalized throughput, novelty, practical utility or a breakthrough.

## Frozen gates and observations

| Platform | Shape | Expected DFFs | Observed DFFs | Full-local DFFs | Fraction of local | Synthesis area (um2) |
|---|---:|---:|---:|---:|---:|---:|
| NanGate45 | 5x8 | 1,899 | 1,899 | 2,284 | 83.14% | 55,843.2420 |
| NanGate45 | 8x5 | 1,872 | 1,872 | 2,232 | 83.87% | 55,001.3520 |
| Sky130HD | 5x8 | 1,899 | 1,899 | 2,284 | 83.14% | 262,460.4704 |
| Sky130HD | 8x5 | 1,872 | 1,872 | 2,232 | 83.87% | 259,797.9168 |

Every row matched its exact DFF target and remained below the fixed 90% of
full-local budget. The functional logs contain the expected pass marker for
5x8 and 8x5. All result JSON records identify the frozen source commit, and
the functional artifact's recorded source hashes verify against that commit.

## Interpretation

The earlier critical-bit physical diagnostic remains a null. Its DFF counts
were identical to ordinary stride-two because the intended replicas did not
survive synthesis. The canary repairs that implementation-fidelity defect:
68 additional DFFs survive at 5x8 and 76 at 8x5, exactly matching the
predeclared selective-replica structure. This is evidence that a physical
mechanism test is now meaningful; it is not evidence that the repair improves
timing or density.

The next permitted step is a separately frozen physical diagnostic using
only already-opened shapes and seeds. Any later confirmation must use source,
geometries and seeds not opened in earlier ASIC work, with every electrical,
timing, cost and evidence-quality gate fixed before routing.

## Reproducibility

The repository preserves the five original workflow artifact ZIPs, extracted
functional logs and four result JSON files. Re-run the independent audit with:

```console
python scripts/similarity_replica_preservation_independent_audit.py
```

The audit requires the exact four-row set, the frozen source SHA, successful
synthesis, exact DFF counts, the 90% budget and both functional markers. It
does not trust the workflow's aggregate conclusion.
