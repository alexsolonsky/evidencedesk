import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import local_review as lr
from app import Handler

DIFF = 'diff --git a/config.py b/config.py\n--- a/config.py\n+++ b/config.py\n@@ -1 +1 @@\n-timeout = 10\n+timeout = 30\n'


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.pack = lr.build_pack(DIFF)
        self.ids = list(lr.evidence_index(self.pack))

    def fake(self, review):
        def request(path, body=None, timeout=2):
            if path == '/api/tags':
                return {'models': [{'name': 'local-test', 'size': 1, 'digest': 'test'}]}
            self.assertEqual(path, '/api/chat')
            enum = body['format']['properties']['claims']['items']['properties']['evidence_ids']['items']['enum']
            self.assertEqual(set(enum), set(self.ids))
            self.assertFalse(body['stream'])
            return {'done': True, 'message': {'content': json.dumps(review)}}
        return request

    def test_end_to_end_claim_has_exact_source_text_and_coordinates(self):
        review = {'claims': [{'claim': 'Timeout changes from 10 to 30.', 'status': 'supported',
                              'evidence_ids': self.ids, 'rationale': 'Both changed assignment lines are present.'}]}
        with patch('local_review.request', self.fake(review)):
            result = lr.review_pack(self.pack, 'local-test')
        self.assertTrue(result['validation']['structurally_valid'])
        self.assertFalse(result['validation']['semantic_truth_checked'])
        self.assertEqual({x['text'] for x in result['evidence_index'].values()}, {'timeout = 10', 'timeout = 30'})
        self.assertEqual({x['line'] for x in result['evidence_index'].values()}, {1})
        self.assertEqual({x['side'] for x in result['evidence_index'].values()}, {'new', 'old'})

    def test_model_invented_reference_is_rejected_not_repaired(self):
        review = {'claims': [{'claim': 'All tests pass.', 'status': 'supported',
                              'evidence_ids': ['E-made-up'], 'rationale': 'A hallucinated citation.'}]}
        with patch('local_review.request', self.fake(review)):
            result = lr.review_pack(self.pack, 'local-test')
        self.assertFalse(result['validation']['structurally_valid'])
        self.assertEqual(result['review'], review)

    def test_missing_runtime_has_no_fixture_or_cloud_fallback(self):
        with patch('local_review.request', side_effect=lr.RuntimeUnavailable('offline')) as req:
            with self.assertRaises(lr.RuntimeUnavailable):
                lr.review_pack(self.pack)
        self.assertEqual(req.call_count, 1)

    def test_cloud_models_are_not_offered(self):
        with patch('local_review.request', return_value={'models': [
            {'name': 'qwen:cloud', 'size': 100}, {'name': 'remote', 'size': 0}]}):
            self.assertFalse(lr.runtime_status()['available'])

    def test_context_limit_rejects_without_truncating(self):
        pack = lr.build_pack(DIFF.replace('timeout = 30', 'x' * 22000))
        with patch('local_review.request', self.fake({'claims': []})) as req:
            with self.assertRaisesRegex(ValueError, 'context limit'):
                lr.review_pack(pack, 'local-test')

    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError):
            lr.strict_json('{"claims":[],"claims":[]}')

    def test_line_addition_does_not_imply_new_file(self):
        index = lr.evidence_index(self.pack)
        self.assertEqual({x['file_status'] for x in index.values()}, {'modified'})
        self.assertEqual({x['old_path'] for x in index.values()}, {'config.py'})
        self.assertEqual({x['new_path'] for x in index.values()}, {'config.py'})

    def test_no_newline_marker_on_context_is_not_attached_to_changed_line(self):
        from pathlib import Path
        pack = lr.build_pack(Path('fixtures/semantic-v2/eof.diff').read_text())
        index = lr.evidence_index(pack)
        self.assertTrue(all(not x['no_newline_at_eof'] for x in index.values() if x['path'] == 'message.txt'))
        self.assertTrue(next(x['no_newline_at_eof'] for x in index.values()
                             if x['path'] == 'end.txt' and x['side'] == 'new'))


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def post(self, path, data, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        req = urllib.request.Request(self.base + path, json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.load(r)

    def test_diff_to_imported_review_through_http(self):
        result = self.post('/api/analyze', {'diff': DIFF})
        ids = list(result['evidence_index'])
        review = {'claims': [{'claim': 'Timeout changes.', 'status': 'supported',
                              'evidence_ids': ids, 'rationale': 'Assignment changed.'}]}
        result = self.post('/api/validate', {'diff': DIFF, 'review': json.dumps(review)})
        self.assertTrue(result['validation']['structurally_valid'])
        self.assertFalse(result['provenance']['authorship_verified'])

    def test_other_website_cannot_trigger_local_inference(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post('/api/review', {'diff': DIFF}, 'https://example.com')
        self.assertEqual(caught.exception.code, 403)

    def test_injection_text_remains_data(self):
        malicious = '<script>alert("unsafe")</script>'
        result = self.post('/api/analyze', {'diff': DIFF.replace('timeout = 30', malicious)})
        self.assertIn(malicious, [x['text'] for x in result['evidence_index'].values()])
        # The client renders untrusted strings with textContent, not HTML parsing.
        from pathlib import Path
        source = Path(__file__).with_name('app.js').read_text()
        self.assertNotIn('innerHTML', source)
        self.assertNotIn('eval(', source)


if __name__ == '__main__':
    unittest.main()
