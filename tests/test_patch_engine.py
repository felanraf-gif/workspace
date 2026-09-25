"""Controlled patch regressions: no Git execution or permission changes."""
import pytest
from core import observer_policy as policy
from brain.patch_engine import Patch, PatchEngine


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    root.mkdir()
    (root / '.git').mkdir()
    monkeypatch.setenv('OBSERVER_MODE', 'false')
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization.from_startup(str(root)))
    engine = PatchEngine()
    engine._project_root = str(root)
    return root, engine


def patch(file='test.py', content='VALUE = 2\n'):
    return Patch('test', file, 'test patch', 'VALUE = 1\n', content, confidence=1.0)


def test_outside_root_is_rejected(repo, tmp_path):
    root, engine = repo
    outside = tmp_path / 'outside.py'
    outside.write_text('original')
    assert not engine.apply_patch(patch(str(outside)))
    assert outside.read_text() == 'original'


def test_invalid_python_has_no_side_effects(repo):
    root, engine = repo
    (root / 'test.py').write_text('VALUE = 1\n')
    assert engine.apply_patch(patch(content='def broken(:\n')) is False
    assert (root / 'test.py').read_text() == 'VALUE = 1\n'
    assert not list(root.glob('*.backup.*'))


def test_valid_patch_is_verified_without_git(repo, monkeypatch):
    import subprocess
    root, engine = repo
    (root / 'test.py').write_text('VALUE = 1\n')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('Git was executed'))
    change = patch()
    assert engine.apply_patch(change) is True
    assert (root / 'test.py').read_text() == 'VALUE = 2\n'
    assert change.applied
    assert engine.rollback(change) is True
    assert (root / 'test.py').read_text() == 'VALUE = 1\n'


def test_new_file_removed_on_verification_failure(repo, monkeypatch):
    root, engine = repo
    monkeypatch.setattr(engine, 'verify_patch', lambda p: (False, 'forced verification failure'))
    assert engine.apply_patch(patch()) is False
    assert not (root / 'test.py').exists()


def test_batch_preflight_blocks_all_writes_on_outside_target(repo, tmp_path):
    root, engine = repo
    assert engine.apply_patches([patch(), patch(str(tmp_path / 'outside.py'))]) == []
    assert not (root / 'test.py').exists()


def test_multiple_valid_patches_do_not_commit(repo, monkeypatch):
    import subprocess
    root, engine = repo
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('Git was executed'))
    assert len(engine.apply_patches([patch(), patch('second.py')])) == 2
    assert (root / 'test.py').read_text() == 'VALUE = 2\n'
    assert (root / 'second.py').read_text() == 'VALUE = 2\n'
    assert list((root / '.git').iterdir()) == []


def test_multiple_patches_roll_back_on_late_failure(repo, monkeypatch):
    root, engine = repo
    (root / 'test.py').write_text('VALUE = 1\n')
    original = engine.verify_patch
    monkeypatch.setattr(engine, 'verify_patch', lambda p: (False, 'forced') if p.file == 'second.py' else original(p))
    assert engine.apply_patches([patch(), patch('second.py')]) == []
    assert (root / 'test.py').read_text() == 'VALUE = 1\n'
    assert not (root / 'second.py').exists()


def test_rollback_outside_authority_is_denied(repo, tmp_path):
    root, engine = repo
    outside = tmp_path / 'outside'
    outside.write_text('original')
    change = patch(str(outside))
    assert engine.rollback(change) is False
    assert outside.read_text() == 'original'


def test_explicit_no_confirmation_never_writes(repo):
    root, engine = repo
    target = root / 'test.py'
    target.write_text('VALUE = 1\n')
    assert not engine.apply_patches([patch()], auto_confirm=False)
    assert target.read_text() == 'VALUE = 1\n'
    assert not list(root.glob('*.backup.*'))
