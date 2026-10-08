from __future__ import annotations

import jax
import jax.numpy as jnp
from dfbench import AlgorithmType, Objective, OptimizationAlgorithm


def _row_clip(x, max_norm=1.0):
    x = jnp.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    norms = jnp.linalg.norm(x, axis=-1, keepdims=True)
    return x * jnp.minimum(1.0, max_norm / (norms + 1e-12))


def _candidate_rank(losses, feasible, penalty):
    safe_loss = jnp.nan_to_num(losses, nan=1e6, posinf=1e6, neginf=-1e6)
    safe_penalty = jnp.nan_to_num(penalty, nan=1e6, posinf=1e6, neginf=1e6)
    return jnp.where(feasible, safe_loss, 1000.0 + safe_penalty + 1e-3 * safe_loss)


def _choose_batch_and_warmup(obj):
    # BENCHMARK-ONLY CPU variant. The actual submission still prefers batch 8.
    preferred = (1,)
    last_error = None
    for batch_size in preferred:
        try:
            obj.warmup_vmap_value_and_grad_aux(batch_size=batch_size)
            return batch_size
        except Exception as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return 1


class KERNR3G(OptimizationAlgorithm):
    algorithm_str: str = "kern_r3g_v0_cpu_smoke"
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
        obj = objective
        _, key = self.prepare(obj, unbounded=True, random_seed=random_seed)

        batch_size = _choose_batch_and_warmup(obj)

        z = obj.random_params_unbounded(n_samples=batch_size)
        if init_params is not None:
            p0 = jnp.asarray(init_params)
            if p0.ndim == 1 and p0.shape[0] == obj.n_params:
                z = z.at[0].set(p0)

        lr_bank = jnp.asarray(
            [0.55, 0.72, 0.90, 1.00, 1.15, 1.32, 0.82, 1.08],
            dtype=z.dtype,
        )[:batch_size]

        m = jnp.zeros_like(z)
        v = jnp.zeros_like(z)
        age = jnp.zeros((batch_size,), dtype=jnp.int32)

        beta1 = 0.9
        beta2 = 0.997
        eps = 1e-8

        best_feasible_loss = jnp.asarray(jnp.inf, dtype=z.dtype)
        best_feasible_z = z[0]
        best_any_loss = jnp.asarray(jnp.inf, dtype=z.dtype)
        best_any_z = z[0]

        iteration = 0
        obj.start_logging()

        while not obj.budget_exceeded:
            z_eval = z
            losses, grads, aux = obj.vmap_value_and_grad_aux(z_eval)
            losses = jnp.asarray(losses)
            grads = _row_clip(jnp.asarray(grads), max_norm=1.0)

            feasible = jnp.asarray(aux["is_feasible"], dtype=bool)
            penalty = jnp.asarray(aux.get("penalty", jnp.zeros_like(losses)))
            finite = jnp.isfinite(losses)

            feasible_scores = jnp.where(feasible & finite, losses, jnp.inf)
            f_idx = jnp.argmin(feasible_scores)
            f_loss = feasible_scores[f_idx]
            f_better = f_loss < best_feasible_loss
            best_feasible_loss = jnp.minimum(best_feasible_loss, f_loss)
            best_feasible_z = jnp.where(f_better, z_eval[f_idx], best_feasible_z)

            any_scores = jnp.where(finite, losses, jnp.inf)
            a_idx = jnp.argmin(any_scores)
            a_loss = any_scores[a_idx]
            a_better = a_loss < best_any_loss
            best_any_loss = jnp.minimum(best_any_loss, a_loss)
            best_any_z = jnp.where(a_better, z_eval[a_idx], best_any_z)

            iteration += 1
            progress = min(float(obj.budget_progress_fraction), 1.0)

            base_lr = 0.0020 + 0.0180 * (1.0 - progress) ** 1.15
            age = age + 1
            m = beta1 * m + (1.0 - beta1) * grads
            v = beta2 * v + (1.0 - beta2) * (grads * grads)

            age_f = age.astype(z.dtype)[:, None]
            mhat = m / (1.0 - jnp.power(beta1, age_f))
            vhat = v / (1.0 - jnp.power(beta2, age_f))
            direction = mhat / (jnp.sqrt(vhat) + eps)
            z = z_eval - (base_lr * lr_bank[:, None]) * direction
            z = jnp.clip(z, -12.0, 12.0)

            if iteration % 24 == 0 and not obj.budget_exceeded and batch_size >= 4:
                rank = _candidate_rank(losses, feasible & finite, penalty)
                order = jnp.argsort(rank)

                keep = max(3, int(round(0.75 * batch_size)))
                keep = min(keep, batch_size - 1)
                keep_idx = order[:keep]

                z_keep = z[keep_idx]
                m_keep = m[keep_idx]
                v_keep = v[keep_idx]
                age_keep = age[keep_idx]
                lr_keep = lr_bank[keep_idx]

                n_new = batch_size - keep
                have_feasible = jnp.isfinite(best_feasible_loss)
                center = jnp.where(have_feasible, best_feasible_z, best_any_z)

                key, sub = jax.random.split(key)
                radius = max(0.015, 0.75 * (1.0 - progress) ** 1.8)
                clones = center[None, :] + radius * jax.random.normal(
                    sub, (n_new, obj.n_params), dtype=z.dtype
                )
                clones = jnp.clip(clones, -12.0, 12.0)

                if progress < 0.45 and n_new >= 1:
                    random_z = obj.random_params_unbounded(n_samples=1)
                    clones = clones.at[-1].set(random_z[0])

                z = jnp.concatenate([z_keep, clones], axis=0)
                m = jnp.concatenate([m_keep, jnp.zeros_like(clones)], axis=0)
                v = jnp.concatenate([v_keep, jnp.zeros_like(clones)], axis=0)
                age = jnp.concatenate(
                    [age_keep, jnp.zeros((n_new,), dtype=jnp.int32)], axis=0
                )

                refill_lr = jnp.asarray(
                    [1.25, 0.68, 1.05, 0.86, 1.40, 0.60, 1.12, 0.95],
                    dtype=z.dtype,
                )[:n_new]
                lr_bank = jnp.concatenate([lr_keep, refill_lr], axis=0)
