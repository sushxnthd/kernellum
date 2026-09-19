from kernellum.cost import Constraints
from kernellum.workload import named_workload
from kernellum.search import random_search, evolutionary_search
from kernellum.pareto import pareto_front

def test_search_returns_feasible_candidates():
    w = named_workload("ffn_expand", 64)
    c = Constraints(1200, 600)
    r = random_search(w, c, budget=80, seed=1)
    e, _ = evolutionary_search(w, c, budget=80, seed=1, population_size=16, elite_size=4)
    assert any(x.estimate.feasible for x in r)
    assert any(x.estimate.feasible for x in e)
    assert len(pareto_front(r)) > 0
    assert len(e) == 80

def test_evolutionary_budget_advances_past_stagnation():
    w = named_workload("qkv", 128)
    e, history = evolutionary_search(w, Constraints(), budget=300, seed=3, population_size=24, elite_size=6)
    assert len(e) == 300
    assert len(history) > 2
