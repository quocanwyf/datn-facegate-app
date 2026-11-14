"""Sao chép nguồn đóng băng nguyên byte; từ chối ghi đè bản vendor khác hash."""
from pathlib import Path
import hashlib
import json
import shutil

HUB = Path(__file__).resolve().parents[1]
ROOT = HUB.parent.parent
VENDOR = HUB / 'vendor'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sync() -> None:
    research = ROOT / '02-thuc-nghiem'
    pairs = [(research / 'code/train.py', VENDOR / 'code/train.py')]
    pairs += [(source, VENDOR / 'code/fr' / source.relative_to(research / 'code/fr'))
              for source in sorted((research / 'code/fr').rglob('*'))
              if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc']
    pairs += [(research / f'eval-test/evaltest/{name}.py', VENDOR / f'evaltest/{name}.py')
              for name in ('__init__', 'features', 'common')]
    pairs += [(research / 'eval-test/manifest/manifest_24.json', VENDOR / 'manifest/manifest_24.json'),
              (research / 'eval-test/tools/windows/logs/strip_map_ban_sao.json', VENDOR / 'manifest/strip_map_ban_sao.json')]
    rows = []
    # Kiểm toàn bộ đầu vào/đích trước khi sao, tránh ghi đè nguồn đóng băng.
    for source, destination in pairs:
        expected = digest(source)
        if destination.exists() and digest(destination) != expected:
            raise RuntimeError(f'Vendor khác nguồn, không ghi đè: {destination.relative_to(HUB)}')
        rows.append({'path': destination.relative_to(VENDOR).as_posix(), 'source': source.relative_to(ROOT).as_posix(), 'sha256': expected})
    for source, destination in pairs:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copyfile(source, destination)
        if digest(destination) != digest(source):
            raise RuntimeError(f'Hash sau sao không khớp: {destination.name}')
    # Giữ byte nguồn qua Git trên Windows, không chuyển đổi LF/CRLF trong vendor.
    attributes = VENDOR / '.gitattributes'
    if not attributes.exists():
        attributes.write_bytes(b'* -text\n')
    manifest = VENDOR / 'MANIFEST.sha256'
    content = json.dumps({'format': 1, 'files': rows}, ensure_ascii=False, indent=2) + '\n'
    if manifest.exists() and manifest.read_text(encoding='utf-8') != content:
        raise RuntimeError('Manifest vendor đã khác; không tự thay manifest đóng băng.')
    if not manifest.exists():
        manifest.write_text(content, encoding='utf-8', newline='\n')
    print(f'OK: {len(rows)} file vendor khớp SHA256; không chạy train.py.')


if __name__ == '__main__':
    sync()
