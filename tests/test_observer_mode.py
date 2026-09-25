"""Observer keeps useful analysis while refusing all persistent work."""
import builtins
import json

import pytest


@pytest.fixture
def observer(monkeypatch):
    from core import observer_storage
    monkeypatch.setenv('OBSERVER_MODE', 'true')
    monkeypatch.setattr(observer_storage, '_files', {})
    monkeypatch.setattr(observer_storage, '_directories', set())


def test_role_manager_proposes_without_calling_builder(tmp_path, monkeypatch, observer):
    from brain.roles.manager import RoleManager
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'module.py').write_text('import os\nprint("hello")\n')
    manager = RoleManager()
    def forbidden(*args, **kwargs):
        pytest.fail('Execution must not be called')
    monkeypatch.setattr(manager.builder, 'build', forbidden)
    monkeypatch.setattr(manager.critic, 'critique', forbidden)
    result = manager.run_cycle(False, {'path': str(project), 'name': 'project'})
    assert result['overall_status'] == 'OBSERVED'
    assert result['agent_intel']['issues']
    assert result['recommendations']
    assert all(task['priority'] in {'HIGH', 'MEDIUM', 'LOW'} for task in result['recommendations'])
    assert result['roles']['builder']['executed'] is False
    assert 'success_rate' not in result['roles']['builder']


def test_real_state_read_but_updates_stay_in_memory(tmp_path, monkeypatch, observer):
    import memory.memory as module
    state = tmp_path / 'system' / 'state.json'
    state.parent.mkdir()
    state.write_text(json.dumps({'status': 'existing', 'retained': 123}))
    before = state.read_bytes()
    monkeypatch.setattr(module, 'MEMORY_PATH', str(tmp_path / 'memory'))
    monkeypatch.setattr(module, 'SYSTEM_PATH', str(state.parent))
    monkeypatch.setattr(module.Memory, '_instance', None)
    memory = module.Memory()
    assert memory.get_state()['retained'] == 123
    memory.save_state({'status': 'stopped'})
    assert memory.get_state()['status'] == 'stopped'
    assert state.read_bytes() == before
    assert not (tmp_path / 'memory').exists()


def test_one_complete_loop_with_disk_writes_denied(tmp_path, monkeypatch, observer, capsys):
    import core.loop as loop
    import memory.memory as memory_module
    project = tmp_path / 'projects' / 'example'
    project.mkdir(parents=True)
    (project / 'requirements.txt').write_text('')
    (project / 'main.py').write_text('import os\nprint("hello")\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(memory_module.Memory, '_instance', None)
    monkeypatch.setattr(memory_module, 'MEMORY_PATH', str(tmp_path / 'memory'))
    monkeypatch.setattr(memory_module, 'SYSTEM_PATH', str(tmp_path / 'system'))
    monkeypatch.setattr(loop, 'PROJECT_SCAN_PATHS', [str(project.parent)])
    monkeypatch.setattr(loop, 'WORKSPACE_PATH', str(project))
    monkeypatch.setattr(loop, 'ENABLE_PROJECT_DISCOVERY', True)
    real_open = builtins.open
    def deny_writes(file, mode='r', *args, **kwargs):
        if any(flag in mode for flag in 'wax+'):
            raise PermissionError('read-only test filesystem')
        return real_open(file, mode, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', deny_writes)
    state = loop.main_loop(max_cycles=1)
    output = capsys.readouterr().out
    assert state['cycle'] == 1
    assert state['status'] == 'stopped'
    assert state['current_module'] == 'complete'
    assert state['v9_status'] == 'OBSERVED'
    assert '[OBSERVER] BLOCKED' in output
    assert '[ERROR]' not in output
    assert '[ROLES] Error' not in output
    assert 'Błąd cyklu' not in output
    assert not (tmp_path / 'memory').exists()
    assert not (tmp_path / 'system').exists()


def test_external_writes_and_cleanup_are_blocked(tmp_path, observer):
    from integrations.obsidian import Obsidian
    from integrations.todoist import Todoist
    from memory.project_memory import MultiProjectMemory
    obsidian = Obsidian(str(tmp_path / 'vault'))
    assert obsidian.save_focus_task({})['blocked']
    assert Todoist()._safe_request('POST', 'https://unused.invalid') is None
    assert MultiProjectMemory().cleanup_old_projects()['blocked']
    assert not (tmp_path / 'vault').exists()


def test_observer_blocks_llm_requests_and_unknown_os_mutation(tmp_path, monkeypatch, observer):
    from integrations.llm import LLM
    from core.observer_storage import os as runtime_os
    import requests
    def forbidden(*args, **kwargs):
        pytest.fail('No external request in observer mode')
    monkeypatch.setattr(requests, 'post', forbidden)
    llm = LLM()
    for call in (llm._call_groq, llm._call_openai, llm._call_anthropic):
        assert call('test')['blocked']
    target = tmp_path / 'retained.txt'
    target.write_text('unchanged')
    assert runtime_os.unlink(target)['blocked']
    assert runtime_os.chmod(target, 0o777)['blocked']
    assert target.read_text() == 'unchanged'
