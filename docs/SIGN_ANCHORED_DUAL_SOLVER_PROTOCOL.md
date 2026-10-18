# Sign-anchored dual-solver arbitration: opened-development protocol

**Classification:** EXPLOITATION / OPENED DEVELOPMENT / POST-HOC MECHANISM PROBE

This protocol was written after inspecting the four known candidate-versus-independent disagreements. It is not preregistration and cannot provide confirmatory evidence. Its purpose is to turn the observed mechanism into an exact, reproducible candidate rule that can later be frozen on genuinely shifted conditions.

## Active kernel

- **Question:** can two independently implemented solvers be combined without allowing a lower cross-validation score from a wrong-sign basin to create catastrophic extrapolation?
- **Best-known frontier:** cheap pre-selection routing failed. Of four implementation disagreements, three favor the candidate and one favors the independent solver on extrapolation; the sole cross-sign disagreement is catastrophically worse under the independent fit despite its lower exact-LOO CV.
- **Exact objective:** apply one truth-blind rule to all 120 persisted paths and measure inside, near-shell, and far-shell performance against both constituent solvers.
- **Rule:** if candidate and independent selected signs disagree, retain the candidate sign anchor. Otherwise choose the solver with lower exact-LOO CV, breaking ties toward the candidate.
- **Mechanism:** sign disagreement is treated as an invalid cross-basin comparison because normalized CV can reward the wrong response orientation; within a common sign, lower fold error remains admissible evidence.
- **Strongest alternative explanation:** the apparent success is a four-case artifact and the rule degrades ordinary paths or shifted families.
- **Cheapest decisive falsification:** apply the fixed rule across all 120 opened paths, including the 116 model-agreement paths, and compare aggregate error and catastrophic-tail counts.
- **Publishable success condition:** a prospectively frozen shifted-condition study independently confirms reduced catastrophic tails and non-inferior ordinary performance versus a fully globalized control.
- **Project-relevance threshold:** opened evidence must show no new catastrophic cases versus the candidate and improvement on at least one known disagreement; otherwise discard the rule before confirmation.
- **Kill condition:** any new catastrophic case or failure to improve the known negative-Gaussian disagreement.

## Integrity boundary

The runner first materializes and hashes every decision using only model sign, family, and exact-LOO CV. It then joins persisted test metrics. This prevents truth-conditioned selection inside the run, but it does not erase the post-hoc origin of the rule.
