import unittest
import numpy as np
from kernellum.discovery.robust_revision import combine, RobustStack
from kernellum.discovery.representation import RepresentationBank


class RobustTests(unittest.TestCase):
    def test_median_ignores_extreme_minority_weight(self):
        values=np.array([[1.,2.,1e100],[-1e100,-2.,-1.]])
        np.testing.assert_array_equal(combine(values,[.2,.6,.2],'median'),[2.,-2.])

    def test_geometric_sign_and_mixed_sign_fallback(self):
        values=np.array([[1.,9.],[-1.,-9.],[-1.,9.],[0.,4.]])
        np.testing.assert_allclose(combine(values,[.5,.5],'geometric'),[3.,-3.,4.,2.])

    def test_zero_weight_component_does_not_change_sign_domain(self):
        np.testing.assert_allclose(combine(np.array([[1.,9.,-3.]]),[.5,.5,0.],'geometric'),[3.])

    def test_choice_is_fixed_before_prediction(self):
        rng=np.random.default_rng(123)
        x=rng.uniform(1,5,(50,2)); y=x[:,0]**1.3/x[:,1]
        stack=RobustStack(RepresentationBank(x).fit(range(25),y[:25]))
        before=stack.describe()
        result=stack.predict(x[25:])
        self.assertEqual(before,stack.describe())
        self.assertEqual(stack.choice,min(stack.cv,key=stack.cv.get))
        self.assertTrue(all(np.isfinite(v).all() for v in result.values()))


if __name__=='__main__': unittest.main()
