# Project SIMILARITY: ASIC flow canary report

Date: 2026-09-21

Status: **PASS — tooling only, not a scientific result.**

## Decision

The stage-0 NanGate45 canary authorizes preregistration of the cross-technology experiment. It does not authorize a claim about whether broadcast or registered-local transport is better in an ASIC.

The 3x3 canary is permanently excluded from discovery, confirmation, effect-size estimation and publicity.

## Audited run

- GitHub Actions run: `35548878352`
- job: `106179789287`
- source head: `c034fade10dfbb2fa9ac7619e90167418fc9d0b9`
- artifact: `similarity-asic-canary`, ID `10617343435`
- artifact ZIP SHA-256: `4e64cdddc0e0f6988c340ad3d14dd7779245ffc1d3335990a269b7610164d67c`
- OpenROAD Flow Scripts commit: `3a964e13f11a4e435aac01ffa14db0a7d2853720`
- OpenROAD container digest: `sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`

The audited run used those pins and emitted Yosys `0.68+post` and KLayout `0.30.12` into `toolchain.txt`. The container's OpenROAD binary reported an unknown build string, so the immutable container digest is the executable provenance anchor.

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

The raw reports contain timing, area and unannotated power estimates. None is interpreted here. In particular, the power table has no preregistered switching-activity model and is inadmissible for energy claims.

## Reproducible validation

`scripts/similarity_asic_canary_validate.py` verifies the artifact tree, parses only final-route timing, rejects nonzero final timing or detailed-route DRC violations, checks that the topology distinction survived synthesis, hashes final artifacts and emits a JSON audit record.

## What remains blocked

The scientific study must not begin until its geometries, platform split, physical-design conditions, normalized estimands, success thresholds, null handling, equivalence test and portfolio evaluation are frozen in a separate preregistration. The canary values cannot inform those thresholds.
