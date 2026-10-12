"""Print every clean-room exponential candidate for one opened path."""
import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.independent_additive_replication import fit_with_loo


def main(function: str, seed: int, noise: float) -> None:
    evidence = ROOT / "results/additive_response/confirmation"
    reference = None
    with gzip.open(evidence / "traces.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if (row["function"] == function and row["seed"] == seed
                    and float(row["noise"]) == noise and row["domain"] == "inside"
                    and row["method"] == "exponential_only"):
                reference = row
                break
    if reference is None:
        raise ValueError("path not found")
    arrays = np.load(evidence / "inputs_and_truth.npz")
    pool = arrays[f"{function}_{seed}_pool"]
    selected = np.asarray(reference["selected"], dtype=int)
    observed = np.asarray(reference["observed"], dtype=float)
    span = np.maximum(pool.max(axis=0) - pool.min(axis=0), 1e-12)
    x = 2.0 * (pool[selected] - pool.min(axis=0)) / span - 1.0
    results = []
    for sign in (1, -1):
        for family in ("exp_affine", "exp_concave"):
            try:
                model = fit_with_loo(x, observed, sign, family)
                results.append({"sign": sign, "family": family, "cv": model["cv"],
                                "objective": model["objective"], "solver": model["solver"],
                                "fold_solvers": model["fold_solvers"]})
            except Exception as exc:
                results.append({"sign": sign, "family": family, "error": str(exc)})
    print(json.dumps({"function": function, "seed": seed, "noise": noise,
                      "candidate_winner": reference["models"][0], "independent": results},
                     indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("function")
    parser.add_argument("seed", type=int)
    parser.add_argument("noise", type=float)
    args = parser.parse_args()
    main(args.function, args.seed, args.noise)
