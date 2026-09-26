# Flow-qualified prospective B-local study: preregistered null

**Status (27 September 2026): NULL.** The 72-route study frozen on main at
`a8f24cb1825f249c43ef43457d74bbabaac31625` before routing
([run 36262319975](https://github.com/sushxnthd/kernellum/actions/runs/36262319975))
does **not** support its all-required claim. This is neither confirmation nor a
breakthrough, and it does not rescue either earlier prospective null.

## Frozen outcome

The run attempted every planned row and passed signed-GEMM equivalence on all
four previously unopened shapes. All 18 patch manifests match the preregistered
headless-report, capacitance/slew-margin, and antenna-ratio-margin flow. The
frozen evaluator and a separately implemented audit agree on the outcome:

| Item | Result |
| --- | ---: |
| Planned and attempted rows | 72 / 72 |
| Native routes with full finish evidence | 68 / 72 |
| Rows meeting every route/electrical/evidence/headroom gate | 67 / 72 |
| Complete matched topology trios | 19 / 24 |
| Complete three-seed platform/shape groups | 5 / 8 |
| Original Actions artifacts with matching official digest | 20 / 20 |
| Frozen claim | **FAIL** |

The five ineligible rows are:

| Platform | Topology | Shape | Seed | Frozen failure |
| --- | --- | ---: | ---: | --- |
| NanGate45 | broadcast | 7x10 | 347 | clean route, but capacitance headroom 1.97% < 2% |
| Sky130HD | B-local | 7x10 | 347 | native route exceeded the fixed 3600 s timeout |
| Sky130HD | full local | 7x10 | 293 | native route exceeded the fixed 3600 s timeout |
| Sky130HD | full local | 10x7 | 293 | native route exceeded the fixed 3600 s timeout |
| Sky130HD | full local | 10x7 | 347 | native route exceeded the fixed 3600 s timeout |

The NanGate45 row has zero setup, hold, slew, fanout, capacitance, DRC and final
antenna violations and all final products. Its final capacitance slack is
0.5136103 fF against a 26.0161991 fF limit, or 1.97%; the preregistered residual
headroom threshold was 2%. The approximately 0.03 percentage-point shortfall is
small but unambiguous and cannot be rounded into a pass.

The four Sky130HD CSV rows record `route_ok=False`,
`error_stage=native_route`, and no certified final products. Each corresponding
driver log ends with the literal `TIMEOUT` emitted by the frozen 3600-second
subprocess limit. They are evidence-completeness/runtime failures, not proven
electrical failures. One B-local 7x10 route had completed an initially clean
detailed route, detected one antenna violation, inserted five diodes and timed
out during the required second detailed route. One full-local 10x7 route had
completed detailed routing and reported zero antenna violations before timing
out later in the native flow. The other two stopped during detailed routing.
None reached the required native finish marker and complete final evidence.

## Gate interpretation

The all-72 evidence and clean-route prerequisites fail. Consequently the
required eight groups, all 24 DFF/area comparisons, 12 holdout timing pairs,
four holdout timing/retention groups, both area-normalized win tests and the
wirelength gate also fail under the frozen evaluator. NanGate45 holdout
launch-Q fanout is the only downstream gate that remains independently
evaluable and it passes. The correct decision is the conjunction of all frozen
gates: **false**.

For diagnosis only, the five eligible complete groups retained 83.12% to 100%
of full-local timing benefit at their medians. Both complete discovery groups
on each platform and the complete NanGate45 10x7 holdout had B-local routed
cell area below full local and median wirelength no higher than full local.
Including the route-complete but headroom-ineligible NanGate45 7x10 control
only for diagnosis gives B-local median raw timing benefit 11.70%, retention
117.65%, routed-area-normalized factors 1.0696 versus broadcast and 1.0461
versus full local, and wirelength ratio 0.9893 versus full local. These opened
descriptive values cannot rescue the null or substitute for missing Sky130HD
holdout cohorts.

Vectorless OpenROAD power is preserved but not used as evidence of workload
energy, measured power, silicon efficiency, or deployed throughput. Its values
depend on default activity assumptions and are descriptive only.

## Evidence and independent audit

`evidence/blocal_qualified/original_zips/` contains all 18 route ZIPs, the
functional ZIP and the final-summary ZIP. Every downloaded ZIP matches the
official GitHub artifact SHA-256 digest in `artifact_digests.json`. The
`extracted_evidence.zip` bundle contains all 468 extracted files, including 72
CSV rows, 72 driver logs, 72 DRC reports, 68 finish reports, 68 route logs, 18
patch manifests and four functional logs.

`independent_audit.py` does not import the frozen evaluator. It independently
reconstructs the exact cohort, source and patch identity, artifact integrity,
raw evidence counts, electrical/headroom eligibility, matched topology trios,
group medians, DFF and area comparisons, timing retention, normalized products,
wirelength and fanout. Its JSON output matches the frozen counts, gate vector
and null decision. The exact summary preserved here is byte-identical to the
one in the Actions artifact.

## Diagnosis and next decision

The qualified electrical and antenna settings eliminated the prior study's
final cap/slew/antenna violations across every route that reached finish. The
remaining failures identify two narrower flow-qualification boundaries:

1. the largest Sky130HD holdout routes can exceed a one-hour native-process
   budget, especially when antenna diode insertion triggers a second detailed
   route; and
2. a 30% repair margin does not guarantee the separately required 2% final
   capacitance reserve on every opened NanGate45 control.

These observations justify, but do not validate, a distinct opened-data flow
canary with a preregistered longer native timeout and a minimally larger
capacitance margin derived from the 1.97% miss. It must use a new canary-only
seed, cannot retry any failed row from this cohort, and can qualify only the
flow. Any later architecture test must again use unopened shapes and seeds and
freeze every functional, evidence, electrical, timing, DFF, synthesis-area,
post-route-area, normalized-throughput, wirelength and fanout gate before
routing.

The study shapes 6x10, 10x6, 7x10 and 10x7 and seeds 293, 317 and 347 are now
opened and excluded from later confirmation. The preliminary novelty screen in
draft PR #75 remains separate: operand reuse, bounded broadcast and register
replication have substantial prior art. This null does not support a field-level
novelty claim or an admissions outcome.

The workflow's route and validator jobs are pinned to the exact frozen source
SHA in this evidence change, so merging the report cannot rerun the physical
cohort.
