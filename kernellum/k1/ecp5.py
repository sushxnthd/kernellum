from __future__ import annotations

from math import ceil
from kernellum.k1.model import K1Architecture


def dp16kd_word_width(depth: int) -> int:
    """Maximum practical DP16KD word width for a requested memory depth."""
    if depth <= 512:
        return 36
    if depth <= 1024:
        return 18
    if depth <= 2048:
        return 9
    if depth <= 4096:
        return 4
    if depth <= 8192:
        return 2
    if depth <= 16384:
        return 1
    raise ValueError("depth exceeds one DP16KD address space")


def predicted_mult18x18d(arch: K1Architecture, precision_bits: int = 8) -> int:
    if precision_bits > 18:
        raise ValueError("K1 ECP5 model only covers <=18-bit single-DSP multiplies")
    return arch.rows * arch.cols


def predicted_dp16kd(arch: K1Architecture, precision_bits: int = 8) -> int:
    width_per_block = dp16kd_word_width(arch.k_tile)
    a_width = arch.rows * precision_bits
    b_width = arch.cols * precision_bits
    return ceil(a_width / width_per_block) + ceil(b_width / width_per_block)
