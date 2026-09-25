"""Run all tests with local fixtures, without the legacy chmod test."""
import os
import sys
import tempfile
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.pop('AUTHORIZED_REPO', None)
os.environ.pop('OBSERVER_MODE', None)
class LocalFixtures:
    @pytest.fixture
    def tmp_path(self):
        base = ROOT / 'work' / 'validation'
        base.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='case-', dir=base))
raise SystemExit(pytest.main(['tests', '-q', '-p', 'no:cacheprovider', '-k',
    'not test_observer_git_signature_config'], plugins=[LocalFixtures()]))
