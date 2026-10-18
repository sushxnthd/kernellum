# Three-solver consensus-medoid selector: frozen prospective protocol

**Classification:** positive-mechanism search; prospective synthetic evaluation  
**Frozen before outcome generation:** 2026-10-18  
**Source commit:** `8616652b12e308daaeb084b3cb44bac188c4286b`

## Active kernel

- **Question:** Can agreement geometry among three independently constructed nonlinear solvers identify and suppress catastrophic solver/model-selection tails without degrading ordinary predictions?
- **Frontier:** cheap scalar/factorized diagnostics failed on opened data; three-start globalization alone failed prospectively; a two-solver envelope had useful coverage but no harmful switches in its untouched cohort.
- **Mechanism:** a catastrophic basin is often a prediction outlier. When the independent implementation and the globalized multi-start implementation agree on all requested inputs while the legacy candidate lies outside that envelope, their agreement is evidence about solver invariance (not truth). Select the lower-CV member of that agreeing pair. Otherwise preserve the candidate.
- **Diagnostic before outcomes:** normalized pairwise prediction RMS and maximum over the concatenated requested inputs for candidate C, independent I, and globalized G. The consensus edge is the pair with minimum RMS; an edge is admissible iff RMS <= 0.5 and maximum <= 4.0. The scalar diagnostic is `margin = min(d(C,I),d(C,G)) - d(I,G)`, with vector companion of all three RMS/max distances.
- **Selector:** override C only when (I,G) is the unique minimum-RMS admissible edge and neither (C,I) nor (C,G) is admissible. Choose the lower exact-LOO-CV member of I,G. Otherwise return C. Ties return C.
- **Strongest alternative explanation:** two non-candidate solvers can share the same misspecified basin, so consensus may merely duplicate error; any gains may also come from conservative fallback rather than identifying basin topology.
- **Cheapest decisive falsification:** on the frozen prospective cohort, the selector makes at least two overrides but fails to reduce catastrophic count in every domain, or worsens ordinary aggregate inside NMSE by >5%.
- **Mechanism-derived unseen prediction:** candidate-only catastrophes will concentrate at positive consensus margins; eligible I/G consensus overrides will reduce catastrophic count relative to candidate, while paths without an eligible edge remain exactly candidate-equivalent.
- **Publishable threshold:** all 16 paths complete; >=2 overrides; catastrophic count no larger than candidate in every domain and at least 50% smaller in at least one domain; inside geometric NMSE <=1.05x candidate; far-shell geometric NMSE <=0.90x candidate; independent audit exact.
- **Project-consequence threshold:** if all gates pass, add the selector as an experimental robust arbitration policy with an explicit solver-invariance receipt. If any safety/noninferiority gate fails, kill this selector and retain candidate fallback; do not tune on the opened prospective cohort.
- **Kill condition:** fewer than two overrides is non-discriminating and kills this cohort as a confirmation; any excess catastrophic tail or >5% inside degradation kills the mechanism.

## Frozen cohort

The runner will define new deterministic families, seeds, dimensions, and noise laws not used by prior shifted evaluations:

- families: `oscillatory_cauchy`, `tilted_matern`;
- dimensions: 2 and 6;
- seeds: 5201 and 5207;
- noise: `asymmetric_contamination`, `variance_ramp`;
- 24 maximin training points; 256 points in each of inside, near-shell, and far-shell request domains.

The truth values are joined only after all three solver fits, pairwise diagnostics, admissible edges, selected solver identities, and failures have been written to the decision object.

## Controls

1. legacy candidate solver;
2. independent implementation alone;
3. three-start globalized solver alone;
4. naive minimum-CV across all three;
5. fixed candidate fallback (selector with no eligible edge).

No threshold fitting or post-outcome rule changes are allowed. A failed or non-discriminating result remains on this branch.

## Claim boundary

Agreement is not correctness, global optimality, or calibrated uncertainty. A pass would support only the frozen three-solver mechanism on the stated regime family pending external replication and prior-art audit.
