# ShiftGuard — competition snapshot

**Status:** PROMOTE TO FULL INSEF ENTRY

## Real temporal result

Chronological Elec2 protocol:
- 27,549 ordered rows, no temporal shuffling
- first 60% scorer training
- next 20% historical non-key calibration
- final 20% untouched future stream
- 13,197 stored keys
- scorer/preprocessing memory counted in all learned-filter comparisons

### Failure exposed
- Aggregate future static-PLBF FPR was safer than target, demonstrating that raw drift magnitude is not enough.
- A local future block reached **1.432x target FPR**.
- Naive audit-based reallocation overfit independent holdouts at **2.156x** and **1.625x target**.

### Audit-recentered ShiftGuard
With 500 audited non-keys, 500 independent holdout non-keys, and a 95% finite-sample TV certificate:

| Target FPR | Window 1 saving | Window 2 saving | Holdout / target |
|---|---:|---:|---:|
| 1% | 31.6% | 17.8% | 0.634 / 0.960 |
| 0.3% | 25.0% | 14.1% | 0.634 / 0.960 |
| 0.1% | 21.0% | 11.9% | 0.634 / 0.960 |

The robust optimization certificate satisfies the requested FPR throughout the stated TV ambiguity set.

### Fallback result
The sharp 214-query spike leaves only 107 audited negatives after a half/half split. The 95% uncertainty set becomes large enough that the learned design is larger than a classical Bloom filter. ShiftGuard therefore falls back to the classical filter rather than claiming an unsupported saving.

## Reproducibility

- Code: `research/shiftguard/elec2_temporal.py`
- Raw pinned results: `research/shiftguard/results/elec2_temporal_results.json`
- Dataset revision: `vlosing/incrementalLearning@4ee6b377a6710fa352e8fef1bbe3cbe29e7bcc57`
- EMBER2024 remains a planned malware-domain replication and is not used to claim the present temporal result.

## Claim boundary

The certificate is distributional under the finite-sample TV ambiguity model. It is not an adversarial-query security guarantee.
