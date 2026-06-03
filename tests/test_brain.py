"""
Tests for Brain modules
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_analyzer_import():
    """Test that Analyzer can be imported."""
    from brain.analyzer import Analyzer
    assert Analyzer is not None


def test_planner_import():
    """Test that Planner can be imported."""
    from brain.planner import Planner
    assert Planner is not None


def test_assistant_import():
    """Test that Assistant can be imported."""
    from brain.assistant import Assistant
    assert Assistant is not None


def test_alerts_import():
    """Test that Alerts can be imported."""
    from brain.alerts import Alerts
    assert Alerts is not None


def test_analyzer_scan():
    """Test that analyzer can scan agent code."""
    from brain.analyzer import Analyzer
    analyzer = Analyzer()
    result = analyzer.analyze_agent_code()
    assert result is not None
    assert "project" in result
    assert "issues" in result


def test_planner_create_tasks():
    """Test that planner can create tasks from intelligence."""
    from brain.analyzer import Analyzer
    from brain.planner import Planner
    
    analyzer = Analyzer()
    planner = Planner()
    
    intel = analyzer.analyze_agent_code()
    tasks = planner.create_tomorrow_plan_from_intelligence(intel)
    
    assert isinstance(tasks, list)


def test_planner_select_focus():
    """Test that planner can select focus task."""
    from brain.analyzer import Analyzer
    from brain.planner import Planner
    
    analyzer = Analyzer()
    planner = Planner()
    
    intel = analyzer.analyze_agent_code()
    tasks = planner.create_tomorrow_plan_from_intelligence(intel)
    focus = planner.select_focus_task(tasks)
    
    assert focus is None or isinstance(focus, dict)
