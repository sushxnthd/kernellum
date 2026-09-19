from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class GEMMWorkload:
    name: str
    m: int
    n: int
    k: int

    @property
    def macs(self) -> int:
        return self.m * self.n * self.k

    def to_dict(self) -> dict:
        return asdict(self)

def tiny_transformer_suite(hidden: int = 312, ffn: int = 1200, seq_lengths=(64, 128, 256)) -> list[GEMMWorkload]:
    """Representative GEMMs for a small Transformer encoder."""
    out: list[GEMMWorkload] = []
    for s in seq_lengths:
        out.extend([
            GEMMWorkload(f"s{s}_qkv", s, 3 * hidden, hidden),
            GEMMWorkload(f"s{s}_attn_out", s, hidden, hidden),
            GEMMWorkload(f"s{s}_ffn_expand", s, ffn, hidden),
            GEMMWorkload(f"s{s}_ffn_contract", s, hidden, ffn),
        ])
    return out

def named_workload(name: str, seq: int = 128) -> GEMMWorkload:
    h, f = 312, 1200
    table = {
        "qkv": GEMMWorkload(f"s{seq}_qkv", seq, 3*h, h),
        "attn_out": GEMMWorkload(f"s{seq}_attn_out", seq, h, h),
        "ffn_expand": GEMMWorkload(f"s{seq}_ffn_expand", seq, f, h),
        "ffn_contract": GEMMWorkload(f"s{seq}_ffn_contract", seq, h, f),
    }
    if name not in table:
        raise ValueError(f"unknown workload {name!r}; choose one of {sorted(table)}")
    return table[name]
