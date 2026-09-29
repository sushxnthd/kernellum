import unittest
import numpy as np
from kernellum.discovery.design import METHODS, choose, features, fit, investigate, risk_scores
from experiments.discovery_design.run import evaluate, equations, data


class DiscoveryDesignTests(unittest.TestCase):
    def test_proxy_matches_every_explicit_refit(self):
        rng = np.random.default_rng(52)
        x = rng.uniform(-1, 1, (30, 2))
        phi = features(x)
        y = rng.normal(size=12)
        beta, inv = fit(phi[:12], y)
        targets = rng.normal(size=(3, 30))
        scores = risk_scores(phi, beta, inv, targets)
        for j in range(12, len(x)):
            deltas = []
            for target in targets:
                bnew, _ = fit(np.vstack([phi[:12], phi[j]]), np.r_[y, target[j]])
                deltas.append(np.mean((phi@beta-target)**2)-np.mean((phi@bnew-target)**2))
            self.assertAlmostEqual(scores[j], np.mean(deltas), places=9)

    def test_callback_budget_and_unique_queries_all_methods(self):
        x = np.random.default_rng(3).uniform(-1, 1, (40, 2))
        starts = []
        for method in METHODS:
            called = []
            def query(i):
                called.append(i)
                return x[i, 0]**3 + x[i, 1]
            selected, values = investigate(x, query, method, budget=16, seed=31)
            self.assertEqual(called, selected)
            self.assertEqual(len(set(called)), 16)
            self.assertEqual(len(values), 16)
            starts.append(selected[:12])
        self.assertTrue(all(s == starts[0] for s in starts))

    def test_selection_depends_only_on_observed_labels(self):
        x = np.random.default_rng(11).uniform(-1, 1, (30, 2))
        observed = list(range(12))
        y = x[:, 0]**3
        altered = y.copy()
        altered[12:] = 1e99
        for method in METHODS:
            a = choose(x, observed, y[observed], method, np.random.default_rng(1))
            b = choose(x, observed, altered[observed], method, np.random.default_rng(1))
            self.assertEqual(a, b)

    def test_invalid_measurements_and_exhausted_pool(self):
        x = np.zeros((13, 1))
        with self.assertRaises(ValueError):
            investigate(x, lambda i: float('nan'), budget=13)
        with self.assertRaises(ValueError):
            choose(x, list(range(13)), np.zeros(13), 'random', np.random.default_rng(1))
        with self.assertRaises(ValueError):
            choose(x, [0, 0], [1, 2], 'random', np.random.default_rng(1))

    def test_ast_has_no_executable_escape(self):
        x = np.ones((5, 1))
        for expression in ["__import__('os').system('false')", 'x.__class__', '[x for x in x]', 'sin(x, x)']:
            with self.assertRaises(ValueError):
                evaluate(expression, ['x'], x)
        np.testing.assert_allclose(evaluate('x**2+sin(x)', ['x'], x), 1+np.sin(1))

    def test_all_external_domains_are_finite(self):
        # Input/domain validation only; no comparative benchmark results inspected.
        spec = dict(pool_size=8, test_size=8)
        self.assertEqual(len(equations()), 52)
        for row in equations():
            x, y, xt, yt = data(row, 99, 0, spec)
            self.assertTrue(np.isfinite(y).all() and np.isfinite(yt).all())


if __name__ == '__main__':
    unittest.main()
