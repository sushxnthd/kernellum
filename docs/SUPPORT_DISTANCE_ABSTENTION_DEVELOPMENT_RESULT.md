# Support-distance abstention: fixed mechanism killed

**Classification:** opened-cohort development evidence  
**Scientific gate:** **FAIL**  
**Decision:** `KILL_FIXED_SUPPORT_DISTANCE`

## Smallest supported claim

On the 48 archived path/domain cells, the frozen 95th-percentile normalized
nearest-support distance rejected 7 of 11 catastrophic single-start cells at a
fixed 16-cell rejection budget. It retained all 16 inside cells and 28 of 37
non-catastrophic cells, but its AUROC was only 0.7248 and it rejected no more
catastrophes than coarse domain order, shell radius, or coordinate excursion.

The fixed mechanism therefore fails. Nearest-support distance is useful for
recognizing extrapolation, but this result provides no evidence that it
localizes solver/model-selection catastrophes beyond the benchmark's obvious
shell structure.

## Exact result

| Truth-blind score | AUROC | Catastrophes rejected / 11 | Safe cells retained / 37 | Inside retained / 16 |
|---|---:|---:|---:|---:|
| nearest-support distance | 0.7248 | 7 | 28 | 16 |
| coarse domain order | 0.7359 | 7 | 28 | 16 |
| shell radius | 0.6880 | 7 | 28 | 16 |
| coordinate excursion | 0.6806 | 7 | 28 | 16 |
| deterministic random | 0.5553 | 4 | 25 | 10 |

The candidate passed completeness, safe-retention, inside-retention, and
random-control gates. It failed the preregistered AUROC, 8/11 tail-rejection,
domain-order superiority, and shell-radius superiority gates. No threshold,
quantile, rejection budget, or tie rule was swept after the join.

An independently written implementation reproduced all 240 cell/score values
and 21 aggregate/hash checks: 261/261 checks passed.

## Mechanism interpretation

The result separates two questions that should not be conflated:

1. **Is a request outside observed input support?** The candidate answers this
   geometrically and preserved every inside cell at the chosen budget.
2. **Will the exact-LOO winner fail catastrophically?** The score does not add
   discrimination beyond shell identity on this cohort.

The four catastrophes left accepted include three near/inside cells and one
far-shell cell ranked below the fixed cutoff. That pattern is consistent with
model-family or solver/model-choice failure in regions not captured by a
single geometric distance.

## SCIENCE ledger

- **FALSIFIED:** the fixed normalized nearest-support score removes at least
  8/11 catastrophic cells at 2/3 coverage.
- **FALSIFIED:** it adds predictive information over coarse shell/radius
  controls under the frozen superiority gate.
- **SUPPORTED:** catastrophic risk is enriched in extrapolative cells; 7/11
  positives occur in the 16 rejected cells, versus 3.67 expected under uniform
  rejection.
- **UNTESTED:** a joint score using input support and model-class disagreement,
  or an acquisition rule that changes the support set before model selection.
- **LIMITATION:** this is opened synthetic development evidence, not an
  untouched or external validation.

## CONSEQUENCE ledger

Do not ship nearest-support distance as a Kernellum catastrophe certificate.
It may remain descriptive telemetry, explicitly labeled as support geometry.

The single successor kernel is now interactional rather than scalar:

> Can one support-point acquisition, chosen without requested truth, collapse
> model-class disagreement and prevent catastrophic exact-LOO selection more
> reliably than abstention-only, random acquisition, and nearest-point
> acquisition controls?

That kernel changes the system action from merely refusing a request to asking
for the most discriminating measurement. It must freeze new support geometries,
compare matched acquisition baselines, and use an untouched outcome join. A
standalone distance score may not be reintroduced under a new name.

## Reproduction and receipts

```bash
python scripts/evaluate_support_distance_abstention.py \
  --archived-result results/robust_solver_control_development.json \
  --decisions /tmp/support-decisions.json \
  --output /tmp/support-result.json
python scripts/audit_support_distance_abstention.py \
  --archived-result results/robust_solver_control_development.json \
  --decisions /tmp/support-decisions.json \
  --result /tmp/support-result.json \
  --output /tmp/support-audit.json
```

- Frozen protocol commit: `90114b9dae953ae266f769a2c11745ca872fb04a`
- Decision SHA-256: `a0f664b281e3436ea7fd2ea7706d0655b57794b11bf700f6a2607f77e6db31ff`
- Result canonical SHA-256: `52034a22362e12f528733bd6d1ed718fcec1e3f33a3c10455f8434732f269391`
- Audit canonical SHA-256: `32e93737de3ce8527f73d433abdb26c254c8f4d357f158c83571b49c14136297`
- Archived robust-control canonical SHA-256: `ce9b0b53c07d04817999b7f472cfc01e5ca31b4516eec998149ee09012c7c97b`

