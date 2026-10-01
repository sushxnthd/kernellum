# Kernellum

**An independent AI research lab building systems that can reason, investigate, and discover.**

Kernellum's research programs are Machine Reasoning, Scientific Discovery,
AI Systems & Architecture, and Evaluation & Reliability. The accelerator work
below is the current concrete implementation within AI Systems & Architecture.

### Scientific Discovery: choose the next experiment

A new [experiment-selection component](docs/DISCOVERY_DESIGN_RESULT.md) accepts
observed measurements and recommends the next point to measure. It now has a
completed 52-equation external-formula evaluation, with full query traces and a
separate arithmetic audit. **The proposed adaptive method failed its improvement
gate against space-filling sampling.** The usable baseline and all negative
results are preserved. This is a non-hardware research component, not yet an
autonomous scientist or a scientific breakthrough.

### Scientific Discovery: model revision follow-up

The [48-equation follow-up](docs/MODEL_REVISION_RESULT.md) ran 2,592 trials on
previously excluded higher-dimensional rows. Observed-data model selection reduced
geometric mean prediction error **70.44%** against the earlier quadratic predictor
using identical measurements (47/48 equation wins). Its broader gate still failed
against an RBF-only control. The proposed acquisition rule added only **4.64%**
over maximin with the revised model. **Both full acceptance gates failed; no
breakthrough is established.** All traces and a second arithmetic implementation
recomputing 7,776 checkpoint errors are retained.

### Scientific Discovery: representation revision

The [publicly frozen external confirmation](docs/REPRESENTATION_REVISION_RESULT.md)
tested 39 UQ functions across 2,730 method trajectories. Transforming inputs and
outputs reduced geometric mean error 69.59% against original-space selection, but
**the full gate failed** against stronger controls and one noisy prediction
exploded to 8.427e16 NMSE. A second arithmetic implementation verifies all 5,460
checkpoint scores. Nested cross-validation and bounded-output repairs were also
tested and rejected as breakthrough candidates. These are research results;
the unstable ensemble is not promoted as a default predictor.

The [acquisition and noise follow-up](docs/REPRESENTATION_ACQUISITION_RESULT.md)
completed another 2,808 exploratory outcomes. Hybrid measurement selection reduced
geometric mean error 20.52% versus maximin on the opened cohort, but its advantage
over a matching hybrid control was only 1%. Noise-aware fitting added about 3%
and regressed on clean data. **Neither is a verified breakthrough.**

### Try the first engineering preview

[Route Review](docs/ROUTE_REVIEW.md) compares supplied K1 route observations for
your GEMM dimensions and resource limits. It produces a ranked report with
exclusion reasons and source hashes, offline and without an API key.
It reviews existing evidence; customer adoption and time savings are unvalidated.
The [customer validation sprint](docs/YC_EXECUTION_SPRINT.md) defines the next
commercial tests and a source-grounded application draft.

**Latest research decision:** the 27 September B-local audit closed that
intervention as a negative result. See the
[closure audit](docs/SIMILARITY_BLOCAL_NOVELTY_SCREEN.md) and
[final prospective report](docs/SIMILARITY_BLOCAL_FLOWQUALIFIED_REPORT.md).
The earlier bounded K1 results below do not overturn that decision.

Kernellum is currently a research-first system, not a production EDA product. The core question is whether an automated search can choose hardware architectures for AI workloads whose predicted advantages survive synthesis, place-and-route, and eventually physical measurement.

## Current result: K1

K1 implements a parameterized INT8 tiled GEMM engine and a closed-loop ECP5 physical-design search.

The evidence chain is:

```text
Transformer workload
      ↓
analytical architecture model
      ↓
final-route-Fmax surrogate
      ↓
candidate acquisition
      ↓
RTL
      ↓
functional simulation
      ↓
synthesis
      ↓
place-and-route
      ↓
physical-design feedback
      ↺
```

### Routed architecture validation

Nine frozen architectures were synthesized and routed on a Lattice ECP5-85K / CABGA381 target.

- **9 / 9** routes completed
- predicted vs final-routed workload ranking: **mean Spearman ρ = 0.944**
- analytically selected winner: **0.583% mean final-routed regret**
- DSP prediction: **ρ = 1.000**
- functional tiled-GEMM RTL simulation: **PASS**

### Closed-loop physical-design search

K1 then expanded to a frozen **172-architecture** design space.

Using only the original nine routed observations:

- Kernellum selected **4** new architectures
- an equal-budget random arm selected **4**
- total physical implementations attempted: **17 / 172 = 9.88%**
- all **8 / 8** new designs routed
- final-route-Fmax surrogate MAPE: **6.475%**
- active-search final mean best latency: **16.74 ms**
- random-control final mean best latency: **19.44 ms**
- active search improved the routed optimum on **12 / 12** Transformer GEMMs
- random search improved it on **0 / 12**

These latency values are derived from the K1 kernel cycle model and **final-routed Fmax**, not measurements from a physical FPGA board.

See:

- `docs/K1_REPORT.md`
- `docs/K1_CLOSED_LOOP_REPORT.md`
- `results/k1_routes.csv`
- `results/k1_validation.json`
- `results/k1_closed_loop_routes.csv`
- `results/k1_closed_loop_validation.json`
- `docs/K1_FINAL_ROUTE_CORRECTION_REPORT.md`

## Project SIMILARITY: corrected routed-timing result

Kernellum also isolated a physical-design effect that the architecture search should model explicitly: operand-distribution topology changes routed timing scaling.

A preregistered correction study used only nextpnr post-route JSON timing on 96 ECP5 implementations. Square arrays and seeds 17 to 19 formed the discovery set; unseen rectangular arrays and seeds 20 to 22 formed the held-out set.

