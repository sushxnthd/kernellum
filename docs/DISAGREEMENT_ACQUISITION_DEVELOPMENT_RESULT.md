# One-point disagreement acquisition: mechanism killed

**Result date:** 16 October 2026  
**Classification:** opened-cohort development evidence  
**Scientific gate:** **FAIL**  
**Decision:** `KILL_ONE_POINT_DISAGREEMENT`

## Smallest supported claim

On the 48 archived path/domain cells, adding one noiseless response at the
point of maximum frozen model-class disagreement reduced catastrophic cells
from 11 to 9. It did not halve catastrophes, beat every matched acquisition
control by two, or avoid domain-level regression. In the far shell it increased
catastrophes from 7 to 8 and worsened geometric NMSE by **13,246.6×** relative
to no acquisition and **43,606.1×** relative to the best acquisition control.

Therefore maximum-disagreement one-point acquisition must not be shipped as a
safety intervention. This result does not say that active learning or
experimental design is generally harmful; it falsifies this exact rule under
unstable exact-LOO selection on the opened synthetic cohort.

## Frozen result

| Method | Total catastrophes | Inside | Near shell | Far shell |
|---|---:|---:|---:|---:|
| No acquisition | 11 | 1 | 3 | 7 |
| Maximum disagreement | **9** | **0** | **1** | **8** |
| Deterministic random | 11 | 0 | 2 | 9 |
| Nearest support | 10 | 1 | 2 | 7 |
| Farthest support | 11 | 2 | 3 | 6 |

| Domain | No-acquisition geometric NMSE | Disagreement | Best matched control |
|---|---:|---:|---:|
| Inside | 1.2958 | **0.4479** | 0.6687 |
| Near shell | 161.8824 | **25.2634** | 122.8009 |
| Far shell | 17,038,685.4210 | **225,705,362,472.5836** | 5,176,009.0243 |

Disagreement passed decision completeness, post-acquisition completeness,
inside noninferiority, and the near-shell matched-control gate. It failed all
four terminal tail/safety gates: catastrophe halving, two-case superiority,
no domain excess, and far-shell superiority.

The independent implementation reproduced 48 selected-index decisions, all
240 method/cell scores, 30 aggregate statistics, and the decision digest:
**319/319 checks passed**. A second primary execution produced byte-identical
decision and result artifacts.

## Mechanism evidence

One new datum changed the selected sign/family candidate in 11/48
disagreement acquisitions, including two sign flips. The intervention fixed
three previously catastrophic cells, but created two new far-shell
catastrophes:

- one cell changed from log-NMSE `-0.160` to `6.327` without changing its
  sign/family label;
- one cell changed from `0.006` to `127.355` after an
  `exp_concave → exp_affine` winner flip.

It also drove an already-catastrophic far-shell cell from `10.342` to `82.572`
after a sign and family flip. Thus maximal predictive disagreement can choose
an informative observation while still moving the discontinuous exact-LOO
selection map into a catastrophically worse extrapolator. Information gain and
tail safety are not interchangeable objectives here.

Candidate-level optimization failures were not hidden: 149 failed
sign/family fits across post-acquisition LOO banks are preserved in the raw
result. Every cell still had at least one valid winner for every method.

## Strongest controls and wildcard

Random acquisition tests whether any extra response suffices. Nearest-support
and farthest-support acquisition test local-density and support-expansion
explanations using the same oracle budget and refit code.

The preregistered wildcard—farthest-support acquisition—did not replace the
kernel: it had 11 total catastrophes and catastrophically poor near-shell
geometric NMSE. It did, however, have the fewest far-shell catastrophes (6), a
regime split worth preserving but not enough to justify retuning on this opened
cohort.

## Prior-art collision audit

Maximum-disagreement acquisition is an instance of query by committee, whose
core rule dates to Seung, Opper, and Sompolinsky (1992):
<https://doi.org/10.1145/130385.130417>. Transductive experimental design and
active learning under model discrepancy are also established areas:
<https://jinbo-bi.uconn.edu/wp-content/uploads/sites/2638/2018/12/experimentdesign_icml.pdf>
and <https://arxiv.org/abs/2502.05372>.

No novelty is claimed for disagreement sampling. The defensible contribution
is the frozen negative mechanism test: under exact-LOO nonlinear model
selection, a maximally disagreeing noiseless measurement can improve average
inside/near behavior yet worsen catastrophic far extrapolation.

## SCIENCE ledger

- **FALSIFIED:** one maximum-disagreement response halves catastrophic exact-LOO
  cells.
- **FALSIFIED:** it beats random, nearest-support, and farthest-support controls
  by the frozen margin.
- **SUPPORTED on this cohort:** disagreement acquisition improves inside and
  near-shell aggregate error while remaining unsafe in the far shell.
- **MECHANISM:** the measurement can induce a discontinuous winner change; a
  lower post-acquisition LOO score is not a tail-safety certificate.
- **LIMITATION:** opened synthetic evidence with noiseless acquisition; no
  untouched or external validation.

## CONSEQUENCE ledger

- Do not expose one-point maximum-disagreement acquisition as a safe Kernellum
  action.
- A measurement planner must jointly constrain the post-acquisition selection
  transition; acquisition informativeness alone is insufficient.
- The broader intervention kernel remains alive for at most two more
  discriminating runs. Its successor must freeze a **stability-constrained
  acquisition** rule or batch design, with far-shell safety as a hard gate.
- No new holdout should be spent until that rule beats the opened controls.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python scripts/evaluate_disagreement_acquisition.py \
  --decisions results/disagreement_acquisition_decisions.json \
  --output results/disagreement_acquisition_result.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python scripts/audit_disagreement_acquisition.py \
  --decisions results/disagreement_acquisition_decisions.json \
  --result results/disagreement_acquisition_result.json \
  --output results/disagreement_acquisition_audit.json
```

- Protocol commit: `c6318557d635b19598b80037554740f23eae6fd8`
- Pre-outcome addendum commit: `413dc742349c07c92bc98cbfdca0ee0d46582cf3`
- Decision SHA-256: `8f2039f95b1138896448e5ac5e8f35ec902afd5632ff391f3402ef66ce9a1986`
- Result canonical SHA-256: `51a247c49d2784363d8e2666a48d6fe187cea91fbe75cfd64ed9eb3c8eb47b6f`
- Audit canonical SHA-256: `935c30594cf1b6e9c5bd73410fd22c42f5b0d1a04588e64320fe6e56fd4ca503`
