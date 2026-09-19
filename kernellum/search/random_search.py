from __future__ import annotations
import random
from kernellum.architecture import Architecture, design_axes
from kernellum.cost import Constraints, estimate, scalar_objective
from kernellum.workload import GEMMWorkload
from .common import Candidate

def _sample(rng: random.Random) -> Architecture:
    axes = design_axes()
    return Architecture(**{k: rng.choice(v) for k, v in axes.items()})

def random_search(w: GEMMWorkload, c: Constraints, budget: int = 2000, seed: int = 0) -> list[Candidate]:
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < budget:
        a = _sample(rng)
        if a in seen:
            continue
        seen.add(a)
        e = estimate(w, a, c)
        out.append(Candidate(a, e, scalar_objective(e, c)))
    return out
