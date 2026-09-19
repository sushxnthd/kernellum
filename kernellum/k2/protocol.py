from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Protocol


ACK = 0xA5
CMD_PING = 0x01
CMD_INFO = 0x02
CMD_LOAD_A = 0x10
CMD_LOAD_B = 0x11
CMD_RUN = 0x20
CMD_READ_CELL = 0x30
CMD_READ_CYCLES = 0x31


class ByteTransport(Protocol):
    def write(self, data: bytes) -> int | None: ...
    def read(self, size: int) -> bytes: ...


@dataclass(frozen=True)
class K2Info:
    rows: int
    cols: int
    k_tile: int
    clock_mhz: int


@dataclass(frozen=True)
class TrialResult:
    trial: int
    k_total: int
    chunks: int
    cycles: int
    expected_cycles: int
    correct: bool


class K2Link:
    def __init__(self, transport: ByteTransport):
        self.transport = transport
        self._info: K2Info | None = None

    def _write(self, payload: bytes) -> None:
        self.transport.write(payload)

    def _read_exact(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            chunk = self.transport.read(n - len(out))
            if not chunk:
                raise TimeoutError(f"expected {n} bytes, received {len(out)}")
            out.extend(chunk)
        return bytes(out)

    def _expect_ack(self, n_payload: int) -> bytes:
        data = self._read_exact(1 + n_payload)
        if data[0] != ACK:
            raise RuntimeError(f"device returned non-ACK response: {data.hex()}")
        return data[1:]

    def ping(self) -> bool:
        self._write(bytes([CMD_PING]))
        return self._expect_ack(2) == b"K2"

    def info(self) -> K2Info:
        self._write(bytes([CMD_INFO]))
        payload = self._expect_ack(4)
        self._info = K2Info(*payload)
        return self._info

    @property
    def hardware_info(self) -> K2Info:
        if self._info is None:
            return self.info()
        return self._info

    def load_a(self, address: int, values: list[int]) -> None:
        info = self.hardware_info
        if len(values) != info.rows:
            raise ValueError(f"A vector requires {info.rows} values")
        payload = bytes([CMD_LOAD_A, address & 0xFF] + [v & 0xFF for v in values])
        self._write(payload)
        response = self._expect_ack(1)
        if response != bytes([CMD_LOAD_A]):
            raise RuntimeError("LOAD_A acknowledgement mismatch")

    def load_b(self, address: int, values: list[int]) -> None:
        info = self.hardware_info
        if len(values) != info.cols:
            raise ValueError(f"B vector requires {info.cols} values")
        payload = bytes([CMD_LOAD_B, address & 0xFF] + [v & 0xFF for v in values])
        self._write(payload)
        response = self._expect_ack(1)
        if response != bytes([CMD_LOAD_B]):
            raise RuntimeError("LOAD_B acknowledgement mismatch")

    def run(self, k_len: int, *, clear: bool) -> int:
        self._write(bytes([CMD_RUN, k_len & 0xFF, 1 if clear else 0]))
        payload = self._expect_ack(4)
        return int.from_bytes(payload, "little", signed=False)

    def read_cycles(self) -> int:
        self._write(bytes([CMD_READ_CYCLES]))
        return int.from_bytes(self._expect_ack(4), "little", signed=False)

    def read_cell(self, row: int, col: int) -> int:
        self._write(bytes([CMD_READ_CELL, row & 0xFF, col & 0xFF]))
        return int.from_bytes(self._expect_ack(4), "little", signed=True)


def reference_gemm(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    if not a or not b:
        raise ValueError("matrices must be non-empty")
    m, k = len(a), len(a[0])
    if any(len(row) != k for row in a):
        raise ValueError("A is ragged")
    if len(b) != k:
        raise ValueError("inner dimensions do not match")
    n = len(b[0])
    if any(len(row) != n for row in b):
        raise ValueError("B is ragged")
    return [
        [sum(a[i][q] * b[q][j] for q in range(k)) for j in range(n)]
        for i in range(m)
    ]


def _upload_chunk(link: K2Link, a: list[list[int]], b: list[list[int]], start: int, length: int) -> None:
    info = link.hardware_info
    for q in range(length):
        link.load_a(q, [a[r][start + q] for r in range(info.rows)])
        link.load_b(q, [b[start + q][c] for c in range(info.cols)])


def run_one_gemm(link: K2Link, a: list[list[int]], b: list[list[int]]) -> tuple[list[list[int]], int, int]:
    info = link.hardware_info
    k_total = len(b)
    first = True
    offset = 0
    cycles = 0
    chunks = 0

    while offset < k_total:
        length = min(info.k_tile, k_total - offset)
        _upload_chunk(link, a, b, offset, length)
        cycles += link.run(length, clear=first)
        first = False
        chunks += 1
        offset += length

    result = [
        [link.read_cell(r, c) for c in range(info.cols)]
        for r in range(info.rows)
    ]
    return result, cycles, chunks


def run_random_trials(
    link: K2Link,
    *,
    trials: int = 100,
    seed: int = 20260919,
    max_abs_value: int = 3,
) -> list[TrialResult]:
    info = link.hardware_info
    rng = random.Random(seed)
    results: list[TrialResult] = []

    for trial in range(trials):
        if trial % 5 == 4:
            k_total = rng.randint(info.k_tile + 1, 2 * info.k_tile)
        else:
            k_total = rng.randint(1, info.k_tile)

        a = [
            [rng.randint(-max_abs_value, max_abs_value) for _ in range(k_total)]
            for _ in range(info.rows)
        ]
        b = [
            [rng.randint(-max_abs_value, max_abs_value) for _ in range(info.cols)]
            for _ in range(k_total)
        ]

        expected = reference_gemm(a, b)
        observed, cycles, chunks = run_one_gemm(link, a, b)
        expected_cycles = k_total + 1

        results.append(TrialResult(
            trial=trial,
            k_total=k_total,
            chunks=chunks,
            cycles=cycles,
            expected_cycles=expected_cycles,
            correct=observed == expected,
        ))
    return results
