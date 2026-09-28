import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kernellum.pilot import ROOT, load_spec, prior, choose, simulate_policy, latency, testbench, audit
from kernellum.k1.model import K1Architecture
from kernellum.k1.closed_loop import RoutedObservation


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.spec = ROOT / 'experiments/pilot_search/spec.json'
        self.s,self.pool = load_spec(self.spec)
        self.obs = prior(self.s)
        self.w = self.s['workloads'][1]

    def test_frozen_spec_has_16_routes_and_2_call_budget(self):
        self.assertEqual(len(self.pool)*len(self.s['seeds']),16)
        self.assertEqual(self.s['budget'],2)
        self.assertEqual(len(self.obs),17)

    def test_analytic_matches_hand_cycle_minimum(self):
        chosen = choose(self.pool,self.obs,self.w,'analytic')
        values = [(latency(self.w,a,1),a.name) for a in self.pool]
        self.assertEqual(chosen.name,min(values)[1])

    def test_callback_receives_only_selected_architectures(self):
        called=[]
        def evaluate(a):
            called.append(a.name)
            return {'eligible':True,'fmax_mhz':50}
        result=simulate_policy(self.pool,self.obs,self.w,'adaptive',2,evaluate)
        self.assertEqual(len(called),2)
        self.assertEqual(len(set(called)),2)
        self.assertEqual([x['candidate'] for x in result['trace']],called)

    def test_failed_routes_consume_budget(self):
        r=simulate_policy(self.pool,self.obs,self.w,'adaptive',2,lambda a:{'eligible':False,'fmax_mhz':50})
        self.assertEqual(r['route_calls'],2)
        self.assertIsNone(r['best_ms'])

    def test_nonfinite_callback_values_rejected(self):
        for value in (float('nan'),float('inf'),-1,0,None,'100'):
            r=simulate_policy(self.pool,self.obs,self.w,'adaptive',2,lambda a:{'eligible':True,'fmax_mhz':value})
            self.assertIsNone(r['best_ms'])

    def test_prior_and_pool_not_mutated(self):
        old=copy.deepcopy((self.pool,self.obs))
        simulate_policy(self.pool,self.obs,self.w,'adaptive',2,lambda a:{'eligible':True,'fmax_mhz':50})
        self.assertEqual((self.pool,self.obs),old)

    def test_adaptive_sees_feedback_static_does_not(self):
        for policy,expected_sizes in [('adaptive',[17,18]),('static',[17,17])]:
            seen=[]
            def fake_choose(pool,observations,w,p):
                seen.append(len(observations));return pool[0]
            with patch('kernellum.pilot.choose',side_effect=fake_choose):
                simulate_policy(self.pool,self.obs,self.w,policy,2,lambda a:{'eligible':True,'fmax_mhz':50})
            self.assertEqual(seen,expected_sizes)

    def test_invalid_spec_rejected(self):
        for change in ({'budget':9},{'seeds':[1103,1103]},{'target':'other'},
                       {'candidates':[{'rows':0,'cols':8,'k_tile':128}]},
                       {'candidates':[{'rows':8,'cols':8,'k_tile':127}]}):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'spec.json';p.write_text(json.dumps({**self.s,**change}))
                with self.assertRaises(ValueError):load_spec(p)

    def test_testbench_checks_every_output_and_accumulation(self):
        tb=testbench(K1Architecture('tiny',2,3,8))
        self.assertIn('R=2, C=3, K=8',tb)
        self.assertIn('for(r=0;r<R*C;r=r+1)',tb)
        self.assertIn('clear_before=(trial!=1)',tb)
        self.assertIn('$fatal(1,"TIMEOUT")',tb)

    def test_missing_evidence_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('builtins.print'):
                r=audit(self.spec,d,Path(d)/'summary.json')
            self.assertFalse(r['claim_supported'])
            self.assertFalse(r['complete_and_eligible'])
            self.assertEqual(len(r['missing']),16)


if __name__=='__main__':unittest.main()
