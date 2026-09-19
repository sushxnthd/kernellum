# Kernellum K2: physical FPGA validation

Date frozen: 2026-09-19

## Question

Can the K1 accelerator execute correctly on a real FPGA board, with hardware-measured kernel cycles matching the RTL model and with reproducible board-level telemetry?

K2 is the first stage that may produce physical hardware measurements. Until the board run happens, all K2 artifacts are preparation and simulation only.

## Target board

Lattice ECP5 Evaluation Board:

- ordering part: LFE5UM5G-85F-EVN
- FPGA: LFE5UM5G-85F-8BG381
- board clock: 12 MHz FTDI-derived clock on FPGA ball A10
- JP2 must be installed to connect the 12 MHz clock
- JP1 must remain removed for normal FTDI operation

The first K2 bitstreams intentionally run at the board's 12 MHz clock. This is far below the K1 routed Fmax and is a bring-up/measurement choice, not a performance claim.

## Host link

Default K2 transport uses an external 3.3 V USB-UART adapter on J31:

- J31 pin 1 / FPGA C6: FPGA UART RX
- J31 pin 2 / FPGA C7: FPGA UART TX
- J31 pin 5: GND
- 115200 baud, 8N1

This avoids requiring board modifications.

The board's onboard FTDI UART path is not populated by default. Using it requires installing the R34/R35 0-ohm links described in the Lattice board guide, so it is optional and outside the default K2 path.

## Programming

K2 produces ECP5 bitstreams suitable for openFPGALoader.

Expected SRAM-load command:

    openFPGALoader -b ecp5_evn -m <bitstream>.bit

## Architecture set

Three frozen variants:

1. baseline: 8x8, K_TILE=32
2. K1 active-search selection: 10x12, K_TILE=32
3. K1 active-search alternative: 8x14, K_TILE=64

The set includes a conventional square baseline and two architectures found through physical-design feedback.

## Hardware protocol

Commands are byte-oriented over UART:

- 0x01 PING
- 0x02 INFO
- 0x10 LOAD_A: address + ROWS signed INT8 values
- 0x11 LOAD_B: address + COLS signed INT8 values
- 0x20 RUN: k_len + flags
- 0x30 READ_CELL: row + col
- 0x31 READ_CYCLES

RUN flag bit 0 requests accumulator clear before execution.

Responses start with 0xA5.

The FPGA measures accelerator busy cycles internally. UART transfer time is therefore excluded from kernel-cycle measurements.

## Predeclared K2 physical gate

K2 passes only after a real board run satisfies all of the following for all three frozen variants:

1. programming and host handshake succeed;
2. at least 100 randomized tile-level GEMM trials per architecture are bit-exact;
3. measured busy-cycle count equals the RTL state-model expectation for every trial;
4. repeated identical trials have exactly identical hardware cycle counts;
5. no output mismatch is discarded as a transport error without a logged rerun;
6. all raw host logs and machine-readable trial results are preserved.

## K2 does not claim

A K2 bring-up pass at 12 MHz does not establish:

- maximum stable board clock;
- superiority over CPU/GPU execution;
- board power efficiency;
- end-to-end Transformer acceleration;
- ASIC performance.

Those require K2.1/K3.

## K2.1

After basic K2 passes, clock-rate validation can be added deliberately. The K1 routed Fmax values should then be tested with target-specific clock generation or another controlled clock source before comparing routed and physical maximum frequency.

## Evidence policy

GitHub is the technical source of truth:

- preregistered plan before measurements;
- RTL and host code;
- CI-generated bitstreams;
- raw physical run logs;
- machine-readable results;
- post-run technical report.

Potentially protectable search/architecture methods should be reviewed before additional public disclosure.
