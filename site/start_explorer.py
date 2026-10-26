"""Serve the bundled read-only explorer; no API key or packages required."""
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
