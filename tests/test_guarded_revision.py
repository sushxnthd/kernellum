import unittest
import numpy as np
from kernellum.discovery.guarded import GuardedRepresentationBank
from kernellum.discovery.representation import METHODS

class GuardedTests(unittest.TestCase):
 def test_loo_bounds_exclude_held_out_extreme(self):
  x=np.random.default_rng(915).uniform(1,3,(30,2));y=x[:12,0]**2;y[-1]=100
  bank=GuardedRepresentationBank(x).fit(range(12),y)
  for family in ('linear','rbf_medium'):
   model=next(m for m in bank.models if m['input']=='identity' and m['response']=='identity' and m['family']==family and m['ridge']==.001)
   actual=[]
   for i in range(12):
    ids=[j for j in range(12) if j!=i]
    other=GuardedRepresentationBank(x).fit(ids,y[ids])
    fit=next(m for m in other.models if m['input']=='identity' and m['response']=='identity' and m['family']==family and m['ridge']==.001)
    actual.append((y[i]-other.predict_model(fit,x[i:i+1])[0])/bank.yscale)
   np.testing.assert_allclose(model['error'],actual,atol=1e-7,rtol=1e-6)
   self.assertGreater(model['error'][-1],2)

 def test_output_bound_also_holds_outside_pool(self):
  x=np.random.default_rng(916).uniform(1,3,(50,2));y=np.exp(2*x[:24,0])
  bank=GuardedRepresentationBank(x).fit(range(24),y)
  xt=np.array([[1e-8,1e-8],[100,200]])
  for method in METHODS:
   p=bank.predict(xt,method)
   self.assertTrue(np.isfinite(p).all())
   self.assertTrue((p>=bank.bounds[0]-1e-10).all() and (p<=bank.bounds[1]+1e-10).all())

if __name__=='__main__':unittest.main()
