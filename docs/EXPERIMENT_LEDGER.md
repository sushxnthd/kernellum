# Kernellum experiment ledger

This file is the index of the technical evidence. Chat history is not treated as the research record.

## K0: analytical design-space exploration

Question: can a budgeted search recover near-optimal accelerator configurations without enumerating the full finite design space?

Evidence:

- `experiments/k0_transformer/run.py`
- `results/benchmark_summary.csv`
- `results/search_efficiency.csv`
- `results/search_efficiency_summary.csv`
- `docs/K0_REPORT.md`

Result: at 256 evaluations, evolutionary search achieved 0.431% mean analytical latency regret versus 3.788% for random search.

Boundary: analytical model only.

## K0.5: synthesis calibration

Question: do coarse DSP/BRAM resource rankings survive real RTL elaboration and technology mapping?

Evidence:

- `docs/K05_PLAN.md`
- `rtl/kernellum_mac_array.sv`
- `scripts/synthesize_k05.py`
- `results/k05_synthesis.csv`
- `results/k05_validation.json`
- `docs/K05_REPORT.md`

Result: predeclared gate passed; DSP and BRAM rank Spearman both 1.000.

Boundary: no place-and-route or board measurement.

## K1: routed architecture ranking

Question: do workload-specific architecture rankings remain useful after synthesis and ECP5 place-and-route?

Evidence:

- `docs/K1_PLAN.md`
- `rtl/kernellum_gemm_engine.sv`
- `scripts/run_k1_pnr.py`
- `results/k1_routes.csv`
- `results/k1_validation.json`
- `docs/K1_REPORT.md`

Result: after the final-route timing correction, 9/9 routed, mean predicted-versus-final-routed workload rank Spearman 0.9441, and mean predicted-winner regret 0.5828%.

## K1 closed loop

Question: can physical-design observations guide a fixed routing budget better than an equal-budget random arm?

Evidence:

- `docs/K1_CLOSED_LOOP_PLAN.md`
- `kernellum/k1/closed_loop.py`
- `results/k1_closed_loop_proposals.json`
- `results/k1_closed_loop_routes.csv`
- `results/k1_closed_loop_validation.json`
- `docs/K1_CLOSED_LOOP_REPORT.md`

Result: after rebuilding the baseline from final-route timing, 8/8 new routes succeeded; 17/172 designs were physically attempted; surrogate Fmax MAPE was 6.4750%; active mean final-best latency was 16.7398 ms versus 19.4428 ms for random; active improved 12/12 workloads versus 0/12 for the fixed-seed random arm.

Boundary: routed timing, not physical-board measurement.

Correction evidence:

- `docs/K1_FINAL_ROUTE_CORRECTION_PLAN.md`
- `docs/K1_FINAL_ROUTE_CORRECTION_REPORT.md`
- GitHub Actions runs `35508660108` and `35508660102`

Historical K1 timing values used a worst-implementation-stage console parser and are superseded by the corrected result files.

## Project SIMILARITY: corrected final-route causal law

Question: does nonlocal operand broadcast cause a size-dependent final-routed timing penalty relative to registered nearest-neighbor transport, and does a relation learned only from square arrays transfer to unseen rectangular arrays and disjoint seeds?

Evidence:

- `docs/SIMILARITY_ROUTED_LAW_PLAN.md`
- `scripts/similarity_routed_route.py`
- `scripts/similarity_routed_validate.py`
- `results/similarity_routed_law_combined.csv`
- `results/similarity_routed_law_summary.json`
- `docs/SIMILARITY_ROUTED_LAW_REPORT.md`
- GitHub Actions run `35498260194`

Result: all 96 routes succeeded with exact DSP mapping. The broadcast slope was 0.4503 ns / sqrt(PE) and the local slope was 0.1493 ns / sqrt(PE). The discovery-frozen tax equation transferred to six unseen rectangular device/geometry pairs with 0.3039 ns MAE, 0.3815 ns RMSE and 0.8921 correlation. All 13 preregistered criteria passed.

Boundary: the result is limited to the tested ECP5 INT8 MAC-fabric family and final-routed timing. It does not establish physical-board performance, power, energy, cross-vendor universality or end-to-end workload latency.

Correction note: numerical routed-law coefficients in earlier SIMILARITY reports used a historical worst-implementation-stage parser. They remain part of the audit trail but are superseded by `SIMILARITY_ROUTED_LAW_REPORT.md` for final-routed timing claims.

## Project SIMILARITY: cross-technology ASIC transfer

Question: can a dimensionless operand-transport timing law discovered in
NanGate45 predict unopened Sky130HD geometries after a frozen six-geometry
calibration?

Status: preregistered; no eligible route result exists at freeze time.

Frozen evidence definition:

- `docs/SIMILARITY_ASIC_TRANSFER_PREREGISTRATION.md`
- `rtl/similarity_asic_transfer_top.sv`
- `rtl/tb_similarity_asic_transport_equivalence.sv`
- `scripts/similarity_asic_transfer_route.py`
- `scripts/similarity_asic_transfer_validate.py`
- `.github/workflows/similarity-asic-transfer.yml`

Boundary: two open/academic standard-cell platforms in one pinned ORFS
toolchain; post-route timing and implementation costs only. No fabricated
silicon, commercial signoff, power, energy or end-to-end workload claim.

## K2: physical FPGA validation

Status: board-ready infrastructure under development; no physical result may be recorded until a real ECP5 Evaluation Board is programmed and measured.

Frozen plan:

- `docs/K2_PLAN.md`

Planned evidence:

- three board bitstreams
- UART host protocol
- hardware busy-cycle counter
- 100+ deterministic randomized trials per architecture
- raw JSON trial logs
- post-run `docs/K2_REPORT.md`

No simulated or routed result may be labelled as a K2 physical measurement.
