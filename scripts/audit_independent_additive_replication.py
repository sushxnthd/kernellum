"""Independently audit persisted clean-room additive-response records.

This audit intentionally imports neither the candidate fitter nor the clean-room
runner.  It uses only Python's standard library to recompute the decisive
counts and aggregates from immutable JSON records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = ROOT / "results/additive_response/independent_replication_full"
DOMAINS = ("inside", "near_shell", "far_shell")
COMPARISON_FLOOR = math.log(1e-8)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def recompute(result: Path) -> dict:
    records = json.loads((result / "records.json").read_text())
    keys = [(row["function"], row["seed"], row["noise"]) for row in records]
    if len(keys) != len(set(keys)):
        raise AssertionError("duplicate experimental paths")
    if any("winner" not in row for row in records):
        raise AssertionError("one or more paths did not reproduce")

    ratios = {}
    for domain in DOMAINS:
        deltas = [
            max(row["scores"][domain]["independent_log_nmse"], COMPARISON_FLOOR)
            - max(row["scores"][domain]["candidate_log_nmse"], COMPARISON_FLOOR)
            for row in records
        ]
        ratios[domain] = {
            "independent_over_candidate_geometric_nmse": math.exp(statistics.fmean(deltas)),
            "median_log_ratio": statistics.median(deltas),
            "paths": len(deltas),
        }

    return {
        "paths_attempted": len(records),
        "paths_reproduced": len(records),
        "candidate_winner_agreement": sum(bool(row["winner_agrees"]) for row in records),
        "candidate_winner_trials": len(records),
        "by_domain": ratios,
        "clean_inside_exact": sum(
            row["noise"] == 0.0
            and row["scores"]["inside"]["independent_log_nmse"] <= COMPARISON_FLOOR
            for row in records
        ),
        "clean_paths": sum(row["noise"] == 0.0 for row in records),
    }


def verify(result: Path) -> dict:
    observed = recompute(result)
    recorded = json.loads((result / "summary.json").read_text())
    for key in (
        "paths_attempted",
        "paths_reproduced",
        "candidate_winner_agreement",
        "candidate_winner_trials",
        "clean_inside_exact",
        "clean_paths",
    ):
        if observed[key] != recorded[key]:
            raise AssertionError(f"summary mismatch for {key}: {observed[key]} != {recorded[key]}")
    for domain in DOMAINS:
        for key in ("independent_over_candidate_geometric_nmse", "median_log_ratio"):
            if not math.isclose(
                observed["by_domain"][domain][key],
                recorded["by_domain"][domain][key],
                rel_tol=1e-13,
                abs_tol=1e-15,
            ):
                raise AssertionError(f"summary mismatch for {domain}.{key}")

    manifest = json.loads((result / "manifest.json").read_text())
    source_manifest = manifest.get("source_manifest", manifest)
    evidence = ROOT / "results/additive_response/confirmation"
    for name, expected in source_manifest["input_sha256"].items():
        actual = sha256(evidence / name)
        if actual != expected:
            raise AssertionError(f"input hash mismatch for {name}: {actual} != {expected}")
    return {"status": "PASS", **observed, "input_hashes_verified": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.result), indent=2))
