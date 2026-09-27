# Runtime/headroom canary evidence

This directory preserves the complete evidence for GitHub Actions run
[`36281577690`](https://github.com/sushxnthd/kernellum/actions/runs/36281577690)
at frozen source SHA
`8eb81e96eb1a33ed7f5e0759dece9b365fb52a5a`.

- `original_zips/` contains all 14 byte-identical Actions artifacts: 12 route
  shards, the functional artifact and the final-summary artifact.
- `artifact_digests.json` records the artifact IDs, sizes and GitHub-reported
  SHA-256 digests. Every downloaded ZIP matched its published digest.
- `extracted_evidence.zip` preserves all 103 extracted files, including the 12
  CSV rows, 12 patch manifests, two functional logs, 12 native driver logs, 12
  finish reports, 12 route logs and 12 detailed-route DRC reports.
- `exact_summary.json` is the unmodified frozen evaluator output.
- `independent_audit.py` is a separately written raw-artifact checker that does
  not import the frozen evaluator. `independent_audit.json` is its retained
  output.

The independent audit reproduced every frozen gate and a `PASS`. Its minimum
normalized final headroom was 2.06% for capacitance and 2.22% for slew. This
is opened-data flow-qualification evidence only; it does not rescue any prior
null or confirm B-local performance or novelty.
