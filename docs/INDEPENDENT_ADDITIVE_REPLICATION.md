# Independent additive-response replication: balanced partial PASS

> Superseded for broad replication by `INDEPENDENT_ADDITIVE_FULL_RESULT.md`.
> The full 120-path audit finds four noisy 4-D solver-dependent disagreements;
> this 20-path slice remains valid but is not representative of the full cohort.

## Smallest supported claim

A separately written implementation reproduces the scoped signed-Gaussian
exponential fitting result on a balanced, predetermined 20-path slice of the
opened confirmation data. It agrees with the persisted candidate on the winning
family and sign in **20/20** paths. At the experiment's unchanged `1e-8` NMSE
comparison floor, its geometric predictive-error ratio to the candidate is:

| Domain | Independent / candidate NMSE | Gate status |
|---|---:|---|
| Inside measured domain | 1.0000028 | partial replication PASS |
| Near shell | 0.9999981 | partial replication PASS |
| Far shell | 0.9999957 | partial replication PASS |

The slice balances positive and negative Gaussian responses, dimensions 2 and
4, clean and noisy observations, and two predetermined seeds. All eight clean
inside-domain paths retain NMSE at or below `1e-8`.

## Independence boundary

The replication script does not import or call the candidate `fit_exp`,
`value_jacobian`, runner, or model bank. It reconstructs the written mean,
normalization, fold amplitudes, 64 exact leave-one-out refits, model selection,
and predictions. Its initializer is independently parameterized through a full
symmetric log-quadratic projection and conditional linear refit. It evaluates
L-BFGS-B and a numerical three-point least-squares route; the latter attained
the lower objective on all 20 full fits and 1,280 fold fits.

This is an independent implementation by the same research process, not an
external replication. It uses already-opened evidence, so it strengthens
numerical reproducibility but creates no new confirmation evidence.

## Residual and limitations

The full frozen scoped claim used 120 Gaussian paths and the augmented adaptive
ensemble, whereas this audit covers 20 paths and reconstructs the exponential-
only winner. The exact candidate prediction is reproduced, but the surrounding
kernel-stack aggregation is not independently rebuilt here. Clean fits below
the comparison floor cannot be meaningfully ranked by raw error ratios.

No scientific novelty, physical transfer, or field breakthrough follows.
Established nonlinear least squares remains the relevant prior art. The NIST
transfer and broad synthetic gates remain FAIL.

## Reproduction

From commit `949d69b1de5284a106d6ce99ab6bc95f71bb2ab6` plus this branch:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python scripts/independent_additive_replication.py \
  --out /tmp/kernellum-independent-replay --limit 20
pytest -q tests/test_independent_additive_replication.py
```

Canonical outputs are under
`results/additive_response/independent_replication/`. The next discriminating
action is to complete all 120 frozen Gaussian paths, then freeze genuinely new
external/shifted conditions separating correct additive-noise likelihood from
mere Gaussian-family matching.
