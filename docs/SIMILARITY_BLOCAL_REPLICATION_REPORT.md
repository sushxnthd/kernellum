# B-local prospective replication: preregistered electrical null

**Status (25 September 2026): NULL.** The 72-route replication frozen on main at `e70fee7455876ad08c670df727338a6edbb86cc1` before routing ([run 36112274177](https://github.com/sushxnthd/kernellum/actions/runs/36112274177)) does **not** support its all-required claim. This report does not change the protocol in `SIMILARITY_BLOCAL_REPLICATION_PREREGISTRATION.md` or rescue the earlier 71/72 prospective null. No breakthrough follows from either study.

## Evidence and audit

All 18 route jobs completed successfully and produced 18 original ZIPs; the four-geometry functional ZIP and exact final-summary ZIP complete the 20 preserved original artifacts under `evidence/blocal_replication/original_zips/`. The five numbered files under `evidence/blocal_replication/extracted_parts/` reconstruct a ZIP of **all 480 extracted files**: concatenate in numeric order to `extracted_evidence.zip` (SHA-256 `9e3df8855b96042305e6c9fb8a8f6ea1a96ed40f07099e904c7d378daaedff2c`), then unzip into `evidence/blocal_replication/extracted/`. This includes 18 CSVs, 72 finish reports, 72 native driver logs, DRC and route logs, 18 exact flow patch manifests, functional logs and the byte-identical final summary. Every original ZIP was checked against its GitHub Actions SHA-256 digest in `artifact_digests.json`. `evidence/blocal_replication/independent_audit.py` reconstructs identities, route cleanliness, matching, medians, DFF/area and normalized products independently from the raw CSVs; output is `independent_audit.json`.

All 72 route rows were attempted and have native finish reports, products and driver logs. Four signed-GEMM geometry tests pass, all 18 patch manifests match, and no GUI crash or make failure occurred. **Only 68/72 routes are electrically clean.** The original finish reports identify:

| Platform | Topology | Shape | Seed | Final failure |
| --- | --- | --- | ---: | --- |
| NanGate45 | B-local | 10×5 | 239 | one maximum-capacitance violation, 27.06 fF versus 26.02 fF |
| NanGate45 | broadcast | 7×8 | 239 | one maximum-capacitance violation, 27.15 fF versus 26.02 fF |
| NanGate45 | full local | 7×8 | 211 | one maximum-capacitance violation, 28.48 fF versus 26.02 fF |
| Sky130HD | B-local | 8×7 | 181 | two maximum-slew violations (1.51 ns versus 1.49/1.50 ns) and one maximum-capacitance violation (report rounds both to 0.07 pF; slack -0.001693 pF) |

Every row has zero final setup, hold and DRC violations. These are genuine final electrical violations even when a routed job exits successfully. The frozen all-clean gate fails, leaving only 20 of 24 complete matched seed trios and five of eight complete platform/geometry groups. Completeness prerequisites also make the all-group, DFF, area, four-holdout timing and density gates fail as stated in the frozen evaluator. NanGate45 holdout launch-Q fanout and all evidence-integrity gates pass. The independent audit matches the frozen verdict: **false**. Do not drop dirty controls, replace failed seeds, round a negative slack to zero, or convert this null into confirmation.

For diagnosis only, calculations using all 72 rows *including the four electrically dirty rows* give median (candidate raw benefit, retention, area-normalized factor versus broadcast, versus full local) on sealed holdouts: NanGate45 7×8 `(9.41%, 88.89%, 1.0436, 1.0273)`; NanGate45 8×7 `(12.00%, 92.00%, 1.0637, 1.0150)`; Sky130HD 7×8 `(11.37%, 79.05%, 1.0654, 1.0002)`; Sky130HD 8×7 `(14.67%, 113.12%, 1.0926, 1.0407)`. These descriptive numbers are not eligible results and do not rescue any required gate. The proxy uses synthesis cell area times reported period, not measured energy, die area or deployed throughput.

## Diagnosis and next decision

The optional-image reporting crash is fixed: all 72 rows now have native finish evidence. The new failure is electrical across **three topologies**, including both candidate and controls. A maximum-capacitance or slew violation in the final report is enough to reject the frozen claim. Its appearance in broadcast and full local as well as B-local does not establish a B-local-specific causal mechanism. The tiny Sky130HD margins suggest an edge case in final electrical repair, but the four exact offending pins and reported loads are the evidence; root cause remains to be established. Investigate cell/net topology, final repair and electrical margin on these opened geometries only. A distinct repair needs a separately frozen canary and genuinely unopened confirmation shapes/seeds. No selective retry of this matrix is allowed. The earlier novelty screen in draft PR #75 still warns that bounded operand reuse and register replication have strong prior art; this null offers no field-level breakthrough claim.

The replication route and validator jobs are pinned to their exact frozen SHA in the evidence change, so a report merge will not launch the original physical matrix again.
