# K1 final-route timing correction

Date frozen: 2026-09-20

## Audit finding

`scripts/run_k1_pnr.py` and `scripts/run_k1_closed_loop.py` currently collect every nextpnr console Fmax line and retain the minimum. nextpnr reports timing after placement and after routing, so the stored K1 metric is a reproducible worst-implementation-stage Fmax, not an authoritative final-route Fmax.

The functional RTL, synthesis, DSP/BRAM counts and route-success claims are unaffected. Timing-derived rankings, latency estimates, surrogate error and closed-loop comparisons require correction.

## Frozen correction

1. Add `--report <path>` to every K1 nextpnr invocation.
2. Read only `report.json["fmax"][clock]["achieved"]` and use the minimum achieved value if more than one clock exists.
3. Record the timing metric as `post_route_report_json` in every route row.
4. Rerun the original nine-architecture K1 corpus with the architecture set, workload suite, target, package, seed and gate thresholds unchanged.
5. Generate closed-loop proposals only from the corrected nine-route corpus.
6. Rerun the unchanged four-active versus four-random experiment with the original random seed and gate thresholds.

## Frozen K1 gate

- at least 8/9 routes succeed;
- DSP rank Spearman at least 0.95;
- mean workload rank Spearman at least 0.80;
- every analytically predicted winner routes;
- mean predicted-winner routed regret at most 15%.

## Frozen closed-loop gate

- at least 7/8 new routes succeed;
- at most 10% of the 172-architecture pool is physically attempted;
- surrogate final-route-Fmax MAPE at most 20%;
- active mean final-best latency is no worse than the equal-budget random arm;
- active improves at least as many workloads as random.

No threshold may change after the corrected results are opened.

## Claim boundary

A pass restores the K1 and closed-loop evidence under final-route timing. It remains a toolchain place-and-route result, not a physical-board, power, energy or cross-vendor result.

