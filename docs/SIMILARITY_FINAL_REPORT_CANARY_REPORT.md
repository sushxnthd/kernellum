# SIMILARITY final-report integrity canary: pass

Status: **all frozen reporting-integrity gates passed; implementation evidence only**.  
Date: 25 September 2026

The protocol was frozen by PR #72 at
`be86ce64ff13a1d1d789b8e3d7a1f476eba437f9` before GitHub Actions
[run 36105808821](https://github.com/sushxnthd/kernellum/actions/runs/36105808821)
routed the canary. The run finished successfully on 25 September 2026 at
07:40 UTC.

This canary used the already opened Sky130HD B-local 8x6 geometry and a
canary-only seed, 173. It did not rerun the failed prospective seed 157. It
tested one narrow repair: removal of the optional GUI image block from the
pinned OpenROAD-flow-scripts `final_outputs.tcl`. The B-local RTL, ASIC
configuration and pinned OpenROAD image were unchanged.

## Result

Every all-required gate passed:

- The signed 8x6 GEMM equivalence test emitted the frozen pass marker.
- Exactly one route row exists with identity
  `sky130hd / blocal / 8x6 / seed 173`; it is attempted, complete and has no
  error stage.
- The final report records zero setup, hold, maximum-slew, maximum-fanout and
  maximum-capacitance violations. Detailed routing ended at zero violations,
  the final antenna check found zero net and pin violations, and the retained
  detailed-route DRC report is empty.
- The route row contains positive timing, size and wirelength metrics plus
  four valid final-product SHA-256 values. The reported minimum period is
  6.93 ns, critical-path delay is 7.8145 ns, DFF count is 2,317, synthesis
  cell area is 313,043.984 square micrometres and wirelength is 921,235
  micrometres. These values describe the canary and are not a performance
  claim.
- The patch manifest records exactly one replacement, the frozen image
  digest, the frozen source SHA and distinct before/after file hashes. The
  exact removed and replacement text match the protocol.
- The driver reached `native finish` and contains neither `Signal 11
  received` nor a `make` failure.

The independent checker reproduced every frozen evaluator gate and agreed
with its pass decision. It additionally verified the original Actions ZIP
digests and checked the route, antenna and final electrical evidence directly.

## Evidence

The complete downloaded route and functional ZIPs, extracted CSV, frozen
summary, patch manifest, functional log, driver, routing log and final reports
are preserved in `results/similarity_final_report_canary_artifacts/`.

The original Actions artifact digests are:

- route ZIP:
  `c06f2e0407027f92eedc510758c99ec0e71e73ba86a6136a67823db3204c42e3`
- functional ZIP:
  `00233bbd628c8a0eab546db149ab5687955f446ba72d3669cb6ba498d40cec03`

The independently written checker is
`scripts/similarity_final_report_canary_independent_audit.py`; its retained
output is `results/similarity_final_report_canary_independent_audit.json`.
It can be reproduced with:

```bash
python scripts/similarity_final_report_canary_independent_audit.py \
  --artifacts results/similarity_final_report_canary_artifacts \
  --output /tmp/similarity_final_report_canary_audit.json
```

The canary workflow is pinned to the exact frozen source SHA, so later
evidence commits cannot rerun its functional or physical jobs.

## Interpretation boundary

This pass demonstrates that the diagnosed optional GUI stage can be removed
without losing the mandatory final report, physical products or evidence. It
supports a deterministic headless reporting pipeline for later experiments.
It does not rescue the 72-route preregistered null, confirm B-local timing or
area advantages, establish novelty, or support a breakthrough claim. Seed 173
and the 8x6 geometry remain excluded from later confirmation.
