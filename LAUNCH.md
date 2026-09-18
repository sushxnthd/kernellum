# Kernellum Research — launch copy

## One-line

Kernellum Research is an independent AI-hardware lab exploring whether models and deployment constraints can help specify the machines that run them.

## Short post

I’ve launched **Kernellum Research**, an independent AI-hardware research project.

The first public system is **Kernellum Compiler**: a small, reproducible model-to-RTL prototype that lowers a neural workload, searches accelerator configurations and emits verifiable SystemVerilog.

Current public evidence includes 96.44% INT8 held-out accuracy, 450/450 exact cycle-model agreement, 32/32 RTL golden-vector cases, and ECP5 family-mapped synthesis. Physical FPGA timing, board latency and power are intentionally still unclaimed.

Site: https://sushxnthd.github.io/kernellum/
Repo: https://github.com/sushxnthd/kernellum

## LinkedIn-length

I’ve started **Kernellum Research**, an independent research initiative around AI-native hardware-software co-design.

The question behind it is simple: most AI deployment treats hardware as fixed. What changes if the model and its deployment constraints become inputs to the hardware-design process too?

The first public prototype, **Kernellum Compiler**, takes a deliberately narrow neural workload through quantization, constraint-driven architecture search, generated SystemVerilog, cycle-level verification, RTL simulation and FPGA-family synthesis.

The current public record includes:
- 96.44% held-out INT8 accuracy on the demonstrated workload;
- 450/450 exact agreement between the cycle model and vector INT8 reference;
- 32/32 held-out RTL golden-vector simulations;
- ECP5 family-mapped synthesis evidence.

The 6.8 μs figure on the site is explicitly modeled at an assumed 100 MHz clock—not a measured hardware timing result. The next threshold is a named physical FPGA board, place-and-route, timing closure, and measured latency/power.

I’m publishing the code, generated artifacts, technical report and evidence trail as I go.

Site: https://sushxnthd.github.io/kernellum/
Repository: https://github.com/sushxnthd/kernellum

## GitHub repository description

AI-native systems for efficient computing — model-to-hardware compilation, accelerator architecture search, generated RTL and reproducible evidence.
