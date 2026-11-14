# V27 implementation calibration ledger

Date: 2026-11-14

## Released MGDA scaling

Pinned source: `OptMN-Lab/FairGrad@b58bce810e57288f7bf2c4c9effb7133b856739a`.

The released `MGDA.get_weighted_loss` computes the minimum-norm simplex solution and then executes:

```python
sol = sol * self.n_tasks  # make sure it sums to self.n_tasks
weighted_loss = sum([losses[i] * sol[i] for i in range(len(sol))])
```

Therefore the released implementation is not exact-clone invariant as a full update vector when the declared task count changes. The convex-hull solution/direction can remain invariant while the update scale changes by represented task count. This is the same implementation-atomicity distinction already recognized in the theory manuscript and must remain explicit in the standard-benchmark campaign.

## Benchmark treatment

Two objects are kept distinct:

1. **Released MGDA** — exact pinned code, including `sol *= n_tasks`. It is included in Tier A implementation calibration and reported as such.
2. **Canonical MGDA** — same pinned gradient extraction and minimum-norm solver, but the returned weighted loss is divided by represented `n_tasks`, restoring the mathematical simplex combination whose weights sum to one. This is the invariant control named in the frozen preregistration and is explicitly labeled as a canonical-rule control, not the unmodified released implementation.

No other method is silently renormalized.

## Preflight evidence

The initial five-method smoke check found a nonzero exposed/coarse update difference for released MGDA under exact cloning, which led to this source audit. The result is preserved rather than treated as a failed test.

The canonical MGDA control must satisfy an exact-clone full-update null within numerical solver tolerance before any standard-benchmark outcome is interpreted.
