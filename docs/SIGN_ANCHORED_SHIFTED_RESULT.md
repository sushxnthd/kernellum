# Sign-anchored arbitration on shifted conditions: decisive falsification

**Classification:** PROSPECTIVE SHIFTED EVALUATION  
**Scientific gate:** FAIL  
**Breakthrough gate:** INCONCLUSIVE

## Smallest supported claim

The post-hoc sign-anchored dual-solver rule does not generalize to the frozen
shifted regimes and must be retired. Opposite-sign disagreement was neither
frequent enough nor directionally useful, and choosing lower exact-LOO CV even
within the same sign/family caused catastrophic extrapolation under nearly tied
CV values.

This does not invalidate nonlinear least squares or prove that every robust
arbitration rule is impossible. It falsifies this rule and the assumption that
response sign is the relevant basin boundary.

## Frozen result

All 16 shifted paths completed. The independent aggregation audit passed 55/55
checks and exactly reproduced decisions, metrics, gates, and the canonical
digest.

| Frozen gate | Required | Observed | Status |
|---|---:|---:|---|
| Sign disagreements | >=2 | **1** | FAIL |
| Conditional anchor win rate | >=75% | **0/1** | FAIL |
| No excess catastrophes | all domains | **failed all domains** | FAIL |
| Inside NMSE / candidate | <=1.05 | **1173.25** | FAIL |
| Far NMSE / naive | <=0.90 | **14.25** | FAIL |
| Far NMSE / globalization | <=1.10 | **37.34** | FAIL |
| Globalized tail control | no worse than candidate | **failed** | FAIL |

| Domain | Candidate geometric NMSE | Naive lower-CV | Sign anchor | Globalized |
|---|---:|---:|---:|---:|
| Inside | 1.29582 | 2.52670e3 | **1.52032e3** | 4.15694 |
| Near shell | 1.61882e2 | 8.65403e5 | **1.62395e6** | 1.72467e3 |
| Far shell | 1.70387e7 | 2.67247e10 | **3.80804e11** | 1.01970e10 |

Catastrophic counts (`log NMSE > 5`) for candidate / naive / anchor /
globalized were respectively 1/3/3/3 inside, 3/4/4/4 near, and 7/8/8/7 far.

## Minimal counterexamples and mechanism update

### Opposite-sign counterexample

For 5-D skew-Gaussian response, seed 3101, Student-t noise, the candidate chose
sign -1 with CV 921,611.923 while the independent solver chose sign +1 with
lower CV 275,970.066. Anchoring improved inside log NMSE (7.964 versus 16.092)
but lost badly under extrapolation: near 26.834 versus 16.764 and far 66.111
versus 23.604. Thus sign anchoring did not protect the target failure mode.

### Same-sign near-tie catastrophe

For 5-D skew-Gaussian response, seed 3102, Student-t noise, both solvers chose
the same positive concave family. Independent CV was only
`5.787920534e-7` lower (`1.191028789` versus `1.191029368`), yet selecting that
nominal winner increased inside-domain NMSE by approximately `4.35e46` versus
the candidate. The three-start globalized fit matched the candidate on this
path.

This is the sharpest mechanism clue from the study: a numerically negligible
cross-solver CV advantage can correspond to an enormous predictive difference.
The relevant boundary is therefore not sign alone; it is comparison
identifiability under solver uncertainty plus predictive-basin disagreement.

## Two ledgers

### SCIENCE

- **KNOWN:** the frozen sign-anchor rule fails on shifted misspecified families;
  all eight scientific gates failed.
- **FALSIFIED:** opposite response sign is a reliable certificate for choosing
  the candidate solver; same-sign lower CV is safe.
- **ANOMALOUS:** a relative CV difference below one part per million coincided
  with a roughly `4.35e46` inside-NMSE ratio.
- **CONFLICTING:** three-start globalization fixed that minimal near-tie path but
  failed aggregate tail-control and ordinary-performance gates.
- **UNTESTED:** an equivalence-band certificate combining CV numerical
  uncertainty with prediction-envelope disagreement can identify when solver
  arbitration must abstain.

### CONSEQUENCE

- Remove sign anchoring from Kernellum's robust-selection roadmap.
- Do not compare cross-solver CV point estimates as exact orderings.
- Do not adopt the present three-start globalizer as a safe default.
- The next active kernel is **stability-certified abstention**: estimate a
  reproducible CV equivalence band, treat within-band scores as tied, and
  require prediction-envelope agreement before selecting. The cheapest first
  test is on these permanently opened paths; only a frozen rule may proceed to
  new conditions.

## Provenance and reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python scripts/evaluate_sign_anchor_shifted.py \
  --decisions /tmp/shifted-decisions.json \
  --output /tmp/shifted-result.json
python scripts/audit_sign_anchor_shifted.py \
  --decisions /tmp/shifted-decisions.json \
  --result /tmp/shifted-result.json \
  --output /tmp/shifted-audit.json
```

- Frozen protocol commit: `69ff070bb2464d0584e030794f8a7ebf14f6cd6b`
- Corrected execution commit: `6725e731e05b8d341649f8d60dfe190c7ca6cd3d`
- Workflow run: `38492827875`
- Canonical result SHA-256:
  `14219ba90e667b67e16def4e865bc661b7524f16d586bf8222f8c1599b440b14`
- Result file SHA-256:
  `a1aee8c706686ff51e275bca1643b68b775931ab3ae3ed3fc8d69797d019658c`
- Decision file SHA-256:
  `6bdde39f15ec86df4aeb969fa52c3f726630e520e541b8663a1bb6109c6925c5`
- Audit file SHA-256:
  `665dd321e25339163f4456a2f72534b88a16adf13f7a199eeb2b2d6344a5cc59`
- Workflow artifact digest:
  `sha256:f0041316d2c12bb136193c2c2faed9df1565750f6d66b2f0ca3fb05e00a8cef4`

## Limitations

This is a 16-path synthetic study with deliberately difficult misspecification
and noise. Large aggregate errors should not be generalized to ordinary
regimes. The near-tie catastrophe is a reproducible counterexample, not yet a
general law or historical-novelty claim.
