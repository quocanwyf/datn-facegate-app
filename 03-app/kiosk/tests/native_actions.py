"""Thao tác UI Android thật qua ADB; không gọi handler React hoặc giả dữ liệu Hub."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

ADB = 'C:/Developer/Tools/Android/SDK/platform-tools/adb.exe'
SERIAL = 'emulator-5556'

def adb(*args, timeout=20):
    result = subprocess.run([ADB, '-s', SERIAL, *args], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout

def ui():
    for _ in range(5):
        path = '/sdcard/fg-t08-' + uuid.uuid4().hex + '.xml'
        try:
            result = adb('shell', 'timeout', '12', 'uiautomator', 'dump', path)
            if 'dumped to' in result:
                return ET.fromstring(adb('exec-out', 'cat', path))
        except (RuntimeError, subprocess.TimeoutExpired):
            pass
        finally:
            adb('shell', 'rm', '-f', path)
        time.sleep(.5)
    raise RuntimeError('UI chưa sẵn sàng; không dùng lại XML cũ.')

def center(node):
    x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.attrib['bounds']))
    if x2 <= x1 or y2 <= y1:
        raise RuntimeError('Phần tử không có vùng chạm.')
    return (x1 + x2) // 2, (y1 + y2) // 2

def tap(text=None, label=None, test_id=None):
    root = ui(); parents = {child: parent for parent in root.iter() for child in parent}
    app = next((node for node in root.iter('node') if node.get('package') == 'vn.ptit.facegate.kiosk'), None)
    if app is None:
        raise RuntimeError('Kiosk không ở phía trước; dừng để tránh chạm nhầm app khác.')
    viewport = list(map(int, re.findall(r'\d+', app.attrib['bounds'])))
    found = []
    for node in root.iter('node'):
        if node.get('package') != 'vn.ptit.facegate.kiosk':
            continue
        if not ((text is not None and node.get('text') == text) or (label is not None and node.get('content-desc') == label) or (test_id is not None and node.get('resource-id', '').endswith(test_id))):
            continue
        selected = node
        if text is not None:
            while selected in parents and selected.get('clickable') != 'true':
                selected = parents[selected]
            numbers = re.findall(r'\d+', selected.get('bounds', ''))
            if selected.get('clickable') != 'true' or len(numbers) != 4 or int(numbers[3]) - int(numbers[1]) > 180:
                continue
        if selected.get('enabled') != 'false':
            x, y = center(selected)
            if viewport[0] <= x < viewport[2] and viewport[1] <= y < viewport[3]:
                found.append(selected)
    if not found:
        raise RuntimeError('Không tìm thấy điều khiển đang bật: ' + str(text or label or test_id))
    x, y = center(found[-1]); adb('shell', 'input', 'tap', str(x), str(y)); time.sleep(.25)

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['dump', 'tap', 'pair', 'entry', 'pin', 'employee', 'agree'])
parser.add_argument('value', nargs='?')
args = parser.parse_args()
if args.action == 'dump':
    print(json.dumps([{k: node.get(k) for k in ['text', 'content-desc', 'resource-id', 'bounds', 'clickable', 'enabled']} for node in ui().iter('node') if node.get('text') or node.get('content-desc')], ensure_ascii=False))
elif args.action == 'tap':
    tap(text=args.value)
elif args.action == 'pair':
    context = json.loads((Path(os.environ['LOCALAPPDATA']) / 'FaceGate/T08-last-context.json').read_text(encoding='utf8'))
    invitation = json.loads((Path(context['data_dir']) / 'native-review-context.json').read_text(encoding='utf8'))
    code = invitation['pairing_code']
    assert re.fullmatch(r'\d{6}', code)
    tap(label='Mã ghép 6 số'); adb('shell', 'input', 'text', code); adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
    adb('shell', 'input', 'swipe', '450', '530', '450', '200', '600'); time.sleep(.8)
    tap(text='Ghép thiết bị')
elif args.action == 'entry':
    adb('shell', 'input', 'swipe', '1232', '48', '1232', '48', '3300')
elif args.action == 'pin':
    tap(text=args.value)
    for digit in '2468':
        tap(text=digit)
elif args.action == 'employee':
    tap(label='Tìm tên hoặc mã nhân viên'); adb('shell', 'input', 'text', 'NV006'); time.sleep(1)
    adb('shell', 'input', 'keyevent', 'KEYCODE_BACK'); tap(text='Chọn')
elif args.action == 'agree':
    tap(text='Đồng ý')
print('UI action completed: ' + args.action)
