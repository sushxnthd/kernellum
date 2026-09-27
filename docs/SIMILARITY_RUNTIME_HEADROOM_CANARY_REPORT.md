# SIMILARITY runtime/headroom canary: complete flow-qualification pass

**Status (27 September 2026): every frozen canary gate passed.** This is
opened-data flow-qualification evidence only. It does not rescue any prior
prospective null, confirm B-local performance, establish novelty, support a
breakthrough claim or imply an admissions outcome.

PR #83 froze the protocol at
`8eb81e96eb1a33ed7f5e0759dece9b365fb52a5a` before GitHub Actions
[run 36281577690](https://github.com/sushxnthd/kernellum/actions/runs/36281577690)
routed the matrix. The canary used already opened 7x10 and 10x7 geometries,
canary-only seed 373, both platforms and all three topologies. Relative to the
previously qualified physical flow, only `CAP_MARGIN=31` and the 7200-second
per-stage subprocess limit were newly frozen; `SLEW_MARGIN=25`, the headless
final-report patch and the pre-detailed-route antenna ratio margin of 20 were
unchanged.

## Frozen result

All eight all-required gates pass:

- both signed-GEMM equivalence tests emitted their exact pass markers;
- exactly 12 independent route artifacts contain the 12 planned identities;
- all 12 manifests match the pinned image and source SHA, both exact one-block
  flow patches, the 7200-second limit, 31% capacitance margin, 25% slew margin,
  antenna ratio margin 20, seed 373 and both shapes;
- all 12 native driver logs reached the finish stage without a timeout,
  SIGSEGV or `make` failure;
- all 12 rows are complete, electrically clean and have nonempty GDS, ODB,
  SPEF and netlist SHA-256 values;
- all 12 final reports independently parse to zero setup, hold, maximum-slew,
  maximum-fanout and maximum-capacitance violations;
- all 12 detailed-route DRC reports are empty and all 12 route logs end with
  zero DRC and zero antenna net and pin violations; and
- every row preserves the exact deterministic DFF count and synthesis cell
  area published for the same platform/topology/shape in the earlier frozen
  study.

The weakest final margin is the Sky130HD full-local 10x7 route: 2.06%
capacitance headroom and 2.22% slew headroom, both above the fixed 2% gate.
The longest recorded row elapsed time is 3268.58 seconds, below the qualified
7200-second subprocess limit. These observations qualify this exact flow
setting; they are not an optimization claim and are not architectural effect
sizes.

## Independent audit and evidence

The independently written checker reproduced the official pass without
importing the frozen evaluator. It directly verified all 14 downloaded ZIP
digests against GitHub, all 103 extracted files, the frozen source-hash
manifest, both functional logs, all CSV identities and metrics, all patch
manifests, all native driver logs, every final electrical count and headroom
value, every detailed-route DRC report, every final antenna count, and the
exact DFF/synthesis-area table. Its retained output also confirms that the
official summary rows are byte-for-value consistent with the raw CSV rows.

`evidence/runtime_headroom_canary/` preserves every original Actions ZIP, a
complete extracted-evidence archive, the exact official summary, official
artifact metadata, the independent checker and its exact output. The workflow
route and validator jobs are pinned to the frozen source SHA so evidence and
report commits cannot rerun this cohort.

Shapes 7x10 and 10x7 and seed 373 remain permanently opened and excluded from
later confirmation. Any next architecture study must use genuinely unopened
geometries and seeds, freeze all functional/evidence/electrical/timing/DFF/
synthesis-area/post-route-area/area-normalized/wirelength/fanout gates before
routing, and remain subject to separate novelty, utility, power and external-
replication audits.
