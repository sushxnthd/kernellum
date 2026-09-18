# KRN-BENCH-001 Protocol — Multi-Workload Physical-Feedback Benchmark

**Evidence ID:** KRN-BENCH-001  
**Target:** ULX3S-85F / LFE5U-85F-6BG381C / CABGA381  
**Board clock:** 25 MHz  
**Status:** automated execution implemented; post-route results are promoted only from a successful benchmark P&R run.

## Research question

Does Kernellum's architecture choice remain physically constrained when the same compiler/backend is applied to multiple dense-network shapes, rather than one hand-selected demonstration?

## Workloads

The benchmark uses deterministic synthetic three-layer dense graphs. They are deliberately not presented as customer or application benchmarks.

| Case | Shape |
|---|---|
| compact | 32 → 16 → 8 → 4 |
| reference | 64 → 32 → 16 → 10 |
| wide | 128 → 64 → 32 → 8 |

All cases follow the currently supported ONNX subset:

```text
Gemm → ReLU → Gemm → ReLU → Gemm
```

## Architecture sweep

Each workload is compiled and routed with:

- 1 MAC lane
- 2 MAC lanes
- 4 MAC lanes
- 8 MAC lanes

The same ULX3S-85F package, clock and LPF pin constraints are used for every run.

## Deterministic pre-route cycle model

| Workload | 1 lane | 2 lanes | 4 lanes | 8 lanes |
|---|---:|---:|---:|---:|
| 32 → 16 → 8 → 4 | 728 | 392 | 224 | 140 |
| 64 → 32 → 16 → 10 | 2,836 | 1,476 | 796 | 456 |
| 128 → 64 → 32 → 8 | 10,704 | 5,456 | 2,832 | 1,520 |

These are compiler cycle-model values. They are not measured latency.

## Physical-feedback selection rule

For each workload:

> choose the minimum modeled cycle count among the swept architectures whose post-route Fmax meets the ULX3S 25 MHz board clock.

If none of the 1/2/4/8-lane variants closes 25 MHz, the benchmark records **no feasible swept architecture** rather than inventing a selection.

## Recorded evidence

For every workload/lane pair the automated flow records:

- modeled cycle count;
- modeled core latency at 25 MHz;
- post-route Fmax;
- timing pass/fail at 25 MHz;
- TRELLIS_COMB usage;
- TRELLIS_FF usage;
- TRELLIS_RAMW usage;
- MULT18X18D usage;
- Yosys log;
- nextpnr log;
- routed configuration.

For each timing-feasible selected architecture the flow additionally generates:

- selected ECP5 configuration;
- ULX3S reference bitstream;
- SHA-256 digest of that bitstream.

## Reproduce

```bash
pip install -e '.[test,onnx]'
python scripts/build_benchmark_matrix.py
bash scripts/run_benchmark_pnr_sweep_ulx3s_85f.sh
```

CI workflow:

```text
.github/workflows/benchmark-pnr.yml
```

## Evidence boundary

KRN-BENCH-001 is designed to establish **multi-shape board-targeted place-and-route evidence**.

It does not by itself establish:

- application-level accuracy;
- an external design-partner workload;
- physical-board execution;
- measured latency or throughput;
- measured power;
- measured energy per inference;
- ASIC PPA.

Those require separate evidence records.
