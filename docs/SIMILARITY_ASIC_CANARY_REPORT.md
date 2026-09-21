# Project SIMILARITY: ASIC flow canary report

Date: 2026-09-21

Status: **PASS — tooling only, not a scientific result.**

## Decision

The stage-0 NanGate45 canary authorizes preregistration of the cross-technology experiment. It does not authorize a claim about whether broadcast or registered-local transport is better in an ASIC.

The 3x3 canary is permanently excluded from discovery, confirmation, effect-size estimation and publicity.

## Audited run

- GitHub Actions run: `35548256714`
- job: `106178049206`
- source head: `a3b1fe8797ab00422a0c1ad6fd07fc963eddcb7b`
- artifact: `similarity-asic-canary`, ID `10617446290`
- artifact ZIP SHA-256: `686d2f75bff3f84663e7cadaffc042f3fde82817614b8ba1188d4b080c7dcf02`
- OpenROAD container digest: `sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`

The rerunnable workflow additionally pins the OpenROAD Flow Scripts source commit and emits tool versions into `toolchain.txt`.

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
