"""Build a self-contained, read-only evidence explorer from reviewed run artifacts."""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build(allow_partial=False):
    data=json.loads((ROOT/'study/analysis/results.json').read_text())
    if not data['complete'] and not allow_partial:
        raise ValueError('Main study incomplete; refusing final site build')
    native=ROOT/'study/analysis/native-summary.json'
    data['native']=json.loads(native.read_text()) if native.exists() else None
    if not allow_partial and (not data['native'] or data['native']['episodes']!=72):
        raise ValueError('Native cohort incomplete; refusing final site build')
    data['native_records']=[]
    for path in sorted((ROOT/'study/native-direct').glob('*/episodes/*.json')):
        record=json.loads(path.read_text())
        record['artifact_path']=str(path.relative_to(ROOT))
        record['run_id']=path.parent.parent.name
        data['native_records'].append(record)
    site=ROOT/'site';site.mkdir(exist_ok=True)
    (site/'figures').mkdir(exist_ok=True)
    for name in ['workflow','decisions','primary-outcome']:
        shutil.copy2(ROOT/'figures'/f'{name}.svg',site/'figures'/f'{name}.svg')
    for name in ['lexcollude-paper.pdf','lexcollude-paper.docx','abstract.txt']:
        shutil.copy2(ROOT/'paper'/name,site/name)
    (site/'results.json').write_text(json.dumps(data,indent=2)+'\n')
    template=(ROOT/'site/template.html').read_text()
    safe=json.dumps(data,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    (site/'index.html').write_text(template.replace('/*__STUDY_DATA__*/',safe))
    bundle=ROOT/'deliverables/lexcollude-explorer.zip'
    bundle.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(site.rglob('*')):
            if path.is_file() and path.name!='template.html':
                archive.write(path,path.relative_to(site))
    print('Built site/index.html with',data['completed_episodes'],'completed episodes')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true')
    build(p.parse_args().allow_partial)
