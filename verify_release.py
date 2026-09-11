#!/usr/bin/env python3
"""Verify a source release against its unsigned SHA-256 inventory (no network)."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'release-manifest.json').read_text(encoding='utf8'))
errors = []
expected = {'release-manifest.json'}
for item in manifest['files']:
    name = item['path']
    path = root / name
    if path.is_symlink() or not path.is_file() or '..' in Path(name).parts or Path(name).is_absolute():
        errors.append({'path': name, 'error': 'invalid or missing file'})
        continue
    raw = path.read_bytes()
    if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
        errors.append({'path': name, 'error': 'checksum or size mismatch'})
    expected.add(name)
ignored_parts = {'.git', '__pycache__', '.venv', 'venv'}
for path in root.rglob('*'):
    rel = path.relative_to(root)
    if any(part in ignored_parts for part in rel.parts):
        continue
    if path.is_symlink() or (path.is_file() and rel.as_posix() not in expected):
        errors.append({'path': rel.as_posix(), 'error': 'unexpected file'})
print(json.dumps({'release': manifest['release'], 'verified': not errors,
                  'file_count': len(manifest['files']), 'errors': errors}, indent=2))
raise SystemExit(bool(errors))
