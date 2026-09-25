# SIMILARITY final-report integrity canary

Status: frozen before the canary route  
Date: 25 September 2026

## Why this canary exists

The prospective B-local study at frozen commit `3a0d7f7364f55ad0757964f3d8cb2eb43717c635` is permanently a preregistered null. Its only incomplete row, Sky130HD B-local 8x6 seed 157, completed detailed routing and produced a partial final report before the QEMU-hosted OpenROAD process emitted GUI image warnings and terminated with signal 11. The runner therefore could not certify final products or hashes.

This canary tests only whether removing the optional GUI image call from the pinned OpenROAD-flow-scripts `final_outputs.tcl` allows the mandatory final report and products to complete. It does not retest seed 157, does not estimate B-local performance and cannot rescue the prior null.

## Frozen inputs

- OpenROAD-flow-scripts image: `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.
- Platform: Sky130HD.
- Topology: B-local.
- Geometry: 8x6, already opened by the prior study.
- Canary-only seed: 173. This seed is opened by this canary and excluded from future confirmation.
- RTL and ASIC configuration are unchanged from the prospective study.
- Signed-GEMM equivalence is checked on 8x6 before routing.

The patch must find exactly this block once:

```tcl
# Save a final image if openroad is compiled with the gui
if { [ord::openroad_gui_compiled] } {
  gui::show "source $::env(SCRIPTS_DIR)/save_images.tcl" false
}
```

It replaces only that block with a comment explaining that optional GUI images are disabled for deterministic headless evidence. The patch script records the complete file SHA-256 before and after replacement, the exact removed text, replacement count, image digest and workflow source SHA. A missing or duplicate block is a hard failure.

## All-required pass gates

1. The 8x6 signed-GEMM equivalence test passes before routing.
2. Exactly one CSV row exists with identity `sky130hd / blocal / 8x6 / seed 173` and `attempted=True`, `route_ok=True`, and an empty error stage.
3. Final setup, hold, maximum-slew, maximum-fanout, maximum-capacitance and detailed-route DRC counts are all zero.
4. Period, critical-path delay, cell count, DFF count, synthesis area and wirelength are positive; GDS, ODB, SPEF and netlist hashes are lowercase 64-character SHA-256 values.
5. The patch manifest proves one and only one replacement, distinct before/after hashes and the exact frozen image digest.
6. The driver log contains the native finish stage and contains neither `Signal 11 received` nor a `make` failure.

Every gate is required. A process exit alone is insufficient. All logs, reports, the CSV, patch manifest and validator summary are retained whether the canary passes or fails. No selected retry is permitted.

## Interpretation boundary

A pass is implementation-fidelity evidence for a reporting-pipeline repair only. It says nothing new about B-local timing, area, novelty or practical utility. A later confirmatory study would require new geometries and seeds, the same all-required scientific gates, and a protocol frozen on main before any route. All previously opened geometries and seeds, including this canary's seed 173, remain excluded.
