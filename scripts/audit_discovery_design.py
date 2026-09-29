"""Separate arithmetic audit: imports no Kernellum or experiment-runner code.

Checks source/output hashes, cohort completeness, query accounting, observations,
and all reported test errors using augmented least squares instead of an inverse.
This is a second implementation by the same author, not external replication.
"""
import argparse
import ast
import csv
import hashlib
import gzip
import itertools
import json
import operator
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow}
FUNCS = {name: getattr(np, name) for name in ('sin', 'cos', 'exp', 'sqrt', 'arcsin', 'tanh')}
FUNCS['ln'] = np.log


def formula(text, env):
    def calc(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return node.value
        if isinstance(node, ast.Name): return env[node.id]
        if isinstance(node, ast.BinOp): return OPS[type(node.op)](calc(node.left), calc(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -calc(node.operand)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and len(node.args)==1 and not node.keywords): return FUNCS[node.func.id](calc(node.args[0]))
        raise ValueError('unsupported AST')
    return calc(ast.parse(text, mode='eval').body)


def phi(x):
    columns = [np.ones(len(x))]
    for degree in (1, 2):
        for indices in itertools.combinations_with_replacement(range(x.shape[1]), degree):
            columns.append(np.prod(x[:, indices], axis=1))
    return np.array(columns).T


def check(condition, text):
    if not condition: raise ValueError(text)


def content(path):
    return path.read_bytes() if path.exists() else gzip.decompress(Path(str(path)+'.gz').read_bytes())


def audit(folder):
    spec = json.loads((ROOT/'experiments/discovery_design/spec.json').read_text())
    manifest = json.loads((folder/'manifest.json').read_text())
    summary = json.loads((folder/'summary.json').read_text())
    hash_count = 0
    for base, key in ((ROOT, 'source_hashes'), (folder, 'output_hashes')):
        for path, expected in manifest[key].items():
            check(hashlib.sha256(content(base/path)).hexdigest()==expected, 'hash mismatch: '+path)
            hash_count += 1
    with (ROOT/'experiments/discovery_design/vendor/FeynmanEquations.csv').open(encoding='utf-8-sig') as f:
        rows = {r['Filename']:r for r in csv.DictReader(f) if r['# variables'] and int(r['# variables'])<=3}
    traces = [json.loads(s) for s in content(folder/'traces.jsonl').decode().splitlines()]
    expected = set(itertools.product(rows, spec['seeds'], spec['noise_fractions'], spec['methods']))
    lookup = {}
    cache = {}
    errors = 0
    max_error_difference = 0
    for record in traces:
        name, seed, noise, method = (record[k] for k in ('equation','seed','noise','method'))
        key = (name, seed, noise, method)
        check(key in expected and key not in lookup, 'unexpected/duplicate run')
        lookup[key] = record
        ckey = (name,seed,noise)
        if ckey not in cache:
            row = rows[name]
            d = int(row['# variables'])
            rng = np.random.default_rng(np.random.SeedSequence([seed, int(row['Number'])]))
            x = rng.uniform(-1, 1, (spec['pool_size'], d))
            xt = rng.uniform(-1, 1, (spec['test_size'], d))
            def response(points):
                env = {'pi':np.pi}
                for i in range(d):
                    low, high = float(row[f'v{i+1}_low']), float(row[f'v{i+1}_high'])
                    env[row[f'v{i+1}_name']] = low + (points[:,i]+1)*(high-low)/2
                return formula(row['Formula'], env)
            y, yt = response(x), response(xt)
            y = y + noise*y.std()*rng.normal(size=len(y))
            cache[ckey] = (x,y,xt,yt)
        x,y,xt,yt = cache[ckey]
        idx = record['selected']
        check(len(idx)==spec['budget'] and len(set(idx))==len(idx), 'invalid query count')
        check(all(type(i)==int and 0<=i<len(x) for i in idx), 'invalid pool index')
        check(np.allclose(y[idx],record['observed'],rtol=1e-12,atol=1e-12), 'observations differ')
        initial = list(map(int,np.random.default_rng(seed).choice(len(x),spec['initial'],replace=False)))
        check(idx[:spec['initial']]==initial, 'initial pool differs')
        check([m['budget'] for m in record['metrics']]==spec['checkpoints'], 'checkpoint mismatch')
        for m in record['metrics']:
            n = m['budget']
            z = y[idx[:n]]
            center, scale = z.mean(), max(float(z.std()),1e-12)
            a = phi(x[idx[:n]])
            # Augmented least squares solves ridge without reusing production fit.
            aug = np.vstack((a,np.sqrt(1e-6)*np.eye(a.shape[1])))
            rhs = np.r_[(z-center)/scale,np.zeros(a.shape[1])]
            b = np.linalg.lstsq(aug,rhs,rcond=None)[0]
            pred = center + scale*phi(xt)@b
            nmse = float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
            difference = abs(nmse-m['nmse'])
            max_error_difference = max(max_error_difference,difference)
            check(np.isclose(nmse,m['nmse'],rtol=1e-7,atol=1e-10), 'metric mismatch')
            errors += 1
    check(set(lookup)==expected, 'incomplete cohort')
    comparisons = {}
    all_pass = True
    for baseline in spec['baselines']:
        per_equation, noise_logs = {}, {str(n):[] for n in spec['noise_fractions']}
        for name in rows:
            logs = []
            for seed,noise in itertools.product(spec['seeds'],spec['noise_fractions']):
                a = lookup[(name,seed,noise,spec['primary_method'])]['metrics'][-1]['nmse']
                b = lookup[(name,seed,noise,baseline)]['metrics'][-1]['nmse']
                log = np.log(max(a,1e-8))-np.log(max(b,1e-8))
                logs.append(log)
                noise_logs[str(noise)].append(log)
            per_equation[name] = float(np.exp(np.mean(logs)))
        ratio = float(np.exp(np.mean(np.log(list(per_equation.values())))))
        wins = float(np.mean(np.array(list(per_equation.values()))<1))
        noise_ratios = {k:float(np.exp(np.mean(v))) for k,v in noise_logs.items()}
        saved = summary['comparisons'][baseline]
        check(np.isclose(ratio,saved['geometric_mean_ratio']), 'aggregate mismatch')
        check(wins==saved['equation_win_fraction'], 'win fraction mismatch')
        for name,value in per_equation.items():
            check(np.isclose(value,saved['equation_ratios'][name]), 'equation summary mismatch')
        for key,value in noise_ratios.items():
            check(np.isclose(value,saved['by_noise'][key]), 'noise summary mismatch')
        passed = ratio<=0.8 and wins>=0.6 and max(noise_ratios.values())<=1
        comparisons[baseline] = dict(ratio=ratio,win_fraction=wins,by_noise=noise_ratios,passes=passed)
        all_pass &= passed
    check(summary['complete'] and summary['runs']==len(traces) and summary['equations']==len(rows), 'wrong total')
    check(summary['criterion_supported']==all_pass, 'wrong verdict')
    return dict(audit_passed=True, runs=len(traces), equations=len(rows), measurement_calls=len(traces)*spec['budget'],
                checkpoint_metrics_recomputed=errors, hashes_verified=hash_count,
                max_absolute_metric_difference=max_error_difference, criterion_supported=bool(all_pass),
                comparisons=comparisons, boundary='Same-author separate arithmetic implementation; not independent external replication')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('folder',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    result=audit(args.folder)
    text=json.dumps(result,indent=2)+'\n'
    if args.out:
        with args.out.open('x') as f: f.write(text)
    print(text)
