# SIMILARITY preserved-replica physical diagnostic report

## Result

The frozen opened-data diagnostic at commit
`9678983c99e4cf282b47a50e2deaea67397926a9` is a **null**. GitHub Actions
run `36062724349` completed on 24 September 2026. All six route jobs ran to
completion and produced exactly twelve candidate rows, but only ten passed
the all-required electrical gate. The frozen evaluator therefore returned
`prospective_study_warranted: false`.

This is not confirmation and is not a breakthrough. No failed seed was
replaced or rerun, and no threshold was changed after results were opened.

## Gate result

Functional equivalence and the exact twelve-row evidence gate passed. Two
NanGate45 8x5 routes each retained one final maximum-capacitance violation:

| Seed | Pin | Limit (fF) | Extracted capacitance (fF) | Slack (fF) |
|---:|---|---:|---:|---:|
| 71 | `_37122_/ZN` | 26.02 | 27.04 | -1.03 |
| 89 | `_36731_/ZN` | 26.02 | 27.33 | -1.31 |

All setup, hold, slew, fanout and DRC counts were zero on those rows. The
other ten rows were fully clean. Because the evaluator excludes electrically
dirty rows before matched-group statistics, the exact-DFF, cost, all-group
timing and targeted-improvement gates correctly evaluate false from an
incomplete clean set even though every synthesized row contained the intended
register count.

The mechanism-specific fanout gate independently failed. NanGate45 8x5
maximum paths launched with Q fanouts 16, 16 and 10, giving median 16 versus
the frozen maximum 10. The two fanout-16 paths launch from unreplicated
`b_common` registers; the third also launches from `b_common`. Selectively
replicating A[7] and B[2:0] therefore moved the NanGate45 limiting path to
the still-shared B[7:3] transport instead of removing the shared-operand
bottleneck.

## Descriptive timing, not a gate rescue

For diagnosis only, the table below includes the two electrically dirty rows.
These values cannot rescue the frozen null.

| Platform | Shape | Candidate median period (ns) | Raw benefit vs broadcast | Retained local benefit | Density vs broadcast | Density vs local |
|---|---:|---:|---:|---:|---:|---:|
| NanGate45 | 5x8 | 1.53 | 11.05% | 86.36% | 1.060 | 1.015 |
| NanGate45 | 8x5 | 1.52 | 8.98% | 88.24% | 1.043 | 1.028 |
| Sky130HD | 5x8 | 7.07 | 11.29% | 130.43% | 1.072 | 1.069 |
| Sky130HD | 8x5 | 6.78 | 19.67% | 120.29% | 1.177 | 1.075 |

The targeted NanGate45 8x5 median is descriptively 0.06 ns better than
ordinary stride-two and 0.04 ns better than the prior merged-replica no-op.
All four groups would meet the numerical timing and joint density thresholds
if electrical cleanliness were ignored. It must not be ignored.

## Diagnosis and disposition

The experiment demonstrates two useful points without establishing the
predeclared claim:

1. Preserved selective replicas can materially improve routed timing and
   area-normalized throughput, especially on Sky130HD.
2. On NanGate45, B[7:3] remains a shared high-fanout path and two seeds are
   not electrically clean. The intervention is therefore incomplete.

This exact intervention stops. A justified distinct discovery intervention
is to keep A[6:0] stride-two shared, preserve per-PE A[7], and preserve all
eight B bits per PE. That directly targets the observed B-common paths while
remaining structurally cheaper than full local: predicted DFF counts are
1,979/2,284 (86.65%) at 5x8 and 1,972/2,232 (88.35%) at 8x5. Those predictions
require a separately frozen synthesis canary before any further routing.

## Reproducibility

The repository preserves all eight original workflow artifact ZIPs, six raw
CSV shards, functional logs, the byte-identical final JSON and an independent
audit. The frozen evaluator was rerun against the downloaded artifacts and
produced SHA-256
`6489fa1ff1520ec55eebda4f6f943f38766f1513a1b6f61ef576fd5386dff7c6`,
byte-for-byte identical to the workflow summary.

Run the independent audit with:

```console
python scripts/similarity_preserved_independent_audit.py
```
