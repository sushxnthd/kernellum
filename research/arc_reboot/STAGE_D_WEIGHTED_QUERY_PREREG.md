# ARC Reboot Stage D — Risk-Weighted Posterior-Predictive Voting

Status: PREREGISTERED AFTER STAGE C PRIMARY FAILURE, BEFORE ANY STAGE D EXECUTION.

## Motivation

Stage B showed that counterfactual behavioral centrality predicts global held-out program quality. Stage C showed that selecting the single most central semantic class does not satisfy the preregistered query-accuracy survival rule against duplicate-invariant semantic-class plurality.

This exposes a distinction between two decisions:

1. **mechanism selection**: choose one program expected to generalize globally;
2. **query prediction**: choose one output for the current query.

For a query, collapsing the version space to one program can discard useful posterior-predictive mass even if that program is globally strong.

## Frozen candidate construction

Use exactly the Stage C candidate construction, seeds, execution-validity rule, semantic deduplication, agnostic probes, canonical class representative, 32 fresh queries per usable family, and pinned ARC-TGI commit.

No mutation operators, family selection rules, or query-generation rules may change.

## Baseline B

Duplicate-invariant semantic-class plurality from Stage C:

- quotient candidates by complete agnostic-probe behavioral signature;
- choose the minimum-AST representative per class, ties by frozen mutation index;
- each class casts exactly one vote for its representative's query grid;
- output the grid with most class votes; ties by canonical serialized grid order.

## Primary method W_all

For each semantic class c, compute the same all-probe class centrality used in Stage C:

C_c = average over frozen agnostic probes of the fraction of valid semantic classes that agree with class c on that probe.

For a query grid prediction y, define

S_all(y) = sum over classes c with h_c(x_q)=y of C_c.

Predict the y with maximum S_all(y). Ties use canonical serialized grid order.

There are no learned parameters and no temperature.

Pass@2 returns the top two distinct query grids by S_all.

## Secondary method W_D4

Repeat the same weighted vote using D4-only centrality, with the exact D4 probe generator and 12-probe cap already fixed in the completed robustness ablation.

W_D4 is secondary. A positive W_D4 result cannot rescue a failed W_all primary.

## Endpoints

Primary:
- family-macro top-1 accuracy of W_all versus B.

Secondary:
- micro top-1;
- pass@2;
- W_all vs the single-class centrality selector D;
- W_D4 vs B;
- disagreement-query accuracy, restricted to queries where >=2 distinct semantic-class outputs are predicted.

Bootstrap 95% confidence intervals resample families, not individual queries.

## Frozen survival rule

The practical weighted method survives only if all are true:

1. Stage B passed.
2. Stage C single-class method failed or tied its primary practical gate.
3. W_all improves family-macro top-1 over B by >= 0.03 absolute.
4. The family-bootstrap 95% CI for W_all-B is not entirely below zero.
5. W_all improves accuracy in at least 3 independent usable families.
6. W_all has positive gain on disagreement queries.

If W_all fails, the practical centrality-weighted prediction method is killed. W_D4 remains a mechanistic/exploratory result only.

## Interpretation discipline

A successful Stage D would support the claim that counterfactual evidence is useful when retained as uncertainty over semantic mechanisms rather than collapsed to one mechanism.

A failed Stage D would support a narrower result: counterfactual centrality predicts global mechanism quality but does not improve query prediction beyond duplicate-invariant semantic plurality on this benchmark construction.
