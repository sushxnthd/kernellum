# TR-002 working notes — NOT A PUBLISHED TECHNICAL REPORT

**Status:** unassigned / working notes only  
**Reason:** physical-board measurement is still pending.

## Provisional research question

Can post-route implementation feedback improve constraint-driven architecture selection for generated neural accelerators compared with a cycle-only search?

## Evidence already being generated

- named ULX3S-85F implementation target;
- variable-depth dense ONNX frontend;
- multi-topology benchmark matrix;
- lane-count P&R sweep;
- post-route Fmax and resource feedback;
- feedback-aware architecture search.

## Required evidence before assigning Technical Report 002

1. A real ULX3S-85F is programmed with a generated bitstream.
2. Core timing is captured from the committed GP0/GN0 markers.
3. Repeated latency statistics are recorded.
4. Board idle/active power and energy/inference are measured with method notes.
5. Software P&R results and physical measurements are clearly separated.
6. Benchmark and physical results are frozen to a release commit.

## Possible title after the threshold is crossed

*Closing the Loop: Implementation-Feedback Architecture Search for Generated Neural Accelerators*

This filename and text deliberately do not claim that TR-002 exists yet.
