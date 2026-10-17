# Robust solver-control development result: kernel killed

**Classification:** opened-cohort development evidence  
**Frozen protocol commit:** `0955587c1f717143af35443e026fa2ad3c73605f`  
**Final runner commit:** `665de2f9f0aa1758d17c089d407e79800d2581b4`  
**Successful workflow:** https://github.com/sushxnthd/kernellum/actions/runs/38864637182  
**Artifact digest:** `sha256:7aa57890511dd40123652369521c44167090525889baee4db8495f56c64cc5b8`  
**Canonical result SHA-256:** `ce9b0b53c07d04817999b7f472cfc01e5ca31b4516eec998149ee09012c7c97b`  
**Terminal decision:** `KILL_SOLVER_BASIN_KERNEL`

## Question

Can deterministic multi-start/globalized, median-ensemble, or stability-penalized
optimization eliminate at least half of single-start catastrophic tails on the
opened 16-path shifted cohort, without increasing catastrophes in any domain or
sacrificing ordinary performance?

## Frozen controls and gates

The screen compared the original single-start solver with the exact prior
three-start globalizer, a nine-start objective-minimizing globalizer, a
nine-start median prediction ensemble, and a nine-start stability-penalized
selector. A robust alternative had to satisfy all of the following:

1. complete all 16 paths;
2. create no excess catastrophes in any domain;
3. reduce total catastrophes by at least 50% relative to single-start;
4. remain within 1.10x single-start inside-domain geometric NMSE;
5. remain within 1.10x the better of single-start and the three-start control
   on both near- and far-shell geometric NMSE.

No method passed.

## Exact results

| Method | Inside catastrophes | Near catastrophes | Far catastrophes | Total | Survived |
|---|---:|---:|---:|---:|---|
| Single start | 1 | 3 | 7 | 11 | baseline |
| Three-start globalized | 3 | 4 | 7 | 14 | no |
| Nine-start globalized | 3 | 5 | 8 | 16 | no |
| Nine-start median ensemble | 2 | 3 | 6 | 11 | no |
| Nine-start stability selector | 3 | 4 | 7 | 14 | no |

| Method | Inside geometric NMSE | Near-shell geometric NMSE | Far-shell geometric NMSE |
|---|---:|---:|---:|
| Single start | 1.2958168 | 161.8823551 | 17,038,685.42 |
| Three-start globalized | 4.1569413 | 1,724.6661880 | 10,196,988,114.22 |
| Nine-start globalized | 3.1971891 | 12,033.3355036 | 191,417,421,867,617.84 |
| Nine-start median ensemble | 1.0495796 | 181.8018048 | 115,508,262.92 |
| Nine-start stability selector | 2.0063956 | 1,793.1187280 | 141,547,393,961.95 |

The median ensemble was the strongest alternative: its inside geometric NMSE
improved to 0.810x single-start, but it did not reduce total catastrophes
(11 versus 11), increased inside catastrophes (2 versus 1), worsened near-shell
geometric NMSE to 1.123x, and worsened far-shell geometric NMSE to 6.779x.
The nine-start objective minimizer was especially destructive: its far-shell
geometric NMSE was about 11.23 million times the single-start value.

The run attempted 11,016 optimizer fits; 10,475 succeeded. All failed attempts
and method/family unavailability records remain embedded in the artifact. The
workflow executed the result twice and required byte identity.

## SCIENCE ledger

- **FALSIFIED:** more deterministic starts plus lowest training objective
  robustly suppress solver-dependent catastrophic extrapolation.
- **FALSIFIED:** median ensembling of deterministic solver basins halves
  catastrophic tails without ordinary-regime cost.
- **FALSIFIED:** the frozen training-prediction stability penalty removes
  catastrophic tails.
- **SUPPORTED:** the failure is not merely a weak three-start grid. Expanding to
  nine starts can expose still lower-objective basins whose extrapolation is
  substantially worse.
- **LIMITATION:** this is an opened synthetic development cohort, not an
  untouched external benchmark. It establishes a kill decision for the current
  mechanism, not a universal impossibility theorem for all globalized solvers.

## CONSEQUENCE ledger

Retire the nonconvex solver-basin kernel as a KERNELLUM flagship route. Do not
launch another score, start grid, ensemble statistic, or stability coefficient
on this cohort. The sequence has now produced multiple discriminating failures:
the prospective envelope opportunity generators failed, the three-start
globalizer failed tail control, and every frozen nine-start robust control
failed its terminal gate.

KERNELLUM should pivot at the model/system boundary rather than continue
optimizer rescue:

> detect unsupported extrapolation from input support and model-class
> disagreement, then abstain or acquire data before exact-LOO/model selection.

That successor requires its own prior-art audit, frozen untouched regimes,
matched conformal/support-distance and uncertainty baselines, and a system
action that changes acquisition or refusal. No claim for that successor is made
here.

## Preserved workflow failures

The successful workflow follows three preserved pre-classification failures:

- run 38855897670: sibling-module import failure;
- run 38864234106: exact single-start subset absent after a failed fit;
- run 38864414676: all deterministic starts failed on one LOO sign/family.

Commits `73657b298de04d0c464e51ad96c641482619bc3a`,
`70680cca4e1e29fb328c6d6bdb6173ffa7c36dce`, and
`665de2f9f0aa1758d17c089d407e79800d2581b4` repaired only evaluation
plumbing and failure bookkeeping. They did not alter the cohort, solvers,
thresholds, or scientific gates.
