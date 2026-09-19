# Kernellum

**AI-native computer architecture research for workload-specific accelerator synthesis with physical-design feedback.**

Kernellum is currently a research-first system, not a production EDA product. The core question is whether an automated search can choose hardware architectures for AI workloads whose predicted advantages survive synthesis, place-and-route, and eventually physical measurement.

## Current result: K1

K1 implements a parameterized INT8 tiled GEMM engine and a closed-loop ECP5 physical-design search.

The evidence chain is:

```text
Transformer workload
      ↓
analytical architecture model
      ↓
routed-Fmax surrogate
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
- predicted vs routed workload ranking: **mean Spearman ρ = 0.927**
- analytically selected winner: **1.00% mean routed regret**
- DSP prediction: **ρ = 1.000**
- functional tiled-GEMM RTL simulation: **PASS**

### Closed-loop physical-design search

K1 then expanded to a frozen **172-architecture** design space.

Using only the original nine routed observations:

- Kernellum selected **4** new architectures
- an equal-budget random arm selected **4**
- total physical implementations attempted: **17 / 172 = 9.88%**
- all **8 / 8** new designs routed
- routed-Fmax surrogate MAPE: **11.95%**
- active-search final mean best latency: **24.01 ms**
- random-control final mean best latency: **26.61 ms**
- active search improved the routed optimum on **12 / 12** Transformer GEMMs
- random search improved it on **0 / 12**

These latency values are derived from the K1 kernel cycle model and **routed Fmax**, not measurements from a physical FPGA board.

See:

- `docs/K1_REPORT.md`
- `docs/K1_CLOSED_LOOP_REPORT.md`
- `results/k1_routes.csv`
- `results/k1_validation.json`
- `results/k1_closed_loop_routes.csv`
- `results/k1_closed_loop_validation.json`

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
- routed Fmax extraction
- target-aware ECP5 DSP/BRAM modelling
- routed-Fmax surrogate
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

GitHub Actions contains reproducible workflows for the HDL and physical-design experiments.

## Current scientific boundary

Kernellum has **not** yet established:

- physical-board latency
- power or energy consumption
- thermal behaviour
- end-to-end Transformer inference
- ASIC PPA
- superiority to commercial EDA systems
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
