# SIMILARITY ASIC repair canary: final report

Result checked: 2026-09-24. Qualification gate: **PASS**.

The previously opened 7x7 geometry was routed with broadcast and full-local
transport at seeds 11, 29 and 47 on NanGate45 and Sky130HD. All twelve
individual route CSVs were downloaded and compared with every row of the
published final JSON summary. There are exactly twelve unique planned rows;
each reports `route_ok=True`, six zero final violation counts (setup, hold,
slew, fanout, capacitance and detailed-route DRC), positive final minimum
period and synthesis area, and nonempty SHA-256 hashes for GDS, ODB, SPEF
and final netlist. The local evaluator and the published evaluator both
return `complete=true` and `all_final_routes_electrically_clean=true`.

| Platform | Topology | Seed | Final period (ns) | Synthesis cell area (µm²) | DFF cells | Final violations (six fields) |
|---|---|---:|---:|---:|---:|---:|
| NanGate45 | Broadcast | 11 | 1.74 | 64,235.808 | 1,650 | 0 |
| NanGate45 | Broadcast | 29 | 1.73 | 64,235.808 | 1,650 | 0 |
| NanGate45 | Broadcast | 47 | 1.68 | 64,235.808 | 1,650 | 0 |
| NanGate45 | Full local | 11 | 1.52 | 70,919.324 | 2,743 | 0 |
| NanGate45 | Full local | 29 | 1.53 | 70,919.324 | 2,743 | 0 |
| NanGate45 | Full local | 47 | 1.52 | 70,919.324 | 2,743 | 0 |
| Sky130HD | Broadcast | 11 | 8.53 | 304,852.3776 | 1,650 | 0 |
| Sky130HD | Broadcast | 29 | 8.29 | 304,852.3776 | 1,650 | 0 |
| Sky130HD | Broadcast | 47 | 8.21 | 304,852.3776 | 1,650 | 0 |
| Sky130HD | Full local | 11 | 7.21 | 330,998.704 | 2,743 | 0 |
| Sky130HD | Full local | 29 | 7.20 | 330,998.704 | 2,743 | 0 |
| Sky130HD | Full local | 47 | 7.25 | 330,998.704 | 2,743 | 0 |

The [pinned workflow run](https://github.com/sushxnthd/kernellum/actions/runs/36004416945)
contains all twelve route CSV artifacts and the `similarity-asic-repair-canary-summary`
artifact. Source commit:
`28cae4b95c2bbb3d1a98084c03834caf82187387`. The unchanged pinned ORFS
image is `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.
The only planned configuration repair was `CAP_MARGIN=20`, `SLEW_MARGIN=20`.
The exact unmodified final JSON summary, including all twelve raw rows and
their artifact hashes, is checked into `results/similarity_asic_repair_canary.json`.
Artifacts have a 30-day retention setting; the checked-in JSON preserves the
gate outcome and raw CSV values afterward.

This is a plumbing qualification. Because all 7x7 routes were already
opened, **none of the twelve rows may be used as discovery or confirmation
evidence for the prospective scientific claim**. The original 96-route
cross-technology study and its failed gates remain unchanged.
