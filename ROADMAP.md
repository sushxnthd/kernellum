# Kernellum Roadmap

The roadmap is organized by **evidence thresholds**, not marketing versions.

## Completed threshold — compiler + reference-board P&R feedback

Completed:
- model training and INT8 lowering;
- architecture search;
- independent cycle model;
- generated SystemVerilog;
- golden-vector RTL simulation;
- generic Yosys synthesis;
- ECP5 family-mapped synthesis;
- narrow ONNX -> hardware IR -> RTL path;
- ULX3S-85F board/package/pin constraints;
- multi-architecture nextpnr sweep at 25 MHz;
- physical-feedback selection of a timing-feasible 2-lane accelerator;
- reference-board bitstream generation.

## Next — physical board execution

Measurement infrastructure is now ready:
- frozen KRN-HW-001 physical-measurement protocol;
- reproducible ULX3S SRAM programming capture;
- exact bitstream SHA-256 recording;
- raw latency / idle-power / active-power CSV schema;
- automatic statistics and energy/inference analysis;
- completion gate that refuses to mark evidence complete without functional correctness, ≥100 latency trials, power samples and measurement metadata.

Remaining physical actions:
- obtain access to a compatible ULX3S-85F board;
- load the selected bitstream;
- demonstrate the expected class-8 reference inference on hardware;
- measure end-to-end latency;
- measure board power and energy/inference;
- compare those measurements against the compiler/post-route model.

Tracking: GitHub Issue #1. Hardware-access call: Issue #9.

## Parallel validation — external workload

KRN-EXT-001 pins a public third-party ONNX model from tiny-NPU and runs it through provenance checking, supported ONNX lowering, cycle/reference verification, RTL simulation and the same ULX3S physical-feedback sweep. Clean-room CI validation is in progress; it is not promoted as completed evidence until that run succeeds.

A genuine external design-partner/customer workload remains a separate milestone from this public third-party-model test.

## After physical evidence — broader compiler

Candidate directions:
- broader ONNX operator coverage;
- multiple dense graph shapes;
- memory-aware architecture search;
- mixed precision;
- richer area/timing/power feedback from physical design;
- board-target profiles as first-class compiler objects.

## Later — research-grade hardware co-design

Longer-term questions:
- when should the compiler search memory hierarchy?
- when should placement/timing feedback enter the search loop?
- which model transformations and hardware transformations should be optimized jointly?
- how much of verification can be generated alongside RTL?

TR-002 remains intentionally unassigned until a second substantive technical contribution is complete.
