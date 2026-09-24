# SIMILARITY stride-two ASIC study: prospective null

**Decision (2026-09-24 UTC): the preregistered all-required claim failed.**
The frozen run at [GitHub Actions #36026520081](https://github.com/sushxnthd/kernellum/actions/runs/36026520081), commit
`0b3fd3c58385bd8158ac2e7bbad55cfdaa9be897`, finished 18 routing
shards, 72/72 successful and electrically/DRC-clean final routes, and four
functional-equivalence shape checks. The frozen validator exited 1 for a
**timing-retention gate**, not an electrical or missing-evidence failure. No
threshold was changed, seed replenished, or failed holdout reclassified.

## Exactly what failed

The 8x5 NanGate45 sealed holdout retained a **52.94%** median seed-paired
fraction of full-local's period benefit, below the frozen **60%** minimum.
Its per-seed fractions at seeds 53, 71 and 89 are respectively 52.94%,
52.38% and 68.75%. Its three seed medians are B=1.67 ns, L=1.50 ns and
S=1.58 ns. The median *individual* q-values are qL=10.18% and qS=6.47%;
the median of per-seed retention fractions, not a ratio of these medians,
is the preregistered 52.94%. Stride-two still saves 436 DFFs (19.53%)
and 2924.138 µm² of synthesis cell area (5.10%) versus full-local on this
shape. The period gap, rather than an area or register-count problem, defeats
the conjunction.

| Sealed holdout | Median qS | Median retained benefit | Median density vs broadcast | Median density vs full-local |
|---|---:|---:|---:|---:|
| NanGate45 5x8 | 8.72% | 68.42% | 1.04164 | 1.00410 |
| NanGate45 8x5 | 6.47% | **52.94% (fails)** | 1.02694 | 1.00044 |
| Sky130HD 5x8 | 6.02% | 72.73% | 1.01917 | 1.02112 |
| Sky130HD 8x5 | 10.19% | 66.41% | 1.06528 | 0.98448 |

The density proxy is reciprocal of final routed period times **synthesis
cell area**; it is not silicon area, energy, or power. Three of four holdout
groups beat both comparators on this proxy, including one group on each
platform; Sky130HD 8x5 loses to full-local. This narrower observation does
not rescue the all-required claim.

## Frozen gate vector and evidence

All frozen gates pass **except** `holdout_retains_at_least_60pct_full_local_benefit`:
functional equivalence; exactly 72 unique attempts; 72 electrically and
DRC-clean final routes; two complete paired seeds per eight groups (actually
three each); full-local positive timing on all eight groups; stride-two
register and area savings on all 24 triples; four holdout medians with at
least 5% raw stride-two period improvement; joint density wins on at least
three of four groups and on both platforms. Consequently
`claim_supported=false` in the frozen JSON.

The original 18 route ZIPs and the functional and final-summary ZIPs are
preserved in `results/similarity_stride2_artifacts/`. Their 18 raw CSVs are
also extracted in `results/similarity_stride2_download/`; the exact frozen
validator output is `results/similarity_stride2_summary.json`. Each route
ZIP retains all four shape-specific `6_finish.rpt`, `synth_stat.txt`,
`5_route_drc.rpt`, route logs and driver logs. The functional ZIP includes
four simulator logs and `source_sha.txt`. The summary JSON SHA-256 of
`6520dd8a1d325ea9e051ea796b180da4420b86f2afc655f7054ef7e0fa526159`
reproduces byte-for-byte from the 18 raw CSVs plus functional marker using
the evaluator frozen before routing. Independently,
`scripts/similarity_stride2_independent_audit.py` reads every archived route
report, compares its timing/area/electrical/wire metrics with every CSV row,
checks the functional logs and original commit ID, independently computes
the 11 gates, and matches all four holdout medians and the final decision.
The physical GDS/ODB/SPEF/netlist bytes were intentionally omitted by the
original workflow to conserve free artifact space: their recorded SHA-256
digests cannot be independently rehashed from this public evidence. This
is a reproducibility limitation, not proof of absent output files.

To reproduce from this checkout (no physical rerouting required):

```bash
PYTHONPATH=. python scripts/similarity_stride2_validate.py \
  --input results/similarity_stride2_download \
  --output results/similarity_stride2_summary.json
# Exit 1 is EXPECTED because the frozen all-required gate is false.
python scripts/similarity_stride2_independent_audit.py \
  --archives results/similarity_stride2_artifacts \
  --summary results/similarity_stride2_summary.json
sha256sum results/similarity_stride2_summary.json
```

## Diagnostic and next intervention

The failing 8x5 group is a **timing-retention null**, not an electrical
failure. All 8x5 NanGate45 stride-two maximum-delay reports launch from
shared `g_a[..].g_seg[..].data_q[7]` operand registers and terminate in PE
accumulators; those launching register Q pins have fanout **15**. The
corresponding full-local maximum-delay reports launch from individual
`a_local`/`b_local` operand registers into PE accumulators with Q fanout
**8, 9, 8** at seeds 53, 71, 89. This supports a *hypothesis* that the
shared segment's operand fanout and multiply-accumulate path consume some
of its routing advantage on this transposed shape; it does **not** isolate
fanout as a proven causal mechanism. The paths are arithmetic as well as
transport and the technology/shape dependence matters.

A justified next step is to prototype a distinct fanout-aware operand
delivery topology and inspect its functional behavior and critical paths
only on already-opened discovery shapes before pre-registering fresh,
unopened shapes and new seeds. Its area-normalized throughput, electrical
cleanliness and timing benefit all need explicit frozen gates. Do not rerun
these opened 5x8/8x5 holdouts as confirmation, silently omit their failures,
or re-label this preregistered null as a breakthrough. A proposal is not a
new prospective result.

The former 7x7 stride-two pilot and its mixed outcomes also remain excluded.
No claim here establishes practical energy savings, commercial signoff,
independent novelty, or an HAA admission outcome.
