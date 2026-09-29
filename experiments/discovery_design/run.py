"""Frozen external-formula benchmark. Run from repository root with PYTHONPATH=."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
from kernellum.discovery.design import METHODS, features, fit, investigate

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FUNCTIONS = {s: getattr(np, s) for s in ('exp', 'sqrt', 'sin', 'cos', 'tanh', 'arcsin')}
FUNCTIONS['ln'] = np.log


def evaluate(formula, names, x):
    """Restricted arithmetic AST interpreter; never eval upstream text."""
    env = dict(zip(names, x.T)) | {'pi': np.pi}
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and node.id in env:
            return env[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return (-1 if isinstance(node.op, ast.USub) else 1) * visit(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            for typ, op in ((ast.Add, np.add), (ast.Sub, np.subtract),
                            (ast.Mult, np.multiply), (ast.Div, np.divide), (ast.Pow, np.power)):
                if isinstance(node.op, typ):
                    return op(a, b)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords):
            return FUNCTIONS[node.func.id](visit(node.args[0]))
        raise ValueError('unsupported formula syntax')
    with np.errstate(all='raise'):
        y = np.broadcast_to(visit(ast.parse(formula, mode='eval')), (len(x),)).copy()
    if not np.isfinite(y).all():
        raise ValueError('invalid equation domain')
    return y


def equations():
    with (HERE / 'vendor/FeynmanEquations.csv').open(encoding='utf-8-sig') as f:
        return [row for row in csv.DictReader(f) if row['# variables'] and int(row['# variables']) <= 3]


def data(row, seed, noise, spec):
    d = int(row['# variables'])
    ident = int(row['Number'])
    rng = np.random.default_rng(np.random.SeedSequence([seed, ident]))
    x = rng.uniform(-1, 1, (spec['pool_size'], d))
    xt = rng.uniform(-1, 1, (spec['test_size'], d))
    lo = np.array([float(row[f'v{i}_low']) for i in range(1, d+1)])
    hi = np.array([float(row[f'v{i}_high']) for i in range(1, d+1)])
    names = [row[f'v{i}_name'] for i in range(1, d+1)]
    yp = evaluate(row['Formula'], names, lo + (x+1) * (hi-lo)/2)
    yt = evaluate(row['Formula'], names, lo + (xt+1) * (hi-lo)/2)
    y = yp + noise * np.std(yp) * rng.normal(size=len(yp))
    return x, y, xt, yt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(records, spec):
    complete = len(records) == len(equations()) * len(spec['seeds']) * len(spec['noise_fractions']) * len(spec['methods'])
    lookup = {(r['equation'], r['seed'], r['noise'], r['method']): r for r in records}
    comparisons = {}
    for baseline in spec['baselines']:
        by_eq, by_noise = {}, {str(n): [] for n in spec['noise_fractions']}
        for row in equations():
            logs = []
            for seed in spec['seeds']:
                for noise in spec['noise_fractions']:
                    a = lookup[(row['Filename'], seed, noise, spec['primary_method'])]['metrics'][-1]['nmse']
                    b = lookup[(row['Filename'], seed, noise, baseline)]['metrics'][-1]['nmse']
                    ratio = float(np.log(max(a, 1e-8) / max(b, 1e-8)))
                    logs.append(ratio)
                    by_noise[str(noise)].append(ratio)
            by_eq[row['Filename']] = float(np.exp(np.mean(logs)))
        overall = float(np.exp(np.mean(np.log(list(by_eq.values())))))
        win_fraction = float(np.mean(np.array(list(by_eq.values())) < 1))
        noise_ratios = {n: float(np.exp(np.mean(v))) for n, v in by_noise.items()}
        comparisons[baseline] = dict(geometric_mean_ratio=overall, equation_win_fraction=win_fraction,
                                    by_noise=noise_ratios, equation_ratios=by_eq)
    gates = spec['gates']
    passed = complete and all(
        c['geometric_mean_ratio'] <= gates['geometric_mean_ratio_vs_each_baseline_max']
        and c['equation_win_fraction'] >= gates['equation_win_fraction_vs_each_baseline_min']
        and max(c['by_noise'].values()) <= gates['geometric_mean_ratio_each_noise_vs_each_baseline_max']
        for c in comparisons.values())
    return dict(complete=complete, runs=len(records), equations=len(equations()),
                criterion_supported=passed, field_breakthrough_established=False,
                comparisons=comparisons,
                median_seconds_by_method={m:float(np.median([r['seconds'] for r in records if r['method']==m])) for m in METHODS})


def run(out):
    spec = json.loads((HERE/'spec.json').read_text())
    out.mkdir(parents=True, exist_ok=False)
    files = ['kernellum/discovery/design.py', 'experiments/discovery_design/run.py',
             'experiments/discovery_design/spec.json', 'experiments/discovery_design/vendor/FeynmanEquations.csv']
    manifest = dict(source_hashes={p:sha(ROOT/p) for p in files}, python=platform.python_version(),
                    numpy=np.__version__, platform=platform.platform(),
                    blas_threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    records = []
    start = time.perf_counter()
    with (out/'traces.jsonl').open('w') as f:
        for row in equations():
            for seed in spec['seeds']:
                for noise in spec['noise_fractions']:
                    x, y, xt, yt = data(row, seed, noise, spec)
                    for method in spec['methods']:
                        before = time.perf_counter()
                        calls = []
                        def query(idx):
                            if idx in calls:
                                raise RuntimeError('duplicate query')
                            calls.append(idx)
                            return y[idx]
                        selected, values = investigate(x, query, method, spec['budget'], seed, spec['initial'])
                        # Evaluate only after the entire selection trace is closed.
                        metrics = []
                        for budget in spec['checkpoints']:
                            ys = np.asarray(values[:budget])
                            center, scale = ys.mean(), max(float(ys.std()), 1e-12)
                            beta, _ = fit(features(x[selected[:budget]]), (ys-center)/scale)
                            pred = center + scale * (features(xt) @ beta)
                            nmse = float(np.mean((pred-yt)**2) / max(float(np.var(yt)), 1e-30))
                            metrics.append(dict(budget=budget, nmse=nmse))
                        record = dict(equation=row['Filename'], seed=seed, noise=noise, method=method,
                                      selected=selected, observed=values, metrics=metrics,
                                      seconds=time.perf_counter()-before)
                        f.write(json.dumps(record, allow_nan=False)+'\n')
                        f.flush()
                        records.append(record)
            print(f"{row['Filename']}: {len(records)} runs, {time.perf_counter()-start:.1f}s", flush=True)
    summary = summarize(records, spec)
    summary['elapsed_seconds'] = time.perf_counter()-start
    (out/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    manifest['output_hashes'] = {p:sha(out/p) for p in ('traces.jsonl','summary.json')}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='comparisons'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
