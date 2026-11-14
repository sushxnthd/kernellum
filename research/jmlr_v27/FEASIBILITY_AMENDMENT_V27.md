# V27 pre-outcome feasibility amendment record

Date: 2026-11-14

## Status

The original `STANDARD_BENCHMARK_PREREG_V26.md` and generated 1,350-cell manifest are preserved unchanged as the historical preregistration. No standard-benchmark outcome cell had completed when this feasibility record was written.

The original full-training grid is computationally infeasible with the available resources. Its 875 QM9 cells at 300 epochs imply 262,500 QM9 epochs. Using the published Nash-MTL appendix runtime of approximately 6.76 min/epoch as an optimistic uniform reference gives about 29,575 accelerator-hours (3.38 sequential accelerator-years) before NYUv2 and overhead.

This document records the feasibility failure before any outcome-bearing amendment. It does **not** silently authorize a smaller outcome grid.

## Infrastructure/source findings

- The pinned FairGrad run scripts create `./save`; direct runtime probes omitted this and therefore failed at checkpoint saving. Creating `./save` is an infrastructure repair matching released execution.
- The pinned QM9 trainer computes target mean/std through `train_dataset.data.y`. PyG warns that this accesses the underlying full InMemoryDataset even when the dataset object is a subset. Source-faithful replication will preserve and disclose this behavior. A train-only normalization arm, if later run, is a separately labeled robustness/correction analysis rather than a replacement hidden inside the primary result.
- FairGrad parser default is alpha=1.0, while the released benchmark run scripts explicitly set alpha=2.0. The frozen protocol uses alpha=2.0 as the released run-script configuration.
- Exposed refinements require the multi-task combiner to be instantiated with represented task count `T+k-1`; coarse/canonicalized arms use `T`.

## Outcome-bearing amendment gate

Before any reduced outcome grid is launched, it must be written here (or in a successor file committed before the run) with:
1. exact retained benchmark cells;
2. exact training horizon;
3. exact seeds and stopping rule;
4. why the selection is outcome-independent;
5. which original acceptance conditions it can and cannot satisfy.

Until that is done, only non-outcome-bearing source, patch, calibration, runtime, and synthetic preflight work is permitted.
