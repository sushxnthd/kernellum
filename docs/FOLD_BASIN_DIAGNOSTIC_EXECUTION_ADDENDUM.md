# Fold-basin diagnostic execution addendum

The frozen single-process runner completed six label-blind path scores but was interrupted before producing any result because one path required several minutes. No disagreement labels were loaded and no aggregate metric was observed.

Only orchestration changes: the unchanged frozen `score_path` function is executed in deterministic path batches across six processes. All 60 scores are sorted and written to a label-free intermediate file before the frozen labels are loaded. Metric definitions, gates, starts, optimizer limits, population, and kill conditions are unchanged. A sequential independent audit will recompute the ten highest-ranked paths and all four positives after the result.
