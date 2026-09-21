# Project SIMILARITY: Sky130HD canary report

Date: 2026-09-21

Status: **PASS — independent-platform tooling only, not a scientific result.**

## Decision

The Sky130HD canary qualifies a second open standard-cell platform for the
preregistered cross-technology experiment. It does not establish a timing,
area, power or energy advantage for either operand-transport topology.

The 3x3 canary was opened before the hypothesis and thresholds were frozen. It
is permanently excluded from discovery, confirmation, effect-size estimation
and publicity.

## Audited run

- GitHub Actions run: `35551836837`
- job: `106187884516`
- source head: `ef8d902776a5fea9d8e5156453385e96a96a6e05`
- artifact: `similarity-asic-sky130hd-canary`, ID `10618338684`
- artifact ZIP SHA-256: `dc79689c6afd0bf9340f942e3526b428eb973d1e309a409a6f3ea8c21366a355`
- OpenROAD container: `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`
- platform: `sky130hd`
- library corner: `sky130_fd_sc_hd__tt_025C_1v80`
- clock constraint: 10.0 ns

The flow source was copied from the pinned image, so the executable tools,
platform files and orchestration scripts share one immutable provenance anchor.
The image reported Yosys `0.68+post` and KLayout `0.30.12`; its OpenROAD binary
reported an unknown build string, making the image digest the executable
identity.

The documented `SKIP_CTS_REPAIR_TIMING=1` CI switch avoids a
runner-CPU-dependent illegal-instruction fault in post-CTS repair. This does
not weaken the acceptance gate: final-route setup, hold, slew, fanout and
capacitance counts must all be zero.

Subsequent CI qualification runs execute only the pinned binary's final timing
report through QEMU's deterministic `max` x86-64 CPU model. Synthesis,
floorplanning, placement, CTS and routing remain native. This isolates a
public-runner instruction-set portability fault without changing the routed
database or the executable whose timing report is accepted.

## Gates

| Gate | Result |
|---|---:|
| Broadcast SystemVerilog elaborates | PASS |
| Registered-local SystemVerilog elaborates | PASS |
| Both designs reach final GDS, ODB, SPEF and gate-level netlist | PASS |
| Final timing report is machine-parseable | PASS |
| Final setup, hold, slew, fanout and capacitance violation counts are zero | PASS |
| Detailed-route DRC report is empty for both designs | PASS |
| Nonzero combinational and sequential logic remains after synthesis | PASS |
| Registered-local structure retains additional sequential state | PASS |
| Final GDS hashes differ | PASS |

## Structural audit

| Metric | Broadcast | Registered-local |
|---|---:|---:|
| Synthesized cells | 4,650 | 4,992 |
| Sequential cells | 332 | 461 |
| Synthesized cell area (um^2) | 53,935.4784 | 58,086.9600 |
| Final critical-path delay (ns) | 6.9295 | 6.7852 |
| Final setup/hold/slew/fanout/cap violations | 0/0/0/0/0 | 0/0/0/0/0 |
| Detailed-route DRC count | 0 | 0 |

These values prove that the flow retained two distinct routed structures. They
are not scientific observations and must not influence the frozen experiment.
No power result is admissible because no switching-activity model was supplied.

## Artifact identities

| Artifact | Broadcast SHA-256 | Registered-local SHA-256 |
|---|---|---|
| `6_final.gds` | `3910a7e9755e85ea1ff8b2bb8aa9bbdb5d3c0e9d20c1f5350c35655ecb791efa` | `c0b2ecef2f72aac1b6818e627a04b649b056b0cb2f9f4a6326fdb45fc9951b01` |
| `6_final.odb` | `c6d5a47a056b2a1aed9ece96766850774193aea2952e6fece9c0d43f91b80b2d` | `275d1a2f3cf4f0a1218a2e20864e4b96c8c46fb54abbffd84561c1ac6eed3a79` |
| `6_final.spef` | `0eba9a24186b4c9b8a5299bd12c9bfb0735908114aa3250e8b9249f236fe7f02` | `2274de9efbe46f5fcaae08c3e4e18fac78a488bbdc41d814ef0d420f583158ea` |
| `6_final.v` | `9335d513fef25fb1dcddf0a5f959c60e19fbe90c320481e43d37b43727edf213` | `3dbc65057a6ab22157c1a3349f9e38a20da90586f3090f700b20bf414e330f1d` |

## Reproducible validation

`scripts/similarity_asic_canary_validate.py` reconstructs this audit from the
artifact tree. It rejects missing or empty final artifacts, nonzero final
timing or detailed-route DRC violations, a lost topology distinction, matching
final GDS hashes, or an unparseable report.

Passing this canary authorizes preregistration only. No scientific routing may
start until the geometries, seeds, estimand, calibration rule, holdouts,
failure handling and acceptance thresholds are committed and merged separately.
