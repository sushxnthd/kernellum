import unittest
import numpy as np
from kernellum.discovery.representation_acquisition import investigate,METHODS

class AcquisitionTests(unittest.TestCase):
 def test_every_method_queries_only_budgeted_distinct_labels(self):
  x=np.random.default_rng(281).uniform(1,3,(40,2));y=x[:,0]**1.3/x[:,1]
  initial=np.random.default_rng(917).choice(len(x),8,replace=False).tolist()
  for method in METHODS:
   with self.subTest(method=method):
    called=[]
    def query(i):called.append(i);return y[i]
    ids,values,revisions=investigate(x,query,method,budget=16,initial=8,seed=917)
    self.assertEqual(ids,called);self.assertEqual(ids[:8],initial)
    self.assertEqual(len(ids),16);self.assertEqual(len(set(ids)),16)
    np.testing.assert_array_equal(values,y[ids])
    self.assertTrue(all(v['budget']<16 for v in revisions))

 def test_maximin_matches_independent_geometry(self):
  x=np.random.default_rng(282).normal(size=(40,3));ids=np.random.default_rng(918).choice(40,8,replace=False).tolist()
  z=2*(x-x.min(0))/np.ptp(x,axis=0)-1
  while len(ids)<20:
   available=[i for i in range(40) if i not in ids]
   ids.append(max(available,key=lambda i:min(np.dot(z[i]-z[j],z[i]-z[j]) for j in ids)))
  actual,_,_=investigate(x,lambda i:float(x[i].sum()),'maximin',budget=20,initial=8,seed=918)
  self.assertEqual(actual,ids)

 def test_nonfinite_initial_observation_rejected_even_for_random(self):
  x=np.random.default_rng(283).normal(size=(40,3))
  with self.assertRaises(ValueError):investigate(x,lambda i:float('nan'),'random',budget=16,initial=8)

if __name__=='__main__':unittest.main()
