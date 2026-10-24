# Quintic transfer: incremental mechanism attribution and novelty boundary (2026-10-25)

**Independent accounting audit of already-opened, frozen prospective evidence.** No new holdouts were opened, no solver outputs were regenerated, and the existing PR #119 claim of prospective 23/23 complete certification was not altered. This is a critical decomposition of *where* the reported savings originate, not a new symmetry theorem or a new solver-reliability mechanism.

## Required counterfactual decomposition

The frozen quintic transfer reports the following total work across 23 held-out regimes:

| Route | Work | What it controls |
|---|---:|---|
| Orbit-batched certified starts | 5,504 | Combined structural certification and orbit batching |
| Unbatched certified starts | 6,240 | **Same structural starts, same solver behavior; no orbit batching** |
| Strongest complete simple control, tensor corners | 9,320 | Strong simple reference without structural starts |

All 23 regimes have complete coverage for these three routes in the original full-budget evaluation. Batched and unbatched routes have identical solver evaluations, starts and full/capped outcomes; only certificate-construction work changes. The independent script verifies these properties from the original raw per-regime rows, not only the published summary.

The precise, non-interchangeable quantities are:

- **40.9442%** = `(9320-5504)/9320 = 477/1165`: combined end-to-end improvement versus tensor corners.
- **11.7949%** = `(6240-5504)/6240 = 23/195`: *incremental* savings attributable to orbit batching over the certified-unbatched ablation.
- **33.0472%** = `(9320-6240)/9320 = 77/233`: improvement from certified structural starts versus tensor corners **without** batching.
- Of 3,816 total absolute work units saved versus tensor corners, **736 units (19.2872%)** come from batching and **3,080 (80.7128%)** are already achieved by the unbatched structural route.

The 40.9442% number remains a correct *combined-system* comparison, but **must not be described as the benefit of orbit batching alone**. Any headline attributing all savings to the new routing optimization would fail the causal ablation.

## Independent audit and falsification

`python3 scripts/audit_quintic_incremental_attribution.py --self-test` validates a fabricated fixture and verifies that a corrupted summary fails closed. `python3 scripts/audit_quintic_incremental_attribution.py` checks the committed 23-regime result without rerunning a solver: complete control presence, every per-row total-work identity, summary reconstruction, exact published reduction, paired start/outcome equivalence, equal solver evaluations and positive savings ordering. The targeted workflow is `.github/workflows/quintic-incremental-attribution.yml`.

**Evidence tier:** independent accounting of existing prospective results. This is not new prospective transfer, and it does not increase confidence in the untested family-level generalization beyond the existing evidence.

## Scientific decision and system consequence

Preserve the existing prospective result and honest bounds, but require future discovery/evaluation reports to distinguish `combined_system_vs_best_complete_control` from `incremental_mechanism_vs_nearest_ablation`. The selector's safety benefit is **not** an incremental reduction in catastrophic tails relative to unbatched certification: those outcomes are identical. The incremental contribution is reduced certificate construction work. Symmetry-orbit batching, proof-carrying start selection and exact equivariance are classical techniques; this experiment does not establish fundamentally new theory.

For a stronger Kernellum result, pursue a genuinely pre-outcome diagnostic of *solver/model-selection instability* that improves catastrophic tails **against the strongest already-certified alternative**, with held-out cross-family transfer, independent proof checks and a real selector integration. Kill diagnostics that only restate existing symmetry, merely predict their own certificate success, or fail to beat the unbatched certified control on the claimed outcome. This audit is not a replacement for PR #119 and does not modify its raw evidence.
