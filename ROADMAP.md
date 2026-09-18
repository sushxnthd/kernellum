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
