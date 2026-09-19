# Kernellum K0 Technical Note

## Objective

K0 tests whether a budgeted search procedure can recover near-optimal accelerator configurations for Transformer GEMMs without enumerating the full design space.

Every latency, resource, traffic and energy value in K0 is an analytical estimate. K1 must validate rankings against synthesis and measured hardware.

## Design space

Each candidate varies systolic-array geometry, dataflow, tiling and on-chip buffer size. INT8 is fixed in the benchmark. The discrete space contains 24,576 candidates per workload with hard limits of 512 DSP-equivalent units and 120 BRAM18K-equivalent units.

The suite contains 12 dense GEMMs representative of a small Transformer encoder at sequence lengths 64, 128 and 256.

## Search result

Random and evolutionary search receive identical evaluation budgets and are repeated over five seeds per workload.

At 256 evaluations, evolutionary search reaches 0.431% mean latency regret versus 3.788% for random search. Exact-optimum rates are 60.0% and 8.3%, respectively.

At 512 evaluations, evolutionary search reaches 0.069% mean regret and a 95.0% exact-optimum rate. Random search reaches 1.674% mean regret and a 13.3% exact-optimum rate.

## What K0 establishes

1. A reproducible workload-to-architecture experiment harness exists.
2. Evolutionary search is more sample-efficient than random search under the K0 analytical evaluator.
3. The optimizer selects different array orientations, tile shapes, buffers and dataflows across workload shapes.
4. Exhaustive enumeration supplies known ground truth for the finite K0 space.

## What K0 does not establish

- real FPGA latency or power;
- timing closure;
- quantization accuracy effects;
- superiority to mature accelerator generators;
- novelty of evolutionary search;
- commercially valuable IP.

## K0.5 validation gate

Proceed only if predicted latency/resource rankings correlate materially with synthesized results and top-ranked candidates remain competitive after synthesis constraints are applied.

Kill or pivot the current model if ranking correlation remains weak after calibration, synthesis invalidates many supposedly feasible designs, simple heuristics match the search with fewer evaluations, or mature open generators dominate comparable design points.

## Immediate K1 direction

Add a parameterized HLS/RTL generator for one dense GEMM engine, automated correctness tests, synthesis-result ingestion, and calibration of K0's estimator. FPGA deployment follows after that loop works.
