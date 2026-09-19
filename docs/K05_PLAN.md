# Kernellum K0.5: synthesis-validation gate

K0.5 is designed to answer one narrow question before K1: does K0's coarse FPGA resource model preserve useful architectural rankings after real RTL elaboration and technology mapping?

## RTL under test

`rtl/kernellum_mac_array.sv` implements a parameterized outer-product MAC array plus block-RAM scratchpad. One step consumes one signed value per row and one signed value per column and accumulates every pairwise product. Repeated K steps therefore perform the inner-product work for a ROWS x COLS matrix tile.

This is intentionally smaller than the eventual K1 engine. K0.5 validates the expensive resource assumptions first rather than hiding uncertainty inside a full accelerator stack.

## Functional gate

`rtl/tb_kernellum_mac_array.sv` multiplies a 2x3 matrix by a 3x2 matrix and checks all four accumulated outputs. It separately verifies scratchpad read/write behavior with Icarus Verilog.

## Synthesis gate

Nine stratified array/buffer configurations are synthesized with Yosys `synth_xilinx -family xc7`. K0's predicted DSP-equivalent and BRAM18K-equivalent resources are compared with mapped DSP48 and RAMB18/36 resources.

The predeclared resource-model gate requires:

- Spearman rank correlation >= 0.90 for DSP and BRAM;
- mean BRAM relative error <= 20%;
- generic synthesis preserves one multiplier per PE in >=99% of candidates;
- average mapped DSP / predicted DSP ratio >= 0.80.

These thresholds were fixed before observing K0.5 synthesis results.

## What a pass does not mean

A pass does not validate K0's latency or energy model. It does not establish timing closure, place-and-route feasibility, power, quantization accuracy, or superiority to other accelerator generators.

## Next gate

If the resource gate passes, K1 should add a tiled GEMM controller and synthesis/place-and-route timing feedback. If it fails, K0's resource model must be recalibrated before expanding the design space.
