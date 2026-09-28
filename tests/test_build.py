import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from kernellum.build import build
from kernellum.pilot import ROOT


class BuildTests(unittest.TestCase):
    def test_analytical_default_needs_no_prior_and_executes_exact_budget(self):
        def fake_route(a,seed,s,spec,out):
            return dict(name=a.name,rows=a.rows,cols=a.cols,k_tile=a.k_tile,seed=seed,
                        synth_ok=True,route_ok=True,eligible=True,fmax_mhz=50,
                        timing_metric='post_route_report_json',resources=dict(dsp=a.pe_count,bram=8,lut4=100,ff=1000))
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run'
            with patch('kernellum.build.route',side_effect=fake_route) as backend,patch('kernellum.build.prior') as prior:
                r=build(ROOT/'experiments/pilot_search/spec.json',out,workload='expand',seed=1103)
            self.assertEqual(backend.call_count,2)
            prior.assert_not_called()
            self.assertEqual(r['policy'],'analytic')
            self.assertEqual(r['new_route_calls'],2)
            self.assertTrue((out/'report.html').is_file())

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'new output'):
                build(ROOT/'experiments/pilot_search/spec.json',d,workload='expand',seed=1103)

    def test_unknown_workload_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('kernellum.build.route') as backend:
                with self.assertRaises(ValueError):
                    build(ROOT/'experiments/pilot_search/spec.json',Path(d)/'run',workload='unknown',seed=1103)
                backend.assert_not_called()


if __name__=='__main__':unittest.main()
