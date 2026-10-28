# ARC Reboot — Land V6 Independent Replication of Counterfactual-Weighted Voting

Status: PREREGISTERED AFTER OBSERVING THE V7 SECONDARY W RESULT, BEFORE INGESTING OR EVALUATING V6 CANDIDATE-LEVEL OUTPUTS.

## Discovery being replicated

On the independent Land V7 public run, the preregistered primary single-central-class selector D failed. However, the preregistered secondary weighted predictive vote W_all achieved:

- B_cls: 48.45% top-1
- W_all: 54.64% top-1
- W_all - B_cls: +6.19 pp
- 6 case wins, 0 case losses
- task-bootstrap 95% CI for W-B: approximately [+2.6, +14.3] pp
- oracle-positive gain: +8.57 pp
- minority-correct gain: +16.67 pp

This V7 result is discovery evidence only for W.

## Independent replication source

Johan Land V6 public ARC-AGI-2 run:
- notebook: `johanland/johan-land-solver-v6-public`
- cited public scriptVersionId: `286318109`
- reported solver performance: 70.7% on ARC-AGI-2 public evaluation
- candidate generation/search predates V7 and is treated as an independent released run.

Use the exact historical notebook output corresponding to scriptVersionId 286318109. If Kaggle version mapping is required, mapping must be established before candidate extraction. Do not substitute another V6 version after inspecting candidate correctness.

## Candidate extraction and execution

Reuse the V7 frozen pipeline without methodological changes:

1. codegen candidates only;
2. complete executable `solver`;
3. Land training verification PASS, followed by independent exact re-verification on every ARC demonstration;
4. byte/source deduplication before execution;
5. static safety gate;
6. isolated execution with no network, read-only runtime, resource limits, and per-call timeout;
7. semantic classes defined by the complete 24 mixed-probe behavior signature;
8. canonical representative = shortest normalized source, tie by source SHA.

Released correctness, judge score, vote count, model identity, and final selected answer are unavailable to the selector.

## Frozen probes

Primary mixed probes:
- D4 rotations/reflections;
- nonzero color permutations preserving zero;
- cyclic row/column rolls;
- deterministic seed 20261028;
- cap 24 unique probes.

Secondary D4-only:
- cap 12.

## Primary replication selector W_all

For every semantic class c, compute counterfactual centrality

C(c) = mean across valid probes of the fraction of valid semantic classes agreeing with c on that probe.

For each actual test-output grid y, score

S(y) = sum over semantic classes c predicting y of C(c).

Predict the y with maximum S(y). Ties by canonical serialized grid order.

## Baseline B_cls

Duplicate-invariant semantic-class plurality:
- one vote per semantic class for its canonical representative's test prediction;
- ties by canonical serialized grid order.

## Secondary selectors

- D: single highest-centrality class;
- W_D4: D4-centrality weighted predictive vote;
- D4: single D4-central class;
- Raw: duplicate-sensitive raw candidate plurality.

None can rescue a failed W_all primary.

## Usable case

A task/test case is usable when:
- >=3 independently reverified executable source candidates;
- >=3 primary semantic classes;
- >=2 distinct valid semantic-class predictions on the actual test input.

Oracle-negative cases remain in overall accuracy.

## Primary endpoints

- top-1 accuracy W_all versus B_cls;
- task-ID bootstrap 95% CI for W-B;
- task-level direction counts.

## Frozen survival rule

The V6 replication passes only if all hold:

1. >=30 usable cases;
2. >=20 distinct ARC task IDs;
3. W_all - B_cls >= +3 percentage points;
4. task-bootstrap 95% CI is not entirely below zero;
5. W_all improves at least 5 distinct task IDs;
6. W_all is non-inferior to B_cls on oracle-positive cases;
7. W_all yields positive gain on minority-correct cases.

A coverage failure is INCONCLUSIVE_COVERAGE.
Adequate coverage plus failure of any effect gate is REPLICATION_FAIL.

## Mechanism endpoints

Report, without affecting the primary verdict:
- case-macro AUC of class centrality for exact test correctness;
- median case AUC;
- correct-vs-incorrect class centrality means;
- W gain stratified by semantic-class count;
- W gain on minority-correct cases.

## Cross-run interpretation

V6 PASS:
counterfactual behavior provides a reproducible label-free weighting signal for heterogeneous LLM-generated ARC hypotheses.

V6 FAIL with positive AUC:
centrality tracks hypothesis quality but V7's query-level W gain is run-specific.

V6 FAIL with no positive AUC:
the real-LLM V7 discovery is substantially weakened and should not be promoted.

No V6 methodological changes are allowed after candidate-level correctness is inspected.
