# SIMILARITY antenna-ratio-margin flow canary report

Status: **PASS as opened-data flow qualification; not architectural confirmation**.

## Frozen experiment

The protocol was merged before routing in PR #79 at source SHA
`952bc668d50222ecd274b72150b511f291aae61b`. GitHub Actions run
`36173718315` executed the fixed matrix of two platforms, three topologies,
the already-opened 10x5 geometry, and canary-only seed 277. The architecture,
clock, utilization, placement density, pinned OpenROAD-flow image, headless
final-report patch, `CAP_MARGIN=30`, and `SLEW_MARGIN=25` were unchanged. The
only new flow intervention was the preregistered addition of
`-ratio_margin 20` to global-route antenna repair before detailed routing.

This canary did not retry seed 263 or any failed row from an earlier study.
Geometry 10x5 and seed 277 remain excluded from later confirmation.

## Result

All required gates passed:

- signed 10x5 GEMM equivalence passed;
- exactly six route shards produced the exact six planned rows;
- all six manifests identify the frozen source, pinned image, exact two
  patches, and 20% antenna-ratio margin;
- all six native flows reached finish without a crash or make failure;
- all six rows have positive timing, area and wire metrics, valid product
  hashes, and zero final setup, hold, slew, fanout, capacitance and DRC
  violations;
- all six final detailed-route antenna checks report zero net and zero pin
  violations;
- every row preserved its exact preregistered DFF count and synthesis area;
- minimum normalized capacitance headroom was 27.68%, and minimum normalized
  slew headroom was 18.64%, both above the required 2% floor.

| Platform | Topology | Cap headroom | Slew headroom | Final antenna nets/pins |
|---|---:|---:|---:|---:|
| NanGate45 | B-local | 31.23% | 51.10% | 0 / 0 |
| NanGate45 | broadcast | 29.32% | 47.18% | 0 / 0 |
| NanGate45 | full local | 27.68% | 47.57% | 0 / 0 |
| Sky130HD | B-local | 33.38% | 18.64% | 0 / 0 |
| Sky130HD | broadcast | 44.08% | 22.40% | 0 / 0 |
| Sky130HD | full local | 38.65% | 19.47% | 0 / 0 |

## Independent audit and evidence custody

The audit was reproduced independently from the eight original Actions ZIPs,
without importing the frozen evaluator. The independent checker verified the
complete row matrix, signed-GEMM log, source SHA, exact patch manifests,
native-finish logs, CSV metrics and hashes, finish-report headroom, empty DRC
reports, final route-log antenna counts, exact DFF/area values, and consistency
with the official summary. It also recomputed SHA-256 for all eight original
ZIPs and all 53 extracted files. The original ZIP digests byte-match the
digests reported by GitHub Actions.

The repository preserves the eight original ZIPs, the independent checker,
its machine-readable output, and this report under
`evidence/antenna_margin_canary/`. The physical and validator jobs are pinned
to the frozen source SHA so evidence commits cannot rerun or alter the matrix.

## Interpretation

This is credible evidence that the exact `CAP_MARGIN=30`, `SLEW_MARGIN=25`,
pre-detailed-route `-ratio_margin 20`, and headless-report combination can
produce complete electrically, DRC and antenna-clean evidence across the
fixed opened-data matrix. It closes the identified flow-integrity problem for
this scope.

It does **not** rescue either preregistered B-local null, confirm B-local
performance, establish architectural novelty, measure power or deployed
throughput, support an HAA admissions claim, or constitute a scientific
breakthrough. A new architecture test must be frozen on never-opened
geometries and seeds before routing, and any positive result still requires
reproducibility, prior-art, practical-utility, routed-area and power audits.
