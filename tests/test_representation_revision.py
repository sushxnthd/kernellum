import unittest
import numpy as np
from kernellum.discovery.aggregation import simplex_stack,aggregate_weights
from kernellum.discovery.representation import RepresentationBank,invert_response,METHODS
from kernellum.discovery.revision import solve_model,ModelBank

class RepresentationTests(unittest.TestCase):
 def setUp(self):
  self.rng=np.random.default_rng(821)
  self.x=self.rng.uniform(1,5,(70,3));self.y=self.x[:,0]**1.3*self.x[:,1]**-.8*self.x[:,2]**.2

 def test_inverse_response(self):
  for y in (self.y,-self.y):
   kind='log_positive' if y[0]>0 else 'log_negative'
   np.testing.assert_allclose(invert_response(np.log(abs(y)),kind),y)

 def test_original_scale_loo_matches_explicit_refit(self):
  bank=RepresentationBank(self.x).fit(range(12),self.y[:12])
  for xkind in ('identity','log'):
   for ykind in ('identity','log_positive'):
    m=next(m for m in bank.models if m['input']==xkind and m['response']==ykind and m['family']=='rbf_medium' and m['ridge']==.001)
    k=bank.banks[xkind][0].kernels[m['family']]
    transformed=self.y[:12] if ykind=='identity' else np.log(self.y[:12])
    expected=[]
    for i in range(12):
     ids=[j for j in range(12) if j!=i]
     fit=solve_model(k[np.ix_(ids,ids)],transformed[ids],m['ridge'])
     val=fit['intercept']+k[i,ids]@fit['alpha']
     pred=invert_response(np.asarray(val),ykind)
     expected.append((self.y[i]-pred)/bank.yscale)
    np.testing.assert_allclose(m['error'],expected,atol=2e-7,rtol=2e-6)

 def test_power_law_prediction(self):
  bank=RepresentationBank(self.x).fit(range(32),self.y[:32])
  prediction=bank.predict(self.x[32:],'representation')
  self.assertLess(np.mean((prediction-self.y[32:])**2)/np.var(self.y[32:]),1e-8)

 def test_raw_model_matches_previous_bank(self):
  bank=RepresentationBank(self.x).fit(range(32),self.y[:32])
  base,lo,span=bank.banks['identity'];base.fit(range(32),self.y[:32])
  np.testing.assert_allclose(bank.predict(self.x,'raw'),base.predict(2*(self.x-lo)/span-1),rtol=1e-7,atol=1e-7)

 def test_mixed_sign_responses_disable_log_response(self):
  bank=RepresentationBank(self.x).fit(range(32),self.y[:32]-self.y[:32].mean())
  self.assertTrue(all(m['response']=='identity' for m in bank.models))

 def test_negative_power_law(self):
  bank=RepresentationBank(self.x).fit(range(32),-self.y[:32])
  self.assertLess(np.mean((bank.predict(self.x[32:])+self.y[32:])**2)/np.var(self.y[32:]),1e-8)

 def test_identity_duplicate_removed(self):
  x=self.rng.uniform(-1,1,(70,3));bank=RepresentationBank(x)
  self.assertEqual(list(bank.banks),['identity'])

 def test_all_methods_eligible_and_weights_valid(self):
  bank=RepresentationBank(self.x).fit(range(32),self.y[:32])
  for method in METHODS:
   _,w=bank.selected(method);self.assertAlmostEqual(w.sum(),1)
   self.assertTrue((w>=0).all());self.assertTrue(np.isfinite(bank.predict(self.x,method)).all())

 def test_simplex_qp_analytic_two_models(self):
  e=self.rng.normal(size=(40,2));delta=e[:,1]-e[:,0]
  t=np.clip(-np.mean(e[:,0]*delta)/np.mean(delta**2),0,1)
  np.testing.assert_allclose(simplex_stack(e),[1-t,t],atol=1e-9)

 def test_simplex_qp_kkt(self):
  e=self.rng.normal(size=(40,6));w=simplex_stack(e);g=e.T@e/len(e)@w
  active=w>1e-8;level=np.mean(g[active])
  np.testing.assert_allclose(g[active],level,atol=1e-8)
  self.assertTrue(np.all(g[~active]>=level-1e-8))

 def test_bootstrap_deterministic(self):
  e=self.rng.normal(size=(40,6));names=['linear','quadratic','cubic','rbf_short','rbf_medium','rbf_long']
  a=aggregate_weights(e,names,'conservative_10',2)
  np.testing.assert_array_equal(a,aggregate_weights(e,names,'conservative_10',2))

if __name__=='__main__':unittest.main()
