# Kernellum Project SIMILARITY

Date frozen: 2026-09-20

## Scientific question

Do post-route AI accelerator architectures obey a compact physical-design similarity law that transfers across FPGA device sizes and unseen workload shapes?

This project is not primarily an optimizer benchmark. It is a search for a falsifiable empirical law.

## Architecture family

The frozen RTL family is the existing Kernellum tiled INT8 GEMM engine:

- ROWS in {2,4,6,8,10,12,14}
- COLS in {2,4,6,8,10,12,14}
- K_TILE in {8,16,32,64}
- ROWS*COLS <= 120
- fixed INT8 precision
- fixed accumulator width and controller structure

This gives 172 architecture points on devices large enough to fit them.

## FPGA family

All experiments use the open Yosys + nextpnr-ecp5 flow, CABGA381 package, speed grade 6 where supported.

Device roles are frozen before corpus generation:

- LFE5U-45F: **law discovery**
- LFE5U-85F: **held-out device validation**
- LFE5U-25F: **low-capacity replication** for architectures with <=48 PEs

The 25F subset contains 100 architecture points.

## Raw observables

For every attempted route:

- route success/failure
- routed maximum clock frequency
- MULT18X18D count
- DP16KD count
- LUT4 count
- TRELLIS_FF count
- ROWS
- COLS
- K_TILE
- device

No physical-board measurement is involved.

## Candidate similarity variables

The discovery stage may search compact formulae built from:

- PE count: P = ROWS*COLS
- array perimeter: S = ROWS+COLS
- array anisotropy: A = |log(ROWS/COLS)|
- tile depth: T = K_TILE
- log2(T)
- device-normalized DSP occupancy
- device-normalized BRAM occupancy
- device-normalized LUT occupancy

The key test is whether a low-complexity normalized formula learned on 45F predicts 85F and 25F timing materially better than raw-coordinate baselines.

## Discovery protocol

1. Route the complete 172-point architecture space on 45F.
2. Fit only low-complexity interpretable timing laws.
3. Prefer formulae with <=4 independent terms.
4. Select using leave-one-architecture-out or grouped cross-validation.
5. Freeze the selected law and all coefficients before reading held-out-device errors.

## Held-out validation

After the law is frozen:

1. evaluate it without refitting on the 85F corpus;
2. evaluate it without refitting on the 25F low-capacity corpus;
3. report MAPE, R², rank correlation, and residual structure;
4. explicitly test orientation pairs ROWSxCOLS vs COLSxROWS;
5. reject universality if systematic device-specific residuals remain large.

## Workload phase-diagram test

The routed architecture corpus is reused to evaluate workload optima without new P&R.

Discovery workloads:

- M,N in {64,96,128,192,256,384}
- K in {128,192,256,312,384,512}

Held-out workload dimensions:

- M,N in {80,112,160,224,320,448}
- K in {160,224,320,448}

For each GEMM, routed latency is:

    predicted engine cycles / routed Fmax

A candidate regime law may use only dimensionless quantities built from workload dimensions, architecture dimensions, and normalized device resources.

## Breakthrough criteria

Project SIMILARITY is considered a genuine positive scientific result only if at least one compact law satisfies all of:

1. discovery-set timing MAPE <= 8%;
2. held-out 85F timing MAPE <= 12% without refitting;
3. held-out 25F timing MAPE <= 15% without refitting;
4. held-out-device Spearman rank correlation >= 0.90;
5. the law substantially outperforms a raw linear model using ROWS, COLS, K_TILE;
6. residual analysis shows no large unexplained orientation/device phase;
7. a workload-level regime rule derived from the law predicts the optimal architecture family on held-out workload shapes significantly better than chance and simple largest-array heuristics.

If these fail, the universal-law hypothesis is rejected or revised. Results are not relabeled post hoc as a breakthrough.

## Stronger breakthrough condition

The strongest result would be a dimensionless critical boundary or scaling relation that:

- predicts a change in optimal architecture family;
- transfers across 45F, 85F, and 25F;
- survives held-out workload shapes;
- admits a mechanistic explanation from routing/fanout/memory structure.

Only such a result should be described externally as a hardware similarity law.
