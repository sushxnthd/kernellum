#!/usr/bin/env python3
"""Frozen prospective evaluation of a fail-closed structural-start selector."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[2]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FR = load("selector_fr", "experiments/profile_critical_root_transfer/run.py")
HB = load("selector_hb", "experiments/himmelblau_four_basin_transfer/run.py")
FT = load("selector_ft", "experiments/residual_root_lattice/run.py")


@dataclass(frozen=True)
class Transform:
    angle: float
    scale_1: float
    scale_2: float
    shift_1: float
    shift_2: float


def prospective_transforms() -> list[Transform]:
    rng = np.random.default_rng(20261022)
    return [Transform(float(rng.uniform(-np.pi, np.pi)),
                      float(rng.uniform(0.45, 2.2)),
                      float(rng.uniform(0.45, 2.2)),
                      float(rng.uniform(-3.0, 3.0)),
                      float(rng.uniform(-3.0, 3.0))) for _ in range(12)]


def adapt(module, transform: Transform):
    return module.Transform(**asdict(transform))


def certificates() -> dict:
    profile_derivative = ((FR.P1 - FR.P2) * (FR.P1 - FR.P2) / 2).deriv()
    critical = profile_derivative.roots()
    real_critical = [float(root.real) for root in critical if abs(root.imag) < 1e-9]
    fr_candidates = FR.profile_candidates()
    profile = (FR.P1 - FR.P2) * (FR.P1 - FR.P2) / 2
    real_minima = [root for root in real_critical if profile.deriv(2)(root) > 1e-8]
    fr_valid = (
        len(critical) == profile_derivative.degree()
        and all(np.isfinite([root.real, root.imag]).all() for root in critical)
        and len(fr_candidates) == len(real_minima) == 2
        and all(np.isfinite(fr_candidates.ravel()))
        and len({tuple(np.round(row, 10)) for row in fr_candidates}) == 2
    )

    hb_roots = HB.ELIMINANT.roots()
    hb_candidates = HB.eliminant_candidates()
    hb_valid = (
        len(hb_roots) == HB.ELIMINANT.degree()
        and all(abs(root.imag) < 1e-9 for root in hb_roots)
        and len(hb_candidates) == 4
        and all(np.linalg.norm(HB.residual_z(z)) < 1e-8 for z in hb_candidates)
        and all(abs(np.linalg.det(HB.jacobian_z(z))) > 1e-6 for z in hb_candidates)
    )

    ft_candidates = FT.root_lattice()
    ft_stationary = [float(np.linalg.norm(FT.residual_z(z))) < 1e-8 for z in ft_candidates]
    ft_valid = all(ft_stationary)
    return {
        "freudenstein_roth": {"kind": "profile_complete", "passed": bool(fr_valid),
                              "candidates": len(fr_candidates),
                              "real_critical_roots": len(real_critical)},
        "himmelblau": {"kind": "zero_set_complete", "passed": bool(hb_valid),
                       "candidates": len(hb_candidates),
                       "real_eliminant_roots": int(sum(abs(root.imag) < 1e-9 for root in hb_roots))},
        "ftrig": {"kind": "none", "passed": bool(ft_valid),
                  "candidates": len(ft_candidates),
                  "zero_residual_candidates": int(sum(ft_stationary))},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("results/certificate_conditioned_selector.json"))
    args = parser.parse_args()
    certs = certificates()
    transforms = prospective_transforms()
    records = []
    for transform_id, transform in enumerate(transforms):
        fr_t = adapt(FR, transform)
        fr_truth = FR.profile_candidates()
        fr_selector = FR.run_starts(fr_truth, fr_t, fr_truth)
        fr_baseline = FR.run_starts(FR.generic_starts("maximin", 0), fr_t, fr_truth)
        records.append({"family": "freudenstein_roth", "transform_id": transform_id,
                        "activated": certs["freudenstein_roth"]["passed"],
                        "selector": fr_selector, "baseline": fr_baseline})

        hb_t = adapt(HB, transform)
        hb_truth = HB.eliminant_candidates()
        hb_selector = HB.run_starts(hb_truth, hb_t, hb_truth)
        hb_baseline = HB.run_starts(HB.starts("corner_maximin", 0), hb_t, hb_truth)
        records.append({"family": "himmelblau", "transform_id": transform_id,
                        "activated": certs["himmelblau"]["passed"],
                        "selector": hb_selector, "baseline": hb_baseline})

        ft_t = adapt(FT, transform)
        ft_baseline = FT.run_method("grid", transform_id, ft_t)
        records.append({"family": "ftrig", "transform_id": transform_id,
                        "activated": certs["ftrig"]["passed"],
                        "selector": ft_baseline, "baseline": ft_baseline})

    selector_nfev = sum(row["selector"]["nfev"] for row in records)
    baseline_nfev = sum(row["baseline"]["nfev"] for row in records)
    coverage_losses = int(sum(row["selector"]["coverage"] < row["baseline"]["coverage"]
                          if "coverage" in row["selector"]
                          else row["selector"]["distinct_minima"] < row["baseline"]["distinct_minima"]
                          for row in records))
    objective_losses = int(sum(row["selector"]["best_objective"] >
                               row["baseline"]["best_objective"] + 1e-12 for row in records))
    reduction = 1.0 - selector_nfev / baseline_nfev
    expected_routes = (certs["freudenstein_roth"]["passed"]
                       and certs["himmelblau"]["passed"]
                       and not certs["ftrig"]["passed"])
    if not expected_routes:
        gate = "KILL_ROUTE_MISMATCH"
    elif coverage_losses or objective_losses:
        gate = "KILL_PERFORMANCE_LOSS"
    elif reduction < 0.25:
        gate = "KILL_AGGREGATE_SAVINGS"
    else:
        gate = "PASS"
    by_family = {}
    for family in ("freudenstein_roth", "himmelblau", "ftrig"):
        rows = [row for row in records if row["family"] == family]
        selected = sum(row["selector"]["nfev"] for row in rows)
        baseline = sum(row["baseline"]["nfev"] for row in rows)
        by_family[family] = {"trials": len(rows), "activated": rows[0]["activated"],
                             "selector_nfev": selected, "baseline_nfev": baseline,
                             "evaluation_reduction": 1.0-selected/baseline}
    result = {
        "protocol": "certificate-conditioned-selector-v1",
        "transform_seed": 20261022,
        "certificates": certs,
        "transforms": [asdict(transform) for transform in transforms],
        "records": records,
        "summary": {"trials": len(records), "coverage_losses": coverage_losses,
                    "objective_losses": objective_losses,
                    "selector_nfev": selector_nfev, "baseline_nfev": baseline_nfev,
                    "evaluation_reduction": reduction, "by_family": by_family},
        "scientific_gate": gate,
    }
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"], "scientific_gate": gate},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