- **96 / 96** routes completed with exact one-DSP-per-PE mapping
- broadcast critical-period slope: **0.4503 ns / sqrt(PE)**
- registered local-transport slope: **0.1493 ns / sqrt(PE)**
- held-out tax MAE: **0.3039 ns**
- held-out tax RMSE: **0.3815 ns**
- held-out predicted-versus-observed correlation: **0.8921**
- positive broadcast tax: **6 / 6** unseen device/geometry pairs
- all **13 / 13** frozen criteria passed

The supported claim is limited to this ECP5 INT8 MAC-fabric family. It is a final-routed timing result, not a physical-board, power, energy or vendor-independent result.

See `docs/SIMILARITY_ROUTED_LAW_REPORT.md` and `results/similarity_routed_law_summary.json`.

## Project SIMILARITY: route-aware portfolio confirmation

The latest preregistered study addresses placement-and-routing variability directly. Broadcast-only characterization on three selection seeds constructed a two-candidate local-architecture portfolio for each Transformer workload. On three disjoint deployment seeds, the compiler inspected final-route timing for only those two candidates before choosing one.

- **72 / 72** new final-route implementations completed
- all **13 / 13** frozen confirmation criteria passed
- portfolio choices beat the best broadcast-only implementation in **36 / 36** unseen deployment cases
- mean workload-latency improvement: **23.56%**
- mean regret versus the full routed oracle: **1.44%**
- maximum per-seed mean oracle regret: **3.58%**
- second-ranked candidate selected in **21 / 36** cases
- regret reduction versus rank-1 alone: **2.15 percentage points**
- mean sequential-logic cost: **70.57% more flip-flops**, with **0.00% additional block RAM**

This confirms a bounded physical-feedback protocol within the functional ECP5 INT8 GEMM family. It remains a final-route result, not board-measured latency, power, energy or vendor-independent evidence.

See `docs/SIMILARITY_PORTFOLIO_CONFIRMATION_REPORT.md` and `results/similarity_portfolio_summary.json`.

## K2 board-ready

K2 is the current hardware-validation stage.

The repository now includes:

- official ECP5 Evaluation Board pin constraints;
- 12 MHz board-clock bring-up;
- synthesizable 115200-baud UART transport;
- a hardware accelerator busy-cycle counter;
- host-side randomized signed-INT8 GEMM verification;
- three frozen board variants;
- automated Yosys + nextpnr + ecppack bitstream generation.

**No K2 physical measurement is claimed yet.** K2 becomes physically validated only after the generated bitstreams run on the real board and the preregistered 100-trial-per-architecture gate passes.

See `docs/K2_PLAN.md`, `docs/K2_BOARD_SETUP.md`, and `docs/EXPERIMENT_LEDGER.md`.

## Evidence ladder

### K0

Analytical accelerator design-space exploration over 12 Transformer GEMMs.

At 256 architecture evaluations:

- evolutionary search mean regret: **0.431%**
- random search mean regret: **3.788%**

The K0 values are analytical estimates only.

### K0.5

The first parameterized MAC-array RTL was checked with Icarus Verilog and synthesized with Yosys.

Across nine Xilinx-7 synthesis configurations:

- DSP rank Spearman: **1.000**
- BRAM rank Spearman: **1.000**
- generic multiplier preservation: **100%**
- mean BRAM prediction error: **11.21%**

K0.5 exposed a target-specific BRAM granularity effect instead of hiding it.

### K1

K1 adds:

- tiled A/B buffers
- controller-driven execution
- accumulation across K chunks
- ECP5 synthesis
- nextpnr place-and-route
- final-routed Fmax extraction from nextpnr report JSON
- target-aware ECP5 DSP/BRAM modelling
- final-route-Fmax surrogate
- active acquisition
- equal-budget random control
- physical-design feedback ingestion

## Reproduction

Python tests:

```bash
PYTHONPATH=. python -m pytest -q
```

K0 analytical experiment:

```bash
python experiments/k0_transformer/run.py
```

K0.5 functional RTL simulation:

```bash
bash scripts/run_rtl_sim.sh
```

K1 tiled-GEMM simulation:

```bash
bash scripts/run_k1_sim.sh
```

K1 frozen routing sweep, with Yosys and nextpnr-ecp5 installed:

```bash
PYTHONPATH=. python scripts/run_k1_pnr.py
```

K1 closed-loop routed-feedback experiment:

```bash
PYTHONPATH=. python scripts/run_k1_closed_loop.py
```

GitHub Actions contains reproducible workflows for the HDL and physical-design experiments. K1 timing is read only from nextpnr's final post-route report JSON.

Corrected SIMILARITY routed-law validation:

```bash
PYTHONPATH=. python scripts/similarity_routed_validate.py
```

## Current scientific boundary

Kernellum has **not** yet established:

- physical-board latency
- power or energy consumption
- thermal behaviour
- end-to-end Transformer inference
- ASIC PPA
- superiority to commercial EDA systems
- universality of the SIMILARITY timing relation across vendors or RTL families
- patentability or commercial licensing value

The next gate is physical FPGA execution.

## Next: K2

K2 should freeze one or more K1-selected architectures on a real FPGA board and measure:

- achieved clock
- kernel latency
- power
- energy per operation / inference kernel
- prediction error relative to routed estimates

Only after that validation should Kernellum make physical hardware performance claims.

## Licensing and IP

No broad open-source license has been attached to the reset-stage repository yet. Public research infrastructure and potentially protectable architecture/search IP should be separated deliberately before a final licensing decision.

See `docs/IP_BOUNDARY.md`.
