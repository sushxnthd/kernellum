# Sign-anchored dual-solver arbitration on shifted conditions

Status: **FROZEN BEFORE OUTCOMES**

Classification: PROSPECTIVE DISCRIMINATION / MECHANISM / SYSTEM CAPABILITY.

## Active kernel

- **Question:** when independently implemented nonlinear model-selection stacks
  choose opposite response signs, does retaining the candidate sign prevent
  catastrophic extrapolation better than blindly choosing lower exact-LOO CV?
- **Frontier:** on 120 opened signed-Gaussian paths, a post-hoc sign anchor
  selected the better extrapolator on all four solver disagreements and reduced
  far-shell geometric NMSE 29.55%, but that cohort generated the rule.
- **Objective:** prospectively compare six fixed policies on shifted function,
  dimension, seed, and noise regimes.
- **Strongest alternative:** the earlier effect was a four-case artifact; sign
  disagreement is not intrinsically dangerous and globalization dominates.
- **Cheapest decisive falsification:** enumerate the frozen shifted factorial,
  materialize solver decisions before test metrics, then open the test outcomes
  once.
- **Publishable success condition:** sign disagreement prospectively marks a
  regime where naive cross-basin CV arbitration creates extrapolation tails,
  while anchoring removes them without ordinary-regime regression and remains
  close to full globalization.
- **Project-relevance threshold:** every frozen gate below passes.
- **Kill condition:** fewer than two sign disagreements, any excess catastrophe
  versus the candidate, or failure of conditional/aggregate performance gates.

## Untouched shifted factorial

- response shapes: skewed Gaussian peak and Student-t peak, neither used by the
  fitted exponential bank;
- dimensions: 3 and 5 (the opened cohort used 2 and 4);
- seeds: 3101 and 3102; the former generates positive responses and the latter
  negative responses;
- noise: heteroscedastic Gaussian and standardized Student-t(3), both at 0.35
  times the clean-response standard deviation;
- 128 candidate points, deterministic 20-point maximin design;
- 256 test points per inside, near-shell, and far-shell domain;
- all 16 factorial paths; no path may be dropped.

The model bank remains the misspecified signed exponential-affine and
exponential-concave families.

## Frozen controls

1. candidate analytic-Jacobian solver;
2. clean-room independent numerical solver;
3. naive lower exact-LOO-CV arbitration across the two winners;
4. sign anchor: candidate on sign disagreement, otherwise lower CV;
5. abstention on sign disagreement, otherwise lower CV;
6. deterministic globalized candidate bank using three fold-only starts per
   sign/family and selecting the lowest training objective on every full fit and
   every LOO refit.

Decisions are hashed before test metrics are evaluated.

## Frozen gates

PASS requires:

1. all 16 paths complete with finite predictions;
2. at least two candidate/independent sign disagreements;
3. on sign-disagreement paths, the anchor has lower far-shell error than naive
   lower-CV arbitration in at least 75% of cases;
4. anchor catastrophic counts (`log NMSE > 5`) do not exceed either candidate
   or naive arbitration in any domain;
5. anchor inside-domain geometric NMSE is no more than 1.05 times candidate;
6. anchor far-shell geometric NMSE is no more than 0.90 times naive arbitration;
7. anchor far-shell geometric NMSE is no more than 1.10 times globalization;
8. globalization has no more catastrophic cases than candidate in any domain;
9. an independent aggregation audit exactly reproduces all decisions, metrics,
   gates, and the canonical payload digest.

No threshold or policy may be changed after outcomes. A failure kills the
current sign-anchor rule; an inconclusive disagreement count also prevents a
positive claim.

## Consequence boundary

A pass authorizes a Kernellum selection certificate: opposite-sign solver
choices must block naive CV arbitration and trigger anchoring or globalization.
A fail removes sign anchoring from the robust-selection roadmap and makes full
globalization the default. This study does not establish historical novelty or
performance outside the frozen synthetic regimes.
