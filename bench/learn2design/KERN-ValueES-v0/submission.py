from __future__ import annotations

import math
import jax
import jax.numpy as jnp
from dfbench import AlgorithmType, Objective, OptimizationAlgorithm


class KERNValueES(OptimizationAlgorithm):
    """Low-memory value-only basin explorer for real-UIFO diagnostics.

    This branch is intentionally derivative-free so it can run on a CPU runner.
    It keeps exact evaluated points, ranks feasibility first, searches at several
    radii around the best observed point, and reserves one slot for global
    exploration each generation.
    """

    algorithm_str: str = "kern_value_es_v0"
    algorithm_type: AlgorithmType = AlgorithmType.EVOLUTIONARY

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

        try:
            obj.warmup_value_aux()
        except AttributeError:
            obj.warmup_value()

        pop_size = 6
        z = obj.random_params_unbounded(n_samples=pop_size)
        if init_params is not None:
            p0 = jnp.asarray(init_params)
            if p0.ndim == 1 and p0.shape[0] == obj.n_params:
                z = z.at[0].set(p0)

        best_feasible_loss = math.inf
        best_feasible_z = None
        best_rank = math.inf
        best_any_loss = math.inf
        generation = 0

        obj.start_logging()

        while not obj.budget_exceeded:
            records = []
            for i in range(pop_size):
                if obj.budget_exceeded:
                    break
                z_eval = z[i]
                loss, aux = obj.value_aux(z_eval)
                loss_f = float(loss)
                feasible = bool(aux["is_feasible"])
                penalty = float(aux["penalty"])

                if math.isfinite(loss_f):
                    best_any_loss = min(best_any_loss, loss_f)
                    if feasible and loss_f < best_feasible_loss:
                        best_feasible_loss = loss_f
                        best_feasible_z = z_eval

                if feasible and math.isfinite(loss_f):
                    rank = loss_f
                else:
                    safe_penalty = penalty if math.isfinite(penalty) else 1e12
                    safe_loss = loss_f if math.isfinite(loss_f) else 1e6
                    rank = 1e6 + safe_penalty + 1e-6 * safe_loss

                best_rank = min(best_rank, rank)
                records.append((rank, z_eval))

            if not records or obj.budget_exceeded:
                break

            records.sort(key=lambda x: x[0])
            center = best_feasible_z if best_feasible_z is not None else records[0][1]

            generation += 1
            progress = min(float(obj.budget_progress_fraction), 1.0)
            envelope = max(0.08, 1.0 - 0.88 * progress)
            scales = (0.12, 0.30, 0.65, 1.30)
            next_points = [center]
            for scale in scales:
                key, sub = jax.random.split(key)
                step = (scale * envelope) * jax.random.normal(
                    sub, (obj.n_params,), dtype=center.dtype
                )
                next_points.append(jnp.clip(center + step, -12.0, 12.0))

            global_z = jnp.asarray(obj.random_params_unbounded(n_samples=1))
            if global_z.ndim == 2:
                global_z = global_z[0]
            next_points.append(global_z)
            z = jnp.stack(next_points, axis=0)

            if generation <= 3 or generation % 5 == 0:
                bf = best_feasible_loss if math.isfinite(best_feasible_loss) else float("nan")
                print(
                    f"KERN_VALUE_ES generation={generation} "
                    f"best_feasible={bf:.12g} best_any={best_any_loss:.12g} "
                    f"progress={progress:.4f}"
                )
