from __future__ import annotations
from kernellum.architecture import default_design_space
from kernellum.cost import Constraints, estimate, scalar_objective
from kernellum.workload import GEMMWorkload
from .common import Candidate

def exhaustive_search(w: GEMMWorkload, c: Constraints) -> list[Candidate]:
    out = []
    for a in default_design_space():
        e = estimate(w, a, c)
        out.append(Candidate(a, e, scalar_objective(e, c)))
    return out
