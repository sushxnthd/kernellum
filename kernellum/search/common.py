from __future__ import annotations
from dataclasses import dataclass
from kernellum.architecture import Architecture
from kernellum.cost import Estimate

@dataclass(frozen=True)
class Candidate:
    architecture: Architecture
    estimate: Estimate
    objective: float

    def to_dict(self) -> dict:
        return {**self.architecture.to_dict(), **self.estimate.to_dict(), "objective": self.objective}
