import unittest
import numpy as np
from kernellum.discovery.revision import kernel
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import solve_trend, TrendBank


class TrendTests(unittest.TestCase):
    def test_press_matches_actual_leave_one_out_refits(self):
        rng=np.random.default_rng(839)
        x=rng.normal(size=(19,3)); y=np.sin(x[:,0])+x[:,1]**2
        k=kernel(x,x,'rbf_medium'); m=solve_trend(k,x,y,.001)
        predictions=[]
        for i in range(len(x)):
            mask=np.arange(len(x))!=i
            fit=solve_trend(k[np.ix_(mask,mask)],x[mask],y[mask],.001)
            predictions.append(np.r_[1.,x[i]]@fit['beta']+k[i,mask]@fit['alpha'])
        np.testing.assert_allclose(y-m['loo'],predictions,rtol=2e-8,atol=2e-8)

    def test_affine_trend_preserves_power_law_extrapolation(self):
        x=np.column_stack((np.geomspace(1,9,30),np.linspace(2,5,30)))
        bank=RepresentationBank(x).fit(range(25),3*x[:25,0]**1.7/x[:25,1]**.8)
        trend=TrendBank(bank)
        m=next(m for m in trend.models if m['trend']=='affine' and m['input']=='log'
               and m['response']=='log_positive' and m['family']=='rbf_short')
        xt=np.array([[30.,.5],[.2,14.]])
        np.testing.assert_allclose(trend.predict_model(m,xt),3*xt[:,0]**1.7/xt[:,1]**.8,rtol=1e-7)

    def test_bounded_correction_under_far_extrapolation(self):
        rng=np.random.default_rng(840);x=rng.normal(size=(24,2));y=np.sin(x[:,0])+x[:,1]
        k=kernel(x,x,'rbf_short');m=solve_trend(k,x,y,.01)
        xt=rng.normal(size=(100,2))*100
        correction=kernel(xt,x,'rbf_short')@m['alpha']
        self.assertLessEqual(float(abs(correction).max()),m['correction_bound']+1e-12)

    def test_selection_frozen_and_log_polynomial_tails_excluded(self):
        rng=np.random.default_rng(841);x=rng.uniform(1,6,(55,2));y=np.exp(np.sin(x[:,0])+x[:,1]/2)
        trend=TrendBank(RepresentationBank(x).fit(range(40),y[:40]))
        before=trend.describe('trend_stack');trend.predict(x[40:])
        self.assertEqual(before,trend.describe('trend_stack'))
        self.assertFalse(any(m['response']!='identity' and m['family'] in ('quadratic','cubic') for m in trend.models))

    def test_rank_deficiency_declines_affine_candidate(self):
        x=np.ones((12,2))
        with self.assertRaises(ValueError):solve_trend(kernel(x,x,'rbf_short'),x,np.arange(12.),.01)


if __name__=='__main__':unittest.main()
