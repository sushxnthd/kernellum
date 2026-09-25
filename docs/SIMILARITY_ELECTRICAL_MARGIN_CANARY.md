# SIMILARITY larger-shape electrical-margin canary

Status: **draft until merged to main; no physical route from this canary is eligible before that merge**.

## Why this intervention is justified

The B-local replication frozen at `e70fee7455876ad08c670df727338a6edbb86cc1` completed all 72 native finishes but only 68 final routes were electrically clean. Three NanGate45 routes retained one maximum-capacitance violation each; one Sky130HD route retained two maximum-slew and one maximum-capacitance violation. The affected topologies were B-local, broadcast and full local. This is therefore a cross-topology final electrical-repair problem, not evidence of a B-local-specific defect.

The fixed flow repaired design-rule limits from global-route parasitics with `CAP_MARGIN=20` and `SLEW_MARGIN=20`, then checked detailed-route parasitics. [OpenROAD's Resizer documentation](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-design) states that placement/global-route parasitics do not perfectly predict routed parasitics and that margins deliberately over-repair to compensate. The worst NanGate45 final capacitance was 28.48 fF against 26.016 fF, an overshoot of 9.46%. Under the conservative proportional model used only to choose a canary setting, an 80% repair target followed by that overshoot requires a target at or below 73.09% of the library limit, hence a capacitance margin of at least 26.91%. The canary freezes `CAP_MARGIN=30`. Sky130HD's worst slew overshoot was 1.18%; the analogous minimum is 20.93%, so the canary freezes `SLEW_MARGIN=25`.

These calculations motivate settings; they do not prove causality or predict a pass. The canary is allowed to fail.

## Frozen matrix and exclusions

The source RTL, 20 ns clock, 35% core utilization, 0.50 placement density, post-CTS repair choice, pinned ORFS image, headless final-report patch and route parser remain unchanged. Only the two repair margins change. The matrix is:

- platforms: NanGate45 and Sky130HD;
- topologies: broadcast, full local and B-local;
- already-opened larger shapes: 10x5, 7x8 and 8x7;
- one previously unused, canary-only physical seed: 263;
- 18 planned routes in six independent shards.

The shapes and seed 263 are permanently excluded from any later discovery, calibration or confirmation claim. This canary cannot rescue either earlier prospective null, confirm B-local performance, establish novelty or support a breakthrough claim.

## All-required gates frozen before routing

1. Signed-GEMM equivalence between B-local and full-local RTL passes on all three shapes.
2. Exactly six route shards contain exactly the 18 unique planned rows. Exactly six patch manifests certify the pinned image, merged source SHA and one exact removal of the optional GUI image block.
3. All 18 driver logs reach native finish without SIGSEGV or `make` failure, and all 18 finish reports are present.
4. Every row is attempted, has no error stage, has positive timing/area/wire metrics and hashes for nonempty GDS, ODB, SPEF and netlist products, and reports zero final setup, hold, maximum-slew, maximum-fanout, maximum-capacitance and detailed-route DRC violations.
5. Every row exactly preserves the deterministic DFF count and synthesis cell area published by the frozen replication for the same platform/topology/shape. This prevents an accidental architecture or synthesis change from masquerading as a flow repair.
6. Beyond integer violation counts, every final report retains at least 2% normalized headroom for both maximum capacitance and maximum slew (`max_*_check_slack_limit >= 0.02`). This guards against rounded or tool-filtered near misses.

Every gate is required. No failed route may be retried, replaced or dropped; no threshold or seed may change after merge. A pass is implementation-fidelity evidence only. A failure is published as a complete opened-data null and stops this exact intervention.

If and only if the canary passes, a distinct prospective architecture study may be frozen on geometries and seeds never opened by prior ASIC work. Its evidence, electrical, timing, DFF, synthesis-area, routed-cost and area-normalized gates must be committed before routing. Novelty and practical-utility audits remain separate requirements.
