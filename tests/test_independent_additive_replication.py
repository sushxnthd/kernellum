import numpy as np

from scripts.independent_additive_replication import fit, mean


def test_independent_concave_fit_recovers_signed_gaussian_shape():
    rng = np.random.default_rng(8841)
    x = rng.uniform(-1, 1, (80, 2))
    target = np.exp(0.3 + x @ np.array([0.4, -0.2]) - 1.7 * x[:, 0] ** 2 - 0.8 * x[:, 1] ** 2)
    theta, objective, _ = fit(x, target, "exp_concave")
    prediction = mean(theta, x, "exp_concave", 700.0)
    assert objective < 1e-14
    np.testing.assert_allclose(prediction, target, rtol=1e-7, atol=1e-9)


def test_independent_concave_parameterization_cannot_add_positive_curvature():
    rng = np.random.default_rng(771)
    x = rng.uniform(-1, 1, (50, 3))
    target = np.exp(-np.sum(x * x, axis=1))
    theta, _, _ = fit(x, target, "exp_concave")
    dimension = x.shape[1]
    lower = np.zeros((dimension, dimension))
    lower[np.tril_indices(dimension)] = theta[1 + dimension :]
    log_hessian = -2.0 * lower @ lower.T
    assert np.linalg.eigvalsh(log_hessian).max() <= 1e-12
