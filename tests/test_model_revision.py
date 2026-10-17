import unittest
import numpy as np
from kernellum.discovery.revision import (ModelBank, solve_model, kernel, ivr_scores,
                                          ideal_scores, investigate, METHODS)


class ModelRevisionTests(unittest.TestCase):
    def setUp(self):
        self.rng=np.random.default_rng(13)
        self.x=self.rng.uniform(-1,1,(40,3))
        self.y=np.sin(self.x[:,0])+self.x[:,1]**2-.3*self.x[:,2]

    def test_loo_matches_explicit_leave_one_out_refits(self):
        k=kernel(self.x[:12],self.x[:12],'rbf_medium')
        y=self.y[:12]
        for ridge in (1e-6,1e-3,.1):
            model=solve_model(k,y,ridge)
            residuals=[]
            for i in range(len(y)):
                ids=[j for j in range(len(y)) if j!=i]
                refit=solve_model(k[np.ix_(ids,ids)],y[ids],ridge)
                pred=refit['intercept']+k[i,ids]@refit['alpha']
                residuals.append(y[i]-pred)
            np.testing.assert_allclose(model['loo'],residuals,rtol=1e-6,atol=1e-7)

    def test_integrated_variance_matches_explicit_trace_reduction(self):
        z=self.rng.normal(size=(17,8));c=z@z.T;noise=.03
        scores=ivr_scores(c,noise)
        explicit=[]
        for i in range(len(c)):
            updated=c-np.outer(c[:,i],c[:,i])/(c[i,i]+noise)
            explicit.append((np.trace(c)-np.trace(updated))/len(c))
        np.testing.assert_allclose(scores,explicit,atol=1e-12)

    def test_posterior_matches_augmented_intercept_solve(self):
        bank=ModelBank(self.x).fit(range(15),self.y[:15])
        for m in bank.models:
            k=bank.kernels[m['family']]
            a=np.block([[k[:15,:15]+m['ridge']*np.eye(15),np.ones((15,1))],
                        [np.ones((1,15)),np.zeros((1,1))]])
            cross=np.column_stack([k[:,:15],np.ones(len(k))])
            ref=k-cross@np.linalg.solve(a,cross.T)
            np.testing.assert_allclose(bank.posterior(m),ref,atol=1e-7)

    def test_mixture_covariance_is_symmetric_positive_semidefinite(self):
        bank=ModelBank(self.x).fit(range(16),self.y[:16])
        c,noise,_,w=bank.mixture()
        np.testing.assert_allclose(c,c.T,atol=1e-10)
        self.assertGreater(np.linalg.eigvalsh(c).min(),-1e-7)
        self.assertGreater(noise,0);self.assertAlmostEqual(w.sum(),1)

    def test_ideal_matches_scalar_definition(self):
        d=((self.x[:,None]-self.x[:10][None,:])**2).sum(2)
        pred=self.y+.1
        got=ideal_scores(d,pred,self.y[:10])
        expected=[]
        for i in range(len(self.x)):
            w=np.array([np.exp(-v)/max(v,1e-15) for v in d[i]])
            expected.append(sum(w*(pred[i]-self.y[:10])**2)/sum(w)+2/np.pi*np.arctan(1/sum(w)))
        np.testing.assert_allclose(got,expected)

    def test_budget_common_start_and_geometric_control_identity(self):
        traces={}
        for method in METHODS:
            calls=[]
            def query(i):
                self.assertNotIn(i,calls);calls.append(i);return self.y[i]
            ids,values,_=investigate(self.x,query,method,budget=20,initial=8,seed=5)
            self.assertEqual(calls,ids);self.assertEqual(len(ids),20)
            np.testing.assert_allclose(values,self.y[ids]);traces[method]=ids
        for ids in traces.values(): self.assertEqual(ids[:8],traces['mixture_ivr'][:8])
        self.assertEqual(traces['maximin'],traces['quadratic_maximin'])
        self.assertEqual(traces['maximin'],traces['rbf_maximin'])

    def test_label_affine_equivariance(self):
        a=ModelBank(self.x).fit(range(16),self.y[:16])
        b=ModelBank(self.x).fit(range(16),3*self.y[:16]+27)
        np.testing.assert_allclose(b.predict(self.x),3*a.predict(self.x)+27,atol=1e-7)
        self.assertEqual(a.models[0]['family'],b.models[0]['family'])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): ModelBank(np.array([[np.nan]]))
        with self.assertRaises(ValueError): ModelBank(self.x).fit([0,0,1],[1,2,3])
        with self.assertRaises(ValueError): investigate(self.x,lambda i:float('nan'),'maximin',20,initial=8)
        with self.assertRaises(ValueError): investigate(self.x,lambda i:1,'unknown',20)


if __name__=='__main__': unittest.main()
