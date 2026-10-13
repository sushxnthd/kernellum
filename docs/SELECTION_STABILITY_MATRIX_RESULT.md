# Selection-stability matrix result: predictive routing killed

**Classification:** OPENED DEVELOPMENT / DECISIVE FALSIFICATION  
**Scientific gate:** FAIL  
**Breakthrough gate:** INCONCLUSIVE

## Smallest supported claim

On the frozen 60-path opened-development cohort, a preregistered factorized matrix of four cheap pre-selection observables did not reliably identify the four known solver-dependent exact-LOO/model-selection failures. It improved on the earlier scalar diagnostic, but it missed three failures in the top ten and therefore cannot support cheap predictive routing. This is not an impossibility result for every future diagnostic.

## Frozen result

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| Pairwise AUROC | >= 0.90 | 0.821429 | FAIL |
| Known failures in top ten | 4/4 | 1/4 | FAIL |
| False-positive rate at full recall | <= 0.25 | 0.25 | PASS |
| Overall | 3/3 | 1/3 | **FAIL** |

The canonical result digest is `d6b9b2c77538aa40927071cc716b1957532fe822e3e60988a9c6ca99e0a23c3c`.

### Ablations

Each row omits the named component.

| Omitted component | AUROC | Top-ten recall |
|---|---:|---:|
| Selected-model CV burden | 0.629464 | 0.50 |
| Signed pair asymmetry | 0.714286 | 0.50 |
| Within-objective dispersion | 0.848214 | 0.25 |
| Within-prediction dispersion | 0.821429 | 0.50 |

## SCIENCE ledger

- **Hypothesis:** heterogeneous solver-dependent selection failures are prospectively separable by a factorized matrix of cheap disagreement and fold-burden observables.
- **Mechanism:** different failure modes should activate distinct axes, allowing their union to rank all catastrophic paths ahead of ordinary paths.
- **Preregistered prediction:** AUROC at least 0.90, all four positives in the top ten, and false-positive rate at full recall at most 0.25.
- **Observed result:** AUROC 0.821429; one of four positives in the top ten; false-positive rate 0.25. Overall gate FAIL.
- **Residual/surprise:** the matrix contains real partial signal, especially from fold burden and pair asymmetry, but the union score does not concentrate the heterogeneous failures. Within-objective dispersion is weakly harmful in this cohort.
- **Assumption falsified:** four inexpensive pre-selection observables are sufficient for dependable failure routing on this opened family.
- **Competing explanation strengthened:** solver dependence is determined by information available only after globalization or explicit competing-basin search, rather than by cheap local summaries.
- **Uncertainty:** only four positives and one opened synthetic family; the result kills this frozen routing kernel, not all possible diagnostics.
- **Provenance:** GitHub Actions run 38427324974; artifact 11829950546; immutable input hashes are stored in the result JSON. Two preceding failed workflows are preserved because the trace did not retain the originally requested runner-up margin.

## CONSEQUENCE ledger

- Do not ship either the scalar or the frozen factorized diagnostic as a gate that decides when exact-LOO/model selection deserves robust solving.
- Replace predictive routing with a **globalized/certified selection kernel**: deterministic multi-start on every fold and full fit, plus a certificate recording best/runner-up objective separation and restart agreement.
- The cheapest next discriminating test is whether this control eliminates all four opened-development disagreements without materially degrading ordinary-path error or compute, followed only then by a frozen shifted-condition evaluation.
- Project-direction threshold is met: Kernellum's system design changes from predicting rare instability to making selection robust and auditable by construction.

## Reproduction

```bash
python scripts/audit_selection_stability_matrix.py \
  results/selection_stability_matrix_development.json
```

The independent audit recomputes pairwise AUROC, top-ten recall, the full-recall operating point, the exact gate vector, and the canonical SHA-256 without importing the experiment runner.
