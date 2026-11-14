import os
import subprocess
import sys
from app.recog.model_loader import VENDOR


def test_import_uses_only_vendor_without_research_on_sys_path(tmp_path):
    code = '''
import json,os,sys
from pathlib import Path
vendor=Path(sys.argv[1]).resolve()
os.environ['DATN_CODE_DIR']=str(vendor/'code')
sys.path=[str(vendor)]+[path for path in sys.path if '02-thuc-nghiem' not in path]
import evaltest.features
import fr.backbones
assert all('02-thuc-nghiem' not in path for path in sys.path)
assert Path(evaltest.features.__file__).resolve().is_relative_to(vendor)
assert Path(fr.backbones.__file__).resolve().is_relative_to(vendor)
print(json.dumps({'features':evaltest.features.__file__,'backbones':fr.backbones.__file__,'research_on_sys_path':False}))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(VENDOR)], cwd=tmp_path,
                            env={**os.environ, 'PYTHONUTF8': '1'}, capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout)
