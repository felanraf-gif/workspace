"""Project tracking must not change the agent's working directory."""

import os
import subprocess

import pytest

from brain.project_tracker import ProjectTracker


@pytest.mark.parametrize("relative_path", [False, True])
def test_git_metrics_target_project_without_changing_cwd(tmp_path, monkeypatch, relative_path):
    agent = tmp_path / "agent"
    project = tmp_path / "project"
    agent.mkdir()
    project.mkdir()
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    (project / "pending.txt").write_text("uncommitted project work")
    monkeypatch.chdir(agent)
    path = os.path.relpath(project, agent) if relative_path else str(project)

    metrics = ProjectTracker()._get_git_metrics(path)

    assert os.getcwd() == str(agent)
    assert "error" not in metrics
    assert metrics["has_uncommitted"] is True
    assert metrics["commits_last_7d"] == 0


@pytest.mark.parametrize("interrupted", [False, True])
def test_git_metrics_preserve_cwd_on_failure(tmp_path, monkeypatch, interrupted):
    agent = tmp_path / "agent"
    project = tmp_path / "project"
    agent.mkdir()
    project.mkdir()
    monkeypatch.chdir(agent)

    def fail_git(*args, **kwargs):
        if interrupted:
            raise KeyboardInterrupt
        raise subprocess.TimeoutExpired("git", 3)

    monkeypatch.setattr(subprocess, "run", fail_git)
    tracker = ProjectTracker()
    if interrupted:
        with pytest.raises(KeyboardInterrupt):
            tracker._get_git_metrics(str(project))
    else:
        metrics = tracker._get_git_metrics(str(project))
        assert "timed out" in metrics["error"]

    assert os.getcwd() == str(agent)
