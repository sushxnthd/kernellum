"""Pre-outcome fail-closed contract tests for the frozen v27 analysis.

These tests intentionally do not edit the preregistered experiment or its
historical analyzer. Expected failures document existing analysis risks.
Run: python -m unittest research/jmlr_v27/test_analysis_rejection_gates.py
"""
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("locked_v27_analysis", ROOT / "analyze_preregistered.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def record(arm, seed=0, task=0, k=2, status="ok"):
    return {
        "benchmark": "nyuv2", "method": "ls", "seed": seed,
        "arm": arm, "refine_task": -1 if arm == "coarse" else task,
        "clone_k": 1 if arm == "coarse" else k, "status": status,
        "metrics": {"delta_m": 0.0 if arm == "coarse" else 0.1},
        "semantic_scores": [0.5, 0.5, 0.5],
        "semantic_directions": [1, 1, 1],
    }


class RejectionGateContract(unittest.TestCase):
    def test_no_canonicalized_observations_must_not_pass(self):
        output = A.summarize([record("coarse"), record("refined")])
        self.assertFalse(output["canonicalized_gate_pass"],
                         "Canonicalized-null gate cannot pass with zero canonicalized cells")

    def test_missing_coarse_must_fail_closed(self):
        output = A.summarize([record("refined")])
        self.assertTrue(output.get("analysis_blocked"),
                        "An unmatched refined cell cannot silently disappear")

    def test_duplicate_success_must_fail_closed(self):
        output = A.summarize([record("coarse"), record("coarse"), record("refined")])
        self.assertTrue(output.get("analysis_blocked"),
                        "Duplicate successful keys cannot be overwritten silently")

    def test_infrastructure_failure_must_not_count_as_null(self):
        output = A.summarize([record("coarse"), record("refined", status="failed")])
        self.assertTrue(output.get("analysis_blocked"),
                        "Infrastructure failure cannot satisfy empirical completeness")

    def test_constant_nonzero_effect_must_serialize_strict_json(self):
        d = A.effect_size_paired([0.1] * 5)
        self.assertTrue(math.isfinite(d) or d is None,
                        "Undefined standardized effects need an explicit JSON-safe representation")
        json.dumps({"paired_effect_size": d}, allow_nan=False)

    def test_manifest_parent_k_schema_must_be_explicit(self):
        r = record("refined")
        r.pop("refine_task")
        r.pop("clone_k")
        r.update(parent=0, k=2)
        self.assertRaises((KeyError, ValueError), A.key, r)

    def test_five_distinct_paired_seeds_required(self):
        rows = [record("coarse", seed=s) for s in range(4)]
        rows += [record("refined", seed=s) for s in range(4)]
        output = A.summarize(rows)
        self.assertTrue(output.get("analysis_blocked"),
                        "Four seeds cannot be presented as five-seed confirmation")


    def test_canonicalized_opposite_signed_seed_errors_must_fail(self):
        rows = [record("coarse", seed=i) for i in range(5)]
        for i, delta in enumerate([0.01, -0.01, 0.0, 0.0, 0.0]):
            r = record("canonicalized", seed=i)
            r["metrics"]["delta_m"] = delta
            r["final_param_l2_to_coarse"] = 0.0
            rows.append(r)
        out = A.summarize(rows)
        self.assertTrue(out["analysis_blocked"])
        self.assertFalse(out["canonicalized_gate_pass"])
        self.assertEqual(sum(x["kind"] == "per_seed_canonicalization_violation"
                             for x in out["analysis_issues"]), 2)

    def test_missing_single_seed_parameter_distance_must_fail(self):
        rows = [record("coarse", seed=i) for i in range(5)]
        for i in range(5):
            r = record("canonicalized", seed=i)
            r["metrics"]["delta_m"] = 0.0
            if i != 2:
                r["final_param_l2_to_coarse"] = 0.0
            rows.append(r)
        out = A.summarize(rows)
        self.assertTrue(out["analysis_blocked"])
        self.assertTrue(any(x["kind"] == "missing_or_nonfinite_per_seed_canonicalization"
                            for x in out["analysis_issues"]))

    def test_failed_coarse_cannot_be_a_valid_parent(self):
        rows = [record("coarse", seed=0, status="failed"),
                record("refined", seed=0)]
        out = A.summarize(rows)
        self.assertTrue(out["analysis_blocked"])
        self.assertTrue(any(x["kind"] == "unmatched_or_failed_coarse"
                            for x in out["analysis_issues"]))
        self.assertEqual(out["paired_cells"], [])


    def test_missing_status_cannot_be_assumed_success(self):
        rows = [record("coarse", seed=i) for i in range(5)]
        rows += [record("refined", seed=i) for i in range(5)]
        for r in rows:
            r.pop("status")
        out = A.summarize(rows)
        self.assertTrue(out["analysis_blocked"],
                        "Absent execution status cannot certify a completed cell")
        self.assertTrue(any(x["kind"] == "missing_status"
                            for x in out["analysis_issues"]))

    def test_complete_one_group_is_not_complete_frozen_grid(self):
        rows = [record("coarse", seed=i) for i in range(5)]
        rows += [record("refined", seed=i) for i in range(5)]
        rows += [dict(record("canonicalized", seed=i),
                      final_param_l2_to_coarse=0.0) for i in range(5)]
        for r in rows:
            if r["arm"] == "canonicalized":
                r["metrics"]["delta_m"] = 0.0
        out = A.summarize(rows)
        self.assertTrue(out["analysis_blocked"],
                        "Five seeds in one group cannot certify the frozen NYUv2/QM9 grid")
        self.assertTrue(any(x["kind"] == "missing_preregistered_cells"
                            for x in out["analysis_issues"]))

if __name__ == "__main__":
    unittest.main()
