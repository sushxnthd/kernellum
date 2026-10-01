import unittest
import numpy as np
from kernellum.discovery.noise_revision import NoiseConsistentBank

class NoiseRevisionTests(unittest.TestCase):
 def test_weighted_loo_matches_refits_without_held_out_weight_scale(self):
  rng=np.random.default_rng(439);x=rng.uniform(1,4,(40,2));y=np.exp(.7*x[:14,0])+rng.normal(0,.1,14)
  bank=NoiseConsistentBank(x).fit(range(14),y)
  for xkind in ('identity','log'):
   model=next(m for m in bank.models if m['input']==xkind and m['response']=='log_positive' and m['family']=='rbf_medium' and m['ridge']==.001 and m['weighting']=='delta')
   expected=[]
   for i in range(3,14):
    ids=[j for j in range(14) if j!=i]
    other=NoiseConsistentBank(x).fit(ids,y[ids])
    fit=next(m for m in other.models if m['input']==xkind and m['response']=='log_positive' and m['family']=='rbf_medium' and m['ridge']==.001 and m['weighting']=='delta')
    self.assertEqual(other.anchor,bank.anchor)
    expected.append((y[i]-other.predict_model(fit,x[i:i+1])[0])/bank.yscale)
   np.testing.assert_allclose(model['error'][3:],expected,rtol=2e-5,atol=2e-7)
   self.assertAlmostEqual(model['original_cv'],np.mean(np.array(expected)**2),places=6)

 def test_mixed_sign_response_has_no_delta_log_models(self):
  x=np.random.default_rng(440).uniform(1,4,(40,2));y=x[:20,0]-2.5
  bank=NoiseConsistentBank(x).fit(range(20),y)
  self.assertTrue(all(m['weighting']=='uniform' for m in bank.models))
  np.testing.assert_array_equal(bank.predict(x,'noise_consistent'),bank.predict(x,'anchor_control'))

 def test_output_unit_change_preserves_predictions(self):
  rng=np.random.default_rng(441);x=rng.uniform(1,4,(40,2));y=np.exp(.7*x[:24,0])+rng.normal(0,.15,24)
  a=NoiseConsistentBank(x).fit(range(24),y);b=NoiseConsistentBank(x).fit(range(24),7*y)
  np.testing.assert_allclose(b.predict(x[24:]),7*a.predict(x[24:]),rtol=2e-6,atol=1e-6)

if __name__=='__main__':unittest.main()
