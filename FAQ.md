# Kernellum — Technical Diligence FAQ

## What is Kernellum?

Kernellum is building an **AI-native model-to-hardware compiler** for workload-specific accelerators.

The intended interface is:

```text
trained model + deployment constraints
                ↓
hardware IR → architecture search → verified RTL
                ↓
      physical implementation feedback
```

The current public implementation is research-stage and deliberately narrow.

## Is this just an LLM writing Verilog?

No. The current public compiler path is deterministic software, not a prompt-to-Verilog demo.

A supported workload is lowered into an explicit hardware IR, quantized, evaluated across candidate parallelism choices, emitted as SystemVerilog and checked against integer/cycle references and RTL simulation.

AI-assisted engineering may be used in development, but the technical claim is about the **compiler/evidence pipeline**, not the ability of a language model to produce plausible RTL.

## How is this different from HLS?

High-level synthesis usually begins with a hardware-oriented algorithm expressed in C/C++ or another high-level hardware description and lowers that implementation to RTL.

Kernellum is exploring a higher-level design interface: **the ML workload and deployment constraints themselves** influence the accelerator architecture.

The project is not currently a replacement for mature HLS products.

## How is this different from an ML compiler?

ML compilers usually optimize software/kernel execution for an existing target architecture.

Kernellum's research question is whether the compiler can also **select or generate the target accelerator microarchitecture**.

The long-term system should use physical timing/area/power feedback to influence those architecture choices.

## What works today?

The public prototype demonstrates:

- supported neural workload → hardware IR;
- INT8 quantization;
- architecture search across MAC-lane configurations;
- generated SystemVerilog;
- exact cycle/reference checking;
- golden-vector RTL simulation;
- generic Yosys synthesis;
- ECP5-family synthesis;
- a named ULX3S-85F board target with real package/pin/clock constraints;
- a 1/2/4/8-lane nextpnr sweep with post-route Fmax/resource evidence;
- physical-feedback selection of the 2-lane design for the 25 MHz target;
- reproducible reference-bitstream generation in CI;
- completed KRN-EXT-001 clean-room validation on a pinned third-party tiny-NPU ONNX model, including RTL simulation and ULX3S P&R.

See [BUILD_STATUS.md](BUILD_STATUS.md) for the exact current boundary.

## What does not work yet?

Kernellum does not currently claim:

- arbitrary ONNX support;
- production ASIC readiness;
- tapeout;
- physical-board validation;
- measured board latency/power/energy;
- a broad operator library;
- customer production deployment;
- guaranteed speedups over mature alternatives.

## What are the current headline results?

For the demonstrated digits MLP:

- 96.22% float held-out accuracy;
- 96.44% INT8 held-out accuracy;
- 99.78% float/INT8 prediction agreement;
- 450/450 cycle-model / vector-INT8 agreement;
- 32/32 RTL golden-vector cases PASS;
- generic Yosys synthesis PASS;
- ECP5 family mapping PASS;
- ULX3S-85F post-route Fmax of 35.96 / 29.64 / 22.12 / 16.10 MHz for 1/2/4/8 lanes;
- 2 MAC lanes selected because it is the lowest-cycle swept design that closes the 25 MHz board target;
- reference bitstream generated in CI.

Modeled latency values are explicitly separated from post-route timing and from physical-board measurements.

For the external tiny-NPU workload:

- network: 64 → 64 → 64 → 32;
- 1/2/4/8-lane post-route Fmax: 33.51 / 28.18 / 22.06 / 14.82 MHz;
- 2 lanes selected for the 25 MHz target;
- selected bitstream generated with SHA-256 `50761b00fad5afda5f18c9841291bceea47a04c94155df044b5fb60ef09b2590`;
- externality applies to the model graph/weights, not to an application dataset or customer relationship.

## Why start with such a small workload?

Because the first useful proof is not breadth. It is a complete, inspectable path.

A narrow compiler that rejects unsupported graphs and closes the loop from model to verifiable RTL is a stronger foundation than a broad interface that silently falls back to hand-authored hardware or unsupported claims.

## Where can the moat come from?

The current prototype itself is not yet a durable moat.

Potential defensibility would need to emerge from a combination of:

1. a workload-aware hardware IR;
2. increasingly rich architecture search;
3. physical PPA feedback integrated into the search loop;
4. verification generated alongside hardware;
5. accumulated workload → architecture → physical-result data;
6. proprietary optimization/search methods;
7. design-partner integration and deployment knowledge;
8. eventually, reusable accelerator IP.

The project should be judged on whether it actually builds those layers.

## Why can this become a business before fabricating chips?

Potential earlier commercial surfaces include:

- compiler/tool licensing;
- paid hardware-software co-design;
- FPGA optimization;
- licensable RTL / accelerator IP;
- architecture exploration for constrained edge-AI workloads.

Owning fabricated silicon is a possible later path, not a prerequisite for the first revenue.

## What is the next technical proof point?

Actual ULX3S-85F board execution: load the generated bitstream, verify inference on-device, and measure end-to-end latency, power and energy/inference.

Named-board place-and-route, timing/resource evidence, physical-feedback architecture selection and reference-bitstream generation are already complete.

## What is the next commercial proof point?

An external team supplies a real, non-confidential inference workload and deployment constraint, and Kernellum produces an evaluation that the partner considers useful.

See [DESIGN_PARTNERS.md](DESIGN_PARTNERS.md).

## What would falsify the thesis?

Examples:

- physical feedback consistently shows generated architectures are uncompetitive even after optimization;
- useful workloads require so much manual hardware intervention that the compiler interface provides little leverage;
- mature HLS/ML-compiler tools close the same abstraction gap more effectively;
- the search space cannot be expanded without becoming prohibitively expensive;
- external teams do not value generated accelerator/IP outputs enough to pay or integrate.

Kernellum should treat these as engineering questions, not assumptions.

## Who is building it?

**Sushanth Dasari — Founder & Research Lead**

Public source and evidence: https://github.com/sushxnthd/kernellum
