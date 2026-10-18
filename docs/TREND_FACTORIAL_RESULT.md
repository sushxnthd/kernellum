# Trend component ablation

3 October 2026. **A useful explanatory result; the general breakthrough gate
still fails.** All evidence here is exploratory on the previously opened
39-function cohort. No new test function or physical measurement was acquired.

The failed affine-trend predictor changed two things at once: it removed
quadratic/cubic kernels under exponentiation and added affine RBF means. This
follow-up separates those interventions on identical archived observations.
The protocol and runner were frozen locally at `a8c2301` before ablation scores
were read. Publication is after outcomes, not public preregistration.

All 390 paths (39 functions × five seeds × two noise levels) completed four
arms, producing **1,560 outcomes**. Each uses the same 64 observed labels.
Ratios are geometric-mean normalized MSE; lower is better. The existing 1e-8
error floor and all nine controls are retained.

| Intervention | Overall / original | Clean / original | Noisy / original | Overall / adaptive | Wins / original |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original replay | 1.0000 | 1.0000 | 1.0000 | 1.1274 | Replay |
| Remove exponential polynomial terms only | 1.5496 | 2.9141 | 0.8240 | 1.7470 | 10/39 |
| Add affine RBF means only | **0.8345** | **0.9159** | **0.7604** | **0.9409** | **26/39** |
| Both changes (previous candidate) | 1.0611 | 1.4943 | 0.7535 | 1.1963 | 21/39 |

Tail errors must be read alongside these geometric averages. Worst NMSE is
8.427e16 for original, **5.590e26 for remove-only**, 28.534 for add-only, and
5.385 for both. The remove-only catastrophe is Franke5, clean, seed 930101:
an exponentiated long/medium RBF mixture has small PRESS risk but an enormous
test error. Deleting exponential polynomial kernels does not by itself
guarantee stable inverse-response predictions. A bounded kernel correction
can still have a very large coefficient-dependent bound. Add-only retains a
large noisy GenzCornerPeak error at seed 930102 and is not reliably safe.

Adding affine means while retaining the original model families yields 16.55%
lower aggregate error than the original stack and 5.91% lower than the adaptive
control. Without GenzCornerPeak the original-control ratio is 0.9366: a 6.34%
descriptive improvement, rather than the full 16.55%. This is a more useful
development foothold than the combined intervention. It still fails the
unchanged <=0.8 ratio against several strong controls, the adaptive comparison
has only 23/39 function wins, and two other controls have noise-stratum
regressions. No predictor is promoted to the default.

The clean regressions on McLainS2/S3/S4 and Franke4/5 follow the removal arm.
With affine additions alone, all five retain errors below the evaluation floor.
Removing terms alone produces clean geometric-mean errors of approximately
9.00e-7, 1.92e-7, 1.33e-6, 3.76e-7 and 63.23 respectively. For Franke5 the
combined candidate's affine models repair most of that loss, but its error
still rises above the floor to 2.01e-7. This factorial comparison identifies
which intervention loses expressivity on these observed functions; it does
not prove a general causal law outside the cohort.

The preceding paired diagnosis also verified all 18 published trend/control
aggregate comparisons with separate standard-library arithmetic. Its noisy
ratio against the original stack changes from 0.7535 to 0.9920 after excluding
GenzCornerPeak; against the adaptive stack the corresponding ratios are 0.9873
and 0.9904. Descriptive function-bootstrap intervals include 1 for both noisy
comparisons. This narrow noisy effect is not strong enough to justify a
noise-specific performance claim.

Two other cautions emerged. Adding 2% noise changes response-transform
availability on 40/195 paired function/seed paths. Raw clean-error aggregation
is dominated by machine-precision fits: its ratio is 0.1423, while the original
floored metric is 1.4943. The original stack has 45/195 clean errors below 1e-8,
versus 20/195 for the combined candidate. These are sensitivity diagnostics,
not replacement metrics. Function families are related; bootstrap intervals
are descriptive rather than population-valid coverage statements.

Archived pairing metadata were checked for seven controls. The nested-winner
and noise-consistent control traces contain scores and model selection but not
the queried indices, input digest and observed labels; their scores reproduce
the published arithmetic, but this analysis cannot separately certify their
pairing from those sparse traces.

The runner replayed the original and combined arms for 780 outcomes within
the existing prediction tolerance. Maximum absolute NMSE discrepancy was
1.021e-8; reported ratios for tiny errors can differ in the last digits.
All 1,560 scores also passed a separate scalar error reduction. The second
predictor-arithmetic check is recorded in
`results/trend_factorial/development/audit.json`; it reconstructs kernel and
augmented-system predictions, checks candidate PRESS scores and simplex KKT
conditions, and recomputes every aggregate from traces. It uses the recorded
simplex weights rather than independently refitting them. This is same-author
verification, not external reproduction.

The completed second arithmetic check passed all 1,560 outcomes and 36
aggregate comparisons, with all four general criterion decisions false in
both implementations. It reports 28 ridge-selection numerical ties. Maximum
scaled simplex KKT residual is 2.058e-9. The largest absolute NMSE difference,
1.492e18, occurs on the 5.590e26 remove-only failure; a targeted second
calculation gives relative discrepancy 2.669e-9. An enormous failing score
must not be confused with a failure of the arithmetic check. The focused
trend/representation/adaptive regression suite passed 18 tests.

The first second-arithmetic run passed all 1,560 prediction checks, then found
a numerical tie in the original-versus-itself win count: one function ratio
was 0.9999999999999999 in the published NumPy reduction and 1.0 in the separate
log reduction. The auditor reports that tie explicitly with a 1e-12 proximity
check and requires the full gate decisions to agree; predictor arithmetic,
performance thresholds and published scores were unchanged. Near-exact replay
ratios should be treated as ties, not improvements.

Evidence:

- `results/noise_regime_diagnosis/development/`: paired rows, per-function
  comparisons, uncertainty, floor sensitivity and source/output hashes.
- `results/trend_factorial/development/`: all raw scores, selected model
  metadata, nine-control comparisons, manifest and arithmetic audit.
- Original exact inputs: `Kernellum_Affine_Trend_Inputs_2026-10-03.npz`, SHA256
  recorded in the manifest. Use the original saved archive or reconstruct
  using the existing exact-input helper on a matching numerical platform.

Reproduce on Python 3.12, NumPy 2.3.5, SciPy 1.17.0, UQTestFuns 0.6.0:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python scripts/diagnose_noise_regime.py --out build/noise-regime-diagnosis
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python experiments/trend_factorial/develop.py --data /path/to/Kernellum_Affine_Trend_Inputs_2026-10-03.npz --out build/trend-factorial
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python scripts/audit_trend_factorial.py --folder build/trend-factorial --data /path/to/Kernellum_Affine_Trend_Inputs_2026-10-03.npz --out build/trend-factorial/audit.json
```

The next decisive action is a separate frozen boundary test of the add-only
foothold: clean log-quadratic relations versus additive-noise sign changes and
out-of-support extrapolation, with at least ten predetermined seeds and all
four arms. Derive predictions before opening those conditions. Keep the
present cohort permanently marked as opened. Prior art for affine/universal
kriging remains established; novelty and a broad accuracy claim are unresolved.
