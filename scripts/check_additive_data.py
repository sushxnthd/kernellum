"""Separate closed-form truth and domain checks from recorded parameters."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'results/additive_response/confirmation'
archive=np.load(folder/'inputs_and_truth.npz',allow_pickle=False);parameters=json.loads((folder/'parameters.json').read_text());checked=0;largest=0.
for prefix,p in parameters.items():
 family=prefix.rsplit('_',2)[0];center=np.array(p['center']);second=np.array(p['second_center']);curvature=np.array(p['curvature']);slope=np.array(p['slope']);amplitude=p['amplitude']
 for kind in ['pool','inside','near_shell','far_shell']:
  x=archive[f'{prefix}_pool' if kind=='pool' else f'{prefix}_{kind}_test'];z=np.log(x) if family=='power_law' else x
  radius=abs(z).max(1)
  if kind in ['pool','inside']:assert max(radius)<=1+1e-12
  if kind=='near_shell':assert min(radius)>1 and max(radius)<=1.5
  if kind=='far_shell':assert min(radius)>1.5 and max(radius)<=3
  delta=z-center;q=np.sum((delta@curvature)*delta,axis=1);gaussian=amplitude*np.exp(-q)
  if family=='gaussian':truth=gaussian
  elif family=='negative_gaussian':truth=-gaussian
  elif family in ['exp_affine','power_law']:truth=amplitude*np.exp(np.sum(z*slope,axis=1))
  elif family=='convex_exponential':truth=amplitude*np.exp(.15*np.sum(z*z,axis=1)+np.sum(z*slope,axis=1))
  elif family=='rational_peak':truth=amplitude/(1+q)
  elif family=='sine':truth=np.sin(3*np.sum(z*slope,axis=1))+.3*np.cos(2*z[:,0]*z[:,-1])
  elif family=='signed_cubic':truth=np.sum(z*slope,axis=1)+.3*z[:,0]**3+.2*z[:,0]*z[:,-1]
  elif family=='gaussian_mixture':truth=gaussian+.7*amplitude*np.exp(-3*np.sum((z-second)**2,axis=1))
  else:raise ValueError(family)
  saved=archive[f'{prefix}_clean' if kind=='pool' else f'{prefix}_{kind}_truth']
  np.testing.assert_allclose(truth,saved,rtol=1e-12,atol=1e-13);largest=max(largest,float(abs(truth-saved).max()));checked+=1
result=dict(passed=True,truth_and_domain_arrays_checked=checked,max_absolute_truth_discrepancy=largest,
 source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_archive_sha256=hashlib.sha256((folder/'inputs_and_truth.npz').read_bytes()).hexdigest(),same_author=True)
(folder/'data_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
