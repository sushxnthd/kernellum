from __future__ import annotations
import random
from kernellum.architecture import Architecture, design_axes
from kernellum.cost import Constraints, estimate, scalar_objective
from kernellum.workload import GEMMWorkload
from .common import Candidate

def _random_arch(rng: random.Random) -> Architecture:
    axes = design_axes()
    return Architecture(**{k: rng.choice(v) for k, v in axes.items()})

def _mutate(a: Architecture, rng: random.Random) -> Architecture:
    axes = design_axes()
    d = a.to_dict()
    n_mut = 1 if rng.random() < 0.78 else 2
    for key in rng.sample(list(axes), n_mut):
        vals = [v for v in axes[key] if v != d[key]]
        d[key] = rng.choice(vals)
    return Architecture(**d)

def evolutionary_search(w: GEMMWorkload, c: Constraints, budget: int = 2000, seed: int = 0, population_size: int = 48, elite_size: int = 12) -> tuple[list[Candidate], list[float]]:
    rng = random.Random(seed)
    cache: dict[Architecture, Candidate] = {}

    def evaluate(a: Architecture) -> Candidate:
        if a not in cache:
            e = estimate(w, a, c)
            cache[a] = Candidate(a, e, scalar_objective(e, c))
        return cache[a]

    population: list[Architecture] = []
    while len(population) < population_size and len(cache) < budget:
        a = _random_arch(rng)
        if a not in cache:
            population.append(a)
            evaluate(a)

    history: list[float] = []
    while len(cache) < budget:
        ranked = sorted((evaluate(a) for a in population), key=lambda x: x.objective)
        elites = [x.architecture for x in ranked[:min(elite_size, len(ranked))]]
        history.append(ranked[0].objective)
        next_pop = elites.copy()

        attempts = 0
        while len(next_pop) < population_size and len(cache) < budget and attempts < population_size * 40:
            attempts += 1
            child = _mutate(rng.choice(elites), rng)
            if child in cache:
                continue
            next_pop.append(child)
            evaluate(child)

        attempts = 0
        while len(next_pop) < population_size and len(cache) < budget and attempts < population_size * 200:
            attempts += 1
            child = _random_arch(rng)
            if child in cache:
                continue
            next_pop.append(child)
            evaluate(child)

        if len(next_pop) == len(elites):
            break
        population = next_pop

    ranked_all = sorted(cache.values(), key=lambda x: x.objective)
    if ranked_all:
        history.append(ranked_all[0].objective)
    return ranked_all, history
