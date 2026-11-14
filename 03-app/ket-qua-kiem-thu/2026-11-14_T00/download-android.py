"""Tải archive Android chính thức bằng HTTP Range, kiểm kích thước/SHA/CRC trước dùng."""
import argparse
import concurrent.futures
import hashlib
import os
from pathlib import Path
import time
import urllib.request
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('destination', type=Path)
parser.add_argument('--sha256')
parser.add_argument('--sha1')
args = parser.parse_args()
if not args.url.startswith('https://dl.google.com/'):
    raise SystemExit('Chỉ dùng nguồn HTTPS dl.google.com đã đối chiếu.')
headers = {'Accept-Encoding': 'identity', 'User-Agent': 'FaceGate-dev-setup'}
with urllib.request.urlopen(urllib.request.Request(args.url, headers=headers, method='HEAD'), timeout=30) as response:
    total = int(response.headers['Content-Length'])
args.destination.parent.mkdir(parents=True, exist_ok=True)
with args.destination.open('wb') as stream:
    stream.truncate(total)
chunk = 1024 * 1024
start_time = time.monotonic()


def fetch(offset):
    end = min(offset + chunk, total) - 1
    for attempt in range(4):
        try:
            request = urllib.request.Request(args.url, headers={**headers, 'Range': f'bytes={offset}-{end}'})
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{end}/{total}':
                    raise ValueError('Phản hồi Range không khớp yêu cầu')
                data = response.read()
            if len(data) != end - offset + 1:
                raise ValueError('Thiếu byte trong segment')
            with args.destination.open('r+b') as stream:
                stream.seek(offset)
                stream.write(data)
            return len(data)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


print(f'Nguồn {args.url}; kích thước {total} bytes', flush=True)
completed = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
    futures = [pool.submit(fetch, offset) for offset in range(0, total, chunk)]
    for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
        completed += future.result()
        if index % 64 == 0 or completed == total:
            print(f'Đã nhận {completed}/{total} bytes; {time.monotonic() - start_time:.1f}s', flush=True)
digest = hashlib.file_digest(args.destination.open('rb'), 'sha256').hexdigest()
print(f'SHA256 {digest}', flush=True)
if args.sha256 and digest != args.sha256:
    raise SystemExit('SHA256 không khớp nguồn công bố; không giải nén.')
if args.sha1:
    with args.destination.open('rb') as stream:
        sha1 = hashlib.file_digest(stream, 'sha1').hexdigest()
    if sha1 != args.sha1:
        raise SystemExit('Checksum SHA1 không khớp metadata SDK chính thức; không giải nén.')
    print('SHA1 khớp metadata SDK chính thức.', flush=True)
with zipfile.ZipFile(args.destination) as archive:
    bad_member = archive.testzip()
    if bad_member:
        raise SystemExit(f'CRC lỗi: {bad_member}')
print('Đủ byte và CRC ZIP hợp lệ' + ('; SHA256 khớp nguồn công bố.' if args.sha256 else '.'), flush=True)
