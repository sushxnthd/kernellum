# V27 pre-outcome feasibility amendment

Date: 2026-11-14

## Historical preregistration

`STANDARD_BENCHMARK_PREREG_V26.md` and the generated 1,350-cell manifest remain preserved unchanged as the historical preregistration. No completed standard-benchmark outcome cell existed when this amendment was frozen.

The original full-training grid is computationally infeasible with the available resources. Its 875 QM9 cells at 300 epochs imply 262,500 QM9 epochs. Using the published Nash-MTL appendix runtime of approximately 6.76 min/epoch as an optimistic uniform reference gives about 29,575 accelerator-hours (3.38 sequential accelerator-years) before NYUv2 and overhead.

This is a **pre-outcome feasibility amendment**, not an outcome-driven reduction.

## Unchanged scientific intervention

For every exposed refinement, only the already-computed semantic loss tensor is represented k times. Data, targets, heads, forward graph, semantic losses, initialization, optimizer, scheduler, dataset split, and evaluation remain unchanged. The combiner is instantiated at represented task count T+k-1. Coarse and canonicalized arms use T semantic tasks.

## Tier A — all-condition standard-benchmark update census

This tier preserves the breadth of the original task/multiplicity/method grid without requiring a full training trajectory per representation.

### NYUv2 source trajectories
- MTAN, 200 epochs, batch 2, Adam lr 1e-4, released augmentation and scheduler.
- Five seeds: 0,1,2,3,4.
- Source trajectory: coarse equal weighting.
- Fixed audit epochs: 0,49,99,149,199.
- At each audit epoch, retain the first actual training minibatch and its three already-computed semantic losses/shared gradients.

### QM9 source trajectories
- Released 11-target GNN, 300 epochs, batch 120, Adam lr 1e-3, released scheduler and target-standardization path.
- Five seeds: 0,1,2,3,4.
- Source trajectory: the coarse Nash-MTL runs already required by Tier B; no duplicate source trajectory is launched.
- Fixed audit epochs: 0,74,149,224,299.
- At each audit epoch, retain the first actual training minibatch and its 11 semantic losses/shared gradients.

### Offline combiner census
On every retained gradient system, evaluate source-faithful deterministic combiners:
- equal weighting;
- released MGDA (including its task-count rescaling) for implementation calibration;
- canonical MGDA (same pinned min-norm solver, simplex-scaled control);
- CAGrad;
- Nash-MTL finite released solver;
- FairGrad alpha=2 (released run-script configuration).

Apply the full original representation sweep:
- NYUv2: each of 3 semantic tasks, k in {2,4,8};
- QM9: k=4 for all 11 targets plus k in {2,8} for preregistered target IDs {0,2,12}.

For each system record coarse, exposed and canonicalized update vectors, angle/cosine, norm ratio, clone-family coefficient/response statistics, finite-solver status, and theory-predicted response. Preserve every null, sign reversal, singularity and solver failure.

Tier A tests the full theory-order, geometry-law and canonicalized-null claims on both standard benchmarks. It is not labeled as downstream training evidence.

## Tier B — full-training downstream standard-benchmark cells

The full-training subset is chosen **before outcomes** to span predicted response classes and to avoid task cherry-picking.

### NYUv2 downstream grid
Retain original 200-epoch protocol and five paired seeds.

Methods:
- equal weighting (linear multiplicity response);
- canonical MGDA (invariant mathematical control; explicitly not the released task-count-rescaled wrapper);
- Nash-MTL (bargaining/power-equilibrium response).

For each method:
1. coarse: one run per seed;
2. exposed: k=4, refine each of segmentation/depth/normals in turn, one run per seed;
3. canonicalized: parent segmentation, k=4, one run per seed.

This is 25 runs per method, 75 NYUv2 full-training runs total. k={2,8} dose response remains tested in Tier A rather than full downstream trajectories.

### QM9 downstream grid
Retain original 300-epoch protocol and five paired seeds.

Method:
- Nash-MTL.

Target and multiplicity:
- first target in the frozen released target list, target ID 0;
- k=4.

Arms:
1. coarse;
2. exposed;
3. canonicalized.

Five paired seeds produce 15 QM9 full-training runs total. Target ID 0 is selected by frozen list order before outcomes, not by observed effect size. All 11 targets still enter the Tier A update census.

## Locked analysis

For Tier B retain the original paired-by-seed analysis:
- all source metrics and Delta-m;
- untouched-task/target effects;
- paired seed-level differences;
- mean/median and 95% paired bootstrap intervals;
- parameter distance;
- canonicalized-minus-coarse null gate;
- method ranking/reversal analysis where multiple methods are present.

No seed removal except a preregistered infrastructure failure. No per-arm retuning.

## Source-faithfulness repairs and disclosures

- Create `./save` before training, matching the released run scripts.
- The pinned QM9 trainer computes mean/std through `train_dataset.data.y`, which accesses underlying full PyG storage. Primary source-faithful runs preserve and disclose this released behavior. A train-only normalization sensitivity run, if later added, is explicitly secondary.
- FairGrad alpha=2 is the released run-script setting, not the parser default.
- Exposed arms instantiate the combiner at T+k-1 represented tasks.
- Released FairGrad MGDA multiplies the simplex solution by declared n_tasks; it is therefore separately audited as an implementation-sensitive rule. Tier B's "canonical MGDA" divides this released weighted loss by represented n_tasks, leaving the pinned min-norm solver unchanged and restoring the mathematical simplex combination.

## Compute planning boundary

Published/reference epoch times imply roughly 1,190 accelerator-hours for Tier B using the available NYUv2/QM9 runtime references, before overhead. This is a planning estimate, not a measured runtime on the eventual GPU. It may fit only through low-cost/spot GPU execution and checkpointing. No paid resource may be created until separately authorized.

## Amended empirical gate

The standard-benchmark empirical gate passes only if:
1. Tier A is complete for all frozen audit systems and canonicalized nulls pass;
2. all 75 NYUv2 Tier B runs complete or fail under a logged infrastructure criterion;
3. all 15 QM9 Tier B runs complete or fail under a logged infrastructure criterion;
4. at least one downstream benchmark shows a practically visible representation effect or ranking consequence in the theory-predicted direction;
5. the second benchmark reproduces the mechanism at update level, with its downstream result (including a null) reported without filtering;
6. all deviations from exact solver theory and all null/negative results remain visible.

If these conditions fail, the manuscript must narrow or pivot; it may not be called submission-ready.
