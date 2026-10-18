# Support-distance abstention: frozen opened-cohort development protocol

**Frozen:** 16 October 2026  
**Classification:** opened-cohort mechanism discrimination  
**Active kernel:** support-aware abstention or acquisition after optimizer rescue failed

## Precise question

Can a truth-blind geometric support score, computed from training inputs and the
actual requested input batch, identify domain/path cells in which the frozen
single-start exact-LOO winner has catastrophic error, while retaining useful
coverage and outperforming coarse extrapolation controls?

This is a development test on the permanently opened 16-path shifted cohort.
It cannot confirm generalization, but it can kill an unpromising successor
before a new holdout is spent.

## Frozen unit and label barrier

The unit is one `(path, request_domain)` cell: 16 paths crossed with `inside`,
`near_shell`, and `far_shell`, for 48 cells. The evaluator must first write and
hash all truth-blind scores. Only then may it join the already archived
single-start log-NMSE values from the robust-control artifact. A cell is
catastrophic iff archived `single` log-NMSE is greater than 5, exactly matching
the preceding study.

## Candidate score

For training inputs `X` and requested batch `Z`, let

```
r_train = median_i min_{j != i} ||X_i - X_j||_2
d_z     = min_i ||Z_z - X_i||_2 / max(r_train, 1e-12)
support_distance = quantile_0.95({d_z : z in Z})
```

Higher means less supported. No response, fitted model, CV score, prediction,
or requested truth may enter the score.

## Matched controls

1. `shell_radius`: 95th percentile Euclidean distance of `Z` from the training
   centroid, divided by the median training radius;
2. `coordinate_excursion`: 95th percentile distance outside the axis-aligned
   training bounding box, divided by `r_train`;
3. `domain_order`: the coarse prespecified order inside < near < far, with ties
   broken by the canonical path key. This control asks whether the candidate is
   more than a relabeling of the benchmark's shell names;
4. deterministic random-ranking control from SHA-256 of the canonical cell key.

All controls use the same rejection budget. The canonical path ordering is
shape, dimension, seed, noise, then domain in the order above.

## Exact objective and gates

Reject the 16 highest-risk cells (fixed 2/3 coverage). The candidate advances
only if every gate holds:

1. exactly 48 scores are produced and hashed before label join;
2. AUROC for catastrophe is at least 0.80;
3. at least 8 of the 11 archived catastrophic cells are rejected;
4. at least 25 of 37 non-catastrophic cells remain accepted;
5. at least 12 of 16 inside-domain cells remain accepted;
6. candidate rejects at least two more catastrophes than deterministic random;
7. candidate rejects at least one more catastrophe than both `domain_order` and
   `shell_radius` at the same budget;
8. a separately implemented audit reproduces scores, hash, rankings, labels,
   counts, AUROCs, and gates exactly.

The count of 11 positives is public from the archived result and fixes the
denominators; no score or threshold was selected from their identities.

## Strongest alternative explanation

Catastrophes may be caused by model-family misspecification or solver/model
choice in well-supported regions. Any apparent support signal may merely encode
the benchmark's inside/near/far construction. Gates 5 and 7 make that
explanation decisive: a score that only refuses all far-shell work does not
advance.

## Publishable success and project relevance

This opened test cannot itself be publishable success. A pass licenses exactly
one prospectively frozen test on new functions, support geometries, dimensions,
and noise families, with conformal/support-distance and model-disagreement
controls. Prospective success must preserve the same fixed-coverage tail gate
and drive a Kernellum runtime action: return, abstain, or acquire a support
point with a machine-readable receipt.

## Kill condition

Failure of any gate kills this fixed nearest-support mechanism. Do not sweep
quantiles, rejection budgets, metrics, or tie breakers on the opened cohort.
The next kernel must combine input support with model-class disagreement or use
explicit acquisition; it may not rename the failed score.

## Ledgers

### SCIENCE

- **KNOWN:** additional starts, objective minimization, median ensembling, and
  training-prediction stability did not remove catastrophic tails.
- **QUESTION:** are those tails prospectively localized by requested-input
  support rather than optimizer diagnostics?
- **ALTERNATIVE:** shell identity or model misspecification explains all signal.

### CONSEQUENCE

- **PASS:** implement an experimental support receipt and freeze one new
  prospective cohort.
- **FAIL:** do not ship nearest-support abstention; require model-disagreement
  or acquisition evidence before exposing a safety action.

