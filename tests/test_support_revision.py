import unittest
import numpy as np
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.support_revision import SupportRouter, latent_variance, METHODS


class SupportTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(492)
        self.x = rng.uniform(1, 4, (40, 2))
        self.y = self.x[:, 0]**1.3 * self.x[:, 1]**-.7
        self.bank = RepresentationBank(self.x).fit(range(20), self.y[:20])

    def test_loo_variance_matches_augmented_system(self):
        for family in ('linear', 'cubic', 'rbf_medium'):
            m = next(m for m in self.bank.models if m['input']=='log' and m['family']==family and m['ridge']==.001)
            k = self.bank.banks['log'][0].kernels[family][:20, :20]
            expected = []
            for i in range(20):
                ids = [j for j in range(20) if j != i]
                a = np.block([[k[np.ix_(ids,ids)] + .001*np.eye(19), np.ones((19,1))],
                              [np.ones((1,19)), np.zeros((1,1))]])
                v = np.r_[k[i,ids], 1.]
                expected.append(k[i,i] - v @ np.linalg.solve(a, v))
            variance, bound = latent_variance(self.bank, m, self.x[:20])
            self.assertAlmostEqual(bound, max(expected), places=8)
            self.assertTrue(np.all(variance <= bound + 1e-8))

    def test_nonlinear_rule_preserves_power_law_extrapolation(self):
        xt = np.array([[8., 9.], [12., .4]])
        self.assertEqual(self.bank.selected('representation')[0][0]['family'], 'linear')
        pred, info = SupportRouter(self.bank, xt).predict('support_nonlinear_leverage')
        np.testing.assert_array_equal(pred, self.bank.predict(xt))
        self.assertEqual(info['any_routed_fraction'], 0.)
        _, box = SupportRouter(self.bank, xt).predict('support_box')
        self.assertEqual(box['any_routed_fraction'], 1.)

    def test_invalid_log_domain_falls_back_without_evaluating_log(self):
        xt = np.array([[-1., 2.], [0., 3.]])
        router = SupportRouter(self.bank, xt)
        for method in METHODS:
            with self.subTest(method=method):
                pred, _ = router.predict(method)
                self.assertTrue(np.isfinite(pred).all())
                if not method.endswith('_stack'):
                    np.testing.assert_array_equal(pred, self.bank.predict(xt, 'raw'))

    def test_raw_selected_component_is_unchanged(self):
        bank = RepresentationBank(self.x).fit(range(20), self.y[:20])
        bank.models = bank.eligible('raw')
        xt = np.array([[8., 9.], [-2., .4]])
        router = SupportRouter(bank, xt)
        for method in METHODS:
            with self.subTest(method=method):
                pred, info = router.predict(method)
                original = 'representation_stack' if method.endswith('_stack') else 'representation'
                np.testing.assert_array_equal(pred, bank.predict(xt, original))
                self.assertEqual(info['any_routed_fraction'], 0.)

    def test_linear_variance_matches_small_feature_system(self):
        m = next(m for m in self.bank.models if m['input']=='log' and m['family']=='linear' and m['ridge']==1e-6)
        base, lo, span = self.bank.banks['log']
        norm = np.sqrt(self.x.shape[1]*base.normalizers['linear'])
        features = base.x[self.bank.ids]/norm
        test = (2*(np.log(self.x)-lo)/span-1)/norm
        centered = features-features.mean(0)
        residual = test-features.mean(0)
        precision = np.eye(2)+centered.T@centered/m['ridge']
        expected = m['ridge']/len(features)+np.sum((residual@np.linalg.inv(precision))*residual,axis=1)
        actual, _ = latent_variance(self.bank,m,self.x)
        np.testing.assert_allclose(actual,expected,rtol=1e-8,atol=2e-14)


if __name__ == '__main__':
    unittest.main()
