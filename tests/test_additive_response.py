import numpy as np
from scipy.optimize._numdiff import approx_derivative
from kernellum.discovery.additive_response import value_jacobian,fit_exp,AdditiveResponseBank


def test_analytic_derivatives_and_clean_gaussians():
    rng=np.random.default_rng(7)
    for d in (1,2,4):
        x=rng.uniform(-1,1,(40,d));theta=np.r_[.4,np.arange(d)*.1,np.ones(d*(d+1)//2)*.2]
        y,j=value_jacobian(theta,x,'exp_concave')
        np.testing.assert_allclose(j,approx_derivative(lambda p:value_jacobian(p,x,'exp_concave')[0],theta),rtol=1e-5,atol=1e-8)
        fit=fit_exp(x,y,'exp_concave')
        np.testing.assert_allclose(value_jacobian(fit,x,'exp_concave')[0],y,rtol=1e-6,atol=1e-7)


def test_negative_measurements_do_not_erase_positive_exponential_mean():
    rng=np.random.default_rng(39);pool=rng.uniform(-1,1,(70,2));ids=np.arange(24)
    y=np.exp(-7*np.sum(pool[ids]**2,axis=1))+rng.normal(0,.005,len(ids))
    assert np.any(y<0)
    bank=AdditiveResponseBank(pool).fit(ids,y)
    assert any(m['family']=='exp_concave' and m['response']=='additive_positive' for m in bank.models)
    model=next(m for m in bank.models if m['family']=='exp_concave' and m['response']=='additive_positive')
    # A selected model's held-out prediction agrees with fitting that fold alone.
    base=bank.banks[model['input']][0];x=base.x[ids];i=4;mask=np.arange(len(ids))!=i
    amplitude=max(float(abs(y[mask]).max()),1e-12)
    theta=fit_exp(x[mask],y[mask]/amplitude,'exp_concave')
    independently_held_out=amplitude*value_jacobian(theta,x[i:i+1],'exp_concave')[0][0]
    recorded_held_out=y[i]-bank.yscale*model['error'][i]
    np.testing.assert_allclose(recorded_held_out,independently_held_out,rtol=1e-10,atol=1e-12)
