# Flow-qualified prospective B-local evidence

This directory preserves the complete evidence for GitHub Actions run
[`36262319975`](https://github.com/sushxnthd/kernellum/actions/runs/36262319975),
executed from frozen source
`a8f24cb1825f249c43ef43457d74bbabaac31625`.

The study is a preregistered **null**. It attempted all 72 rows, but four
Sky130HD rows exhausted the frozen 3600-second native-route timeout and one
otherwise clean NanGate45 control retained 1.97% final capacitance headroom,
below the fixed 2% requirement. No row was retried, replaced, dropped, or
reclassified.

## Contents

- `original_zips/`: all 18 route artifacts plus the functional and exact
  final-summary artifacts downloaded from Actions.
- `artifact_digests.json`: artifact IDs, byte sizes, and official GitHub
  SHA-256 digests. Every downloaded ZIP matched.
- `extracted_evidence.zip`: all 468 extracted files from the 20 original
  artifacts (SHA-256
  `1fca420462f5cc34297499b5c29176202c9a13505a5065db29e5c6f25d4834ef`).
- `exact_summary.json`: byte-identical copy of the frozen evaluator output.
- `independent_audit.py`: standalone audit that does not import the frozen
  evaluator.
- `independent_audit.json`: independently reconstructed identities, evidence
  counts, gate vector, failures, matched trios, group medians, and decision.

## Reproduce the audit

From the repository root:

```bash
python evidence/blocal_qualified/independent_audit.py
```

The expected exit status is `1`, because the archived scientific claim is a
null. A correct reproduction writes `independent_audit.json`, verifies all 20
artifact digests, reports 72 attempts, 68 complete routes, 67 eligible clean
rows, 19 matched seed trios and five complete three-seed groups, and leaves
`frozen_claim_supported` false.
