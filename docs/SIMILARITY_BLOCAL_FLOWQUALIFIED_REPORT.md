# Flow-qualified prospective B-local replication: preregistered null

**Status (27 September 2026): NULL.** The 72-route study frozen on main at
`8aba1ab82c9cfec0388c4ff3bfd6999c8f36cddf` before routing
([run 36298460695](https://github.com/sushxnthd/kernellum/actions/runs/36298460695))
does **not** support its all-required claim. This is neither confirmation nor a
breakthrough, and it does not rescue or reclassify any earlier null.

## Frozen outcome

Signed-GEMM equivalence passed on all four previously unopened shapes. Every
available route artifact matches the preregistered source, image, flow patches,
margin settings, timeout and matrix. The frozen evaluator and a separately
implemented audit agree on the outcome:

| Item | Result |
| --- | ---: |
| Planned route rows | 72 |
| Attempted rows with artifacts | 71 / 72 |
| Clean, fully evidenced rows | 71 / 72 |
| Complete matched topology trios | 23 / 24 |
| Complete three-seed platform/shape groups | 7 / 8 |
| Published Actions artifacts with matching official digest | 73 / 73 |
| Synthesis-area-normalized joint holdout wins | 2 / 4 (required 3 / 4) |
| Post-route-area-normalized joint holdout wins | 3 / 4 (required 3 / 4) |
| Frozen claim | **FAIL** |

The run has two independent failure mechanisms. Either one is sufficient to
make the preregistered result a null.

## Evidence-completeness failure

The missing row is Sky130HD B-local 11x6 seed421 in the discovery split. Its
Actions job ended while `Apply frozen repairs and route one unopened shard`
was still recorded as in progress. Artifact upload and post-job steps remained
pending, and no route artifact was created. GitHub's job-log endpoint returns
`404 BlobNotFound`, so the internal termination cause cannot be recovered.

This row is absent rather than electrically failed: there is no CSV, native
finish marker, finish report, route log, DRC report or final-product hash from
which to make an electrical determination. It is therefore an all-required
evidence-completeness failure, not a proven dirty route. It is not retried,
replaced, dropped or reclassified.

All 71 published route artifacts contain one exact row, patch manifest, native
finish driver, finish report, route log and detailed-route DRC report. Every
one of those rows has complete product hashes, positive metrics, zero setup,
hold, slew, fanout, capacitance, DRC and final-antenna violations, and at least
2% final capacitance and slew headroom. All 23 available matched trios meet the
frozen DFF, synthesis-area and post-route-area constraints. These conditional
facts do not repair the missing 72nd row.

## Independent sealed-holdout failure

The sealed holdouts are complete, so their performance gates are independently
evaluable without the missing discovery row. Median results are:

| Platform | Holdout | Raw B-local timing benefit | Retention | Synthesis proxy vs broadcast / local | Routed proxy vs broadcast / local | Wirelength / local |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NanGate45 | 8x9 | 9.20% | **59.26%** | 1.0258 / **0.9690** | 1.0298 / **0.9718** | 0.9397 |
| NanGate45 | 9x8 | 10.98% | 90.48% | 1.0593 / 1.0147 | 1.0593 / 1.0143 | 0.9651 |
| Sky130HD | 8x9 | 15.75% | 85.99% | 1.1225 / **1.0087** | 1.1107 / 1.0176 | 0.9238 |
| Sky130HD | 9x8 | 13.99% | 89.87% | 1.1043 / 1.0104 | 1.0901 / 1.0187 | 0.9275 |

NanGate45 8x9 retains only 59.26% of full-local's median timing benefit,
below the frozen 70% requirement. The synthesis-area-normalized proxy clears
the joint 1.01 threshold against both controls in only two of four holdouts,
below the required three of four. Sky130HD 8x9 misses the local comparison at
1.0087; NanGate45 8x9 is below full local at 0.9690.

All four holdouts exceed the 5% raw timing-benefit threshold. The independently
required post-route-area-normalized gate passes in three of four groups across
both platforms, as do the wirelength and targeted fanout gates. Those positive
descriptive and secondary results cannot rescue the failed retention and
synthesis-area-normalized gates.

## Vectorless-power boundary

Vectorless OpenROAD power is preserved but is not a frozen performance gate
and is not workload energy, measured power, silicon efficiency or deployed
throughput. Descriptively, B-local's median vectorless-power ratio to full local
is 1.99, 1.96, 1.76 and 1.74 across the four holdouts. These values strengthen
the need for workload-driven power validation before any practical-efficiency
claim; they do not establish an energy result.

## Evidence and independent audit

`evidence/blocal_flowqualified/original_zips/` contains every artifact that
Actions published: 71 route ZIPs, the functional ZIP and the final-summary ZIP.
All 73 downloads match the official GitHub SHA-256 digests recorded in
`artifact_digests.json`. The absent route artifact is named explicitly rather
than synthesized or substituted.

`extracted_evidence.zip` preserves all 579 extracted files from the functional
and route artifacts. `exact_summary.json` is the frozen evaluator output.
`independent_audit.py` imports neither the frozen evaluator nor the route
module; it independently reconstructs the exact matrix, source and patch
identity, artifact integrity, raw-evidence multiplicity, electrical/headroom
eligibility, matched trios, group medians, DFF and area comparisons, timing
retention, normalized products, wirelength and fanout. Its JSON and text
outputs reproduce the frozen gate vector and null decision.

The failed job's step state and unavailable-log response are preserved in
`failed_job_steps.json`. No missing log or artifact is represented as evidence.

## Scientific decision

This result closes the current B-local intervention. After three prospective
cohorts, separately qualified reporting/electrical/antenna/runtime flow repairs,
and this fully qualified-flow replication, the architecture does not meet its
frozen robust claim. The complete holdouts show that the shortfall is not only
tooling: timing retention and synthesis-area-normalized value are
geometry-dependent, and the universal thresholds fail even where every route
is clean and complete.

More B-local geometry or seed repetitions, selected retries, threshold changes
or post hoc metric substitutions would not be a scientifically distinct test.
Any future Kernellum work must begin from a new causal architectural hypothesis
and freeze genuinely new data and practical metrics before opening results.
The separate primary-source and patent novelty review must also be reconciled
before any field-level novelty claim.

The shapes 6x11, 11x6, 8x9 and 9x8 and seeds 397, 421 and 449 are opened and
permanently excluded from later confirmation. The workflow's physical route and
validator jobs are pinned to the exact frozen source SHA in this evidence
change, so merging the report cannot rerun the cohort.
