import subprocess

from brain.roles.architect import Architect
from brain.roles.builder import Builder


def test_architect_creates_patch_task_from_finding():
    scout_report = {
        "findings": {},
        "changes_detected": [],
    }

    agent_intel = {
        "issues": [
            {
                "project": "towarzysz",
                "issue": "Hardcoded API key",
                "priority": "HIGH",
                "type": "security",
                "secrets": [
                    {
                        "file": "config.py",
                        "type": "API Key",
                    }
                ],
            }
        ]
    }

    plan = Architect().design(
        scout_report,
        context={"agent_intel": agent_intel},
    )

    patch_tasks = [
        task for task in plan["tasks"]
        if task.get("action") == "patch"
    ]

    assert len(patch_tasks) == 1
    assert patch_tasks[0]["target"] == "config.py"
    assert patch_tasks[0]["issue"]["type"] == "security"


def test_builder_executes_verified_patch(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()

    from core import observer_policy as policy
    (root / ".git").mkdir()
    monkeypatch.setenv("OBSERVER_MODE", "false")
    monkeypatch.setattr(policy, "_AUTHORIZATION", policy.RepoAuthorization.from_startup(str(root)))

    config = root / "config.py"
    config.write_text('API_KEY = "test-secret"\n')



    task = {
        "action": "patch",
        "project": "test-project",
        "project_root": str(root),
        "target": "config.py",
        "issue": {
            "project": "test-project",
            "issue": "Hardcoded API key",
            "priority": "HIGH",
            "type": "security",
            "secrets": [
                {
                    "file": "config.py",
                    "type": "API Key",
                }
            ],
        },
    }

    result = Builder().build({"tasks": [task]})

    assert result["summary"]["total"] == 1
    assert result["summary"]["success"] == 1
    assert result["summary"]["failed"] == 0

    content = config.read_text()

    assert 'API_KEY = os.getenv("API_KEY")' in content

    assert list((root / ".git").iterdir()) == []


def test_analyzer_detects_uppercase_hardcoded_secret(tmp_path):
    from brain.analyzer import Analyzer

    file_path = tmp_path / "probe.py"
    file_path.write_text(
        'API_KEY = "AUTONOMY_TEST_SECRET"\n'
    )

    analyzer = Analyzer()

    result = analyzer._analyze_python_file(
        {
            "name": "probe.py",
            "path": "probe.py",
            "full_path": str(file_path),
        },
        "test-project",
    )

    secrets = result.get("secrets", [])

    assert secrets
    assert any(secret.get("type") == "API Key" for secret in secrets)


def test_analyzer_reports_unused_local_import(tmp_path):
    from brain.analyzer import Analyzer

    helper = tmp_path / "helper.py"
    probe = tmp_path / "probe.py"

    helper.write_text(
        "def used():\n"
        "    return 1\n\n"
        "def unused():\n"
        "    return 2\n"
    )

    probe.write_text(
        "from helper import used, unused\n\n"
        "print(used())\n"
    )

    analyzer = Analyzer()

    project = {
        "name": "test-project",
        "path": str(tmp_path),
        "files": [
            {
                "name": "helper.py",
                "path": "helper.py",
                "full_path": str(helper),
            },
            {
                "name": "probe.py",
                "path": "probe.py",
                "full_path": str(probe),
            },
        ],
    }

    issues = analyzer._analyze_project_deep(project)

    unused_issues = [
        issue for issue in issues
        if issue.get("type") == "dependency"
        and issue.get("suggestions")
    ]

    assert unused_issues

    suggestions = unused_issues[0]["suggestions"]

    assert any(
        suggestion.get("file") == "probe.py"
        and "unused" in suggestion.get("unused_names", [])
        for suggestion in suggestions
    )


def test_builder_uses_executor_public_execute_api(monkeypatch):
    from brain.roles.builder import Builder

    monkeypatch.setenv("OBSERVER_MODE", "false")

    class DummyExecutor:
        def execute(self, task):
            return {
                "success": True,
                "tool_result": {
                    "success": True,
                    "content": "reviewed",
                },
            }

    builder = Builder(executor=DummyExecutor())

    result = builder.build({
        "timestamp": "test",
        "tasks": [{
            "action": "review",
            "target": "test.py",
            "priority": "MEDIUM",
        }],
    })

    assert result["summary"]["success"] == 1
    assert result["summary"]["failed"] == 0


def test_patch_engine_removes_only_unused_import_name(tmp_path):
    from brain.patch_engine import PatchEngine

    path = tmp_path / "probe.py"
    path.write_text(
        "from helper import used, unused\n"
        "print(used())\n"
    )

    engine = PatchEngine()
    engine._project_root = str(tmp_path)

    patch = engine._fix_unused_import({
        "file": "probe.py",
        "module": "helper.py",
        "unused_names": ["unused"],
    })

    assert patch is not None
    assert patch.new_code == (
        "from helper import used\n"
        "print(used())\n"
    )


def test_patch_engine_removes_unused_alias_only(tmp_path):
    from brain.patch_engine import PatchEngine

    path = tmp_path / "probe.py"
    path.write_text(
        "from helper import used as u, unused as x\n"
        "print(u())\n"
    )

    engine = PatchEngine()
    engine._project_root = str(tmp_path)

    patch = engine._fix_unused_import({
        "file": "probe.py",
        "module": "helper.py",
        "unused_names": ["x"],
    })

    assert patch is not None
    assert patch.new_code == (
        "from helper import used as u\n"
        "print(u())\n"
    )


def test_patch_engine_does_not_match_similar_module_name(tmp_path):
    from brain.patch_engine import PatchEngine

    path = tmp_path / "probe.py"
    path.write_text(
        "from helper_extra import keep\n"
        "print(keep())\n"
    )

    engine = PatchEngine()
    engine._project_root = str(tmp_path)

    patch = engine._fix_unused_import({
        "file": "probe.py",
        "module": "helper.py",
        "unused_names": ["keep"],
    })

    assert patch is None


def test_patch_engine_does_not_auto_remove_star_import(tmp_path):
    from brain.patch_engine import PatchEngine

    path = tmp_path / "probe.py"
    path.write_text(
        "from helper import *\n"
        "print(value)\n"
    )

    engine = PatchEngine()
    engine._project_root = str(tmp_path)

    patch = engine._fix_unused_import({
        "file": "probe.py",
        "module": "helper.py",
        "unused_names": ["*"],
    })

    assert patch is None
