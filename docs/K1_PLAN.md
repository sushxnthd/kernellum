# Kernellum K1: routed architecture-selection gate

Date frozen: 2026-09-19

K1 asks a narrower question than the long-term company thesis:

> Can Kernellum rank workload-specific accelerator architectures well enough that the predicted choice remains competitive after real FPGA synthesis and place-and-route?

## Target

The first K1 target is a Lattice ECP5-85K-class device using the open Yosys + nextpnr-ecp5 flow.

This is intentionally a single-target experiment. K1 does not attempt multi-vendor portability.

## Kernel

K1 uses an INT8 tiled GEMM kernel with:

- parameterized ROWS x COLS MAC array;
- packed A and B tile buffers;
- runtime K length up to K_TILE;
- controller-driven clear / MAC / done sequencing;
- repeatable accumulation across K chunks;
- self-checking simulation.

The routing harness instantiates the real engine behind a deterministic on-chip loader so the datapath, buffers and control logic cannot be optimized away.

## Candidate set

Nine stratified architectures are frozen before routing:

1. 4x4, K_TILE=16
2. 4x8, K_TILE=32
3. 8x4, K_TILE=32
4. 8x8, K_TILE=16
5. 8x8, K_TILE=32
6. 8x8, K_TILE=64
7. 8x12, K_TILE=32
8. 12x8, K_TILE=32
9. 10x10, K_TILE=32

The set deliberately contains equal-PE-count orientation pairs and equal-array/different-buffer-depth candidates.

## Workload suite

Architecture ranking is evaluated on the same 12 Transformer GEMMs used in K0: qkv, attention-output, FFN-expand and FFN-contract shapes at sequence lengths 64, 128 and 256.

For a workload MxK times KxN, K1 predicts kernel cycles as:

    m_tiles = ceil(M / ROWS)
    n_tiles = ceil(N / COLS)
    k_chunks = ceil(K / K_TILE)

    cycles_per_output_tile =
        2*K                    # tile-buffer load + MAC work
        + 3*k_chunks           # per-chunk control overhead
        + 2                    # clear/finalize overhead

    predicted_cycles =
        m_tiles * n_tiles * cycles_per_output_tile

The analytical ranking uses a fixed 100 MHz frequency. Routed ranking uses the same cycle model divided by nextpnr's achieved maximum clock frequency. This isolates whether physical timing changes the architectural choice.

## Predeclared K1 gate

K1 passes only if all of the following hold:

1. self-checking RTL simulation passes;
2. at least 8 of 9 candidates complete place-and-route;
3. predicted PE count vs synthesized ECP5 DSP count has Spearman rho >= 0.95;
4. mean per-workload Spearman rho between fixed-frequency predicted latency and routed-Fmax latency is >= 0.80;
5. the fixed-frequency predicted winner has mean routed-latency regret <= 15% versus the routed optimum across the 12 workloads;
6. no failed route is silently assigned a favorable score.

These thresholds are frozen before the first K1 P&R result is inspected.

## Interpretation

A pass means the ranking is useful for this candidate family and target. It does not establish measured board latency, power, energy, ASIC behavior, or commercial superiority.

A failure is also useful: it identifies whether physical timing, resource mapping or routing feasibility is strong enough to invalidate the current analytical search.
