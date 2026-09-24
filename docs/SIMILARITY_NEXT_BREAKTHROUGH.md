# Kernellum: next scientific gate

Date frozen: 2026-09-24

## What the prior study actually established

The 96-route ASIC transfer study rejected its all-required claim (16/18 gates).
Nine final routes retained max-capacitance or slew violations, and the
size-only cross-technology bridge rank was 0.294 against a frozen 0.60 gate.
The four Sky130HD holdouts had positive timing effects and 2.41 percentage
points mean absolute prediction error, but cannot rescue either failed gate.
The 23.56% routed-workload result is an independent ECP5 portfolio result,
not a measured ASIC or physical-board speedup.

An exploratory diagnostic on the *already opened* ten Sky130HD geometries
also argues against immediately fitting a row/column coefficient. An ordinary
least-squares law with sqrt(PE) has leave-one-geometry-out mean absolute
error of 3.46 percentage points. Adding signed log(rows/cols) increases this
error to 3.97 percentage points. These are retrospective model-selection
numbers, not an independent confirmation or a new breakthrough.

## Gate A: qualify electrical repair on excluded prior geometry

The next build repeats the *previously opened* 7x7 geometry on NanGate45 and
Sky130HD, for broadcast and registered-local transport, on the original
placement seeds 11, 29, 47. This gives 12 routes. The same RTL, clock,
utilization, density, tool image, report parser and final-artifact requirements
are used. Only the ORFS repair margins change: CAP_MARGIN=20 and
SLEW_MARGIN=20 in separate canary configs. OpenROAD Flow Scripts documents
these as margins during max-capacitance and max-slew repair.

Gate A passes only when all 12 expected unique routes finish, all final
setup, hold, slew, fanout, capacitance and detailed-route DRC counts are zero,
and all required GDS, ODB, SPEF and netlist files are present and nonempty.
Null or duplicate routes fail. The old 7x7 data are not replaced.

The 7x7 canary is permanently excluded from future discovery, calibration,
confirmation, effect-size claims and publicity for this prospective gate.
Gate A tests workflow qualification, not a scientific hypothesis. A failure
blocks a new scientific matrix until its cause is diagnosed.

## Gate B: fresh anisotropy and transfer study (pending Gate A)

Only after the repair canary passes, freeze a new model, disjoint discovery
and holdout geometries, seeds, thresholds, source hash and analysis script
**before** starting any new scientific routes. Compare a size-only baseline
against a row/column-aware model on independent geometries. The previous ten
Sky130HD geometries and all previously routed NanGate45 geometries must be
excluded from final confirmation. Fit and choose the model using only a
declared discovery split. Keep identical electrical checks on every successful
route. Report the full matrix, failures, both models' signed and absolute
errors, paired-seed effects, sequential-cell and area costs.

Do not claim a cross-technology mechanism from Gate A. Do not use held-out
routes to choose features or thresholds for Gate B. If no prospective model
beats the size-only baseline, publish that null and investigate timing-path
identity rather than renaming it a breakthrough.

## Reproduction

```bash
PYTHONPATH=. python -m pytest -q tests/test_similarity_asic_repair_canary.py tests/test_similarity_asic_transfer.py
```

The routing workflow uses the pinned image from the earlier transfer study.
It publishes each route CSV and the final canary summary as Actions artifacts.

## References

- Previous frozen study and result: `docs/SIMILARITY_ASIC_TRANSFER_PREREGISTRATION.md`,
  `docs/SIMILARITY_ASIC_TRANSFER_REPORT.md`.
- OpenROAD Gate Resizer: https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html
- OpenROAD Flow variables: https://openroad-flow-scripts.readthedocs.io/en/latest/user/FlowVariables.html
