"""
Tests for Memory module
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
