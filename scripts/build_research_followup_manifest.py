"""Hash the opened-cohort follow-up evidence and record acceptance decisions."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folders=['experiments/representation_acquisition','experiments/noise_revision','results/representation_acquisition','results/noise_revision']
files={p for folder in folders for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json'}
files.update(ROOT/p for p in ['kernellum/discovery/representation.py','kernellum/discovery/revision.py','kernellum/discovery/aggregation.py','experiments/representation_revision/run.py','experiments/representation_revision/spec.json','results/representation_revision/confirmation/exact_nonuniform_inputs.json','results/representation_revision/confirmation/exact_nonuniform_inputs.npz','kernellum/discovery/representation_acquisition.py','kernellum/discovery/noise_revision.py','scripts/audit_representation_acquisition.py','scripts/audit_representation_revision.py','scripts/build_research_followup_manifest.py','tests/test_representation_acquisition.py','tests/test_noise_revision.py','docs/REPRESENTATION_ACQUISITION_RESULT.md'])
a=json.loads((ROOT/'results/representation_acquisition/second_screen/summary.json').read_text())
n=json.loads((ROOT/'results/noise_revision/development/summary.json').read_text())
def meets(comparisons):return all(v['ratio']<=.8 and v['wins']/39>=.6 and max(v['by_noise'].values())<=1 for v in comparisons.values())
result=dict(development_only=True,field_breakthrough_established=False,acquisition_trajectories=a['runs'],noise_fitting_outcomes=n['runs'],acquisition_broad_target_met_by=[m for m,c in a['comparisons'].items() if meets(c)],noise_target_met=meets(n['comparisons']),
 sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
aud=ROOT/'results/representation_acquisition/audit.json'
result['acquisition_arithmetic_audit']=json.loads(aud.read_text()) if aud.exists() else {'status':'running'}
(ROOT/'results/representation_acquisition/manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ('sha256','acquisition_arithmetic_audit')})
