# Electrical-margin canary evidence

This directory preserves the audit-relevant evidence for Actions run
36140794251 at frozen source SHA
`bb9a8887be5411247afe59404652676d293d1cc8`.

- `similarity-electrical-margin-functional.zip` and
  `similarity-electrical-margin-final-summary.zip` are byte-identical Actions
  artifacts.
- `extracted_audit_inputs.zip` contains all six CSV shards and patch
  manifests, three signed-GEMM logs, 18 native driver logs, 18 route logs, 18
  finish reports, 18 detailed-route DRC reports and supporting synthesis/final
  logs. Its SHA-256 is
  `926d7ea10410491db841a9c715797e6d2da321b10436efb6855abf288827a698`.
- `artifact_digests.json` records the official digest of all eight original
  Actions artifacts, including the six large route ZIPs.
- `independent_audit.py` checks the unmodified downloaded artifacts;
  `independent_audit.json` is its retained output.

The original route ZIPs contain large redundant final GDS/ODB/SPEF/netlist
products. They were downloaded, ZIP-tested and verified against the official
digests. The repository evidence keeps every audit-relevant raw text file and
the exact per-product hashes rather than duplicating those binary products.
The Actions run is the source for the original route archives.
