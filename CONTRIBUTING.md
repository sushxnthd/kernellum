# Contributing to Kernellum

Kernellum is a small research codebase. Contributions are welcome when they preserve the project's evidence-first rules.

## Before opening a change

1. Install the project with `pip install -e '.[test,onnx]'`.
2. Run `pytest -q`.
3. For RTL/compiler changes, regenerate the relevant artifacts.
4. Run the applicable EDA scripts.
5. Do not update headline metrics without updating the artifact that produced them.

## Claim discipline

Do not describe:
- modeled latency as measured latency;
- family synthesis as place-and-route utilization;
- synthesis success as board validation;
- a narrow ONNX subset as arbitrary ONNX support;
- prototype RTL as ASIC-ready silicon.

## Generated artifacts

If a compiler change alters generated RTL, weights, vectors, manifests, or reports, include the regenerated artifact set in the same pull request.

## Physical FPGA changes

Board-specific work must include:
- exact board/device/package;
- real constraint file;
- tool versions;
- timing log;
- measurement method for any latency/power claim.

Use `research/FPGA_BRINGUP_PROTOCOL.md` as the checklist.

## Style

Prefer small, inspectable changes with explicit tests over broad unsupported feature claims.
