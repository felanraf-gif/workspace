"""R1 Git reads must not spawn repository-configured helpers."""
import subprocess

import pytest

from brain.project_tracker import ProjectTracker
from core import observer_policy as policy
from tools.git_tools import GitTools


def git_at(repo, *args, input=None):
    return subprocess.run(['git', *args], cwd=repo, input=input,
                          text=True, capture_output=True, check=True).stdout.strip()


@pytest.mark.parametrize('observer', ['false', 'true'])
def test_submodule_helpers_are_not_run(tmp_path, monkeypatch, observer):
    monkeypatch.delenv('AUTHORIZED_REPO', raising=False)
    monkeypatch.setenv('OBSERVER_MODE', observer)
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization(None))
    parent = tmp_path / 'parent'
    child = parent / 'child'
    child.mkdir(parents=True)
    for repo in (parent, child):
        git_at(repo, 'init', '-q')
        git_at(repo, 'config', 'user.name', 'Test')
        git_at(repo, 'config', 'user.email', 'test@example.invalid')
    (child / '.gitattributes').write_text('*.txt filter=r1-test\n')
    target = child / 'tracked.txt'
    target.write_text('original\n')
    git_at(child, 'add', '.')
    git_at(child, 'commit', '-qm', 'child')
    (parent / '.gitmodules').write_text('[submodule "child"]\n path = child\n url = ./child\n')
    git_at(parent, 'add', '.gitmodules', 'child')
    git_at(parent, 'commit', '-qm', 'parent')
    git_at(child, 'config', 'filter.r1-test.clean', '/bin/echo r1-filter-helper >&2; cat')
    git_at(parent, 'config', 'status.submoduleSummary', 'true')
    git_at(parent, 'config', 'diff.submodule', 'diff')
    target.write_text('modified\n')  # Same size: force Git to compare content through clean.
    trace = tmp_path / 'trace'
    monkeypatch.setenv('GIT_TRACE', str(trace))
    git_at(parent, '--no-optional-locks', 'status', '--porcelain')
    assert 'r1-filter-helper' in trace.read_text(), 'fixture must reproduce helper execution'
    tracker = ProjectTracker()
    for read in (lambda: GitTools(str(parent)).status(),
                 lambda: GitTools(str(parent)).status(short=True),
                 lambda: GitTools(str(parent)).diff(),
                 lambda: tracker._get_git_metrics(str(parent))):
        trace.write_text('')
        result = read()
        assert result.get('success', True), result
        assert not result.get('error'), result
        assert 'r1-filter-helper' not in trace.read_text()
    (parent / 'pending.txt').write_text('visible parent change')
    assert 'pending.txt' in GitTools(str(parent)).status(short=True)['output']
    assert tracker._get_git_metrics(str(parent))['has_uncommitted']


@pytest.mark.parametrize('observer', ['false', 'true'])
def test_log_pretty_cannot_spawn_signature_verifier(tmp_path, monkeypatch, observer):
    monkeypatch.delenv('AUTHORIZED_REPO', raising=False)
    monkeypatch.setenv('OBSERVER_MODE', observer)
    monkeypatch.setattr(policy, '_AUTHORIZATION', policy.RepoAuthorization(None))
    git_at(tmp_path, 'init', '-q')
    git_at(tmp_path, 'config', 'format.pretty', '%G?')
    git_at(tmp_path, 'config', 'gpg.program', '/bin/echo')
    git_at(tmp_path, 'config', 'gpg.format', 'openpgp')
    tree = git_at(tmp_path, 'mktree', input='')
    commit = git_at(tmp_path, 'hash-object', '-t', 'commit', '-w', '--stdin', input=(
        f'tree {tree}\n'
        'author Test <test@example.invalid> 1700000000 +0000\n'
        'committer Test <test@example.invalid> 1700000000 +0000\n'
        'gpgsig -----BEGIN PGP SIGNATURE-----\n'
        ' \n ZmFrZQ==\n -----END PGP SIGNATURE-----\n\nSignature fixture\n'))
    git_at(tmp_path, 'update-ref', 'HEAD', commit)
    trace = tmp_path / 'trace'
    monkeypatch.setenv('GIT_TRACE', str(trace))
    git_at(tmp_path, '-c', 'log.showSignature=false', 'log', '-1')
    assert '/bin/echo' in trace.read_text(), 'fixture must invoke verifier despite showSignature=false'
    for oneline in (False, True):
        trace.write_text('')
        result = GitTools(str(tmp_path)).log(n=1, oneline=oneline)
        assert result['success'], result
        assert '/bin/echo' not in trace.read_text()
        assert 'Signature fixture' in result['output']
