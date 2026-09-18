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

The current prototype demonstrates a complete model → RTL → reference-board P&R feedback loop:

| Evidence | Public result |
|---|---:|
| Float held-out accuracy | 96.22% |
| INT8 held-out accuracy | 96.44% |
| Cycle/reference agreement | 450 / 450 |
| RTL golden-vector simulation | 32 / 32 PASS |
| Generic Yosys synthesis | PASS, 0 CHECK problems |
| Current 4-lane ECP5 family mapping | 7,756 LUT4; 8 MULT18X18D |
| Named reference target | ULX3S-85F / LFE5U-85F-6BG381C |
| Physical-feedback sweep | 1 / 2 / 4 / 8 MAC lanes |
| Selected reference-board architecture | **2 MAC lanes** |
| Selected post-route Fmax | **29.64 MHz** vs 25 MHz target |
| Selected post-route TRELLIS_COMB | **5,727 / 83,640** |
| Selected DSP blocks | **6 / 156 MULT18X18D** |
| Reference bitstream | generated in clean-room CI |

The important result is not simply that one design routes. **Physical timing changes the architecture decision.** The cycle-only search favors more parallel variants; on the ULX3S-85F target, 4 lanes closes at only 22.12 MHz and 8 lanes at 16.10 MHz, while 2 lanes reaches 29.64 MHz. Kernellum therefore selects 2 lanes for the 25 MHz reference target.

This is post-route tool evidence, not measured board performance. Physical board loading, measured latency, power and energy remain the next threshold.

Evidence: [KRN-PNR-001](research/ULX3S_PNR_SWEEP_2026-09-18.md) · [Evidence Explorer](https://sushxnthd.github.io/kernellum/evidence.html) · [repository](https://github.com/sushxnthd/kernellum)

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

### 1. Physical board execution
Already completed: named target, package/pin/clock constraints, multi-architecture nextpnr P&R, post-route Fmax/resource evidence, reference bitstream generation, and the KRN-HW-001 programming/measurement/analyzer tooling.

Remaining physical actions:
- obtain/access a compatible ULX3S-85F;
- load the bitstream;
- verify the fixed reference inference on-device;
- capture ≥100 end-to-end latency trials;
- measure idle and active board power;
- publish measured board-level energy/inference with method notes.

### 2. Multi-workload benchmark
- multiple model shapes;
- latency / utilization / throughput comparison;
- compiler decisions reported per workload;
- reproducible benchmark harness.

### 3. External validation and design partner
A pinned public third-party ONNX workload from tiny-NPU is currently under clean-room KRN-EXT-001 validation. This tests external model ingestion/implementation, but it is not presented as a customer relationship or application-accuracy result.

The stronger commercial milestone remains:
- a workload supplied by an outside team;
- real deployment constraints;
- permissioned evaluation evidence;
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
For adjacent approaches and the intended technical wedge, see [LANDSCAPE.md](LANDSCAPE.md).

## Founder

**Sushanth Dasari — Founder & Research Lead**

GitHub: [@sushxnthd](https://github.com/sushxnthd)

---

**Status:** research-stage prototype · September 2026  
**Evidence rule:** modeled numbers stay modeled; physical claims wait for physical hardware.
