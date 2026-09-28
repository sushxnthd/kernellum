# Workload-to-route pilot: executed pipeline, negative adaptive-search result

28 September 2026. Run [36442925007](https://github.com/sushxnthd/kernellum/actions/runs/36442925007).
Frozen scientific source: `9f02b571f34a1b5aa004034fc50de70adc9e5243`.
Input SHA-256: `c536a1dd230ac40c3dc3f64cb550fbcdfeceab21fca889e67aa20018c0303f73`.

## Result and product decision

All **16/16** planned candidate/seed routes passed the functional checks,
synthesis/resource checks, final routing and evidence-integrity audit. The
workflow successfully executed the path from architecture parameters to signed
GEMM checks, specialized RTL, synthesized implementation, final-route timing
and an inspectable decision report.

The adaptive method **failed its frozen performance claim**. Mean per-case modeled
latency change relative to the comparators was:

| Comparator | Adaptive latency reduction | Interpretation |
| --- | ---: | --- |
| Analytical selection | -1.2647% | Adaptive was worse |
| Static timing predictor | -0.4164% | Adaptation did not improve the mean |
| Exact expected random pair | +6.2541% | Beating random did not establish superiority over stronger baselines |

Adaptive mean oracle regret was **1.2647%**, satisfying the 2% gate. It failed
the 3% improvement over analytical selection, nonnegative improvement over the
static predictor, and never-worse-than-analytical gates. `claim_supported=false`
is preserved. Successful CI execution does not change that decision.

The analytical two-candidate policy found the exhaustive eight-candidate optimum
in **6/6** workload/seed cases. Adaptive selection found it in **4/6**. These are
six related cases from three modeled workloads and two seeds on one ECP5 family,
not evidence of universal optimization performance.

**Product decision:** use the analytical policy as the default in
`python -m kernellum.build`. Keep the adaptive method explicitly available as an
experimental option. This default was chosen after inspecting this cohort; it
does not constitute a new held-out result. No further attempts on these same
routes can confirm a new policy.

## Independent reconstruction

`scripts/audit_pilot_search.py` imports no Kernellum modules or original evaluator.
It verifies all nine original archive checksums against GitHub's artifact digests,
208 archived file hashes, all 16 route records, actual synthesis resource counts,
functional pass markers and final timing JSON. It separately implements the cycle
calculation, timing predictor, acquisition sequence, random-pair expectation and
decision gates. All 18 policy traces and the negative conclusion reproduce.

This is an independently implemented checker by the same development process,
not independent external scientific validation. Original ZIPs, including netlists,
routed configurations, test executables, raw logs and timing JSON, are preserved in
`evidence/pilot_search/original_zips/`, so the record is not dependent on Actions'
30-day artifact retention.

```bash
python scripts/audit_pilot_search.py
```

The original full pytest invocation accidentally collected an imported testbench
generator as a test (111 tests passed plus one collection/setup error). Aliasing
that import fixed the regression suite. The frozen routing runner, spec, policies
and testbench were not changed. Subsequent workflow events are prevented from
repeating the registered cohort.

## Run the usable engineering entrypoint

Live execution requires the free `iverilog`, `vvp`, `yosys` and `nextpnr-ecp5`
tools. It uses no model API. The analytical default requires no timing prior.

```bash
python -m kernellum.build \
  --spec experiments/pilot_search/spec.json \
  --workload wide --seed 1109 --execute \
  --out /tmp/kernellum-live-build
```

This runs two candidates, retains raw per-candidate evidence, and emits
`selection.json`, `selected_routes.csv`, `report.json` and `report.html`.
Supply a new output directory; existing evidence is never silently overwritten.
`--policy adaptive` and `--policy static` are optional experimental choices.

The saved demo at `examples/pilot_search/report.html` is explicitly labeled
**Recorded routing replay**. It uses the archived wide-workload seed1109 results:
the first candidate gives 44.4435 modeled ms and the second 41.8313 modeled ms.
No new toolchain work occurs during replay, and the report says so visibly.
These timings exclude host transfers, a full memory hierarchy and full-model
inference. No board, power, energy or customer-saving claim is supported.

## What this changes for Kernellum

There is now a runnable engineering pipeline and a stronger test of the search
claim. The test prevents a misleading 'better than random' pitch. It does not
establish a novel architecture, defensible AI advantage, revenue, product-market
fit or investor interest.

The next justified product evidence is whether someone can use the workflow
on an actual engineering task with less effort and fewer mistakes than their
current tools. The next justified optimization study requires a distinct policy,
a customer-relevant candidate space and untouched outcomes. Another report or
another seed sweep on this opened table will not supply that evidence.
