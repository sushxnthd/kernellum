# KRN-HW-001 Hardware Runbook

This kit is the shortest auditable path from the frozen Kernellum reference bitstream to physical ULX3S-85F evidence. It does not contain a completed measurement and does not imply that the board run has occurred.

## Required equipment

- ULX3S-85F board (`LFE5U-85F-6BG381C`);
- host with Python 3.10+ and `openFPGALoader`;
- two-channel oscilloscope or logic analyzer for `start_btn` to `done_led` latency;
- USB power analyzer, logged bench supply, or characterized shunt measurement;
- a clean copy of this kit.

Use SRAM programming so a power cycle restores the board's prior flash image.

## 1. Verify the handoff

From the kit root:

```bash
python tools/package_krn_hw_001_kit.py verify .
sha256sum -c SHA256SUMS
```

The bitstream must have SHA-256:

```text
19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415
```

The manifest must identify reference workflow run `35321132327`, target `ULX3S-85F / LFE5U-85F-6BG381C / CABGA381`, and a 25 MHz clock.

## 2. Fill the board and instrument metadata

Edit `session/metadata.json` before measurement. At minimum, fill:

- `board_revision`;
- `latency_instrument`;
- `power_instrument`;
- `power_method`;
- `measurement_point`;
- `notes` with probe points, sample period, and any deviations.

Do not replace the target, clock, FPGA density, reference workflow run, or reference bitstream fields for the primary KRN-HW-001 campaign.

## 3. Program SRAM and retain the log

```bash
bash tools/program_krn_hw_001_ulx3s.sh kernellum_demo_top.bit session
```

The wrapper rejects any bitstream that does not match the frozen reference, invokes `openFPGALoader --board=ulx3s`, and records the command, result, timestamp, hash, and console output.

## 4. Record the functional result

Reset the board, start one inference, wait for `done_led`, and read the four class LEDs. Record the observed class:

```bash
python tools/krn_hw_001.py record-functional session 8
```

Replace `8` only with the class actually observed. A class other than the expected class 8 is a failed functional check; retain the result and stop before making latency or energy claims.

## 5. Capture raw measurements

Follow `KRN-HW-001_PROTOCOL.md` and populate:

- `session/latency_us.csv` with at least 100 positive trials after 10 warm-ups;
- `session/idle_power.csv` with at least 10 board-input samples;
- `session/active_power.csv` with at least 10 samples while repeatedly running inference.

For each power row, provide either `power_w` directly or both `voltage_v` and `current_a`. Keep raw instrument exports, photographs, and screenshots alongside the session when available.

## 6. Run the evidence gate

```bash
python tools/krn_hw_001.py doctor session
python tools/krn_hw_001.py analyze session
```

`doctor` shows every pass/fail condition. `analyze` writes `session/result.json` and `session/RESULT.md`. The status remains `INCOMPLETE` unless the exact reference identity, successful programming log, correct class, minimum sample counts, nonnegative dynamic power, and complete metadata all pass.

## 7. Submit the evidence

Open the repository's **Physical hardware measurement** issue form and attach or link:

- `session/metadata.json`;
- all three raw CSV files;
- `session/programming.log`;
- `session/result.json` and `session/RESULT.md`;
- instrument exports or photographs where practical.

Do not post private contact information, credentials, serial numbers you consider sensitive, proprietary lab details, or other confidential material in the public issue.

## Claim boundary

A complete session supports a physical ULX3S reference-implementation claim only. It does not establish ASIC performance, production power efficiency, broad-model generality, customer validation, manufacturability, or production readiness.
