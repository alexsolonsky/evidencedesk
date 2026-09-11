#!/usr/bin/env python3
"""Validate review structure and evidence references, never semantic truth."""
import argparse
import json
from pathlib import Path


def validate_review(evidence, review):
    errors = []
    known = set()

    def error(path, message):
        errors.append({'path': path, 'message': message})

    if not isinstance(evidence, dict) or not isinstance(evidence.get('files'), list):
        error('evidence.files', 'Must be an array of file records')
    else:
        for index, file in enumerate(evidence['files']):
            path = f'evidence.files[{index}]'
            if not isinstance(file, dict):
                error(path, 'Must be an object')
                continue
            for key in ('added_lines', 'removed_lines'):
                lines = file.get(key)
                if not isinstance(lines, list):
                    error(f'{path}.{key}', 'Must be an array')
                    continue
                for offset, line in enumerate(lines):
                    location = f'{path}.{key}[{offset}].evidence_id'
                    eid = line.get('evidence_id') if isinstance(line, dict) else None
                    if not isinstance(eid, str) or not eid.strip():
                        error(location, 'Must be a nonempty string')
                    elif eid in known:
                        error(location, f'Duplicate evidence ID: {eid}')
                    else:
                        known.add(eid)

    claims = review.get('claims') if isinstance(review, dict) else None
    if not isinstance(claims, list):
        error('review.claims', 'Must be an array')
    else:
        if set(review) != {'claims'}:
            error('review', 'Only the claims field is allowed')
        for index, claim in enumerate(claims):
            path = f'review.claims[{index}]'
            if not isinstance(claim, dict):
                error(path, 'Must be an object')
                continue
            if set(claim) != {'claim', 'status', 'evidence_ids', 'rationale'}:
                error(path, 'Required fields are exactly claim, status, evidence_ids, rationale')
            for key in ('claim', 'rationale'):
                if not isinstance(claim.get(key), str) or not claim[key].strip():
                    error(f'{path}.{key}', 'Must be a nonempty string')
            status = claim.get('status')
            if not isinstance(status, str) or status not in ('supported', 'unsupported', 'uncertain'):
                error(f'{path}.status', 'Must be supported, unsupported, or uncertain')
            ids = claim.get('evidence_ids')
            if not isinstance(ids, list):
                error(f'{path}.evidence_ids', 'Must be an array of unique evidence ID strings')
                continue
            if status == 'supported' and not ids:
                error(f'{path}.evidence_ids', 'A supported claim requires at least one citation')
            seen = set()
            for offset, eid in enumerate(ids):
                location = f'{path}.evidence_ids[{offset}]'
                if not isinstance(eid, str) or not eid.strip():
                    error(location, 'Must be a nonempty string')
                    continue
                if eid in seen:
                    error(location, f'Duplicate citation ID within claim: {eid}')
                seen.add(eid)
                if eid not in known:
                    error(location, f'Unknown evidence ID: {eid}')

    return {'schema_version': 1, 'kind': 'structural_review_validation',
            'structurally_valid': not errors, 'semantic_truth_checked': False,
            'notice': 'Checks JSON structure and reference existence only. '
                      'Does not establish that citations support claims or that claims are true.',
            'claim_count': len(claims) if isinstance(claims, list) else None,
            'evidence_id_count': len(known), 'errors': errors}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON object key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'Invalid JSON constant: {value}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('review', type=Path)
    args = parser.parse_args()
    try:
        documents = [json.loads(path.read_text(encoding='utf8'),
                                object_pairs_hook=unique_object, parse_constant=reject_constant)
                     for path in (args.evidence, args.review)]
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f'EvidenceDesk: {exc}\n')
    result = validate_review(*documents)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['structurally_valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
