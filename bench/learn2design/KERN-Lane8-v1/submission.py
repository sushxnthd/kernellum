from __future__ import annotations

import jax
import jax.numpy as jnp
from dfbench import AlgorithmType, Objective, OptimizationAlgorithm


def _row_clip(x, max_norm: float = 1.0):
    x = jnp.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    norms = jnp.linalg.norm(x, axis=-1, keepdims=True)
    return x * jnp.minimum(1.0, max_norm / (norms + 1e-12))


def _pair_properties(pair):
    if (
        isinstance(pair, (list, tuple))
        and len(pair) >= 2
        and isinstance(pair[0], str)
        and isinstance(pair[1], str)
    ):
        pairs = [pair]
    elif isinstance(pair, (list, tuple)):
        pairs = pair
    else:
        pairs = []
    return {
        str(item[1])
        for item in pairs
        if isinstance(item, (list, tuple)) and len(item) >= 2
    }


def _feasibility_anchor(obj: Objective):
    """Conservative low-power bounded-unit point mapped to active space."""
    unit = jnp.full((obj.n_params,), 0.5)
    for i, pair in enumerate(obj.optimization_pairs):
        props = _pair_properties(pair)
        if "power" in props or "db" in props:
            unit = unit.at[i].set(1e-7)
        elif "reflectivity" in props:
            unit = unit.at[i].set(1e-3)
        elif "mass" in props:
            unit = unit.at[i].set(0.995)
    unit = jnp.clip(unit, 1e-7, 1.0 - 1e-7)
    return jnp.log(unit) - jnp.log1p(-unit)


def _batch_size(obj: Objective) -> int:
    # Official H100 measurements support substantially larger gradient batches
    # on representative size-3 UIFOs. Keep headroom for larger hidden problems.
    if jax.default_backend() == "cpu":
        return 1
    if obj.n_params <= 230:
        return 8
    if obj.n_params <= 285:
        return 6
    return 4


class KERNLane8(OptimizationAlgorithm):
    """Persistent heterogeneous Adam lanes with exact evaluated-point archiving.

    Design choices are intentionally conservative: no periodic population reset,
    one feasibility anchor, otherwise independent random starts, and fixed
    heterogeneous learning rates. Long-lived lanes preserve late improvements.
    """

    algorithm_str: str = "kern_lane8_v1"
    algorithm_type: AlgorithmType = AlgorithmType.GRADIENT_BASED

    def __init__(self) -> None:
        pass

    def optimize(
        self,
        objective: Objective,
        init_params=None,
        random_seed: int | None = None,
        **kwargs,
    ) -> None:
        del kwargs
        obj = objective
        self.prepare(obj, unbounded=True, random_seed=random_seed)

        batch_size = _batch_size(obj)
        if batch_size == 1:
            obj.warmup_value_and_grad_aux()
        else:
            obj.warmup_vmap_value_and_grad_aux(batch_size=batch_size)

        z = obj.random_params_unbounded(n_samples=batch_size)
        if z.ndim == 1:
            z = z[None, :]

        next_slot = 0
        if init_params is not None:
            supplied = jnp.asarray(init_params)
            if supplied.ndim == 1 and supplied.shape[0] == obj.n_params:
                z = z.at[0].set(supplied)
                next_slot = 1

        if next_slot < batch_size:
            z = z.at[next_slot].set(_feasibility_anchor(obj))

        # Heterogeneous fixed lane rates. The range is intentionally broad so
        # topology-dependent curvature does not reduce the run to one step scale.
        lrs = jnp.geomspace(0.03, 0.15, batch_size)[:, None].astype(z.dtype)

        m = jnp.zeros_like(z)
        v = jnp.zeros_like(z)
        age = jnp.zeros((batch_size,), dtype=jnp.int32)
        beta1 = 0.9
        beta2 = 0.999
        eps = 1e-8

        # Exact evaluated-point archive: never associate a score with post-step z.
        best_feasible_loss = jnp.asarray(jnp.inf, dtype=z.dtype)
        best_feasible_z = z[0]

        obj.start_logging()

        while not obj.budget_exceeded:
            z_eval = z
            if batch_size == 1:
                loss, grad, aux = obj.value_and_grad_aux(z_eval[0])
                losses = jnp.asarray(loss)[None]
                grads = jnp.asarray(grad)[None, :]
                feasible = jnp.asarray(aux["is_feasible"], dtype=bool)[None]
            else:
                losses, grads, aux = obj.vmap_value_and_grad_aux(z_eval)
                losses = jnp.asarray(losses)
                grads = jnp.asarray(grads)
                feasible = jnp.asarray(aux["is_feasible"], dtype=bool)

            # Ensure device work is complete before the next wall-clock budget test.
            jax.block_until_ready(losses)

            finite = jnp.isfinite(losses)
            feasible_scores = jnp.where(feasible & finite, losses, jnp.inf)
            f_idx = jnp.argmin(feasible_scores)
            f_loss = feasible_scores[f_idx]
            improved = f_loss < best_feasible_loss
            best_feasible_loss = jnp.minimum(best_feasible_loss, f_loss)
            best_feasible_z = jnp.where(improved, z_eval[f_idx], best_feasible_z)

            grads = _row_clip(grads, max_norm=1.0)
            age = age + 1
            m = beta1 * m + (1.0 - beta1) * grads
            v = beta2 * v + (1.0 - beta2) * jnp.square(grads)

            age_f = age.astype(z.dtype)[:, None]
            mhat = m / (1.0 - jnp.power(beta1, age_f))
            vhat = v / (1.0 - jnp.power(beta2, age_f))
            direction = mhat / (jnp.sqrt(vhat) + eps)
            z = jnp.clip(z_eval - lrs * direction, -14.0, 14.0)
