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
    (site/'start_explorer.py').write_text('''"""Serve the bundled read-only explorer; no API key or packages required."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

parser=argparse.ArgumentParser(description="Start the LexCollude evidence explorer")
parser.add_argument("--port",type=int,default=8080)
parser.add_argument("--no-browser",action="store_true")
args=parser.parse_args()
handler=partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parent))
server=ThreadingHTTPServer(("127.0.0.1",args.port),handler)
print(f"LexCollude is running on local port {args.port}. Press Ctrl-C to stop.",flush=True)
if not args.no_browser:webbrowser.open(f"http://127.0.0.1:{args.port}")
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
''')
    (site/'START-HERE.txt').write_text('''LexCollude evidence explorer

1. Unzip this bundle.
2. With Python 3 installed, run: python start_explorer.py
3. Your browser opens the read-only explorer. Press Ctrl-C in the terminal to stop it.

No packages, API key or database are required. The bundle includes the paper and all
displayed evidence. To choose another local port: python start_explorer.py --port 8081
The site can also be served by any ordinary static web server. Direct file opening
depends on browser policy; the managed cloud browser blocks file URLs, so the
local-server launcher is the tested path.

Main results: 144 Responses API episodes. Separate native Codex cohort: 72 episodes.
Do not pool these execution contexts. See the research paper for limitations.
''')
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
