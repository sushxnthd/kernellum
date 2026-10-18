# Basin-transition confirmatory result: fixed diagnostic does not transfer

## Verdict

**KILL the fixed continuation-routing diagnostic without threshold tuning.**

The 24-path prospective confirmatory cohort completed, the duplicate execution was byte-identical, and the independent standard-library audit passed 738/738 checks. The scientific status is `FAIL`: the signal did not transfer across unseen truth families strongly enough to support a robust selector.

## Frozen prediction versus result

| Gate | Frozen requirement | Result | Pass |
|---|---:|---:|:---:|
| Complete paths | 24 | 24 | yes |
| Routes | >= 4 | 1 | no |
| Routed truth families | >= 2 | 1 | no |
| Aggregate route precision | >= 0.75 | 1.00 (1/1) | yes |
| Far geometric-NMSE ratio | <= 0.90 | 0.944830 | no |
| Inside geometric-NMSE ratio | <= 1.05 | 0.988831 | yes |
| Far catastrophes | no increase and halve a domain with >=2 | 4 -> 4 | no |
| Any-domain excess catastrophes | none | none | yes |
| Independent audit | zero failures | 738/738 | yes |

## What survived

The sole routed path was `warped_cauchy / d=5 / seed=9103 / symmetric_t`:

- early-switch fraction: 1.00;
- median transition amplitude: 0.08;
- globalized/candidate request distance: 0.435966;
- residual ratio: 0.450555;
- far-shell NMSE: 2.297534 -> 0.935534;
- near-shell NMSE: 1.247590 -> 0.578896;
- inside NMSE: 0.908232 -> 0.693685 after exponentiating the logged scores.

This is a real within-case win, but it cannot validate the selector: the predeclared transfer claim required repeated firing across at least two families.

## Decisive falsification

The first 16-path cohort produced four routes and a 40.9% far-shell reduction, but three wins belonged to one family. The confirmatory cohort replaced both original families, dimensions, and seeds while freezing all thresholds. It produced:

- zero routes for `rational_mixture`;
- zero routes for `anisotropic_bump`;
- one route for `warped_cauchy`;
- four candidate far catastrophes and four selected far catastrophes;
- only 5.5% aggregate far-shell improvement, below the frozen 10% requirement.

Therefore the earlier signal was not a family-agnostic law. Repeated early transitions plus a hard candidate/globalized separation threshold are too sparse and family-sensitive to be a deployable prospective mechanism.

## Strongest alternative explanation resolved

The live alternative was family confounding. The confirmation supports it: routing again concentrated in a single warped family, while two structurally different families never fired. The evidence does not show that the diagnostic is useless in every model family; it shows that the fixed rule does not generalize as claimed.

## SCIENCE ledger

- True: an extreme repeated-transition signature can identify an individual case where globalization helps.
- Falsified: the frozen four-condition rule transfers across unseen families as a reliable tail-risk selector.
- Not supported: a general continuation-derived law, deployment-ready selector, or flagship claim.
- Reproducibility: canonical result SHA `dd4006eca3bbc88b2b7142fe8976f29ec63dcc13f02669a355a2abc5d0678184`; audit SHA `2c7370bbcb9440bab3702da2ed17456fa34dd75fd2de53e309b88d44f9b41380`.

## CONSEQUENCE ledger

- Do not integrate this binary route into Kernellum evaluation.
- Do not lower thresholds on the opened cohort.
- Retain continuation traces as diagnostic telemetry only.
- Reformulate the positive-mechanism search around a prospective continuous transition-topology representation that must predict *which intervention wins*, not merely whether a transition occurs. The next kernel must predeclare a scalar/vector topology score, a failure region, simple separation and CV baselines, and a fresh untouched cohort before outcome access.

## Smallest supported claim

Across a frozen 24-path, three-family prospective confirmation, the unchanged basin-transition selector fired on only one path and did not reduce four far-shell catastrophes. This decisively falsifies cross-family transfer of the fixed diagnostic while preserving one correctly routed within-family case.
