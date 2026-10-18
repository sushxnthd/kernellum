# Consensus-medoid prospective result: mechanism non-discriminating

**Classification:** PROSPECTIVE UNSEEN / DECISIVE FALSIFICATION  
**Scientific gate:** FAIL  
**Breakthrough gate:** FAIL

## Smallest supported claim

The frozen three-solver consensus-medoid selector made **zero overrides on 16/16 unseen paths**. It therefore left every candidate prediction unchanged, reduced no catastrophic tails, and failed the prospective mechanism gate.

This is not evidence that ensemble consensus is generally useless. It falsifies the specific assumption that the legacy candidate, the independent implementation, and the three-start globalizer provide three sufficiently diverse basin observations for a two-against-one selector.

## Frozen result

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| Complete | 16/16 | 16/16 | PASS |
| Overrides | >=2 | **0** | FAIL |
| No excess catastrophes | all domains | yes | PASS (vacuous) |
| Halve catastrophes in one domain | yes | **no** | FAIL |
| Inside NMSE / candidate | <=1.05 | 1.000 | PASS (identity) |
| Far NMSE / candidate | <=0.90 | **1.000** | FAIL |

Far-shell catastrophic counts were candidate 5, globalized 5, independent 6, naive minimum-CV 4, and frozen selector 5. Far-shell geometric NMSE was candidate 10.528840, globalized 10.528806, independent 128812.34, naive minimum-CV 7.471378, and selector 10.528840.

The independent standard-library audit passed **103/103** checks. Two full executions were byte-identical.

## Why the mechanism failed

The supposed third vote was not independent enough. Candidate and globalized predictions were identical or numerically indistinguishable on most paths. Their edge was therefore commonly the closest admissible edge, preventing the frozen I/G-only override rule from firing.

Two adversarial observations sharpen the boundary:

1. On `oscillatory_cauchy / d=6 / seed=5207 / asymmetric_contamination`, the independent solver was materially better in all three domains, but candidate and globalized were identical. The selector preserved the worse candidate because the two implementations did not form the expected coalition.
2. On `tilted_matern / d=6 / seed=5201 / variance_ramp`, the independent solver was a huge far-shell outlier while candidate and globalized agreed. The selector correctly preserved the candidate.

Thus pairwise prediction geometry contains directional information, but solver identity alone does not determine which coalition is trustworthy. The same candidate/globalized agreement can accompany both a correct rejection of an independent outlier and a missed independent improvement.

## SCIENCE ledger

- **FALSIFIED:** three nominal solver implementations supply enough independent basin diversity for the frozen two-against-one mechanism.
- **FALSIFIED:** an I/G-only consensus edge will prospectively trigger often enough to reduce catastrophic tails.
- **KNOWN:** the rule is fail-safe on this cohort only because it never acted; safety and ordinary noninferiority are vacuous.
- **ANOMALOUS:** naive minimum-CV had fewer far catastrophes (4 versus 5) and 0.710x far geometric NMSE, yet prior work contains a near-tie CV catastrophe. Aggregate improvement does not rehabilitate unguarded CV selection.
- **MECHANISM BOUNDARY:** consensus is informative only when ensemble members are genuinely interventionally diverse; re-running the same objective/start family is not an independent vote.
- **LIMITATION:** 16 deterministic synthetic paths across two unseen families, two dimensions, two seeds, and two noise laws; no external dataset.

## CONSEQUENCE ledger

- Do not ship the consensus-medoid selector.
- Do not count the current three-start globalizer as an independent ensemble member.
- Kill this kernel immediately; do not tune envelope thresholds on these opened outcomes.
- Reformulate the positive-mechanism search around **controlled perturbation diversity**: resampling/jittered training sets or explicitly different objectives must create prospective, measurable basin occupancy. The next diagnostic must predict both when disagreement matters and which intervention is stable, then demonstrate tail reduction against candidate, naive CV, globalization, and abstention controls.

## Reproducibility

- Frozen protocol commit: `3152c98dd1a0f299705fc7efee495189dbfdc913`
- Raw-result commit: `93965eda7b11b904bd403b65385fcd403d3c620d`
- Result canonical SHA-256: `12cf4d1fb3e15bcda09286300a27ee3ad4e25b87990affe403c7d3eb89d91f9b`
- Audit canonical SHA-256: `1432f29c2d466fc8c155740925f1eac03c6d3160a8af62f3d6dade957c911b4d`
- Decision file SHA-256: `d4ece31a0e791cd28f5843c3cc5079217b5991c6a6955825443a632a9f26cd81`
- Workflow run: https://github.com/sushxnthd/kernellum/actions/runs/39097101079

## Claim boundary

This is a prospective falsification of one fixed ensemble mechanism. It is not an impossibility theorem for consensus, perturbation stability, or robust solver selection, and no novelty claim is made.
