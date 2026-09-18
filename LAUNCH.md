# Kernellum Research — launch copy

## One-line

Kernellum Research is building an AI-native compiler that turns supported AI workloads and deployment constraints into workload-specific accelerator architectures, verified RTL and physical-design evidence.

## Short post

I’ve launched **Kernellum Research**, an independent AI-hardware research project.

The first public system is **Kernellum Compiler**: a reproducible model-to-RTL prototype that lowers a neural workload, quantizes it, searches accelerator configurations, emits SystemVerilog, verifies the result and now feeds reference-board place-and-route timing back into architecture selection.

On the ULX3S-85F reference target, the cycle-only search prefers wider designs, but physical timing changes the answer: 4 MAC lanes routes at 22.12 MHz and 8 lanes at 16.10 MHz, both below the 25 MHz board target. The 2-lane design reaches 29.64 MHz, so Kernellum selects it and generates a reference bitstream in CI.

Physical board loading, measured latency, power and energy remain explicitly unclaimed.

Site: https://sushxnthd.github.io/kernellum/
Repo: https://github.com/sushxnthd/kernellum

## LinkedIn-length

I’ve started **Kernellum Research**, an independent research initiative around AI-native hardware-software co-design.

The question behind it is simple: most AI deployment treats hardware as fixed. What changes if the model and its deployment constraints become inputs to the hardware-design process too?

The first public prototype, **Kernellum Compiler**, now takes a deliberately narrow neural workload through quantization, hardware IR lowering, constraint-driven architecture search, generated SystemVerilog, cycle-level verification, RTL simulation, ECP5-family synthesis and board-targeted place-and-route.

The current public record includes:
- 96.44% held-out INT8 accuracy on the demonstrated digits workload;
- 450/450 exact agreement between the cycle model and vector INT8 reference;
- 32/32 held-out RTL golden-vector simulations;
- a ULX3S-85F physical-feedback sweep across 1/2/4/8 MAC lanes;
- post-route Fmax of 35.96 / 29.64 / 22.12 / 16.10 MHz respectively;
- selection of the 2-lane accelerator for the board’s 25 MHz target;
- reproducible reference-bitstream generation in CI.

The part I find most interesting is that physical timing changes the architecture decision. A cycle-only view rewards wider parallelism; the reference-board implementation shows that the fastest modeled candidates do not close the target clock.

This is place-and-route evidence, not a claim of measured physical-board performance. The next threshold is loading the bitstream onto compatible hardware and measuring end-to-end inference latency, power and energy.

I’m publishing the code, generated artifacts, technical reports and evidence trail as I go.

Site: https://sushxnthd.github.io/kernellum/
Repository: https://github.com/sushxnthd/kernellum

## GitHub repository description

AI-native model-to-hardware compilation — workload-aware architecture search, generated RTL, verification and physical-design feedback.
