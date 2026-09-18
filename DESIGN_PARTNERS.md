# Kernellum Design Partner Program

Kernellum is looking for a small number of early technical design partners willing to test the model-to-hardware workflow on a real inference problem.

## The ideal first workload

The current compiler is intentionally narrow. The best early partner workload is:

- inference-only;
- compact enough for FPGA experimentation;
- dominated by dense / matrix operations;
- quantization-tolerant;
- accompanied by a clear latency, area, memory or power constraint;
- shareable without exposing confidential production IP.

Support will broaden over time, but Kernellum will not claim operators or deployment targets that the compiler does not actually support.

## What a design-partner evaluation looks like

A partner provides:

1. a small model or representative public surrogate;
2. representative calibration / test data;
3. the deployment objective;
4. target hardware constraints, if known.

Kernellum attempts to produce:

1. a validated compiler input;
2. an explicit hardware IR;
3. a candidate accelerator architecture;
4. generated RTL;
5. golden-vector and simulation evidence;
6. synthesis / P&R evidence where the target flow is supported;
7. a short result record documenting what worked, what failed and what remains unvalidated.

## What this is not

This program is not yet a production silicon service. Kernellum currently does not promise:

- arbitrary ONNX support;
- manufacturable ASIC output;
- production safety certification;
- a guaranteed speedup;
- confidential handling through public GitHub issues.

Do **not** post confidential model details or proprietary datasets publicly.

## Start a conversation

Open a GitHub issue using the **Design partner interest** template with only non-confidential information:

- organization / team type;
- workload category;
- target platform;
- primary constraint;
- what you would like Kernellum to test.

Repository: https://github.com/sushxnthd/kernellum

If the workload is a fit, the next step can move off the public issue before sensitive information is exchanged.
