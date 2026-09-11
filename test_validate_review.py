import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_review import validate_review

HERE = Path(__file__).parent


class ReviewValidationTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {'files': [{'added_lines': [{'evidence_id': 'E-one'}],
                                    'removed_lines': [{'evidence_id': 'E-two'}]}]}
        self.review = {'claims': [{'claim': 'Example claim', 'status': 'supported',
                                  'evidence_ids': ['E-one'], 'rationale': 'Example explanation'}]}

    def validate(self):
        return validate_review(self.evidence, self.review)

    def test_valid_is_explicitly_not_semantic_verification(self):
        self.review['claims'][0]['claim'] = 'The moon is made of cheese'
        result = self.validate()
        self.assertTrue(result['structurally_valid'])
        self.assertFalse(result['semantic_truth_checked'])
        self.assertEqual(result['kind'], 'structural_review_validation')

    def test_unknown_reference(self):
        self.review['claims'][0]['evidence_ids'] = ['E-missing']
        self.assertIn('Unknown evidence ID', self.validate()['errors'][0]['message'])

    def test_supported_requires_citation_other_statuses_allow_none(self):
        self.review['claims'][0]['evidence_ids'] = []
        self.assertFalse(self.validate()['structurally_valid'])
        for status in ('unsupported', 'uncertain'):
            self.review['claims'][0]['status'] = status
            self.assertTrue(self.validate()['structurally_valid'])

    def test_duplicate_evidence_and_citations_rejected(self):
        self.evidence['files'][0]['removed_lines'][0]['evidence_id'] = 'E-one'
        self.assertFalse(self.validate()['structurally_valid'])
        self.evidence['files'][0]['removed_lines'][0]['evidence_id'] = 'E-two'
        self.review['claims'][0]['evidence_ids'] = ['E-one', 'E-one']
        self.assertFalse(self.validate()['structurally_valid'])

    def test_reuse_across_claims_is_valid(self):
        self.review['claims'].append(copy.deepcopy(self.review['claims'][0]))
        self.assertTrue(self.validate()['structurally_valid'])

    def test_malformed_claim_fields(self):
        for field, value in [('status', 'true'), ('status', []), ('claim', 3),
                             ('rationale', '  '), ('evidence_ids', 'E-one'),
                             ('evidence_ids', [{}]), ('evidence_ids', [None])]:
            review = copy.deepcopy(self.review)
            review['claims'][0][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(validate_review(self.evidence, review)['structurally_valid'])
        del self.review['claims'][0]['rationale']
        self.assertFalse(self.validate()['structurally_valid'])

    def test_malformed_documents_fail_without_exceptions(self):
        for evidence in (None, [], {}, {'files': [3]}, {'files': [{}]},
                         {'files': [{'added_lines': [None], 'removed_lines': []}]}):
            with self.subTest(evidence=evidence):
                self.assertFalse(validate_review(evidence, self.review)['structurally_valid'])
        for review in (None, [], {}, {'claims': {}}, {'claims': [None]},
                       {'claims': [], 'extra': True}):
            with self.subTest(review=review):
                self.assertFalse(validate_review(self.evidence, review)['structurally_valid'])
        self.assertTrue(validate_review({'files': []}, {'claims': []})['structurally_valid'])

    def test_cli_exit_codes_and_strict_json(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / 'evidence.json'
            review = Path(directory) / 'review.json'
            evidence.write_text(json.dumps(self.evidence))
            def run(content):
                review.write_text(content)
                return subprocess.run([sys.executable, str(HERE / 'validate_review.py'),
                                       str(evidence), str(review)], capture_output=True, text=True)
            result = run(json.dumps(self.review))
            self.assertEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)['semantic_truth_checked'])
            result = run('{"claims":[{}]}')
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)['structurally_valid'])
            for invalid in ('{', '{"claims":[],"claims":[]}', '{"claims":NaN}'):
                result = run(invalid)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
