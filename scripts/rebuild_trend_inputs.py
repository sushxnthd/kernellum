"""Reproduce the CI input/truth archive from pinned functions and exact columns.

Run before the arithmetic audit when using compact committed evidence. This
does not import the candidate or its experiment runner; the archive's original
SHA256 must match, so a platform/package mismatch fails rather than being hidden.
"""
import argparse,hashlib,inspect,json
from pathlib import Path
import numpy as np
import uqtestfuns

ROOT=Path(__file__).resolve().parents[1]

def rebuild(folder):
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__==spec['uqtestfuns']
    manifest=json.loads((folder/'manifest.json').read_text())
    archived=np.load(ROOT/'results/representation_revision/confirmation/exact_nonuniform_inputs.npz')
    cols=json.loads((ROOT/'results/representation_revision/confirmation/exact_nonuniform_inputs.json').read_text())['columns']
    arrays={}
    for index,case in enumerate(spec['cohort']):
        name=case['name'];fun=getattr(uqtestfuns,name)()
        assert hashlib.sha256(Path(inspect.getfile(type(fun))).read_bytes()).hexdigest()==case['source_sha256']
        for seed in spec['seeds']:
            fun.prob_input.reset_rng(seed+1000*index)
            pool=fun.prob_input.get_sample(spec['pool_size']);test=fun.prob_input.get_sample(spec['test_size'])
            if name in cols:
                pool[:,cols[name]]=archived[f'{name}_{seed}_pool']
                test[:,cols[name]]=archived[f'{name}_{seed}_test']
            arrays[f'{name}_{seed}_pool']=pool;arrays[f'{name}_{seed}_test']=test
            arrays[f'{name}_{seed}_truth']=np.asarray(fun(test)).reshape(-1)
            arrays[f'{name}_{seed}_clean']=np.asarray(fun(pool)).reshape(-1)
    path=folder/'inputs_and_truth.npz'
    if path.exists():raise FileExistsError(path)
    np.savez_compressed(path,**arrays)
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    expected=manifest['output_hashes']['inputs_and_truth.npz']
    assert actual==expected,('reconstructed archive differs',actual,expected)
    print('Exact CI archive reproduced:',actual)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);rebuild(p.parse_args().folder)
