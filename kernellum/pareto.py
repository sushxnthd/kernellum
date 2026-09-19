from __future__ import annotations
from kernellum.search.common import Candidate

def pareto_front(candidates: list[Candidate]) -> list[Candidate]:
    feasible = [c for c in candidates if c.estimate.feasible]
    feasible.sort(key=lambda c: (c.estimate.latency_ms, c.estimate.dsp, c.estimate.bram))
    dsp_levels = sorted({c.estimate.dsp for c in feasible})
    best_bram_at = {d: float("inf") for d in dsp_levels}
    out: list[Candidate] = []
    for c in feasible:
        ce = c.estimate
        dominated = min((best_bram_at[d] for d in dsp_levels if d <= ce.dsp), default=float("inf")) <= ce.bram
        if not dominated:
            out.append(c)
        if ce.bram < best_bram_at[ce.dsp]:
            best_bram_at[ce.dsp] = ce.bram
    return out
