# Coupled phi4 certified routing: frozen value gate failed

## Decision

**Kill this route as the next KERNELLUM flagship under the preregistered 25%
end-to-end work gate.** Do not lower the threshold.

The structural mechanism itself transferred: all 544 sign boxes across 17
unopened rational coupling regimes certified one unique strict zero-residual
minimum, and the one-step certified Newton route recovered all 32 minima in
every full and capped (`max_nfev=4`) run. The operational gain was real but too
small after charging certificate refinement.

## Frozen results

| Method | Full complete regimes | Capped complete regimes | Capped catastrophes | End-to-end evaluations |
|---|---:|---:|---:|---:|
| Certified one-step Newton | 17/17 | 17/17 | 0 | 5,208 |
| Tensor corners | 17/17 | 0/17 | 17 | 6,552 |
| Optimized LHS | 0/17 | 0/17 | 17 | 7,825 |
| Greedy maximin | 0/17 | 0/17 | 17 | 7,157 |

The strongest control preserving full uncapped coverage was tensor corners.
The certified route reduced end-to-end work by exactly `224/1092 = 20.5128%`,
below the frozen 25% threshold. Its capped catastrophe reduction was 100%, and
ordinary zero-residual performance was retained, but the aggregate value gate
still fails.

## Exact structural result

For the five-site open-chain residual

`F_i=x_i^3-x_i + sum_j w_ij(x_i-x_j)`

with positive adjacent weights at most `1/16`, every sign box
`s_i x_i in [3/4,5/4]` contains one unique zero. On the inner face the
uncoupled magnitude is `21/64`; the coupling is at most `5/16`, leaving strict
margin `1/64`. Poincare--Miranda gives existence. In sign coordinates the
Jacobian is symmetric and strictly diagonally dominant positive definite,
giving uniqueness. The squared-residual Hessian at each zero is `2J^T J`, so
all 32 zeros are strict minima.

The independent Fraction-only audit rederived both exact margins, recomputed
all aggregate counts, recovered the exact work fraction, and confirmed the
frozen gate failure without importing the experiment.

## Alternative explanation and boundary

The failure is not lack of predictive signal. The certificate perfectly
predicted which method would survive the capped solver. The shortfall comes
from honest end-to-end accounting: one residual and one Jacobian evaluation
per box consumed 1,088 calls across the 17 regimes. Excluding that overhead
would overstate deployable value and is prohibited by the protocol.

The tensor-corner control also proves that sign-box geometry itself is not a
general basin-discovery advantage; it attains complete uncapped coverage. The
certificate's advantage is bounded-cost convergence, not identification of
otherwise unreachable minima.

## Priority audit

Discrete phi4 lattices and their stationary/metastable configurations are
established subjects (for example Dmitriev et al., 2001,
https://pubmed.ncbi.nlm.nih.gov/11580417/). Interval Newton methods classically
combine Newton iteration and interval analysis to prove existence and
uniqueness (Kearfott, 1998,
https://interval.louisiana.edu/preprints/EoO/KEARFO01.pdf). Poincare--Miranda
existence arguments are also classical; Gasull and Manosa use the theorem to
locate isolated points in algebraic dynamical systems
(https://arxiv.org/abs/1809.06208).

No novelty is claimed for those ingredients. The supported result is a
prospective KERNELLUM routing boundary with exact certification and honest
cost accounting.

## Project consequence and next kernel

Do not integrate this route as the positive flagship. Preserve the box
certificate as a safe capped-solver primitive, but the next kernel must reduce
certificate overhead rather than seek another low-dimensional basin family.
The sharp target is a **batched certificate amortization law**: determine when
one shared interval/Jacobian proof can certify an entire symmetry orbit of
starts, and prospectively require total work reduction above 25% with the same
tail guarantee. If orbit batching cannot cross the frozen threshold without
weakening safety, kill structural-start routing as a fleet mechanism.

## Reproduction

```bash
python experiments/coupled_phi4_certified_routing/run.py
python scripts/audit_coupled_phi4_certified_routing.py
PYTHONPATH=. python -m pytest -q tests/test_coupled_phi4_certified_routing.py
```
