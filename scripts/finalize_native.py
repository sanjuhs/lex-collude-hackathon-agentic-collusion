"""Derive the explicitly amended native direct cohort without rewriting parent runs."""

import json
import shutil
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lexcollude.report import write_report
from verify_run import verify

conditions=['clean','misinformation','injection','verified_injection']
groups=[]
for parent in sorted((ROOT/'study/runs').glob('*')):
    if not parent.is_dir():continue
    manifest=json.loads((parent/'manifest.json').read_text())
    records=[json.loads(p.read_text()) for p in sorted((parent/'episodes').glob('*.json'))]
    records=[r for r in records if r['condition'] in conditions]
    if len(records)!=12 or any(r['status']!='ok' for r in records):
        raise SystemExit(f'Native direct cohort incomplete: {parent.name}')
    output=ROOT/'study/native-direct'/parent.name
    output.mkdir(parents=True,exist_ok=True)
    for sub in ['episodes','requests','responses']:(output/sub).mkdir(exist_ok=True)
    for r in records:
        name=r['episode_id']+'.json'
        shutil.copy2(parent/'episodes'/name,output/'episodes'/name)
        for call in r['calls']:
            name=r['episode_id']+'__'+call['stage']+'.json'
            for sub in ['requests','responses']:shutil.copy2(parent/sub/name,output/sub/name)
    manifest.update({'run_id':output.name,'conditions':conditions,'planned_calls':12,
                     'status':'completed','completed_episodes':12,'errors':0,'pending':0,
                     'cohort_type':'derived_direct_conditions','parent_run':str(parent.relative_to(ROOT)),
                     'scope_amendment':'study/amendment.json; logistical scope change, no outcome selection'})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    write_report(output,records,manifest)
    verified=verify(output)
    groups.append({'model':manifest['model'],'prompt_policy':manifest['prompt_policy'],
                   'valid':len(records),'unauthorized':sum(r['raw_score']['unauthorized_acceptance'] for r in records),
                   'false_approval_claims':sum(r['raw_score']['false_approval_claim'] for r in records),
                   'report_flags':sum(r['raw_score']['structured_report_discrepancy'] for r in records),
                   'calls':sum(len(r['calls']) for r in records),'parent_run':manifest['parent_run']})
    print(json.dumps(verified))
if len(groups)!=6:raise SystemExit('Expected six native model-policy groups')
summary={'backend':'codex','episodes':sum(r['valid'] for r in groups),'calls':sum(r['calls'] for r in groups),
         'conditions':conditions,'groups':groups,'scope_amendment':'study/amendment.json'}
(ROOT/'study/analysis/native-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
