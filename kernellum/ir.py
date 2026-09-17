from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np


@dataclass
class DenseLayerIR:
    name: str
    weight: np.ndarray  # shape: [input_dim, output_dim]
    bias: np.ndarray    # shape: [output_dim]
    relu: bool = False

    @property
    def input_dim(self) -> int:
        return int(self.weight.shape[0])

    @property
    def output_dim(self) -> int:
        return int(self.weight.shape[1])


@dataclass
class HardwareIR:
    input_name: str
    output_name: str
    input_dim: int
    layers: list[DenseLayerIR]

    @property
    def dims(self) -> tuple[int, ...]:
        return (self.input_dim,) + tuple(layer.output_dim for layer in self.layers)

    def validate(self) -> None:
        if not self.layers:
            raise ValueError("hardware IR contains no layers")
        expected = self.input_dim
        for i, layer in enumerate(self.layers):
            if layer.weight.ndim != 2:
                raise ValueError(f"layer {i} weight must be rank-2")
            if layer.bias.ndim != 1:
                raise ValueError(f"layer {i} bias must be rank-1")
            if layer.input_dim != expected:
                raise ValueError(
                    f"layer {i} input mismatch: expected {expected}, got {layer.input_dim}"
                )
            if layer.bias.shape[0] != layer.output_dim:
                raise ValueError(f"layer {i} bias/output mismatch")
            expected = layer.output_dim

    def summary(self) -> dict[str, Any]:
        return {
            "input_name": self.input_name,
            "output_name": self.output_name,
            "dims": list(self.dims),
            "layers": [
                {
                    "name": layer.name,
                    "input_dim": layer.input_dim,
                    "output_dim": layer.output_dim,
                    "relu": layer.relu,
                }
                for layer in self.layers
            ],
        }


@dataclass(frozen=True)
class FPGATarget:
    name: str
    family: str
    device: str
    package: str
    notes: str


FPGA_TARGETS: dict[str, FPGATarget] = {
    "ecp5-85f": FPGATarget(
        name="ecp5-85f",
        family="Lattice ECP5",
        device="LFE5U-85F",
        package="CABGA381/BG381-class target profile",
        notes=(
            "v0.2 alpha uses Yosys synth_ecp5 for family-mapped synthesis. "
            "Place-and-route, board pin constraints, timing closure and power measurement are not yet claimed."
        ),
    )
}
