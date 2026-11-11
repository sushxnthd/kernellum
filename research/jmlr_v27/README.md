# JMLR Project Zero v27 exact preregistered benchmark campaign

This directory is an execution lock for `STANDARD_BENCHMARK_PREREG_V26.md`. It is not an outcome-selection layer.

## Frozen source revisions

- Nash-MTL: `AvivNavon/nash-mtl@cce18403ef5557a6b30f4ba43b896117107d6902`
- FairGrad: `OptMN-Lab/FairGrad@b58bce810e57288f7bf2c4c9effb7133b856739a`

## Primary deterministic methods

`ls`, `mgda`, `cagrad`, `nashmtl`, `fairgrad`.

Aligned-MTL is not present in the pinned source-faithful code path, so the preregistration's conditional Aligned-MTL clause is not activated. PCGrad remains secondary/randomized; IMTL remains an exact-clone singularity diagnostic rather than a forced long-training cell.

## Frozen grid

`manifest.csv` contains 1,350 cells:

- NYUv2: 475 cells (25 coarse + 225 exposed + 225 canonicalized)
- QM9: 875 cells (25 coarse + 425 exposed + 425 canonicalized)

Every exposed clone is the same already-computed loss tensor/computational graph. No examples, labels, heads, model forwards, or dataset splits are duplicated or changed.

## Canonicalization gate

`atomicity_intervention.py` creates the exposed vector first and then collapses the clone family by mean before the multi-task combiner. `test_atomicity_intervention.py` passes all 9 NYUv2 parent/k combinations with canonicalized gradient relative error below 5e-16 in float64.

## Statistical lock

`analyze_preregistered.py` was written before observing standard-benchmark outcomes. It uses paired-by-seed comparisons, paired bootstrap confidence intervals, effect sizes, untouched-task degradation, Delta-m, and canonicalized-null checks. Null and sign-reversed cells are retained.

## Outcome policy

Do not delete failed, null, or sign-reversed cells. Do not retune coarse/refined hyperparameters separately. Do not replace the standard benchmark with a toy/pilot. Any feasibility amendment must be recorded before examining affected outcomes.
