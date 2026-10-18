# Stability-certified abstention: safe but vacuous conjunction

**Classification:** OPENED DEVELOPMENT DISCRIMINATION  
**Scientific gate:** FAIL  
**Breakthrough gate:** INCONCLUSIVE

## Smallest supported claim

The frozen conjunction of model-identity agreement, CV separation, and
prediction-envelope agreement safely rejected every harmful lower-CV switch,
but it accepted only 2/16 paths and failed its preregistered non-vacuity gate.
It must not ship.

The failure localizes the unnecessary condition: 10 rejected paths had
matching sign/family and extremely close requested predictions, but were
rejected only because the two CV estimates were within the equivalence band.
When requested predictions are already equivalent, identifying the solver's
CV ordering is not operationally necessary.

## Frozen result

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| Complete | 16 | 16 | PASS |
| Harmful switches rejected | all | 3/3 | PASS |
| Accepted pointwise degradation | <=2x | <=2x | PASS |
| Coverage | >=4/16 | **2/16** | **FAIL** |
| Accepted aggregate degradation | <=1.10x | <=1.000001x | PASS |

Accepted-set geometric-NMSE ratios versus candidate were 0.999997 inside,
0.999999 near-shell, and 1.000001 far-shell.

Rejection attribution was: CV separation 12 paths, prediction RMS/max envelope
4 paths, and model identity 1 path. Ten paths failed only the CV-separation
clause while satisfying both prediction-envelope clauses and model identity.

## Mechanism update

### SCIENCE

- **KNOWN:** the fixed conjunction is safe on this opened cohort but too
  conservative to meet its own utility threshold.
- **FALSIFIED:** a separated CV ordering is necessary before treating two
  behaviorally equivalent solver outputs as interchangeable.
- **ANOMALOUS:** 10/16 paths have relative cross-solver CV margins below
  `1e-3` while normalized maximum prediction disagreement remains below 4.
- **BELIEVED:** the prediction envelope, not CV rank identifiability, is the
  direct observable for whether solver choice changes the requested answer.
- **UNTESTED:** a frozen envelope-only equivalence certificate generalizes to
  untouched regimes and external data.

### CONSEQUENCE

Do not ship this conjunctive certificate. Reformulate the runtime contract:

1. if independently fitted candidates are behaviorally equivalent on the
   requested input set, return either prediction with an equivalence receipt;
2. if their prediction envelope is wide, abstain regardless of the nominal CV
   ordering;
3. never represent solver agreement as a correctness certificate for a
   misspecified model family.

The cheapest next decisive action is to freeze an envelope-only certificate on
genuinely new conditions. The current opened data may define the mechanism but
cannot confirm it.

## Provenance and reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python scripts/evaluate_stability_certified_abstention.py \
  --decisions /tmp/stability-decisions.json \
  --output /tmp/stability-result.json
python scripts/audit_stability_certified_abstention.py \
  --decisions /tmp/stability-decisions.json \
  --result /tmp/stability-result.json \
  --output /tmp/stability-audit.json
```

- Frozen protocol commit: `48b3c386a15c88f761c7398a0583355db7160309`
- Result canonical SHA-256:
  `bf9524a57f998f746aaa532e43123a7ec74b012b9e2da6152d7a85d572c32dac`

## Limitations

This is a 16-path opened synthetic development study. The post-result
envelope-only reformulation has not been prospectively tested. Agreement of two
implementations does not bound error to unknown truth, protect against shared
misspecification, or establish optimizer globality.

