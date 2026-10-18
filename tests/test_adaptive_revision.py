import unittest
import numpy as np
from kernellum.discovery.adaptive_revision import AdaptiveStack
from kernellum.discovery.representation import RepresentationBank


class AdaptiveTests(unittest.TestCase):
    def test_threshold_and_choice_are_observation_only(self):
        rng = np.random.default_rng(128)
        x = rng.uniform(1, 5, (50, 2)); y = x[:, 0]**1.3 / x[:, 1]
        stack = AdaptiveStack(RepresentationBank(x).fit(range(25), y[:25]))
        before = (stack.spread_threshold, stack.loo_spread.copy())
        pred, info = stack.predict(x[25:])
        self.assertTrue(np.isfinite(pred).all())
        self.assertEqual(stack.spread_threshold, before[0])
        np.testing.assert_array_equal(stack.loo_spread, before[1])
        self.assertEqual(info['spread_threshold'], stack.spread_threshold)

    def test_finite_on_invalid_log_domain(self):
        rng = np.random.default_rng(129)
        x = rng.uniform(1, 5, (50, 2)); y = x[:, 0]**1.3 / x[:, 1]
        stack = AdaptiveStack(RepresentationBank(x).fit(range(25), y[:25]))
        pred, _ = stack.predict(np.array([[-1., 2.], [0., 3.]]))
        self.assertTrue(np.isfinite(pred).all())


if __name__ == '__main__':
    unittest.main()
