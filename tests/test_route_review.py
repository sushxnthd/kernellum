import csv
import tempfile
import unittest
from pathlib import Path

from kernellum.route_review import review, render_html


class RouteReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.limits = dict(dsp=120, bram=10, lut4=10000, ff=10000)

    def row(self, name="base", **changes):
        row = dict(name=name, rows=4, cols=4, k_tile=16, transport="broadcast",
                   synth_ok="True", route_ok="True", fmax_mhz=50,
                   timing_metric="post_route_report_json", nextpnr_returncode=0,
                   synth_dsp=16, synth_bram=2, synth_lut4=200, synth_ff=600, seed="")
        return {**row, **changes}

    def write(self, rows, filename="routes.csv"):
        path = self.root / filename
        with path.open("w") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        return path

    def check(self, rows, **kwargs):
        return review([self.write(rows)], m=4, n=4, k=16, baseline="base",
                      max_resources=self.limits, **kwargs)

    def test_hand_calculated_latency_and_comparison(self):
        r = self.check([self.row(), self.row("fast", fmax_mhz=100)])
        # One output tile: 2*16 + 3*1 + 2 = 37 cycles.
        self.assertAlmostEqual(r["ranking"][0]["worst_observed_latency_ms"], 37 / 100000)
        self.assertAlmostEqual(r["latency_reduction_vs_baseline_pct"], 50)
        self.assertTrue(r["ranking"][0]["pareto"])
        self.assertFalse(r["ranking"][1]["pareto"])

    def test_failed_attempt_rejects_candidate_even_with_successful_attempt(self):
        r = self.check([self.row(), self.row("fast", seed=1, fmax_mhz=100),
                        self.row("fast", seed=2, route_ok="False", fmax_mhz=200)])
        self.assertEqual(r["best_supplied_candidate"], "base")
        self.assertEqual(r["rejected"][0]["name"], "fast")

    def test_nonfinite_and_nonpositive_fmax_never_rank(self):
        for value in ("NaN", "inf", "-inf", 0, -1):
            with self.subTest(value=value):
                r = self.check([self.row(), self.row("bad", fmax_mhz=value)])
                self.assertEqual(r["eligible_count"], 1)

    def test_bad_timing_labels_and_return_codes_rejected(self):
        for change in ({"timing_metric": "estimated"}, {"nextpnr_returncode": 1},
                       {"synth_ff": -3}, {"synth_dsp": 1.5}, {"rows": 0},
                       {"transport": "unknown"}):
            with self.subTest(change=change):
                self.assertEqual(self.check([self.row(), self.row("bad", **change)])["eligible_count"], 1)

    def test_resource_limit_rejects_fast_candidate(self):
        r = self.check([self.row(), self.row("fast", fmax_mhz=100, synth_dsp=121)])
        self.assertEqual(r["best_supplied_candidate"], "base")

    def test_missing_baseline_does_not_invent_gain(self):
        r = self.check([self.row("other")])
        self.assertEqual(r["status"], "baseline_unavailable")
        self.assertIsNone(r["latency_reduction_vs_baseline_pct"])

    def test_empty_feasible_set_has_no_recommendation(self):
        r = self.check([self.row(synth_dsp=121)])
        self.assertIsNone(r["best_supplied_candidate"])

    def test_worst_observation_and_peak_resources(self):
        r = self.check([self.row(seed=1, fmax_mhz=100),
                        self.row(seed=2, fmax_mhz=40, synth_ff=700)], min_observations=2)
        a = r["ranking"][0]
        self.assertEqual(a["worst_observed_fmax_mhz"], 40)
        self.assertEqual(a["peak_synthesis_resources"]["ff"], 700)

    def test_repeated_unseeded_or_duplicate_seed_cannot_inflate_evidence(self):
        for seed in ("", "2"):
            r = self.check([self.row(seed=seed), self.row(seed=seed)])
            self.assertEqual(r["eligible_count"], 0)

    def test_duplicate_contents_across_files_are_rejected(self):
        p = self.write([self.row()])
        q = self.write([self.row()], "copy.csv")
        with self.assertRaisesRegex(ValueError, "duplicate input"):
            review([p, q], m=1, n=1, k=1, baseline="base", max_resources=self.limits)

    def test_conflicting_geometry_rejects_candidate(self):
        r = self.check([self.row(seed=1), self.row(seed=2, rows=8)])
        self.assertEqual(r["eligible_count"], 0)

    def test_html_escapes_untrusted_candidate_names(self):
        r = self.check([self.row(), self.row('<script>alert(1)</script>', fmax_mhz=100)])
        page = render_html(r)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_missing_columns_fail(self):
        row = self.row()
        del row["timing_metric"]
        with self.assertRaisesRegex(ValueError, "missing columns"):
            self.check([row])

    def test_observation_floor(self):
        self.assertEqual(self.check([self.row()], min_observations=2)["eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
