# Sign-anchored dual-solver arbitration: exploratory foothold

**Classification:** OPENED DEVELOPMENT / POST-HOC MECHANISM PROBE  
**Status:** FOOTHOLD, NOT CONFIRMATION  
**Breakthrough gate:** INCONCLUSIVE

## Smallest supported claim

Across 120 already-opened synthetic paths, a truth-blind arbitration rule—retain the candidate when independently implemented solvers select opposite response signs; otherwise select the lower exact-LOO CV—avoided the independent implementation's wrong-sign catastrophe, selected the better extrapolator on all four known model disagreements, and improved aggregate geometric NMSE relative to either constituent implementation.

The rule was derived after inspecting the four disagreements. These numbers are development evidence only and do not establish generalization.

## Decisive table

| Domain | Candidate geometric NMSE | Independent | Sign-anchored control | Control vs candidate |
|---|---:|---:|---:|---:|
| Inside | 2.16857e-5 | 2.80317e-5 | **2.06730e-5** | 4.67% lower |
| Near shell | 1.06818e-4 | 1.73859e-4 | **9.38355e-5** | 12.15% lower |
| Far shell | 1.68728e-3 | 4.23122e-3 | **1.18873e-3** | 29.55% lower |

| Catastrophic count (`log NMSE > 5`) | Candidate | Independent | Control |
|---|---:|---:|---:|
| Inside | 0 | 2 | **0** |
| Near shell | 6 | 8 | **6** |
| Far shell | 11 | 13 | **10** |

The control chose the candidate on 43 paths and the independent implementation on 77. On the far shell it was better than the candidate on 22 paths and worse on 19; the gain is driven by avoiding severe tails, not uniform pathwise dominance.

## SCIENCE ledger

- **KNOWN:** exact-LOO CV values from different solver basins are not always comparable; the only cross-sign disagreement had lower independent CV but dramatically worse error in every domain.
- **BELIEVED:** response-sign disagreement is a useful certificate that the selection problem has crossed an invalid basin boundary.
- **ANOMALOUS:** a one-bit sign anchor removes an extreme failure that both the scalar and four-axis predictive diagnostics missed.
- **CONFLICTING:** ordinary-path performance is mixed (22 far-shell improvements versus 19 regressions), so aggregate improvement may be dominated by a few tails.
- **FALSIFIED:** lower exact-LOO CV alone is a safe cross-solver arbiter.
- **UNTESTED:** the fixed sign anchor retains its tail advantage on shifted function families, dimensions, noise models, and external data.

## CONSEQUENCE ledger

- Kernellum should not accept a numerically lower CV when independent solvers disagree on response sign.
- The next robust-selection prototype should expose sign/family disagreement as a first-class certificate and either preserve a trusted sign constraint or abstain/globalize.
- The next decisive experiment is a prospectively frozen shifted-condition study comparing: candidate, independent, naive lower-CV arbitration, sign-anchored arbitration, and full multi-start globalization.
- Do not ship the current rule yet; the present cohort was used to derive it.

## Provenance

- Paths: 120
- Decision-table SHA-256: `dcd8d262684d16ad2d87bacd27b22dc54362f2716ba3ae1924ec91fdf09fba1c`
- Canonical result SHA-256: `7ba0a64ab68c2d30bf61bad7e3aa9a36ef4d5e703c8f839476d3d9f13c1836bf`
- Workflow run: `38467961113`

The decision table was written and hashed before the runner joined persisted test metrics. This prevents truth-conditioned decisions within the execution but does not change the post-hoc status of the rule.
