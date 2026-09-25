"""Observer execution rejects writes even when entry points are called directly."""

import subprocess

import pytest

from brain.executor import Executor
from brain.patch_engine import PatchEngine
from brain.roles.builder import Builder
from core.observer_policy import observer_mode, safe_git_args
from tools.bash_tools import BashTools
from tools.executor import ToolExecutor
from tools.file_tools import FileTools
from tools.git_tools import GitTools


@pytest.fixture(autouse=True)
def observer(monkeypatch):
    monkeypatch.setenv("OBSERVER_MODE", "true")


def assert_blocked(result):
    assert result["success"] is False
    assert result["status"] == "blocked"
    assert result["blocked"] is True
    assert not result


def test_policy_default_on_and_dynamic(monkeypatch):
    monkeypatch.delenv("OBSERVER_MODE", raising=False)
    assert observer_mode()
    monkeypatch.setenv("OBSERVER_MODE", "false")
    assert not observer_mode()


def test_file_writes_and_backups_blocked(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    files = FileTools()
    assert_blocked(files.write(str(target), "changed"))
    assert_blocked(files.edit(str(target), "original", "changed"))
    assert target.read_text() == "original"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source.txt"]
    assert files.read(str(target))["content"] == "original"


@pytest.mark.parametrize("method", ["apply_patch", "apply_patches", "rollback",
                                    "_git_commit", "_git_commit_batch"])
def test_direct_patch_entrypoints_do_not_access_files_or_git(method, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("observer reached execution")
    monkeypatch.setattr(subprocess, "run", forbidden)
    engine = PatchEngine()
    assert_blocked(getattr(engine, method)(None))
    assert engine.applied_patches == []


def test_builder_and_direct_helpers_block_execution(monkeypatch):
    builder = Builder()
    result = builder.build({"tasks": [{"action": "execute", "target": "touch forbidden"}]})
    assert_blocked(result)
    assert result["summary"] == {"total": 1, "success": 0, "failed": 0, "blocked": 1}
    assert_blocked(builder._execute_task({}, None))
    assert_blocked(builder._execute_patch({}))
    assert builder.execution_history == []


def test_shell_python_helpers_do_not_spawn(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("observer spawned an arbitrary command")
    monkeypatch.setattr(subprocess, "run", forbidden)
    shell = BashTools()
    assert_blocked(shell.run("echo hello"))
    assert_blocked(shell.run_python("print('hello')"))
    assert_blocked(shell.check_output("echo hello"))
    assert_blocked(shell.is_available("python"))


def test_unknown_registered_tool_fails_closed_and_reads_work(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    executor = ToolExecutor()
    executor.registry.register("surprise", lambda: pytest.fail("unknown tool executed"))
    assert_blocked(executor.execute_tool("surprise", {}))
    assert_blocked(executor.execute_tool("file_write", {"path": str(target), "content": "bad"}))
    assert executor.execute_tool("file_read", {"path": str(target)})["content"] == "original"
    assert_blocked(Executor().execute({"tool": "bash_run", "args": {"command": "true"}}))


@pytest.mark.parametrize("command", [
    "add .", "commit -m test", "branch new", "branch -D main", "diff --output=leak",
    "diff --ext-diff", "diff --textconv", "-c alias.attack=!touch attack attack",
    "status; touch attack", "status && touch attack", "log -1 --output=leak",
    "log -1 --format=%(exec)", "config user.name attacker", "status --porcelain=v2",
])
def test_git_allowlist_rejects_execution_and_writes(command, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("unsafe git spawned"))
    assert safe_git_args(command) is None
    assert_blocked(GitTools()._run(command))


def test_git_reads_disable_external_helpers_and_optional_writes(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    marker = tmp_path / "should-not-exist"
    subprocess.run(["git", "config", "core.fsmonitor", f"touch {marker}"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "diff.external", f"touch {marker}"], cwd=tmp_path, check=True)
    (tmp_path / "pending.txt").write_text("work")
    git = GitTools(str(tmp_path))
    assert "pending.txt" in git.status(short=True)["output"]
    assert git.diff()["success"]
    assert not marker.exists()
    assert not (tmp_path / ".git" / "index").exists()


def test_non_observer_without_authority_is_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSERVER_MODE", "false")
    target = tmp_path / "written.txt"
    from core import observer_policy as policy
    monkeypatch.setattr(policy, "_AUTHORIZATION", policy.RepoAuthorization(None))
    result = FileTools().write(str(target), "normal mode")
    assert result["blocked"] is True
    assert not target.exists()


def test_observer_git_signature_config(tmp_path, monkeypatch):
    """A configured signature verifier is executable code, even for git log."""
    import shlex
    from brain.project_tracker import ProjectTracker

    def git(*args, input=None):
        return subprocess.run(["git", *args], cwd=tmp_path, input=input,
                              capture_output=True, text=True, check=True).stdout.strip()

    git("init", "-q")
    marker = tmp_path / "verifier-executed"
    helper = tmp_path / "signature-helper"
    helper.write_text("#!/bin/sh\nprintf invoked > " + shlex.quote(str(marker)) + "\nexit 1\n")
    helper.chmod(0o700)
    git("config", "log.showSignature", "true")
    git("config", "gpg.format", "openpgp")
    git("config", "gpg.program", str(helper))
    tree = git("mktree", input="")
    commit = git("hash-object", "-t", "commit", "-w", "--stdin", input=(
        f"tree {tree}\n"
        "author Observer Test <observer@example.invalid> 1700000000 +0000\n"
        "committer Observer Test <observer@example.invalid> 1700000000 +0000\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n"
        " \n ZmFrZQ==\n -----END PGP SIGNATURE-----\n\nSignature fixture\n"
    ))
    git("update-ref", "HEAD", commit)

    # The intentionally invalid signature still invokes the configured verifier.
    git("--no-pager", "log", "-1", "--oneline")
    assert marker.read_text() == "invoked"
    marker.unlink()

    assert GitTools(str(tmp_path)).log(n=1, oneline=True)["success"]
    assert not marker.exists()
    monkeypatch.chdir(tmp_path)
    metrics = ProjectTracker()._get_git_metrics(str(tmp_path))
    assert "error" not in metrics
    assert metrics["last_commit_date"] == "2023-11-14"
    assert not marker.exists()


def test_observer_git_status_does_not_execute_clean_filters(tmp_path, monkeypatch):
    import shlex
    from brain.project_tracker import ProjectTracker
    def git(*args):
        return subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init', '-q')
    (tmp_path / '.gitattributes').write_text('*.txt filter=observer-test\n')
    target = tmp_path / 'tracked.txt'
    target.write_text('original')
    git('add', 'tracked.txt', '.gitattributes')
    marker = tmp_path / 'filter-executed'
    git('config', 'filter.observer-test.clean', 'touch ' + shlex.quote(str(marker)) + '; cat')
    target.write_text('modified')
    git('diff')
    assert marker.exists()
    marker.unlink()
    assert GitTools(str(tmp_path)).status()['success']
    assert GitTools(str(tmp_path)).diff()['success']
    monkeypatch.chdir(tmp_path)
    ProjectTracker()._get_git_metrics(str(tmp_path))
    assert not marker.exists()

@pytest.mark.parametrize('value', ['', 'tru', '0', 'yes', 'unexpected'])
def test_invalid_observer_setting_blocks_execution(monkeypatch, value):
    monkeypatch.setenv('OBSERVER_MODE', value)
    assert observer_mode()
