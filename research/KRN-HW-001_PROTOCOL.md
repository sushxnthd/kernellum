# KRN-HW-001 Protocol — Physical ULX3S-85F Measurement

**Evidence ID:** KRN-HW-001  
**Target:** ULX3S-85F / LFE5U-85F-6BG381C / CABGA381  
**Clock:** 25 MHz  
**Status:** measurement harness ready; physical board execution required.

## Objective

Promote Kernellum from L5 board-targeted place-and-route evidence to L6 physical-board evidence by programming the selected reference bitstream onto a compatible ULX3S-85F and measuring:

1. functional inference completion on-device;
2. end-to-end latency from `start_btn` assertion to `done_led` assertion;
3. idle board power;
4. active/inference board power;
5. energy per inference.

## Bitstream

Use the selected bitstream produced by the reproducible reference P&R flow:

```text
artifacts/digits_int8/pnr_sweep_ulx3s_85f/kernellum_demo_top.bit
```

When using a CI artifact, record the workflow run ID and SHA-256 of the exact bitstream loaded.

## Programming

Recommended SRAM programming command:

```bash
openFPGALoader --board=ulx3s kernellum_demo_top.bit
```

Use SRAM programming for the measurement campaign so the board can be returned to its prior flash image after power-cycle.

## Functional check

The current reference top loads one fixed held-out input vector from ROM.

1. Program the bitstream.
2. Reset the board.
3. Assert `start_btn`.
4. Observe `done_led`.
5. Record the four class LEDs after completion.
6. Compare the observed class index against the expected class encoded in the measurement-session metadata.

A functional mismatch invalidates latency/power claims until resolved.

## Latency measurement

Preferred instrument: logic analyzer or oscilloscope with at least two channels.

Probe:

- trigger/start channel: `start_btn` signal;
- completion channel: `done_led`.

Measure elapsed time from the active transition of `start_btn` to the active transition of `done_led`. For latency trials, release `start_btn` after triggering so each capture contains one inference transaction.

Recommended campaign:

- warm-up: at least 10 inferences;
- recorded trials: at least 100;
- report median, mean, minimum, maximum, standard deviation and p95;
- retain raw trial values.

The measured latency is **end-to-end board-level demo latency**, and must not be relabeled as only accelerator-core latency.

## Power measurement

Record board-level input power with the same power source and instrumentation for idle and active conditions.

Preferred methods:

1. inline USB power analyzer with exported voltage/current samples; or
2. bench supply with logged voltage/current; or
3. oscilloscope across a characterized current shunt.

For each state, record voltage, current or direct power, sample period, instrument/model, measurement point, and duration.

Measure:

- **idle:** programmed board, no inference in progress;
- **active:** repeated inference execution at the same clock/configuration. Hold `start_btn` active after programming; the current demo wrapper returns to `T_IDLE` after each result and immediately starts another inference while the button remains asserted, creating a sustained inference loop suitable for averaged board-power sampling.

Report both total board power and dynamic increment:

```text
P_dynamic = P_active - P_idle
```

## Energy per inference

Primary board-level estimate:

```text
E_total = P_active × measured_latency
```

Dynamic incremental estimate:

```text
E_dynamic = (P_active - P_idle) × measured_latency
```

Both must be labeled as board-level estimates derived from measured power and measured end-to-end latency unless direct per-event integration is used.

## Raw-data format

Create a session with:

```bash
python scripts/krn_hw_001.py init --out measurements/krn_hw_001/<session>
```

Then populate:

- `metadata.json`
- `latency_us.csv`
- `idle_power.csv`
- `active_power.csv`

Finalize with:

```bash
python scripts/krn_hw_001.py analyze measurements/krn_hw_001/<session>
```

The analyzer writes `result.json` and `RESULT.md`.

## Evidence required for completion

KRN-HW-001 is complete only when all of the following exist:

- exact bitstream SHA-256;
- board revision / FPGA density recorded;
- programming command and result recorded;
- expected and observed inference output recorded;
- at least 100 valid latency trials;
- raw idle-power samples;
- raw active-power samples;
- instrument/method notes;
- generated statistical summary;
- measured total and dynamic energy/inference estimates;
- photographs or instrument screenshots where practical.

## Claim boundary

KRN-HW-001 measures a physical ULX3S reference implementation. It does not establish ASIC performance, production power efficiency, broad-model generality, customer validation, manufacturability, or production readiness.
