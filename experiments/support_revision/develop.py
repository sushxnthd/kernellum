"""Fixed support-routing ablations on the already-opened 39-function cohort."""
import gzip
import hashlib
import json
import os
import platform
import time
from pathlib import Path
import numpy as np
import scipy
import uqtestfuns
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.support_revision import SupportRouter, METHODS
from experiments.representation_revision.run import sample_case, select_coverage

ROOT = Path(__file__).resolve().parents[2]


def read_records(path):
    with gzip.open(ROOT / path, 'rt') as f:
        return [json.loads(line) for line in f]


def summarize(records, lookup, spec, controls):
    comparisons = {}
    gates = {}
    for method in METHODS:
        comparisons[method] = {}
        for control in controls:
            byfun = {}
            bynoise = {str(n): [] for n in spec['noise_fractions']}
            for case in spec['cohort']:
                vals = []
                for seed in spec['seeds']:
                    for noise in spec['noise_fractions']:
                        key = (case['name'], seed, noise)
                        ratio = np.log(max(lookup[(*key, method)], 1e-8) / max(lookup[(*key, control)], 1e-8))
                        vals.append(ratio)
                        bynoise[str(noise)].append(ratio)
                byfun[case['name']] = float(np.exp(np.mean(vals)))
            comparisons[method][control] = dict(
                ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),
                wins=sum(v < 1 for v in byfun.values()),
                by_noise={k: float(np.exp(np.mean(v))) for k, v in bynoise.items()}, by_function=byfun)
        gates[method] = all(v['ratio'] <= .8 and v['wins']/len(spec['cohort']) >= .6
                            and max(v['by_noise'].values()) <= 1 for v in comparisons[method].values())
    distribution = {}
    for method in list(METHODS) + controls:
        values = [v for (*_, m), v in lookup.items() if m == method]
        distribution[method] = dict(mean=float(np.mean(values)), median=float(np.median(values)),
                                    maximum=float(max(values)), p95=float(np.quantile(values, .95)))
    return dict(development_only=True, field_breakthrough_established=False, runs=len(records),
                functions=len(spec['cohort']), controls=controls, broad_gate=gates,
                comparisons=comparisons, distributions=distribution)


def run():
    spec = json.loads((ROOT / 'experiments/representation_revision/spec.json').read_text())
    if uqtestfuns.__version__ != spec['uqtestfuns']:
        raise ValueError('upstream version changed')
    out = ROOT / 'results/support_revision/development'
    out.mkdir(parents=True, exist_ok=False)
    paths = ['kernellum/discovery/support_revision.py', 'experiments/support_revision/develop.py',
             'tests/test_support_revision.py', 'kernellum/discovery/representation.py',
             'kernellum/discovery/revision.py', 'kernellum/discovery/aggregation.py',
             'experiments/representation_revision/run.py', 'experiments/representation_revision/spec.json',
             'results/representation_revision/confirmation/traces.jsonl.gz',
             'results/crossfit_revision/development/traces.jsonl.gz',
             'results/noise_revision/development/traces.jsonl.gz']
    hashes = lambda ps: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ps}
    manifest = dict(development_only=True, source_hashes=hashes(paths), python=platform.python_version(),
                    numpy=np.__version__, scipy=scipy.__version__, uqtestfuns=uqtestfuns.__version__,
                    threads={k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')})
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    prior = read_records(paths[-3])
    lookup = {(r['function'], r['seed'], r['noise'], r['method']): r['metrics'][-1]['nmse'] for r in prior}
    for path in paths[-2:]:
        for r in read_records(path):
            lookup[(r['function'], r['seed'], r['noise'], r['method'])] = r['nmse']
    controls = spec['methods'] + ['nested_winner', 'noise_consistent']
    records = []
    start = time.perf_counter()
    max_scaled_control_difference = 0.
    with gzip.open(out / 'traces.jsonl.gz', 'wt') as f:
        for index, case in enumerate(spec['cohort']):
            for seed in spec['seeds']:
                # Compute deterministic noiseless outputs once, then reproduce prior noise exactly.
                x, clean, xt, yt = sample_case(case, index, seed, 0., spec)
                ids = select_coverage(x, spec, seed)
                perturbation = np.random.default_rng(seed + 1000000 + index).normal(size=len(x))
                for noise in spec['noise_fractions']:
                    y = clean + noise * np.std(clean) * perturbation
                    bank = RepresentationBank(x).fit(ids, y[ids])
                    variance = max(float(np.var(yt)), 1e-30)
                    # Verify reuse of the existing control scores is numerically valid.
                    for control in ('representation', 'representation_stack', 'raw'):
                        actual = float(np.mean((bank.predict(xt, control)-yt)**2) / variance)
                        old = lookup[(case['name'], seed, noise, control)]
                        scaled = abs(actual-old) / max(abs(old), 1e-8)
                        max_scaled_control_difference = max(max_scaled_control_difference, scaled)
                        if not np.isclose(actual, old, rtol=2e-5, atol=1e-7):
                            raise ValueError('reused control mismatch')
                    router = SupportRouter(bank, xt)
                    for method in METHODS:
                        pred, diagnostic = router.predict(method)
                        error = float(np.mean((pred-yt)**2) / variance)
                        if not np.isfinite(error):
                            raise FloatingPointError('nonfinite outcome; no exclusions allowed')
                        r = dict(function=case['name'], seed=seed, noise=noise, method=method, nmse=error,
                                 selected=ids, observed=y[ids].tolist(), diagnostic=diagnostic,
                                 input_sha256=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest())
                        f.write(json.dumps(r, allow_nan=False) + '\n')
                        f.flush()
                        records.append(r)
                        lookup[(case['name'], seed, noise, method)] = error
            print(case['name'], len(records), round(time.perf_counter()-start, 1), flush=True)
    result = summarize(records, lookup, spec, controls)
    result['seconds'] = time.perf_counter()-start
    result['max_scaled_control_difference'] = max_scaled_control_difference
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    manifest['output_hashes'] = hashes([str(p.relative_to(ROOT)) for p in (out/'summary.json', out/'traces.jsonl.gz')])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for method, comp in result['comparisons'].items():
        print(method, {c: round(v['ratio'], 6) for c, v in comp.items()}, result['broad_gate'][method], flush=True)


if __name__ == '__main__':
    run()
