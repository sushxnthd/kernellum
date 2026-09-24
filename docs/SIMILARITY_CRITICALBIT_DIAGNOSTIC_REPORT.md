# SIMILARITY selective critical-bit diagnostic: opened-data null

**Decision (2026-09-24 UTC): stop this intervention.** The fixed opened-data
diagnostic at [Actions run 36054211731](https://github.com/sushxnthd/kernellum/actions/runs/36054211731),
source commit `7b243236694885fc69affff10fcb6fa83b13c7f1`, completed all 12
planned routes. All routes are electrically and DRC clean and both signed
GEMM checks pass, but only 7 of 11 continue gates pass.
`prospective_study_warranted=false`. These opened 5x8/8x5 results are
exploratory and cannot confirm a claim.

## Results

| Platform and shape | Raw period benefit | Retained local benefit | Density vs broadcast | Density vs local | Candidate period |
|---|---:|---:|---:|---:|---:|
| NanGate45 5x8 | 8.14% | 63.64% | 1.03937 | 0.99553 | 1.59 ns |
| NanGate45 8x5 | 6.02% | 62.50% | 1.01644 | 1.00744 | 1.56 ns |
| Sky130HD 5x8 | **4.39%** | 53.03% | 1.00340 | 1.00542 | 7.61 ns |
| Sky130HD 8x5 | 12.23% | 69.28% | 1.07915 | 0.97601 | 7.48 ns |

The candidate met the targeted NanGate45 8x5 improvement: its median period
is 1.56 ns versus stride-two's 1.58 ns. This isolated success does not rescue
the fixed conjunction. Sky130HD 5x8 misses the 5% raw benefit gate; all four
groups miss the 70% retention gate; only two of four groups jointly beat
broadcast and full-local on period-times-synthesis-area, below the required
three. Candidate synthesis cell area remains below full-local on all routes.

## Implementation-fidelity failure

The most informative failure is structural. The RTL predicted 68 or 76
additional replica DFFs over stride-two, but the synthesized candidate has
**exactly the same DFF count as stride-two** on every route: 1,831 at 5x8
and 1,796 at 8x5. The intended replicas therefore did not survive synthesis
as distinct sequential cells. Candidate maximum-delay launch fanouts remain
14 to 18, rather than falling to per-PE fanout. Driver logs show repeated
Yosys `OPT_MERGE` and `OPT_DFF` passes. The RTL `keep` annotation on
replica registers did not enforce distinct mapped flops in this flow, a
known class of limitation discussed in Yosys issues
[#855](https://github.com/YosysHQ/yosys/issues/855) and
[#4272](https://github.com/YosysHQ/yosys/issues/4272).

This means the run did not faithfully instantiate the hypothesized physical
intervention. It still constitutes a valid null for the exact frozen source
and continue gate. It is not evidence that correctly preserved selective
replication cannot work, and it is not permission to retry this matrix.

## Evidence and reproduction

The six original route ZIPs, functional ZIP and final-summary ZIP are in
`results/similarity_criticalbit_artifacts/`. Six raw CSVs are extracted
under `results/similarity_criticalbit_download/`; the byte-reproduced
summary is `results/similarity_criticalbit_summary.json`. The frozen
evaluator reproduces the artifact summary with SHA-256
`d044ef6403799264e6a6c3cfdb9f475a1096faedd1473791d3ba17edfcf2c82d`.
The independent audit checks all 12 CSV rows against their final timing,
synthesis, DRC and route reports, verifies the source and functional marker,
recomputes every group median and reproduces the complete gate vector.

```bash
PYTHONPATH=. python scripts/similarity_criticalbit_validate.py \
  --input results/similarity_criticalbit_download \
  --output results/similarity_criticalbit_summary.json
# Exit 1 is expected for the fixed null.
python scripts/similarity_criticalbit_independent_audit.py \
  --input results/similarity_criticalbit_download \
  --baseline results/similarity_stride2_download \
  --summary results/similarity_criticalbit_summary.json
```

The GDS/ODB/SPEF/netlist bytes were omitted from the compact artifacts; their
nonempty-file SHA-256 values are recorded but cannot be rehashed from the
published ZIPs. That remains an evidence limitation.

## Next research gate

This candidate stops. Before any distinct physical study, a synthesis-only
repair canary must demonstrate that the intended hardware survives the
pinned synthesis flow: predicted extra DFFs must appear and mapped maximum
fanout must fall. Any repaired or encoded implementation is a new
intervention. It may use opened shapes only for mechanism development, and
cannot reuse any opened geometry or prior seed for confirmation. No new
prospective route should be frozen until this implementation-fidelity cause
is corrected and the cost/timing hypothesis remains credible.
