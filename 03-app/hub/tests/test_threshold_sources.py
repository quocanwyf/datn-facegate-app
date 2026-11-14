import importlib.util
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from gen_thresholds import derive
from m0_common import ROOT


def test_real_sources_match_seed():
    assert derive()['matches_seed']


def test_changed_seed_is_rejected(tmp_path):
    source = (ROOT / '03-app/db/seed.sql').read_text(encoding='utf-8')
    changed = tmp_path / 'seed.sql'
    changed.write_text(source.replace('0.4232754409313202', '0.4'), encoding='utf-8')
    assert not derive(changed)['matches_seed']
