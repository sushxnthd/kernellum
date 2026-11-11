import torch
from atomicity_intervention import transform_losses

def flatgrad(loss,params):
    gs=torch.autograd.grad(loss,params,retain_graph=True)
    return torch.cat([g.reshape(-1) for g in gs])

def test_all():
    torch.manual_seed(73)
    model=torch.nn.Sequential(torch.nn.Linear(5,7),torch.nn.Tanh(),torch.nn.Linear(7,3)).double()
    x=torch.randn(11,5,dtype=torch.float64); y=torch.randn(11,3,dtype=torch.float64)
    out=model(x)
    base=torch.stack([((out[:,i]-y[:,i])**2).mean() for i in range(3)])
    params=list(model.parameters())
    for j in range(3):
      for k in (2,4,8):
        coarse,_=transform_losses(base,'coarse',j,k)
        can,_=transform_losses(base,'canonicalized',j,k)
        exp,_=transform_losses(base,'exposed',j,k)
        assert coarse.shape == can.shape == (3,)
        assert exp.shape == (3+k-1,)
        assert torch.equal(coarse,can)
        gc=flatgrad(coarse.sum(),params); gz=flatgrad(can.sum(),params)
        rel=(gc-gz).norm()/gc.norm(); assert rel.item() < 5e-16
        ge=flatgrad(exp.sum(),params)
        if k>1: assert (ge-gc).norm().item() > 1e-8
    print('PASS: 9 canonicalized graph controls; value equality exact; gradient relerr <5e-16')
if __name__=='__main__': test_all()
