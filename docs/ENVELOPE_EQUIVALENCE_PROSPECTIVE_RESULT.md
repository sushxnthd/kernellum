# Envelope-only equivalence: coverage survives, safety remains untested

**Result date:** 15 October 2026  
**Status:** **INCONCLUSIVE — 2/6 scientific gates failed**

## Smallest supported claim

On 16 prospectively frozen shifted paths using new function families,
dimensions, seeds, and noise processes, the fixed prediction-envelope
certificate accepted 13/16 solver pairs. On accepted paths, selecting the
lower exact-LOO-CV implementation was pointwise within 2x of the candidate and
aggregate geometric NMSE was within 0.00003% in every requested domain.

However, the cohort produced **zero harmful lower-CV switches**. The certificate
therefore received no prospective test of its proposed safety mechanism.
Coverage generalized; harmful-switch rejection did not.

## Decisive table

| Frozen gate | Required | Observed | Status |
|---|---:|---:|---|
| Complete paths | 16 | 16 | PASS |
| Harmful lower-CV opportunities | >=2 | 0 | FAIL |
| Harmful switches rejected | All | 0/0 | FAIL |
| Accepted paths | >=8 | 13 | PASS |
| Accepted pointwise degradation | <=2x | PASS | PASS |
| Accepted aggregate degradation | <=1.10x | 1.00000017x worst | PASS |

Accepted-path geometric-NMSE ratios versus always-candidate were:

- inside: 0.9999997705;
- near shell: 1.0000001644;
- far shell: 1.0000001412.

The independent audit reproduced all decisions, metrics, ratios, and gates:
102/102 checks passed. A complete second execution was byte-identical.

## Interpretation

This is not a scientific failure of prediction-envelope equivalence. It is a
failure of the confirmatory cohort to exercise the safety mechanism. Treating
the 13/16 coverage result as validation would be selective: the preregistered
protocol explicitly required at least two harmful switches.

All 16 paths are now permanently opened and cannot be reused as fresh
confirmation.

## SCIENCE ledger

- **KNOWN:** removing CV separation restores non-vacuous prospective coverage
  on these regimes (13/16 versus 2/16 for the prior conjunction on its opened
  cohort).
- **KNOWN:** accepted solver outputs were numerically and empirically
  interchangeable on this cohort.
- **BELIEVED:** prediction-envelope disagreement may identify solver-dependent
  extrapolation failures.
- **CONFLICTING:** the opened cohort rejected 3/3 known harmful switches, but
  the prospective cohort generated none and therefore supplies no safety
  evidence.
- **FALSIFIED:** this particular shifted factorial is a discriminating safety
  test for solver arbitration.
- **UNTESTED:** rejection of prospectively generated harmful solver switches.

## CONSEQUENCE ledger

Do not promote the envelope receipt as a safety feature yet. The implementation
may remain experimental because it now has evidence of useful coverage, but
its output must continue to say solver_invariance_not_model_correctness.

The next active kernel is not another broad random factorial. It is a frozen
adversarial basin-boundary generator designed to create solver disagreement
without consulting test truth: paired training sets approaching numerical
tie surfaces, with decisions committed before extrapolation labels are joined.
That study must preserve the same envelope thresholds.

## Reproducibility

- Frozen protocol commit:
  a2ed49d8d0ab453392d65455367a75110543dbd7
- Primary canonical digest:
  aac897adec130bbda309b152a3a49cb612f3e1ca88499ef687596a4b1f9c95ed
- Audit canonical digest:
  2abc8f86346c9ae7f491eba069288c5630ebda4f753def3ccf28dd9d1284143f
- Decision file SHA-256:
  611690adc0b694e040e415b4727cf1d9acda99e78392941c9cba3d2d2af95a2b
- Result file SHA-256:
  38c4e474eff11fb4e664fb3989c5ae2560759575f1021b6848d56f807902cfa5
- Audit file SHA-256:
  5d17f283f9d326ccea983c53388b925887ee09fdd8cb7c7b46507df3d3b24507

## Claim boundary

The certificate concerns interchangeability of two solver outputs on a fixed
request set. It does not certify model correctness, global optimality,
calibrated uncertainty, or performance outside those inputs. Historical
novelty is not asserted.
