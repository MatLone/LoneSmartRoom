"""Serve only the static Windows design preview on IPv4 loopback. No agent access."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import json
import os

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'docs/design/windows-dashboard-preview'
ALLOWED = {'/', '/index.html', '/dashboard.css', '/dashboard.js', '/audit-data.js',
           '/assets/logo-horizontal.svg', '/assets/logo-header-small.svg',
           '/assets/symbol.svg', '/assets/windows-icon.svg', '/assets/windows-icon.ico'}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_head(self):
        if unquote(urlsplit(self.path).path) not in ALLOWED:
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'; frame-src 'none'")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(PREVIEW))) as server:
        receipt = {'url': f'http://127.0.0.1:{server.server_port}/', 'pid': os.getpid(),
                   'bind': '127.0.0.1', 'staticPreviewOnly': True, 'agentAccess': False}
        output = ROOT / '.cache/validation/windows-dashboard-preview'
        output.mkdir(parents=True, exist_ok=True)
        (output / 'server.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(receipt), flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
