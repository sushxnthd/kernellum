# Flow-qualified B-local prospective study evidence

This directory preserves the complete available evidence for GitHub Actions run
[`36298460695`](https://github.com/sushxnthd/kernellum/actions/runs/36298460695)
at frozen source SHA
`8aba1ab82c9cfec0388c4ff3bfd6999c8f36cddf`.

- `original_zips/` contains all 73 artifacts that Actions published: 71 route
  shards, the functional artifact and the final-summary artifact. The planned
  Sky130HD B-local 11x6 seed421 route artifact was never published.
- `artifact_digests.json` records the official artifact IDs, sizes and GitHub
  SHA-256 digests. All 73 downloaded ZIPs match their official digests.
- `extracted_evidence.zip` contains all 579 files extracted from the functional
  and 71 route artifacts. It includes 71 CSV rows, manifests, native driver
  logs, finish reports, route logs and detailed-route DRC reports, plus the
  four signed-GEMM functional logs and their retained executables.
- `exact_summary.json` is the unmodified frozen evaluator output.
- `independent_audit.py` is a separately written raw-artifact checker that does
  not import the frozen evaluator or route module. `independent_audit.json` and
  `independent_audit.txt` are its retained machine-readable and concise outputs.
- `failed_job_steps.json` preserves the GitHub job/step state and the failed log
  retrieval for the one route shard that produced no artifact.

The independent audit reproduced the frozen null. There are 71 attempted,
clean, fully evidenced rows and 23 complete topology trios; the missing route
is Sky130HD B-local 11x6 seed421. Independently of that evidence-completeness
failure, the complete holdouts fail two performance gates: NanGate45 8x9
retention is 59.26% against the required 70%, and only two of four holdouts
clear the required synthesis-area-normalized joint-win threshold.

This is a preregistered null, not confirmation or a breakthrough. No row is
retried, replaced, dropped or reclassified.
