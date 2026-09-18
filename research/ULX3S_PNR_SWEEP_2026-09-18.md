# ULX3S-85F Physical-Feedback P&R Evidence — 2026-09-18

**Evidence ID:** KRN-PNR-001  
**Target:** ULX3S-85F reference board  
**FPGA:** LFE5U-85F-6BG381C  
**Package:** CABGA381  
**Board clock target:** 25.00 MHz  
**Workflow run:** https://github.com/sushxnthd/kernellum/actions/runs/35321132327  
**CI result:** PASS

## Result

Kernellum swept four accelerator parallelism settings through the same board-targeted Yosys + nextpnr flow. The compiler-side cycle model and post-route timing were then combined with one explicit rule:

> choose the lowest modeled cycle count among architectures whose post-route Fmax meets the 25 MHz board clock.

| MAC lanes | Modeled cycles | Post-route Fmax | 25 MHz timing | Modeled core latency @ 25 MHz | TRELLIS_COMB | MULT18X18D |
|---:|---:|---:|:---:|---:|---:|---:|
| 1 | 2,836 | 35.96 MHz | PASS | 113.44 µs | 3,562 | 5 |
| **2** | **1,476** | **29.64 MHz** | **PASS** | **59.04 µs** | **5,727** | **6** |
| 4 | 796 | 22.12 MHz | FAIL | 31.84 µs | 10,561 | 8 |
| 8 | 456 | 16.10 MHz | FAIL | 18.24 µs | 19,652 | 12 |

**Selected reference-board architecture: 2 MAC lanes.**

The 4- and 8-lane variants have lower modeled cycle counts but do not close the ULX3S 25 MHz target. This is the first public Kernellum result where physical implementation feedback changes the architecture choice relative to cycle-only search.

## Generated artifact

The CI flow generated an ECP5 bitstream for the selected 2-lane configuration.

**Bitstream SHA-256:**  
`19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415`

The workflow also archives per-lane Yosys JSON/configuration files and nextpnr logs.

## Evidence boundary

This record establishes:

- named-board/package constraints;
- successful place-and-route for timing-feasible variants;
- post-route Fmax evidence;
- resource utilization from nextpnr;
- automatic selection using physical timing feedback;
- bitstream generation for the selected reference target.

It **does not** establish:

- that a physical ULX3S board has been programmed;
- measured board-level inference latency;
- measured throughput;
- measured board power;
- measured energy per inference.

The latency values in the table are modeled from cycle count at the board's 25 MHz clock. They are not oscilloscope- or device-measured latencies.

## Reproduce

```bash
pip install -e '.[test,onnx]'
python -m kernellum --out artifacts/digits_int8
bash scripts/run_pnr_sweep_ulx3s_85f.sh
```

The committed board constraints live at:

`boards/ulx3s_85f/kernellum_demo.lpf`
