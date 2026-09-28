# Workload routing pilot: frozen engineering test

28 September 2026. Status at registration: implementation and protocol, no new
route outcomes observed. The exact input is `experiments/pilot_search/spec.json`.
This is a product/selection-policy test. It is not a new architecture hypothesis,
does not reopen B-local, and cannot establish a scientific breakthrough.

## What is being built

The new `python -m kernellum.pilot` interface accepts a workload and bounded
candidate space. It chooses a candidate using prior routed observations, generates
a signed-INT8 functional test, specializes the existing RTL through synthesis,
routes it with the open ECP5 toolchain, then uses the measured routing feedback
to choose the next candidate. Every attempted candidate consumes one evaluation.
Failed attempts remain visible and cannot improve the incumbent.

This connects selection to execution; Route Review alone only compared supplied
results. Both tools are engineering previews. No customer value has been measured.

```bash
# Works offline without the EDA tools. Does not execute routes.
python -m kernellum.pilot plan \
  --spec experiments/pilot_search/spec.json --workload expand \
  --out /tmp/kernellum-plan.json

# Executes up to two candidates. Needs iverilog, vvp, yosys, nextpnr-ecp5.
python -m kernellum.pilot run \
  --spec experiments/pilot_search/spec.json --workload expand --seed 1103 \
  --out /tmp/kernellum-run
```

Use a new output directory for each execution; the runner refuses to overwrite
an existing candidate evidence directory. Output includes `selection.json`, RTL,
generated testbench, command lines, return codes, wall times, simulation/synthesis/
routing logs, netlist, routed configuration, final timing JSON and SHA-256 hashes.
The pilot does not call an LLM, paid API or cloud service. It uses the existing
deterministic nearest-neighbor Fmax model. Do not describe it as an autonomous
AI scientist or imply training a new foundation model.

## Candidate space and workload scope

Eight broadcast K1 candidates, all K_TILE=128: 6x16, 16x6, 8x14, 14x8, 10x12,
12x10, 9x12, 12x9. Route seeds: 1103 and 1109. The target is ECP5-85K/CABGA381
with a 25 MHz routing constraint. There are exactly 16 planned new routes.
These candidates and seeds were chosen before seeing their new route outputs.
They are related to earlier research and are not an independent device family.

The same frozen set is evaluated for three modeled GEMMs:

| Name | M | N | K |
| --- | ---: | ---: | ---: |
| compact | 32 | 512 | 256 |
| expand | 128 | 1200 | 312 |
| wide | 192 | 768 | 768 |

There are six workload/seed cases, not six statistically independent studies.
All policies receive the same 17 earlier K1 observations. Earlier prior-generation
cost is shared and must be disclosed, not treated as zero-cost training.

## Policies and equal budget

Every tested policy may inspect at most two new candidate route outcomes per
case. Candidate identity and modeled cycles are visible to all policies.

1. **Analytical baseline:** choose the lowest modeled cycle count first, then the
   next lowest, with deterministic name tie-breaking. This represents a simple
   geometry-aware choice without a routed timing predictor.
2. **Static surrogate:** choose twice using the existing Fmax predictor and the
   frozen prior, without updating it from the first new observation.
3. **Adaptive surrogate:** use the same predictor, but add the first successful
   observation before choosing the second candidate. No threshold is tuned on
   the new table.
4. **Random baseline:** compute the exact expected best latency over all 28
   two-candidate subsets. Do not choose one lucky or unlucky random seed.
5. **Oracle:** best of all eight candidates, for regret measurement only.

The benchmark routes all candidates to construct an oracle table. Policies are
then replayed through a callback that reveals only the selected candidate's
outcome. Code and comparison rules are committed before routing. The exhaustive
16-route benchmark cost is real; the two-route policy budgets are controlled
replays. Do not call the difference measured engineering time saved or actual
compute savings achieved during the exhaustive benchmark.

## Eligibility, integrity and functional checks

All 16 expected records must be present exactly once, source/spec/prior hashes
must match, raw output hashes must match, and tool versions must be consistent.
Every candidate must pass the generated signed GEMM simulation at its own geometry:
full K=128, a partial seven-term accumulation into the prior result, and a one-term
clearing run. Every output cell is compared to an integer reference. This is useful
functional coverage, not exhaustive equivalence or formal proof.

Synthesis must preserve one DSP per PE and positive BRAM/register counts. Synthesis
resources must satisfy the spec's limits. Routing must exit successfully, produce
a configuration and expose finite positive Fmax in the final post-route JSON.
The audit rereads that JSON. A missing or failed route makes the all-required
benchmark incomplete. Do not drop it, replenish it or claim a positive result
from the remaining rows.

The timing constraint guides routing; `--timing-allow-fail` allows observation of
slower candidates. This benchmark ranks their achieved Fmax and does not claim
every design meets the requested clock. Resource counts are synthesis counts.
Latency is the existing K1 modeled kernel cycle count divided by routed Fmax.
No board timing, memory-system overhead, model-level inference or power is measured.

## Decision gates, frozen before outcomes

The adaptive method passes this engineering target only if all evidence is complete
and valid, mean oracle regret is at most 2%, mean per-case modeled latency reduction
is at least 3% versus analytical selection and 5% versus expected random selection,
it is no worse on average than the static predictor, and it is never worse than
analytical selection in any case. Equality with static prediction is not evidence
that adaptation itself helps. All policy traces and per-case values are published.

If the target fails, report which gates failed. A complete negative result is a
successful execution of the experiment, so the audit job exits zero when integrity
passes even if `claim_supported=false`. Missing or invalid evidence exits 2.
Workflow green is not scientific success.

If adaptive selection cannot beat the analytical baseline, do not advertise an
AI optimization advantage. Keep the useful execution/reporting path and use the
measured strongest baseline. A distinct future policy requires a new protocol and
unopened data; these results become development data after this test.

## Compute and publication

GitHub's public-repository Linux workflow uses free tools, at most four concurrent
route jobs and eight shards total, with 45-minute job timeouts and ten-minute
per-command limits. No hardware purchase or paid API is required. Artifacts remain
on the run for 30 days; preserve summaries and evidence references in the repo.
The workflow pins all checkouts to the same PR head commit. After registering
source `9f02b571f34a1b5aa004034fc50de70adc9e5243`, its preflight is restricted to
that exact source so later PR synchronizations cannot repeat the cohort.
The initial full pytest job exposed accidental collection of an imported
testbench generator as a test. The test import was aliased after registration;
the routing runner, functional testbench, policies, prior and spec were unchanged.

Tests: `python -m unittest discover -s tests -p test_pilot.py -v`.
The suite checks feedback isolation, budget consumption on failures, immutable
priors, invalid predictions/specs and incomplete evidence, alongside existing K1
model tests and the full repository regression workflow.
