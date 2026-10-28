# Land V6 Independent Replication — D4-Weighted Semantic Voting

Status: PREREGISTERED BEFORE DOWNLOADING, EXTRACTING, OR INSPECTING ANY V6 CANDIDATE CORRECTNESS OR SELECTOR RESULT.

## Independent replication source

Historical Johan Land ARC-AGI-2 V6 public run:
- reported public evaluation score: 70.7%
- Kaggle notebook: `johanland/johan-land-solver-v6-public`
- historical scriptVersionId: `286318109`

This is a separate earlier solver generation from the V7 discovery corpus.

The exact Kaggle notebook version corresponding to scriptVersionId 286318109 will be determined using output-download metadata only. No correctness fields are inspected during version mapping.

## Why V6 is the confirmatory corpus

V7 version 27 generated the exploratory W4 signal.

Public V7 notebook versions 28–39 were scanned chronologically under a preregistered coverage-only rule; none had sufficient trace coverage for replication.

V6 is therefore chosen as a separately released historical full evaluation run, not because of any observed W4 behavior.

## Frozen candidate protocol

Identical to the V27 independent test:
1. extract codegen calls only;
2. extract complete executable `solver(grid)` Python;
3. deduplicate normalized source by SHA256 per task/test case;
4. independently reverify exact correctness on every labeled demonstration;
5. candidate code executes in fresh network-disabled, read-only Docker containers with no evaluation-data mount, no secrets, dropped capabilities, PID/memory/CPU limits, and a 2.0-second per-grid timeout;
6. test truth is unavailable to candidate execution and selector construction.

If V6 codegen logs use a mechanically different JSON key layout, only a schema adapter may change; the semantic inclusion rule above may not.

## Frozen probes and semantic classes

Exactly the V27 protocol.

Primary semantic-class signature:
- mixed 24-probe set generated only from demonstration inputs:
  - D4 transforms;
  - three deterministic nonzero-color permutations preserving zero;
  - cyclic row/column rolls ±1;
- same task/test-seeded deterministic sampling.

D4 weighting probes:
- unique D4 transforms of demonstration inputs;
- cap 12;
- same generation order.

Semantic class:
identical complete mixed-probe signature.

Canonical representative:
shortest normalized source, then SHA256.

Invalid execution centrality:
0 contribution on that probe; invalid outputs cannot form positive agreement mass.

## Replication primary

B_cls:
one equal vote per semantic class for the actual test-grid prediction.

W4:
each semantic class votes for its actual test-grid prediction weighted by its D4-only centrality.

Ties use the same canonical serialized-grid ordering as V27.

No model weighting, temperature, score calibration, task filtering, or learned parameters.

## Usable case

Same as V27:
- >=3 independently verified candidates;
- >=3 mixed-probe semantic classes;
- >=2 distinct valid test predictions.

## Coverage gate

Replication is interpretable only with:
- >=30 usable cases;
- >=20 distinct ARC tasks.

If coverage fails, verdict is INCONCLUSIVE_COVERAGE.

## Frozen practical success rule

W4 replicates only if every condition holds:

1. coverage gate passes;
2. W4-B_cls top-1 >= +3.0 percentage points;
3. task-bootstrap 95% CI for W4-B_cls is not entirely below zero;
4. W4 improves >=5 distinct task IDs;
5. W4 is non-inferior on oracle-positive cases;
6. W4 has positive gain on minority-correct cases.

## Mechanism replication endpoint

Independently of W4 practical success, measure D4 centrality vs exact class correctness:
- mean within-case Spearman;
- mean within-case AUC;
- 10,000 within-case label-permutation null using seed 20261028;
- same-model-family association where model metadata permits.

Mechanism replication is considered positive if:
- mean AUC > 0.55; and
- observed mean AUC exceeds the 97.5th percentile of the permutation null.

This mechanism criterion is secondary to the practical W4 success rule but is fixed before V6 scoring.

## Additional fixed diagnostics

Report:
- W4 vs B on minority-correct cases;
- strict W4 reversals where weighted score uniquely changes the winning output, separately from tie-break changes;
- pass@2;
- raw candidate plurality;
- oracle-negative cases;
- candidate/model coverage.

## Interpretation

W4 PASS + mechanism PASS:
replicated practical and scientific result across two independently generated Land solver generations.

W4 FAIL + mechanism PASS:
counterfactual D4 behavior replicates as a hypothesis-quality signal, but W4 is not a robust selector.

W4 FAIL + mechanism FAIL:
V27 D4 signal is unstable across solver generations; narrow the mechanism claim.

COVERAGE FAIL:
V6 traces cannot adjudicate replication.
