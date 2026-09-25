# SIMILARITY B-local prospective ASIC report

Date: 25 September 2026  
Frozen source: `3a0d7f7364f55ad0757964f3d8cb2eb43717c635`  
GitHub Actions run: [36088664352](https://github.com/sushxnthd/kernellum/actions/runs/36088664352)  
Protocol: [SIMILARITY_BLOCAL_PROSPECTIVE_PREREGISTRATION.md](SIMILARITY_BLOCAL_PROSPECTIVE_PREREGISTRATION.md)

## Result

This study is a **preregistered null** for the exact frozen claim.

The run produced all 72 planned attempt rows, all four signed-GEMM functional logs and all 72 maximum-path reports. Seventy-one rows completed the full evidence contract. The Sky130HD B-local 8x6 discovery route at seed 157 completed detailed routing, but its emulated OpenROAD final-report process terminated with signal 11 during the optional GUI image phase. The frozen row therefore correctly records `route_ok=False`, `error_stage=final_report` and no auditable final metrics or product hashes. The protocol required 72/72 complete, clean rows and prohibited dropping or selectively retrying a row, so the claim fails.

This is primarily an **evidence-completeness/tooling failure**, not a demonstrated electrical failure of the candidate. That distinction does not rescue the confirmatory result.

## Evidence inventory and independent audit

The repository preserves:

- all 18 original route artifact ZIPs with their GitHub artifact SHA-256 digests;
- the original functional and final-summary ZIPs;
- 18 extracted CSVs containing exactly 72 unique planned rows;
- four functional logs and the frozen source/hash manifest;
- all 72 `6_finish.rpt` files inside the original route ZIPs;
- the frozen evaluator JSON; and
- a separately implemented independent checker and its JSON output.

The independent checker does not import the frozen evaluator. It rebuilt the expected cohort and all gates directly from CSV rows, reports and functional evidence. It found 18 route ZIPs, 18 CSVs, 72 rows, 71 complete clean rows, 72 parseable maximum-path reports, 23 complete topology trios and seven complete three-seed groups. All archived ZIP hashes matched the GitHub artifact digests. Its counts, gate vector and final decision exactly matched the frozen evaluator.

Evidence: [`results/similarity_blocal_prospective_artifacts/`](../results/similarity_blocal_prospective_artifacts/)  
Independent checker: [`scripts/similarity_blocal_prospective_independent_audit.py`](../scripts/similarity_blocal_prospective_independent_audit.py)

## Frozen gates

| Gate | Result |
|---|---:|
| Signed-GEMM equivalence on all four shapes | PASS |
| Exactly 72 unique attempted rows | PASS |
| All 72 final routes electrically and DRC clean with complete products | **FAIL (71/72)** |
| All 72 final maximum-path reports present and parseable | PASS |
| Eight groups with three complete matched seeds | **FAIL (7/8; 23/24 trios)** |
| Full-local positive in every required group | **FAIL because one group is incomplete** |
| All 24 B-local DFF comparisons pass | **FAIL because one trio is incomplete** |
| All 24 B-local synthesis-area comparisons pass | **FAIL because one trio is incomplete** |
| Four holdouts have at least 5% median raw benefit | PASS |
| Four holdouts retain at least 70% of full-local timing benefit | PASS |
| At least three of four holdouts jointly win both area-normalized comparisons by at least 1% | PASS (4/4) |
| Joint holdout wins include both platforms | PASS |
| NanGate45 holdout median launch-Q fanout at most 10 | PASS |

The last four performance gates passing is descriptive evidence inside an overall null; it is not permission to discard the failed route or relabel the study as confirmation.

## Sealed-holdout measurements

The four holdout groups were complete and independently reproduced. Ratios are medians of the three seed-paired ratios.

| Platform | Shape | B-local raw timing benefit | Retention vs full-local | Throughput/area vs broadcast | Throughput/area vs full-local |
|---|---:|---:|---:|---:|---:|
| NanGate45 | 6x9 | 10.53% | 128.57% | 1.0466x | 1.0640x |
| NanGate45 | 9x6 | 12.07% | 100.00% | 1.0652x | 1.0319x |
| Sky130HD | 6x9 | 13.23% | 94.78% | 1.0888x | 1.0186x |
| Sky130HD | 9x6 | 16.39% | 95.21% | 1.1258x | 1.0305x |

The NanGate45 B-local holdout maximum paths had launch-Q fanouts `[8, 9, 10]` at 6x9 and `[8, 8, 8]` at 9x6. Across the 23 complete topology trios, every frozen DFF and synthesis-area comparison passed, and all seven complete groups had positive full-local timing benefit. Those facts remain secondary because the all-required evidence gate failed.

## Failure diagnosis

The sole incomplete row is:

`sky130hd / discovery / blocal / 8x6 / seed 157`

Its native detailed-route log reports zero detailed-routing violations and zero antenna violations. The partial `6_finish.rpt` also contains zero setup, hold, maximum-slew, maximum-fanout and maximum-capacitance counts and a 7.9437 ns critical-path delay. However, the final-report driver log then records two GUI image filename warnings followed immediately by `Signal 11 received`; `make` exits 245. The runner consequently does not execute the native finish stage or certify nonempty GDS/ODB/SPEF/netlist hashes.

The ordering makes QEMU-hosted optional GUI image generation the leading cause of the crash. It is not proven as a universal OpenROAD defect, so the report does not claim stronger causality. It is enough to identify why the frozen evidence contract was not completed.

## Scientific interpretation

The run does **not** establish the preregistered claim and is not a breakthrough. It does show that B-local remained promising on all four unopened holdout platform/shape groups that were complete: each met the timing-retention gate and beat both controls on synthesis-area-normalized throughput. The correct status is therefore “promising confirmatory null caused by one incomplete final-report row,” not “confirmed” and not “electrically disproven.”

The geometries 6x8, 8x6, 6x9 and 9x6 and seeds 101, 131 and 157 are now opened and excluded from any future confirmation. No row will be repaired, retried or substituted into this study.

Local versus shared operand movement is an established accelerator design space, including Eyeriss, MAERI and systolic TPU-style arrays. This experiment does not by itself establish that B-local selective replication is novel, and it measures routed timing plus synthesis cell area rather than silicon energy, die area or workload-level performance.

## Reproduction

After extracting the archived route ZIPs and functional ZIP, run:

```bash
python scripts/similarity_blocal_prospective_independent_audit.py \
  --routes <extracted-route-root> \
  --functional <extracted-functional-root> \
  --zips results/similarity_blocal_prospective_artifacts/original \
  --functional-zip results/similarity_blocal_prospective_artifacts/original/similarity-blocal-prospective-functional.zip \
  --summary-zip results/similarity_blocal_prospective_artifacts/original/similarity-blocal-prospective-final-summary.zip \
  --frozen-summary results/similarity_blocal_prospective_artifacts/final/similarity_blocal_prospective_summary.json \
  --output /tmp/similarity_blocal_prospective_independent_audit.json
```

The checker exits successfully when artifact integrity is intact and its independently computed counts, gates and decision match the frozen evaluator. A scientific pass is not expected; `frozen_claim_supported` must remain `false` for this archived run.

## Next justified step

The next step is an opened-data reporting-integrity canary that removes only the optional GUI image call from the pinned final-report flow while preserving extraction, timing, electrical reports and final products. Any such repair must be frozen and validated before a new prospective study. A future confirmation must use new geometries and seeds, retain every all-required gate, and treat this cohort as permanently opened. No new breakthrough or novelty claim is warranted until that distinct study completes and a primary-literature audit supports it.
