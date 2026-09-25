# SIMILARITY electrical-margin canary: frozen-gate pass with antenna follow-up

**Status (25 September 2026): every frozen canary gate passed.** This is
opened-data flow-qualification evidence only. It does not rescue either prior
prospective null, confirm B-local performance, establish novelty or support a
breakthrough claim.

The protocol was frozen by PR #77 at
`bb9a8887be5411247afe59404652676d293d1cc8` before GitHub Actions
[run 36140794251](https://github.com/sushxnthd/kernellum/actions/runs/36140794251)
routed the matrix. The run used the already opened 10x5, 7x8 and 8x7 shapes,
canary-only seed 263, both platforms and all three topologies. Relative to the
published replication, only `CAP_MARGIN=30` and `SLEW_MARGIN=25` changed.

## Frozen result

All seven all-required gates pass:

- all three signed-GEMM equivalence tests emitted their frozen pass markers;
- exactly six route shards contain the exact 18 planned identities and six
  exact headless-flow patch manifests;
- all 18 native drivers finished without a crash or `make` failure;
- all 18 rows are attempted and complete with zero final setup, hold,
  maximum-slew, maximum-fanout, maximum-capacitance and detailed-route DRC
  violations;
- every row preserves the exact DFF count and synthesis cell area from the
  frozen replication comparator;
- all 72 GDS, ODB, SPEF and final-netlist SHA-256 values match the downloaded
  products; and
- all 18 final reports exceed the frozen 2% cap- and slew-headroom thresholds.
  The worst observed normalized headroom is 23.22% for capacitance and 16.17%
  for slew.

The independently written raw-artifact checker reproduces the official pass
without importing the frozen evaluator. Its retained output records eight
verified artifact digests, six CSV shards, 18 rows, six patch manifests, three
functional logs, 18 native drivers, 18 finish reports, 18 detailed-route DRC
reports, 18 route logs and 72 verified final-product hashes.

## Supplemental antenna observation

The frozen protocol did not include antenna counts. Direct inspection of all
18 raw route logs found one final exception: Sky130HD B-local 10x5 seed 263
ends with one antenna net violation and one antenna pin violation. All other
route logs end with zero. This observation cannot retroactively change the
preregistered canary verdict, and it is not hidden.

The affected route began post-detailed-route repair with 22 antenna
violations. Repair reduced the count to one, then the same one violation
remained through every allowed post-route repair iteration. The log reports
`GRT-0243`, “Unable to repair antennas on net with diodes.” OpenROAD documents
that warning for technology rules with a constant
`ANTENNADIFFSIDEAREARATIO`, where inserting more diodes cannot improve the
ratio. Therefore an arbitrary increase in the same diode-repair iteration
count is not a justified intervention.

The frozen cap/slew margin settings are qualified for their exact gates, but
the flow is not yet qualified for a future all-antenna-clean confirmation.
Any next flow canary must freeze an explicit antenna gate and a mechanism
capable of addressing the constant-ratio residue, using only opened geometry
and a canary-only seed. No architecture confirmation should route until that
qualification either passes or is published as a null.

## Evidence

`evidence/electrical_margin_canary/` preserves the byte-identical functional
and final-summary Actions ZIPs, a compact ZIP of all audit-relevant raw CSVs,
manifests, functional/native/route/final logs and reports, the official
artifact digests, the independent checker and its exact output. The six
original route ZIPs were also downloaded and byte-checked; their large binary
GDS/ODB/SPEF payloads are represented in the repository by the official ZIP
digests and by 72 independently recomputed final-product hashes. The compact
evidence ZIP has SHA-256
`926d7ea10410491db841a9c715797e6d2da321b10436efb6855abf288827a698`.

The canary workflow is pinned to its exact frozen SHA so evidence/report
commits cannot rerun the physical matrix. Shapes 10x5, 7x8 and 8x7 and seed
263 remain permanently excluded from later confirmation.
