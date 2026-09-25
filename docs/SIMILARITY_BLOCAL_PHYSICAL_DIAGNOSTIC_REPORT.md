# SIMILARITY B-local physical diagnostic: exploratory pass

Status: **all fixed opened-data continue gates passed; not confirmation**.

The source and thresholds were fixed in [the diagnostic plan](SIMILARITY_BLOCAL_PHYSICAL_DIAGNOSTIC_PLAN.md) by PR #68 at `f2b2c59fb75e1753e49c3f99e488cc5bf91855f5`, before GitHub Actions [run 36070743684](https://github.com/sushxnthd/kernellum/actions/runs/36070743684) routed any candidate. The run finished on 2026-09-24 23:53 UTC with all six route jobs and its validator successful. The intervention preserves all B bits and A[7] per processing element; A[6:0] and valids retain stride-two grouping. Both tested geometries (5x8 and 8x5) and seeds (53, 71, 89) were already opened by earlier work. This is evidence of a plausible mechanism, never a prospective test or scientific breakthrough.

## Fixed-gate result

- Both signed-GEMM functional logs report equivalence against full local.
- Exactly 12 unique routes are present, three seeds in each of four platform/shape groups. All twelve have zero final setup, hold, slew, fanout, capacitance and DRC violations; twelve final timing reports and twelve empty DRC reports are in the original ZIPs.
- Each 5x8 route has 1,979 DFFs, 86.65% of full local's 2,284; each 8x5 route has 1,972, 88.35% of full local's 2,232. Synthesis cell area is lower than full local on every matched row.
- All four groups have at least 5% median raw period benefit over broadcast and at least 70% retention of full local's period benefit. Three groups jointly beat broadcast and full local on median area-normalized throughput; both platforms contribute a win.
- Target NanGate45 8x5 median period is 1.53 ns, versus ordinary stride-two 1.58 ns and the merged-replica no-op 1.56 ns, differences of 0.05 and 0.03 ns above the frozen 0.04 and 0.02 ns minimums. The three target maximum paths launch from a B[2] replica Q at fanout 9, 9 and 9, median 9 versus the frozen maximum 10.

| Platform | Shape | B-local median ns | Raw benefit vs broadcast | Retained local benefit | Density vs broadcast | Density vs local |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| NanGate45 | 5x8 | 1.54 | 10.47% | 79.17% | 1.0485 | 1.0042 |
| NanGate45 | 8x5 | 1.53 | 8.38% | 80.95% | 1.0254 | 1.0037 |
| Sky130HD | 5x8 | 6.89 | 13.60% | 150.65% | 1.0878 | 1.0822 |
| Sky130HD | 8x5 | 7.49 | 11.26% | 70.31% | 1.0617 | 0.9761 |

The final Sky130HD 8x5 group loses the area-normalized comparison with full local. Its retention of 70.31% is close to the 70% gate; the NanGate45 density advantages over local are likewise small. The three-seed observations do not establish robustness on new layouts or general workload usefulness. The change in the observed critical-path launch register is consistent with the targeted fanout mechanism, but a stronger causal claim requires further controlled comparisons.

## Reproduction and provenance

All eight original Actions ZIPs (six route shards, functional and final summary), the six extracted route CSVs, and the exact summary JSON are in `results/similarity_blocal_physical_artifacts/` and `results/similarity_blocal_physical_summary.json`. The independently written checker is `scripts/similarity_blocal_physical_independent_audit.py`; its JSON output is `results/similarity_blocal_physical_independent_audit.json`. It extracts the original ZIPs, checks their 12 original reports, validates functional logs and source SHA, recomputes every arithmetic gate from the published stride-two baseline and critical-bit no-op CSVs, and checks the three launch-Q fanouts directly from route reports. Independently rerunning the original frozen evaluator against these original ZIPs reproduced the published summary **byte for byte** (SHA-256 `d141b54720557bb303df16c8225c42515fdb90c2ec9696207f313c8b96eb9366`). The original artifact hashes are recorded in the independent audit JSON.

Run from the repository root:

```sh
python scripts/similarity_blocal_physical_independent_audit.py \
  --artifacts results/similarity_blocal_physical_artifacts \
  --baseline results/similarity_stride2_download \
  --prior results/similarity_criticalbit_download \
  --output /tmp/similarity_blocal_physical_audit.json
```

The routed GDS/ODB/SPEF/netlist outputs are identified by SHA-256 in each CSV, but these large design binaries were not included in the retained Actions artifacts. The original route reports, logs and summary are retained. The workflow route and validator jobs are pinned to the exact `f2b2c59...` commit so that publishing the report cannot launch a second physical experiment.

## Next evidence needed

Freeze a separate confirmatory protocol on source, geometries and seeds unused in all earlier ASIC experiments, with functional, electrical, DFF, synthesis area, timing and area-normalized throughput gates on main before any confirmatory route. The earlier 7x7, 2x4, 4x2, 3x6, 6x3, 5x5, 3x8, 8x3, 5x9, 9x5, 4x7, 7x4, 5x8 and 8x5 shapes and their seeds remain excluded. A positive confirmation would still require novelty and practical-utility audits against primary prior work before a breakthrough claim.
