"""Read-only paired analysis of the completed trend screen; no model fitting."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
import statistics
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'results/trend_revision/development/traces.jsonl.gz',
    'results/representation_revision/confirmation/traces.jsonl.gz',
    'results/robust_revision/development/traces.jsonl.gz',
    'results/support_revision/development/traces.jsonl.gz',
    'results/adaptive_revision/development/traces.jsonl.gz',
    'results/crossfit_revision/development/traces.jsonl.gz',
    'results/noise_revision/development/traces.jsonl.gz',
)
CONTROLS = ('representation', 'representation_stack', 'raw', 'raw_stack',
            'median_stack', 'adaptive_stack', 'support_nonlinear_leverage_stack',
            'nested_winner', 'noise_consistent')


def read(path):
    with gzip.open(path, 'rt') as stream:
        return [json.loads(line) for line in stream]


def score(row):
    return row['metrics'][-1]['nmse'] if 'metrics' in row else row['nmse']


def models(row):
    if 'metrics' in row:
        return row['metrics'][-1]['models']
    return row.get('models', row.get('diagnostic', {}).get('components', []))


def logratio(a, b, floor=1e-8):
    if floor is None:
        if a <= 0 or b <= 0:
            raise ValueError('raw-error diagnostic requires positive scores')
        return math.log(a) - math.log(b)
    return math.log(max(a, floor)) - math.log(max(b, floor))


def gm(logs):
    return math.exp(statistics.fmean(logs))


def analyze(out):
    out.mkdir(parents=True, exist_ok=False)
    spec = json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    names = [c['name'] for c in spec['cohort']]
    seeds = spec['seeds']
    noises = spec['noise_fractions']
    expected = {(n, s, z) for n in names for s in seeds for z in noises}
    lookup = {}
    for path in FILES:
        for row in read(ROOT/path):
            method = row['method']
            if method not in (*CONTROLS, 'trend', 'trend_stack'):
                continue
            key = (row['function'], row['seed'], row['noise'], method)
            if key in lookup:
                raise ValueError(f'duplicate row: {key}')
            if not math.isfinite(score(row)) or score(row) < 0:
                raise ValueError(f'invalid error: {key}')
            lookup[key] = row
    for method in (*CONTROLS, 'trend', 'trend_stack'):
        assert {key[:3] for key in lookup if key[3] == method} == expected
    sparse_controls = ('nested_winner', 'noise_consistent')
    for key in expected:
        reference = lookup[(*key, 'trend_stack')]
        assert len(reference['selected']) == len(set(reference['selected'])) == 64
        for method in (*CONTROLS, 'trend'):
            row = lookup[(*key, method)]
            if method in sparse_controls:
                continue
            assert row['selected'] == reference['selected']
            assert row['input_sha256'] == reference['input_sha256']
            np.testing.assert_allclose(row['observed'], reference['observed'], rtol=1e-12, atol=1e-12)
    published = json.loads((ROOT/'results/trend_revision/development/summary.json').read_text())
    verified = 0
    for method in ('trend', 'trend_stack'):
        for baseline in CONTROLS:
            values = {n: [logratio(score(lookup[(n,s,z,method)]), score(lookup[(n,s,z,baseline)]))
                          for s in seeds for z in noises] for n in names}
            p = published['comparisons'][method][baseline]
            assert math.isclose(gm([statistics.fmean(v) for v in values.values()]), p['ratio'], rel_tol=1e-12)
            assert sum(gm(v) < 1 for v in values.values()) == p['wins']
            for n, v in values.items():
                assert math.isclose(gm(v), p['by_function'][n], rel_tol=1e-12)
            for z in noises:
                vals = [logratio(score(lookup[(n,s,z,method)]), score(lookup[(n,s,z,baseline)])) for n in names for s in seeds]
                assert math.isclose(gm(vals), p['by_noise'][str(z)], rel_tol=1e-12)
            verified += 1
    rows = []
    for n in names:
        for s in seeds:
            for z in noises:
                original = lookup[(n,s,z,'representation_stack')]
                candidate = lookup[(n,s,z,'trend_stack')]
                old_models = models(original)
                new_models = models(candidate)
                removed = sum(m['weight'] for m in old_models
                              if m['response'] != 'identity' and m['family'] in ('quadratic','cubic'))
                affine = sum(m['weight'] for m in new_models if m.get('trend') == 'affine')
                rows.append(dict(function=n, seed=s, noise=z, original_nmse=score(original),
                    trend_nmse=score(candidate), ratio=math.exp(logratio(score(candidate),score(original))),
                    original_exponential_polynomial_weight=removed, trend_affine_weight=affine,
                    log_response_available=all(v>0 for v in candidate['observed']) or all(v<0 for v in candidate['observed'])))
    with (out/'paired_rows.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    cases = {c['name']:c for c in spec['cohort']}
    bootstrap = np.random.default_rng(20261003).integers(0,len(names),(20000,len(names)))
    comparisons = {}
    function_rows = []
    for baseline in CONTROLS:
        report = {}
        for z in noises:
            logs = [statistics.fmean([logratio(score(lookup[(n,s,z,'trend_stack')]),score(lookup[(n,s,z,baseline)]))
                                      for s in seeds]) for n in names]
            raw_logs = [statistics.fmean([logratio(score(lookup[(n,s,z,'trend_stack')]),score(lookup[(n,s,z,baseline)]),None)
                                         for s in seeds]) for n in names]
            ratios = list(map(math.exp,logs))
            deleted = {n:gm(logs[:i]+logs[i+1:]) for i,n in enumerate(names)}
            family = {}
            for n,v in zip(names,logs):
                family.setdefault(cases[n]['source_module'],[]).append(v)
            report[str(z)] = dict(ratio=gm(logs),raw_positive_error_ratio=gm(raw_logs),
                wins=sum(v<0 for v in logs),median_function_ratio=statistics.median(ratios),
                without_genz_corner_peak=deleted['GenzCornerPeak'],
                leave_one_function_out_range=[min(deleted.values()),max(deleted.values())],
                descriptive_function_bootstrap_interval=np.quantile(np.exp(np.asarray(logs)[bootstrap].mean(1)),[.025,.975]).tolist(),
                equal_source_family_ratio=gm([statistics.fmean(v) for v in family.values()]),
                source_families=len(family),by_function=dict(zip(names,ratios)))
        interactions=[]
        for n in names:
            interaction=math.log(report['0.02']['by_function'][n])-math.log(report['0.0']['by_function'][n])
            interactions.append(interaction)
            function_rows.append(dict(function=n,baseline=baseline,clean_ratio=report['0.0']['by_function'][n],
                noisy_ratio=report['0.02']['by_function'][n],paired_ratio_change=math.exp(interaction)))
        comparisons[baseline]=dict(by_noise=report,paired_noise_interaction_ratio=gm(interactions),
            functions_with_smaller_relative_error_under_noise=sum(v<0 for v in interactions))
    with (out/'by_function.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(function_rows[0]));writer.writeheader();writer.writerows(function_rows)
    changed_sign=[]
    for n in names:
        for s in seeds:
            clean=lookup[(n,s,0.,'trend_stack')]['observed'];noisy=lookup[(n,s,.02,'trend_stack')]['observed']
            available=lambda v:all(a>0 for a in v) or all(a<0 for a in v)
            if available(clean) != available(noisy):changed_sign.append(dict(function=n,seed=s))
    foothold = all(comparisons[b]['by_noise']['0.02']['without_genz_corner_peak']<1 and
                   comparisons[b]['by_noise']['0.02']['wins']>len(names)/2
                   for b in ('representation_stack','adaptive_stack'))
    result=dict(development_only=True,field_breakthrough_established=False,
        candidate_outcomes=780,paired_paths=390,published_comparisons_verified=verified,
        metadata_paired_controls=[b for b in CONTROLS if b not in sparse_controls],
        controls_without_archived_pairing_metadata=list(sparse_controls),
        descriptive_only=True,noise_foothold_diagnostic_passed=foothold,
        response_transform_availability_changes=changed_sign,comparisons=comparisons)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[*FILES,'results/trend_revision/development/summary.json',
           'experiments/representation_revision/spec.json','scripts/diagnose_noise_regime.py',
           'docs/NOISE_REGIME_DIAGNOSIS_PROTOCOL.md']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest=dict(source_commit='283d846852113e5128fdbc05f55981b4e3be74e2',
        protocol_local_freeze='191aeee',python=platform.python_version(),numpy=np.__version__,
        input_sha256={p:digest(ROOT/p) for p in paths},
        output_sha256={p.name:digest(p) for p in out.iterdir()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for b in ('representation_stack','adaptive_stack'):
        print(b,json.dumps({z:{k:v for k,v in r.items() if k!='by_function'} for z,r in comparisons[b]['by_noise'].items()}))
    print('noise foothold',foothold,'availability changes',len(changed_sign))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    analyze(parser.parse_args().out)
