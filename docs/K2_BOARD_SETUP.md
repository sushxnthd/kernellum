# K2 board setup

Target: Lattice ECP5 Evaluation Board, LFE5UM5G-85F-EVN.

## 1. Clock jumper

K2 uses the board's FTDI-derived 12 MHz clock.

- install JP2
- keep JP1 removed

The 12 MHz signal reaches ECP5 ball A10.

## 2. Programming connection

Use the board's mini-USB programming connection.

K2 bitstreams are generated under:

    build/k2_evn/<variant>/<variant>.bit

Load into SRAM with openFPGALoader:

    openFPGALoader -b ecp5_evn -m build/k2_evn/<variant>/<variant>.bit

The project deliberately uses SRAM loading first. Do not write K2 development images permanently to SPI flash unless that is intentional.

## 3. UART measurement link

Default K2 uses J31 plus a **3.3 V TTL USB-UART adapter**.

Connections:

| USB-UART | ECP5 EVN J31 | FPGA |
| --- | --- | --- |
| TX | pin 1 | C6, K2 uart_rx |
| RX | pin 2 | C7, K2 uart_tx |
| GND | pin 5 | GND |

Do not connect a 5 V UART signal to the FPGA I/O.

If the J31 connector is not physically fitted on a particular board revision, populate the header or move the same logical UART signals to another available GPIO header and update `boards/ecp5_evn/k2.lpf`.

## 4. Optional onboard FTDI UART

The board documentation describes an optional FTDI-to-FPGA UART path, but the R34/R35 links are not installed by default.

K2 does not require this modification. Do not solder those links merely to run the default K2 experiment.

## 5. Host environment

Install the serial dependency:

    python -m pip install pyserial

Find the UART port:

Windows examples:

    COM5
    COM6

Linux examples:

    /dev/ttyUSB0
    /dev/ttyUSB1

## 6. Handshake

With a K2 bitstream loaded:

    PYTHONPATH=. python scripts/k2_benchmark.py --port COM6 --trials 5

The host first sends PING and INFO. It should report the architecture parameters encoded in the selected bitstream.

## 7. Physical validation run

The preregistered run uses 100 randomized trials per architecture:

    PYTHONPATH=. python scripts/k2_benchmark.py \
        --port COM6 \
        --trials 100 \
        --seed 20260919 \
        --json-out results/k2_board_trials_<variant>.json

Repeat for:

1. baseline_r08_c08_k32
2. active_r10_c12_k32
3. active_r08_c14_k64

Do not combine or discard failing trials manually. Preserve the JSON exactly as generated.

## 8. What is measured

The FPGA reports accelerator **busy cycles** from an internal hardware counter.

UART upload/download time is intentionally excluded.

For a GEMM split over one or more K chunks:

    expected busy cycles = total K + 1

The +1 comes from the single accumulator-clear cycle before the first chunk. Later chunks accumulate without clearing.

The host separately verifies every output cell against an integer reference GEMM.

## 9. Evidence upload

After all three physical runs, commit the raw JSON files unchanged before writing the interpretation report.

Only then create `docs/K2_REPORT.md`.

## 10. Current status label

Before physical execution, use:

> K2 board-ready

After all preregistered board gates pass, use:

> K2 physically validated

Do not use "physically validated" based only on simulation, synthesis, routing, or bitstream generation.
