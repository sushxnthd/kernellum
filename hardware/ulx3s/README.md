# ULX3S physical measurement record

This directory is intentionally data-empty until a real ULX3S-85F is programmed.

## Generated bitstream

The GitHub Actions P&R flow produces a bitstream for each lane count under:

`artifacts/digits_int8/pnr_ulx3s/lane_<N>/kernellum_ulx3s_85f.bit`

The default physical demo uses lane 4 unless post-route feedback selects a different candidate.

## Program SRAM

With an ULX3S connected through USB1:

```bash
bash scripts/program_ulx3s.sh path/to/kernellum_ulx3s_85f.bit
```

The script uses `openFPGALoader --board=ulx3s` when available, otherwise `fujprog`.

## Core-latency markers

The board wrapper exposes:

- GP0: accelerator `start` pulse
- GN0: accelerator `done` pulse

Capture those two digital signals with a logic analyzer. Export one row per inference:

```csv
start_s,done_s
0.100000,0.100027
...
```

Do not populate the committed template with synthetic values.

## Analyze latency

```bash
python scripts/analyze_measurements.py hardware/ulx3s/latency_measurements.csv
```

## Add power / energy

Export a synchronized trace with:

```csv
time_s,power_w
...
```

Then run:

```bash
python scripts/analyze_measurements.py \
  hardware/ulx3s/latency_measurements.csv \
  --power-csv hardware/ulx3s/power_trace.csv \
  --idle-power-w <measured-idle-power>
```

Only the resulting real measurement summary should be promoted to the website or TR-002.
