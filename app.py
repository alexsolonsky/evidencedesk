#!/usr/bin/env python3
"""EvidenceDesk private loopback UI. No accounts, uploads, database, or cloud AI."""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from local_review import (RuntimeUnavailable, build_pack, evidence_index, review_pack,
                          runtime_status, strict_json)
from validate_review import validate_review

ROOT = Path(__file__).resolve().parent
INFERENCE_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log user diff/review data.

    def allowed(self):
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        return host in allowed and (not origin or origin in {'http://' + h for h in allowed})

    def send(self, status, content, content_type='application/json; charset=utf-8'):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if not self.allowed():
            return self.send(403, {'error': 'Loopback access only'})
        routes = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if self.path in routes:
            file, kind = routes[self.path]
            return self.send(200, (ROOT / file).read_bytes(), kind)
        if self.path == '/api/status':
            return self.send(200, runtime_status())
        if self.path == '/api/example':
            return self.send(200, {'diff': (ROOT / 'fixtures/mixed.diff').read_text(),
                                   'kind': 'synthetic_demo_fixture'})
        self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.allowed():
            return self.send(403, {'error': 'Cross-origin requests are not allowed'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send(415, {'error': 'Use application/json'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 524288:
                return self.send(413, {'error': 'Request limit: 512 KB'})
            data = strict_json(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Request must be a JSON object')
            pack = build_pack(data.get('diff'))
            if self.path == '/api/analyze':
                result = {'evidence_pack': pack, 'evidence_index': evidence_index(pack)}
            elif self.path == '/api/validate':
                review = strict_json(data.get('review', ''))
                result = {'evidence_pack': pack, 'evidence_index': evidence_index(pack),
                          'review': review, 'validation': validate_review(pack, review),
                          'provenance': {'kind': 'imported_review', 'model': None,
                                         'authorship_verified': False, 'semantic_truth_checked': False}}
            elif self.path == '/api/review':
                if not INFERENCE_LOCK.acquire(blocking=False):
                    return self.send(429, {'error': 'A local review is already running'})
                try:
                    result = review_pack(pack, data.get('model', 'qwen3.6:35b'))
                finally:
                    INFERENCE_LOCK.release()
                result['evidence_pack'] = pack
            else:
                return self.send(404, {'error': 'Not found'})
            self.send(200, result)
        except RuntimeUnavailable as exc:
            self.send(503, {'error': str(exc), 'status': 'inference_unavailable', 'fixture_used': False})
        except (ValueError, TypeError, UnicodeError) as exc:
            self.send(400, {'error': str(exc)})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8769)
    args = p.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'EvidenceDesk local UI: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    main()
