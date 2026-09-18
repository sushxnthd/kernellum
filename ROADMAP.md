# Kernellum Roadmap

The roadmap is organized by **evidence thresholds**, not marketing versions.

## Current — compiler + family synthesis

Completed:
- model training and INT8 lowering;
- architecture search;
- independent cycle model;
- generated SystemVerilog;
- golden-vector RTL simulation;
- generic Yosys synthesis;
- ECP5 family-mapped synthesis;
- narrow ONNX -> hardware IR -> RTL path.

## Next — named physical FPGA

Required:
- select an accessible ECP5 board;
- commit real package/pin/clock constraints;
- place-and-route with nextpnr;
- report timing closure and achieved Fmax;
- generate/load bitstream;
- demonstrate inference on hardware;
- measure end-to-end latency;
- measure board power and energy/inference.

Tracking: GitHub Issue #1.

## After physical evidence — broader compiler

Candidate directions:
- broader ONNX operator coverage;
- multiple dense graph shapes;
- memory-aware architecture search;
- mixed precision;
- explicit area/timing feedback from physical design;
- board-target profiles as first-class compiler objects.

## Later — research-grade hardware co-design

Longer-term questions:
- when should the compiler search memory hierarchy?
- when should placement/timing feedback enter the search loop?
- which model transformations and hardware transformations should be optimized jointly?
- how much of verification can be generated alongside RTL?

TR-002 remains intentionally unassigned until a second substantive technical contribution is complete.


## v0.2 implementation-feedback milestone

The active `v0.2-physical-feedback` branch adds:

- named ULX3S-85F board/package/clock constraints;
- variable-depth sequential dense ONNX lowering;
- shape-only Flatten/Reshape/Identity handling;
- per-layer quantization and model-memory reporting;
- a five-topology benchmark matrix with generated RTL verification;
- ULX3S nextpnr lane sweeps for 1/2/4/8/16 MAC lanes;
- feedback-aware architecture search using post-route Fmax/resource estimates;
- logic-analyzer core markers and a physical latency/power analysis pipeline.

### Evidence boundary

A successful nextpnr run is **post-route implementation evidence**. It is not a physical-board measurement.

The following stay pending until a real ULX3S-85F is programmed and measured:

- observed board execution;
- measured core and end-to-end latency;
- measured idle/active power;
- energy per inference.

TR-002 remains unpublished until those physical measurements can be incorporated.
