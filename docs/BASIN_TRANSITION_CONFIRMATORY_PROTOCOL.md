# Frozen confirmatory protocol: basin-transition continuation selector

**Frozen before any outcome evaluation. The routing rule and every numeric threshold are unchanged from the 16-path prospective experiment.**

## Active kernel

Do repeated early model/basin transitions along controlled response-continuation paths predict harmful solver dependence across genuinely new truth families, and does routing only those cases to the existing globalized fit suppress catastrophic tails without degrading ordinary interpolation?

## Prior evidence and frontier

The first frozen prospective cohort routed 4/16 cases, improved 3/4 routed cases, reduced far-shell geometric NMSE by 40.9%, and reduced one far-shell catastrophe to zero. It failed the predeclared catastrophe-halving gate because the cohort contained only one candidate catastrophe. Three routed wins came from `warped_laplace`, while the only routed loss came from `oscillatory_cauchy`; family confounding is therefore the strongest live alternative explanation.

Continuation, homotopy, bifurcation diagnostics, and stability selection are established. This experiment tests a narrower system claim: whether a fixed, truth-blind continuation signature transfers across unseen generative families and supports a useful robust selector.

## Untouched confirmatory cohort

Twenty-four deterministic paths, disjoint from every prior selector cohort:

- truth families: `rational_mixture`, `anisotropic_bump`, and `warped_cauchy`;
- dimensions: 5 and 9;
- seeds: 9103 and 9109;
- noise laws: `symmetric_t` and `leverage_spikes`.

The families deliberately alter tail shape, local bump structure, and oscillatory warping. The cohort becomes opened after the first workflow execution. No threshold, family, seed, loss, or gate may be changed afterward.

## Frozen intervention and pre-outcome diagnostic

For each path:

1. fit the existing candidate, globalized, independent, and naive minimum-CV controls;
2. generate eight deterministic zero-mean unit-RMS response directions;
3. refit the candidate solver bank at response amplitudes alpha in {0.00, 0.08, 0.16, 0.24, 0.32} training-response SD;
4. mark the first transition when selected sign/family changes from alpha=0 or normalized request-prediction RMS exceeds 0.35.

Before request truth is accessed, compute:

- early-switch fraction E: directions transitioning by alpha <= 0.16;
- median first-transition amplitude A, with 0.40 assigned to no transition;
- globalized/candidate request-prediction distance G;
- globalized/candidate full-training residual ratio R.

**Unchanged route:** select the globalized fit iff E >= 0.50, A <= 0.16, G > 0.25, and R <= 1.15. Otherwise retain the candidate. The frozen scalar margin remains min(E-0.50, 0.16-A, G-0.25, 1.15-R).

## Mechanism-derived unseen prediction

If the signal is basin-transition structure rather than family identity, at least four routes should fire across at least two new truth families. Routed cases should improve far-shell truth loss at least 75% of the time in aggregate, and no family with at least two routed cases should have precision below 50%.

## Controls and objective

Controls are the incumbent candidate, independent solver, unconditional globalized fit, naive minimum-CV selector, always-globalized policy, and the frozen continuation-routed selector. Domains are inside, near shell, and far shell. Primary loss is geometric NMSE; a catastrophe is NMSE > 5.

All gates must pass:

1. 24/24 paths complete;
2. at least four routes fire;
3. routed cases span at least two truth families;
4. no domain gains catastrophes;
5. catastrophes are halved in at least one domain containing at least two candidate catastrophes;
6. inside geometric-NMSE ratio is <= 1.05;
7. far-shell geometric-NMSE ratio is <= 0.90;
8. aggregate routed far-shell precision is >= 0.75;
9. every family with at least two routes has routed precision >= 0.50;
10. duplicate output is byte-identical and the independent standard-library audit passes.

## Cheapest decisive falsification / kill condition

Kill without tuning if any gate fails. In particular, confinement to one family, family-stratified precision failure, excess catastrophes, or failure to improve far-shell loss falsifies transfer of this fixed diagnostic. A failure does not falsify continuation methods generally.

## Project consequence threshold

Pass: promote the selector to a Kernellum discovery/evaluation guardrail and begin external-data validation. Fail: retire this fixed mechanism, preserve the exact evidence, and reformulate around transition topology rather than threshold tuning.
