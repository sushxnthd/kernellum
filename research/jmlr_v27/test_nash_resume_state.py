#!/usr/bin/env python3
"""Check that the state we persist for Nash-MTL is sufficient for epoch-boundary resume."""
from __future__ import annotations
import copy, random, sys, tempfile
from pathlib import Path
import numpy as np
import torch

def make():
    from methods.weight_methods import WeightMethods
    p=torch.nn.Parameter(torch.tensor([0.15,-0.25,0.4],dtype=torch.float32))
    wm=WeightMethods("nashmtl",n_tasks=2,device=torch.device("cpu"),
                     optim_niter=20,update_weights_every=1,max_norm=0.0)
    opt=torch.optim.Adam([p],lr=1e-2)
    sched=torch.optim.lr_scheduler.StepLR(opt,step_size=3,gamma=0.8)
    return p,wm,opt,sched

def losses(p,step):
    # Deterministic but changing geometry, like successive minibatches.
    a=torch.tensor([0.7+0.01*step,-0.1,0.2],dtype=p.dtype)
    b=torch.tensor([-0.3,0.5-0.02*step,-0.4],dtype=p.dtype)
    return torch.stack((((p-a)**2).sum()+0.4, ((p-b)**2).sum()+0.7))

def one_step(p,wm,opt,sched,step):
    opt.zero_grad()
    L=losses(p,step)
    wm.backward(losses=L,shared_parameters=[p],
                task_specific_parameters=[p],last_shared_parameters=[p],
                representation=p.reshape(1,-1))
    opt.step()
    sched.step()

def snap(p,wm,opt,sched):
    m=wm.method
    return dict(
        p=p.detach().clone(),
        optimizer=copy.deepcopy(opt.state_dict()),
        scheduler=copy.deepcopy(sched.state_dict()),
        method=dict(kind="NashMTL",step=float(m.step),
                    prvs_alpha=np.asarray(m.prvs_alpha,dtype=np.float32).copy()),
        python_rng=random.getstate(),
        numpy_rng=np.random.get_state(),
        torch_rng=torch.get_rng_state().clone(),
    )

def restore(state):
    p,wm,opt,sched=make()
    with torch.no_grad(): p.copy_(state["p"])
    opt.load_state_dict(state["optimizer"])
    sched.load_state_dict(state["scheduler"])
    m=wm.method
    m.step=float(state["method"]["step"])
    m.prvs_alpha=np.asarray(state["method"]["prvs_alpha"],dtype=np.float32)
    m._init_optim_problem()
    random.setstate(state["python_rng"])
    np.random.set_state(state["numpy_rng"])
    torch.set_rng_state(state["torch_rng"])
    return p,wm,opt,sched

def run_continuous(n=8):
    torch.manual_seed(123); np.random.seed(123); random.seed(123)
    p,wm,opt,sched=make()
    for step in range(n): one_step(p,wm,opt,sched,step)
    return p.detach().clone(),np.asarray(wm.method.prvs_alpha).copy(),wm.method.step

def run_resumed(split=4,n=8):
    torch.manual_seed(123); np.random.seed(123); random.seed(123)
    p,wm,opt,sched=make()
    for step in range(split): one_step(p,wm,opt,sched,step)
    state=snap(p,wm,opt,sched)
    p,wm,opt,sched=restore(state)
    for step in range(split,n): one_step(p,wm,opt,sched,step)
    return p.detach().clone(),np.asarray(wm.method.prvs_alpha).copy(),wm.method.step

def main():
    a,aa,as_=run_continuous()
    b,ba,bs=run_resumed()
    p_err=float((a-b).norm())
    alpha_err=float(np.linalg.norm(aa-ba))
    print({"parameter_l2":p_err,"alpha_l2":alpha_err,
           "continuous_step":as_,"resumed_step":bs})
    if p_err>2e-6 or alpha_err>2e-5 or as_!=bs:
        raise SystemExit("FAIL: Nash resume trajectory differs beyond tolerance")
    print("PASS: Nash-MTL state/Adam/scheduler resume equivalence")

if __name__=="__main__":
    main()
