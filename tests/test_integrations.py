"""
Tests for Integration modules
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_obsidian_import():
    """Test that Obsidian can be imported."""
    from integrations.obsidian import Obsidian
    assert Obsidian is not None


def test_obsidian_init():
    """Test that Obsidian initializes correctly."""
    from integrations.obsidian import Obsidian
    obsidian = Obsidian()
    assert obsidian.vault_path is not None
    assert obsidian.daily_dir is not None
    assert obsidian.projects_dir is not None


def test_obsidian_save_daily_note():
    """Test that Obsidian can save daily note."""
    from integrations.obsidian import Obsidian
    obsidian = Obsidian()
    
    result = obsidian.save_daily_note(
        focus_task={"project": "test", "task": "test task", "priority": "HIGH"},
        message="Test message",
        work_status="TEST",
        projects=[],
        tasks=[],
        summary="Test summary"
    )
    
    assert result is not None
    assert "Daily" in result


def test_obsidian_build_sections():
    """Test that Obsidian helper methods work."""
    from integrations.obsidian import Obsidian
    obsidian = Obsidian()
    
    header = obsidian._build_intel_header("test_project")
    assert "test_project" in header
    
    structure = obsidian._build_structure_section({"language": "python"})
    assert "python" in structure


def test_standup_import():
    """Test that Standup can be imported."""
    from integrations.standup import Standup
    assert Standup is not None


def test_standup_should_run():
    """Test that Standup.should_run() works."""
    from integrations.standup import Standup
    standup = Standup()
    
    result = standup.should_run()
    assert isinstance(result, bool)


def test_standup_build_sections():
    """Test that Standup helper methods work."""
    from integrations.standup import Standup
    standup = Standup()
    
    header = standup._build_header()
    assert "Standup" in header
    
    focus = standup._build_focus_section({"project": "test", "task": "test", "priority": "HIGH"})
    assert "test" in focus
    
    suggestions = standup._build_suggestions_section("REAL_WORK")
    assert "Świetnie" in suggestions
