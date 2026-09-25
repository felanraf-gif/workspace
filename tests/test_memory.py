"""
Tests for Memory module
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pytest


@pytest.fixture(autouse=True)
def isolated_memory(tmp_path, monkeypatch):
    import memory.memory as module
    monkeypatch.setattr(module, "MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setattr(module, "SYSTEM_PATH", str(tmp_path / "system"))
    monkeypatch.setattr(module.Memory, "_instance", None)


def test_memory_import():
    """Test that Memory can be imported."""
    from memory.memory import Memory
    assert Memory is not None


def test_memory_singleton():
    """Test that Memory is a singleton."""
    from memory.memory import Memory
    m1 = Memory()
    m2 = Memory()
    assert m1 is m2


def test_memory_get_state():
    """Test that Memory can get state."""
    from memory.memory import Memory
    memory = Memory()
    state = memory.get_state()
    assert isinstance(state, dict)


def test_memory_save_state():
    """Test that Memory can save state."""
    from memory.memory import Memory
    memory = Memory()
    memory.save_state({"test_key": "test_value"})
    state = memory.get_state()
    assert state.get("test_key") == "test_value"


def test_memory_creates_missing_system_path(tmp_path, monkeypatch):
    """A fresh system directory is created before state.json is written."""
    import memory.memory as memory_module

    from core import observer_policy as policy
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("OBSERVER_MODE", "false")
    monkeypatch.setattr(policy, "_AUTHORIZATION", policy.RepoAuthorization.from_startup(str(tmp_path)))
    system_path = tmp_path / "nested" / "system"
    monkeypatch.setattr(memory_module, "MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setattr(memory_module, "SYSTEM_PATH", str(system_path))
    monkeypatch.setattr(memory_module.Memory, "_instance", None)
    assert not system_path.exists()

    memory = memory_module.Memory()

    assert system_path.is_dir()
    assert (system_path / "state.json").is_file()
    assert memory.get_state()["status"] == "initialized"
    memory.save_state({"regression_key": "saved"})
    assert memory.get_state()["regression_key"] == "saved"
