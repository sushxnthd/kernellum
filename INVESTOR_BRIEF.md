# Kernellum — Investor Brief

## What Kernellum is building

**Kernellum is building an AI-native compiler for workload-specific accelerators.**

The long-term interface is simple:

```text
trained model + deployment constraints
                ↓
           Kernellum
                ↓
hardware IR → architecture search → verified RTL
                ↓
       FPGA / ASIC implementation
```

Instead of treating hardware as a fixed destination for an AI model, Kernellum makes the workload and deployment constraints inputs to hardware design.

Kernellum is currently research-stage. It does **not** yet claim production ASIC readiness or measured physical-FPGA performance.

## Public technical evidence

The current model-to-RTL prototype demonstrates:

| Evidence | Public result |
|---|---:|
| Float held-out accuracy | 96.22% |
| INT8 held-out accuracy | 96.44% |
| Float / INT8 prediction agreement | 99.78% |
| Cycle-model / vector-INT8 agreement | 450 / 450 |
| RTL golden-vector simulation | 32 / 32 PASS |
| Selected architecture | 4 MAC lanes |
| Modeled core compute | 680 cycles |
| Generic Yosys synthesis | PASS, 0 CHECK problems |
| ECP5 family mapping | 7,977 LUT4; 8 MULT18X18D |

The modeled 6.8 µs figure assumes a 100 MHz clock. It is **not** a post-route or measured hardware number.

Evidence: [Evidence Explorer](https://sushxnthd.github.io/kernellum/evidence.html) · [TR-001](https://sushxnthd.github.io/kernellum/TR-001.pdf) · [repository](https://github.com/sushxnthd/kernellum)

## Why this wedge

Custom AI hardware is valuable, but conventional design requires scarce hardware expertise, long iteration cycles, and manually connected model/compiler/RTL/verification workflows.

Kernellum's wedge is **model-to-verified-accelerator generation**:

1. lower a supported model into an explicit hardware IR;
2. quantize and expose hardware-relevant structure;
3. search accelerator configurations under deployment constraints;
4. emit inspectable RTL and test evidence;
5. progressively close the loop with physical-design feedback.

The goal is not "an LLM that writes Verilog." The goal is a compiler-like system whose output is constrained by the workload, architecture model, verification chain, and eventually physical PPA feedback.

## Current product boundary

Today the supported compiler front-end is deliberately narrow: a sequential ONNX `Gemm/ReLU` subset and small dense INT8 accelerators.

That narrowness is intentional. Unsupported graphs are rejected rather than silently approximated.

## Next de-risking milestones

### 1. Physical FPGA evidence
- named ECP5 board;
- real package/pin/clock constraints;
- nextpnr place-and-route;
- achieved Fmax and timing slack;
- loaded bitstream;
- measured end-to-end latency;
- measured board power and energy/inference.

### 2. Multi-workload benchmark
- multiple model shapes;
- latency / utilization / throughput comparison;
- compiler decisions reported per workload;
- reproducible benchmark harness.

### 3. External design partner
- a model supplied by an outside team;
- real deployment constraints;
- a generated implementation and evaluation record.

## Commercial direction

Potential paths include:

- compiler / tool licensing;
- paid hardware-software co-design engagements;
- licensable accelerator RTL/IP;
- optimization tooling for edge-AI teams;
- eventually, workload-specific silicon IP.

The near-term objective is to earn the right to make each step by producing measurable technical evidence rather than projecting unbuilt capability.

## What Kernellum is looking for

Kernellum is open to conversations with:

- semiconductor and EDA engineers;
- edge-AI / robotics teams with constrained inference workloads;
- FPGA teams willing to test generated accelerators;
- researchers working on hardware-software co-design;
- deep-tech investors interested in early technical infrastructure.

For a design-partner evaluation, see [DESIGN_PARTNERS.md](DESIGN_PARTNERS.md).

## Founder

**Sushanth Dasari — Founder & Research Lead**

GitHub: [@sushxnthd](https://github.com/sushxnthd)

---

**Status:** research-stage prototype · September 2026  
**Evidence rule:** modeled numbers stay modeled; physical claims wait for physical hardware.
