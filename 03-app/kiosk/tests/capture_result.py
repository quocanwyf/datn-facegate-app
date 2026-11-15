"""Chờ log result thật, chụp bằng chứng ngoài repo; không ghi khuôn mặt vào Git."""
import argparse
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('--seconds', type=int, default=60)
args = parser.parse_args()
adb = 'C:/Developer/Tools/Android/SDK/platform-tools/adb.exe'
prefix = [adb, '-s', 'emulator-5556']
private = Path(os.environ['LOCALAPPDATA']) / 'FaceGate/T08-evidence'
private.mkdir(parents=True, exist_ok=True)
process = subprocess.Popen(prefix + ['logcat', '-T', '1', '-s', 'ReactNativeJS:I', '*:S'], stdout=subprocess.PIPE, text=True, encoding='utf8', errors='replace')
try:
    import threading
    timer = threading.Timer(args.seconds, process.terminate)
    timer.start()
    for line in process.stdout:
        if 'FACEGATE_SCENE' in line and "'result'" in line:
            time.sleep(.8)
            remote = '/sdcard/fg-result.png'
            subprocess.run(prefix + ['shell', 'screencap', '-p', remote], check=True)
            subprocess.run(prefix + ['pull', remote, str(private / (args.name + '.png'))], check=True)
            subprocess.run(prefix + ['shell', 'rm', '-f', remote], check=True)
            print('Captured actual native result outside Git: ' + args.name)
            break
    else:
        raise SystemExit('Không thấy result trong thời gian chờ.')
finally:
    timer.cancel()
    process.terminate()
    process.wait(timeout=5)
