import hashlib
import json
from app.recog.model_loader import ROOT, VENDOR


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def test_vendor_matches_manifest_and_original_sources():
    records = json.loads((VENDOR / 'MANIFEST.sha256').read_text(encoding='utf-8'))['files']
    assert records
    for record in records:
        assert sha(VENDOR / record['path']) == record['sha256'], record['path']
        assert sha(ROOT / record['source']) == record['sha256'], record['source']
    print(f'Vendor: {len(records)} file khớp manifest và nguồn.')


def test_research_code_and_code_v1_critical_modules_equal():
    for folder in ('backbones', 'eval', 'align', 'utils'):
        source = ROOT / '02-thuc-nghiem/code/fr' / folder
        reference = ROOT / '02-thuc-nghiem/code-v1/fr' / folder
        source_paths = {file.relative_to(source) for file in source.rglob('*') if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc'}
        reference_paths = {file.relative_to(reference) for file in reference.rglob('*') if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc'}
        assert source_paths == reference_paths, folder
        for path in source_paths:
            assert sha(source / path) == sha(reference / path), f'{folder}/{path}'
    print('backbones/eval/align/utils của code và code-v1: byte-equal.')


def test_vendor_has_no_unmanifested_payload():
    records = json.loads((VENDOR / 'MANIFEST.sha256').read_text(encoding='utf-8'))['files']
    expected = {record['path'] for record in records} | {'MANIFEST.sha256', '.gitattributes'}
    # T13 được phép thêm đúng subtree silentface; 33 file T01 vẫn so byte với nguồn.
    actual = {file.relative_to(VENDOR).as_posix() for file in VENDOR.rglob('*') if file.is_file() and file.relative_to(VENDOR).parts[0] != 'silentface'}
    assert actual == expected


def test_t13_vendor_has_exact_manifested_payload():
    from app.recog.liveness import BUNDLE, verify_bundle
    manifest = verify_bundle()
    expected = set(manifest['sha256']) | {'manifest.json', 'NGUON.md'}
    actual = {file.relative_to(BUNDLE).as_posix() for file in BUNDLE.rglob('*') if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc'}
    assert actual == expected
