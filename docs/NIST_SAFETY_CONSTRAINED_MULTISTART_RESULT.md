# External NIST StRD safety-constrained multistart result

## Decision

**KILL — the fixed start-disagreement diagnostic was vacuous on the pinned NIST confirmation cohort.**

Across twelve external NIST nonlinear least-squares problems, SciPy trust-region least squares from NIST Start 1 already reached the certified parameter solution in every case under the frozen `1e-3` componentwise relative-error criterion. The two supplied starting points converged to essentially the same parameters. Consequently the frozen disagreement rule routed zero development cases and zero of four unopened confirmation cases.

## Confirmation result

| Quantity | Result |
|---|---:|
| Unopened confirmation problems | 4 |
| Routed | 0 |
| Incumbent certified failures | 0 |
| Intervention failures | 0 |
| Overrides | 0 |
| RSS worsenings | 0 |
| Maximum incumbent parameter error | 2.82e-7 |

The confirmation problems were `Lanczos2`, `MGH17`, `Misra1d`, and `Rat42`. Their supplied-start disagreement ranged from approximately `2.7e-10` to `2.8e-7`, far below the frozen `0.25` threshold. No result or threshold was changed after opening them.

## SCIENCE ledger

- **True:** modern trust-region least squares solves all twelve tested NIST StRD cases from the supplied Start 1 to substantially tighter accuracy than the preregistered failure threshold.
- **Falsified:** supplied-start disagreement is not a useful routing signal on this cohort because the failure event has zero prevalence and the diagnostic never activates.
- **Strongest alternative:** the NIST supplied starts and small classical models are too benign for contemporary SciPy, rather than solver instability being absent in realistic discovery workloads.
- **Limit:** this is not evidence that multistart is useless generally. It establishes that this benchmark/signal pair cannot support the intended flagship mechanism.

## CONSEQUENCE ledger

Do not continue tuning disagreement thresholds on NIST StRD. The benchmark is retained as a solver-regression control, not a discovery-instability validation set. The next KERNELLUM kernel must source an external benchmark with independently documented local-minimum or model-selection failures, or construct a safety intervention whose event is non-vacuous without choosing cases from observed outcomes.

## Claim boundary

Multistart and trust-region methods are classical. The smallest supported claim is a prospective external-benchmark falsification of this specific start-disagreement router, plus evidence that these pinned NIST problems are regression tests rather than a useful catastrophic-tail cohort for the current SciPy solver.

## Reproducibility and provenance

The independent audit passes 56/56 checks and a duplicate execution is byte-identical. The first CI run is intentionally preserved: it failed all twelve source-hash checks because the local source fetch retained two terminal newline bytes while the pinned upstream Git blobs contain one. The first follow-up changes only the provenance representation, canonicalizing terminal CR/LF bytes to exactly one LF before hashing. A second preserved CI run passed all 56 audit checks but exposed that unpinned newer NumPy/SciPy releases change last-digit floating-point serialization; the workflow now pins the frozen NumPy 2.3.5 and SciPy 1.17.0 environment. Dataset values, partitions, solver settings, diagnostic threshold, success gates, and every substantive numerical conclusion are unchanged.
