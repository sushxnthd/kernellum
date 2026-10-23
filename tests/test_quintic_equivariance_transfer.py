from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
PATH = ROOT / "experiments/quintic_equivariance_transfer/run.py"
SPEC = spec_from_file_location("quintic_equivariance_transfer", PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_certificate_margins_and_holdout_are_frozen():
    pilot, holdout = MODULE.regimes()
    assert len(pilot) == 20
    assert len(holdout) == 23
    assert not (set(pilot) & set(holdout))
    assert MODULE.FACE_MARGIN == Fraction(1063, 3072)
    assert MODULE.MONOTONICITY_MARGIN == Fraction(149, 256)


def test_orbit_starts_transport_exactly_on_every_unseen_regime():
    _, holdout = MODULE.regimes()
    for numerators in holdout:
        weights = np.asarray(numerators, dtype=float) / MODULE.WEIGHT_DENOMINATOR
        batched, calls = MODULE.orbit_starts(weights)
        unbatched = MODULE.unbatched_starts(weights)
        assert calls == 32
        np.testing.assert_array_equal(batched, unbatched)


def test_symmetry_breaking_forcing_abstains_before_construction():
    rows = MODULE.negative_controls()
    assert len(rows) == 8
    assert all(not row["activated"] for row in rows)
    assert all(row["reason"] == "FAILED_PROOF_OBLIGATION" for row in rows)
    assert all(row["construction_calls"] == 0 for row in rows)


def test_committed_transfer_artifact_passes_all_frozen_gates():
    data = json.loads((ROOT / "results/quintic_equivariance_transfer.json").read_text())
    assert data["gate_pass"]
    assert data["decision"] == "TRANSFER_SURVIVES"
    assert Fraction(data["exact_work_reduction"]) == Fraction(477, 1165)
    selected = data["summary"]["orbit_batched_certified"]
    assert selected["full_complete"] == selected["capped_complete"] == 23
    assert selected["capped_catastrophes"] == 0

