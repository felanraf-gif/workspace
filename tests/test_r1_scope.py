"""R1: data and plans cannot grant write authority."""
import os
import subprocess
from dataclasses import FrozenInstanceError

import pytest

from core import observer_policy as policy
from core import observer_storage as storage
from tools.file_tools import FileTools
from tools.executor import ToolExecutor
from tools.bash_tools import BashTools
from tools.git_tools import GitTools
from brain.roles.builder import Builder
from brain.patch_engine import PatchEngine, Patch


@pytest.fixture
def repos(tmp_path, monkeypatch):
    a, b = tmp_path / 'A', tmp_path / 'B'
    for root in (a, b):
        root.mkdir()
        (root / '.git').mkdir()
        (root / 'data.txt').write_text('original')
    monkeypatch.setenv('OBSERVER_MODE', 'false')
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization.from_startup(str(a)))
    monkeypatch.setattr(storage, '_files', {})
    monkeypatch.setattr(storage, '_directories', set())
    return a, b


def test_decisive_scope_and_broad_analysis(repos, monkeypatch):
    a, b = repos
    ft = FileTools()
    assert ft.write(str(a / 'data.txt'), 'allowed')['success']
    assert ft.read(str(b / 'data.txt'))['content'] == 'original'
    executor = ToolExecutor()
    assert executor.execute_tool('file_read', {'path': str(b / 'data.txt')})['success']
    (a / 'escape').symlink_to(b, target_is_directory=True)
    monkeypatch.chdir(a)
    for path in ('../B/data.txt', str(b / 'data.txt'), str(a / 'escape' / 'data.txt')):
        assert ft.write(path, 'forbidden')['blocked']
        assert ft.edit(path, 'original', 'forbidden')['blocked']
        assert executor.execute_tool('file_write', {'path': path, 'content': 'bad'})['blocked']
    assert (a / 'data.txt').read_text() == 'allowed'
    assert (b / 'data.txt').read_text() == 'original'
    assert sorted(p.name for p in b.iterdir()) == ['.git', 'data.txt']


def test_missing_authority_blocks_writes_but_keeps_analysis(repos, monkeypatch):
    a, b = repos
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization(None))
    assert FileTools().write(str(a / 'new'), 'no')['blocked']
    assert FileTools().edit(str(a / 'data.txt'), 'original', 'no')['blocked']
    engine = PatchEngine()
    engine._project_root = str(a)
    patch = Patch('test', 'new.py', 'new', None, 'x = 1\n')
    assert engine.apply_patch(patch)['blocked']
    assert engine.apply_patches([patch])['blocked']
    assert engine.rollback(patch)['blocked']
    result = Builder(executor=__import__('brain.executor', fromlist=['Executor']).Executor()).build(
        {'tasks': [{'action': 'analyze', 'target': str(b / 'data.txt')}]})
    assert result['summary']['success'] == 1
    assert not (a / 'new').exists()


def test_scope_is_frozen_and_not_taken_from_environment_or_plan(repos, monkeypatch):
    a, b = repos
    monkeypatch.setenv('AUTHORIZED_REPO', str(b))
    assert policy.authorized_repo() == str(a)
    with pytest.raises(FrozenInstanceError):
        policy._AUTHORIZATION.root = str(b)
    task = {'action': 'patch', 'project_root': str(b), 'AUTHORIZED_REPO': str(b),
            'issue': {'type': 'structure', 'issue': 'Brak punktu wejścia'}}
    assert Builder().build({'AUTHORIZED_REPO': str(b), 'tasks': [task]})['summary']['success'] == 0
    engine = PatchEngine()
    engine.suggest([], {'path': str(b), 'files': []})
    assert not engine.apply_patch(Patch('test', 'new.py', 'new', None, 'x = 1\n'))
    assert not (b / 'new.py').exists()
    assert policy.authorized_repo() == str(a)


def test_uncontrolled_execution_never_spawns(repos, monkeypatch):
    a, b = repos
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('process spawned'))
    shell = BashTools(cwd=str(a))
    for result in (shell.run('echo bad > ../B/data.txt'), shell.run_python('print(1)'),
                   shell.check_output('pwd'), shell.is_available('git'),
                   GitTools(str(a)).add(), GitTools(str(a)).commit('bad'),
                   PatchEngine()._git_commit(None), PatchEngine()._git_commit_batch([])):
        assert result['blocked']
    executor = ToolExecutor()
    executor.registry.register('unknown', lambda: pytest.fail('unknown tool ran'))
    assert executor.execute_tool('unknown', {})['blocked']
    class Trap:
        def execute(self, task):
            pytest.fail('Builder delegated command')
    result = Builder(Trap()).build({'tasks': [{'action': 'execute', 'target': 'anything'}]})
    assert result['summary']['success'] == 0


