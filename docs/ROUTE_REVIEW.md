# Route Review: engineering preview

Route Review turns existing K1 route observations into a constrained architecture
comparison for a user-specified signed INT8 GEMM. It is a small first product
experiment inside Kernellum's AI Systems & Architecture program. Customer demand
and time savings have not been established.

## Run the real-data demo

From the repository root, with Python 3.10 or later:

```bash
python -m kernellum.route_review \
  --routes results/k1_routes.csv results/k1_closed_loop_routes.csv \
  --m 128 --n 1200 --k 312 \
  --baseline r08_c08_k32 \
  --max-dsp 120 --max-bram 6 --max-lut4 10000 --max-ff 10000 \
  --out /tmp/kernellum-review
```

Open `/tmp/kernellum-review/report.html`. Exact values, rejected candidates,
input SHA-256 hashes and row-level provenance are in `report.json`.
An installed checkout also exposes the `kernellum-review` command.
No API key, GPU, FPGA board, network request or additional Python dependency is
needed for this review. It reuses the existing cycle model and route data.

## What the user can decide

- Which supplied architecture has the lowest modeled kernel latency under the
  stated synthesis-resource limits?
- Which candidates are Pareto-efficient in latency, DSP, BRAM, LUT4 and FF count?
- Which candidates were excluded, and why?
- Is the named baseline eligible, and what descriptive change does the best
  supplied candidate provide relative to it?

The baseline must be explicitly named. If it is absent or ineligible, the report
does not manufacture an improvement number and the command exits 2. Invalid file
schemas also exit 2. Individual invalid attempts are retained as rejection reasons;
any such attempt disqualifies its candidate even if other attempts succeeded.

## Input contract and limitations

Use only observations of the K1 tiled GEMM implementation on the **same device,
toolchain and timing constraints**. These facts must be checked by the operator;
legacy K1 CSVs do not encode them. Do not mix ASIC data, unrelated accelerators,
different boards, timing corners or compiler versions. The program does not
independently verify source RTL, tool reports, functional equivalence or this
same-flow condition.

Required columns: `name,rows,cols,k_tile,synth_ok,route_ok,fmax_mhz,timing_metric,
nextpnr_returncode,synth_dsp,synth_bram,synth_lut4,synth_ff`.
Optional `transport` is `broadcast` (default for legacy K1 rows) or `local`.
Repeated observations require distinct explicit `seed` values. An architecture
name must identify one geometry and transport. All input columns are data only;
no supplied commands or source code are executed.

Latency is the K1 cycle model divided by supplied final-route Fmax. Resource
limits apply to **synthesis** resource counts, not a post-route or board resource
guarantee. Multiple observations use minimum observed Fmax and maximum resource
counts. This conservative descriptive summary is not a confidence bound. Different
seed sets are permitted and disclosed; they do not support a paired statistical
claim. Input hashes establish identity, not correctness.

The demo considers all 17 existing K1 candidates after their measurements are
known. It is not a prospective test, does not reproduce the separate 23.56%
portfolio result, and establishes no new search advantage. No new route run,
board latency, power, energy, end-to-end inference, external adoption or customer
savings is claimed. This version does not generate new RTL or propose unrouted
candidates. Those features require a customer need and a separate evaluation.

## Pilot acceptance test

Ask an external engineer to run the tool unaided on an in-scope workload and
their own compatible route results. Record install time, time to decision,
manual-workflow time, any wrong exclusions or misleading recommendations, and
whether the report changes a real decision. Agree the comparison procedure
before showing results. A favorable internal demo is not completion of this test.

Meaningful regression checks:

```bash
python -m unittest discover -s tests -p test_route_review.py -v
```
