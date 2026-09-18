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

Required:
- obtain access to a compatible ECP5 board;
- load the generated bitstream;
- demonstrate inference on hardware;
- measure end-to-end latency;
- measure board power and energy/inference;
- compare those measurements against the compiler/post-route model.

Tracking: GitHub Issue #1.

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
