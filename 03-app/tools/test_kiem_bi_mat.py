"""Kiểm hồi quy bộ kiểm bí mật bằng repo Git tạm, không dùng bí mật thật."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECKER = Path(__file__).with_name('kiem-bi-mat.py')
CHECKPOINT = ('02-thuc-nghiem/results/V1-s3-Hy/phien-1/'
              'r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt')


class SecretCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git('init', '--quiet')
        (self.root / '.gitignore').write_text('.env\n*.pt\nnode_modules/\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, check=True)

    def write(self, name, text='local-test-value'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def check(self, expected):
        result = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                                env={**os.environ, 'PYTHONUTF8': '1'}, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_ignored_local_env_and_canonical_checkpoint_allowed(self):
        self.write('.env'); self.write(CHECKPOINT)
        self.check(0)

    def test_force_added_env_blocked(self):
        self.write('.env'); self.git('add', '-f', '.env')
        self.check(1)

    def test_force_added_checkpoint_blocked(self):
        self.write(CHECKPOINT); self.git('add', '-f', CHECKPOINT)
        self.check(1)

    def test_nonignored_env_blocked(self):
        (self.root / '.gitignore').write_text('', encoding='utf-8')
        self.write('.env'); self.check(1)

    def test_other_ignored_weight_not_whitelisted(self):
        self.write('other.pt'); self.check(1)

    def test_other_env_blocked(self):
        self.write('nested/.env'); self.check(1)

    def test_secret_in_source_still_blocked_without_echoing_value(self):
        fake = 'sk-' + 'x' * 40
        self.write('app.py', fake)
        result = self.check(1)
        self.assertNotIn(fake, result.stdout)

    def test_force_added_file_in_skipped_directory_checked(self):
        self.write('node_modules/leak.py', 'sk-' + 'x' * 40)
        self.git('add', '-f', 'node_modules/leak.py')
        self.check(1)

    def test_tracked_env_missing_from_worktree_still_blocked(self):
        self.write('.env'); self.git('add', '-f', '.env')
        (self.root / '.env').unlink(); self.check(1)

    def test_without_git_local_exceptions_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            self.root = Path(folder)
            self.write('.env'); self.check(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)