def test_backups_nested_repos_and_hardlinks_cannot_escape(repos):
    a, b = repos
    target = a / 'data.txt'
    (a / 'data.txt.edit.backup').symlink_to(b / 'data.txt')
    assert not FileTools().edit(str(target), 'original', 'changed')['success']
    assert target.read_text() == 'original'
    nested = a / 'nested'
    nested.mkdir()
    (nested / '.git').mkdir()
    assert FileTools().write(str(nested / 'new'), 'bad')['blocked']
    link = a / 'hardlink'
    os.link(b / 'data.txt', link)
    assert FileTools().write(str(link), 'bad')['blocked']
    assert (b / 'data.txt').read_text() == 'original'
    assert FileTools().write(str(a / '.git' / 'config'), 'bad')['blocked']


def test_runtime_state_outside_scope_stays_in_memory(repos, monkeypatch):
    a, b = repos
    for root in (a, b):
        with storage.open(root / 'state.txt', 'w') as stream:
            stream.write('state')
    assert (a / 'state.txt').read_text() == 'state'
    assert not (b / 'state.txt').exists()
    with storage.open(b / 'state.txt') as stream:
        assert stream.read() == 'state'
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization(None))
    storage.os.makedirs(b / 'virtual', exist_ok=True)
    with storage.open(b / 'virtual' / 'state', 'w') as stream:
        stream.write('virtual')
    assert not (b / 'virtual').exists()
    assert storage.os.remove(b / 'data.txt')['blocked']
    assert storage.os.rename(a / 'data.txt', b / 'data.txt')['blocked']


@pytest.mark.parametrize('value', [None, '', '.', '/not/a/real/repository'])
def test_invalid_startup_authority_fails_closed(value):
    assert policy.RepoAuthorization.from_startup(value).root is None


def test_dotenv_is_not_authority_and_late_environment_changes_are_ignored(repos):
    import json
    import sys
    a, b = repos
    (a / '.env').write_text(f'AUTHORIZED_REPO={b}\n')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OBSERVER_MODE='false')
    env.pop('AUTHORIZED_REPO', None)
    code = ('from core import observer_policy as p; from dotenv import load_dotenv; '
            'load_dotenv(' + repr(str(a / '.env')) + '); '
            'import os,json; print(json.dumps([p.authorized_repo(),os.getenv("AUTHORIZED_REPO")]))')
    result = subprocess.run([sys.executable, '-B', '-c', code], env=env,
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == [None, str(b)]
    env['AUTHORIZED_REPO'] = str(a)
    result = subprocess.run([sys.executable, '-B', '-c', code], env=env,
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)[0] == str(a)


@pytest.mark.parametrize('swap_parent', [False, True])
def test_symlink_swap_before_open_cannot_redirect_write(repos, monkeypatch, swap_parent):
    a, b = repos
    parent = a / 'dir'
    parent.mkdir()
    target = parent / 'data.txt'
    target.write_text('original')
    real_open = os.open
    swapped = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal swapped
        trigger = 'dir' if swap_parent else 'data.txt'
        if path == trigger and not swapped:
            swapped = True
            if swap_parent:
                parent.rename(a / 'retained-dir')
                parent.symlink_to(b, target_is_directory=True)
            else:
                target.unlink()
                target.symlink_to(b / 'data.txt')
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', racing_open)
    result = FileTools().write(str(target), 'forbidden', backup=False)
    assert not result['success']
    assert swapped
    assert (b / 'data.txt').read_text() == 'original'


def test_git_read_protections_also_apply_outside_observer(repos, monkeypatch):
    from brain.project_tracker import ProjectTracker
    a, b = repos
    calls = []

    def capture(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, '', '')

    monkeypatch.setattr(subprocess, 'run', capture)
    assert GitTools(str(b)).status()['success']
    assert 'error' not in ProjectTracker()._get_git_metrics(str(b))
    for command in calls:
        if command[1] == 'config':
            continue
        assert '--no-optional-locks' in command
        assert '--no-pager' in command
        assert 'core.fsmonitor=false' in command
        assert 'core.hooksPath=/dev/null' in command
        assert 'log.showSignature=false' in command
