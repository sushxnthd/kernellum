# Validation-aware stacking execution blocker

## Classification

Infrastructure blocker preserved before any requested-domain truth metric was emitted. This is **not** a scientific pass or failure.

## Frozen scientific state

The protocol was committed at `748e7a43bdb7a28c2370c70607d67de3e79dc900` before execution. The implementation was committed at `b9ce787b3a23ae3b1e21a9a0b92a13586d64856b`. A follow-up commit, `c232c7a1272d5e70e09ed8209d9205d6ebfff944`, parallelized independent paths without changing the cohort, fits, folds, simplex grid, prediction, controls, metrics, or gates.

## Failure evidence

Two local attempts were made.

1. The initial single-process runner completed one path after approximately two minutes and printed only its outcome-blind pre-truth decision:
   - key: `damped_chirp / d=6 / seed=12011 / symmetric_t`
   - weights: `[0.5, 0.0, 0.5]`
   - request disagreement: `2.1904386169286214`
   - predicted active: `true`
   The process was interrupted solely to apply path-level parallelism. No requested-domain truth score was computed or written.
2. The six-worker runner remained CPU-active across all workers but did not finish within the workflow's declared 50-minute wall-clock ceiling. It was interrupted with SIGINT (exit 130). Because the runner emits artifacts atomically after every path returns, neither the decisions file nor the result file exists.

The GitHub App commit did not create a hosted Actions run, so there is no remote workflow result to substitute for the bounded local execution.

## Integrity consequence

The truth-domain prospective cohort remains unopened: no inside, near-shell, or far-shell metric was emitted or inspected. The single printed row is a pre-outcome mechanism prediction and may remain part of the frozen decision record.

No threshold, family, seed, weight constraint, solver tolerance, fold, metric, or gate was changed.

## Exact blocker

The current runner assigns complete paths to six long-lived workers. High-dimensional exact-LOO nonlinear fits make the slowest worker exceed the 50-minute integration budget. This is an execution-granularity failure, not evidence for or against validation-aware stacking.

## Frozen remediation

The next run may change infrastructure only:

- expose one path per CLI invocation;
- execute the 24 frozen keys as independent matrix jobs or bounded local shards;
- write one decision-and-score shard per key;
- merge shards in the original lexicographic key order;
- verify every shard's frozen code commit and cohort manifest before aggregation.

The scientific protocol and all gates remain unchanged. Any truth-bearing shard that completes must be preserved even if another shard fails.
