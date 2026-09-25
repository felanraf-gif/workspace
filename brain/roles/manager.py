"""
brain/roles/manager.py - Role Manager
Koordynuje wszystkie role
"""

import os
from core.observer_policy import observer_mode, blocked, authorized_repo
from datetime import datetime
from brain.analyzer import Analyzer
from .scout import Scout
from .architect import Architect
from .builder import Builder
from .critic import Critic


class RoleManager:
    """
    RoleManager - koordynuje wszystkie role agenta.
    
    Przepływ:
    Scout → Analyzer → Architect → Builder → Critic
    """
    
    def __init__(self, executor=None):
        self.scout = Scout()
        self.analyzer = Analyzer()
        self.architect = Architect()
        self.builder = Builder(executor)
        self.critic = Critic()
        self.executor = executor
        self.execution_log = []

    PROJECT_SKIP_DIRS = {
        ".git", "__pycache__", "venv", ".venv", "env", "tor_env",
        "node_modules", ".tox", ".mypy_cache", ".pytest_cache",
        "dist", "build", ".egg-info", "vendor", "target",
    }

    def _prepare_project(self, project):
        """Uzupełnia dane z discovery o pliki wymagane przez Analyzer."""
        snapshot = dict(project)
        if snapshot.get("files"):
            return snapshot

        project_root = snapshot.get("path")
        if not project_root or not os.path.isdir(project_root):
            return snapshot

        files = []
        for root, dirs, filenames in os.walk(project_root):
            dirs[:] = sorted(
                directory for directory in dirs
                if directory not in self.PROJECT_SKIP_DIRS
                and not directory.startswith(".")
            )
            for filename in sorted(filenames):
                if filename.startswith("."):
                    continue

                full_path = os.path.join(root, filename)
                if not os.path.isfile(full_path):
                    continue

                files.append({
                    "name": filename,
                    "path": os.path.relpath(full_path, project_root),
                    "full_path": full_path,
                    "type": "file",
                })

        snapshot["files"] = files
        return snapshot
    
    def run_cycle(self, focus_on_agent=True, project=None):
        """
        Uruchamia pełny cykl wszystkich ról.
        
        Args:
            focus_on_agent: Czy skupić się na kodzie agenta
            project: Projekt do głębokiej analizy (opcjonalny)
            
        Returns:
            dict: Wynik całego cyklu
        """
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "cycle_id": len(self.execution_log) + 1,
            "authorized_repo": authorized_repo(),
            "roles": {},
            "overall_status": "",
            "reflections": []
        }
        
        analysis_project = self._prepare_project(project) if project is not None else None
        scout_report = self.scout.scout(focus_on_agent=focus_on_agent)

        agent_intel = None
        if analysis_project is not None:
            agent_intel = {
                "issues": self.analyzer._analyze_project_deep(analysis_project)
            }
        elif focus_on_agent:
            agent_intel = self.analyzer.analyze_agent_code()

        cycle_result["agent_intel"] = agent_intel

        cycle_result["roles"]["scout"] = {
            "status": "completed",
            "changes_found": len(scout_report.get("changes_detected", [])),
            "files_scanned": scout_report.get("findings", {}).get("agent", {}).get("files_count", 0)
        }
        
        context = {"agent_intel": agent_intel} if agent_intel else {}
        if analysis_project is not None:
            context["project"] = analysis_project

        plan = self.architect.design(
            scout_report,
            context=context or None
        )
        cycle_result["roles"]["architect"] = {
            "status": "completed",
            "goals_count": len(plan.get("goals", [])),
            "tasks_count": len(plan.get("tasks", [])),
            "strategy": plan.get("strategy", "")
        }
        
        if observer_mode():
            blocked("roles.builder", tasks=len(plan.get("tasks", [])))
            cycle_result["plan"] = plan
            cycle_result["roles"]["builder"] = {
                "status": "blocked", "executed": False,
                "blocked_count": len(plan.get("tasks", [])),
            }
            cycle_result["roles"]["critic"] = {
                "status": "skipped", "verdict": "NOT_EXECUTED", "approved": False,
            }
            cycle_result["overall_status"] = "OBSERVED"
            cycle_result["recommendations"] = plan.get("tasks", [])
            self.execution_log.append(cycle_result)
            return cycle_result

        build_result = self.builder.build(plan, executor=self.executor)
        build_summary = build_result.get("summary", {})
        total_tasks = build_summary.get("total", 0)
        successful_tasks = build_summary.get("success", 0)
        cycle_result["roles"]["builder"] = {
            "status": build_result.get("status", "unknown"),
            "success_rate": successful_tasks / total_tasks if total_tasks else 1.0,
            "failed_count": build_summary.get("failed", 0)
        }
        
        critique = self.critic.critique(build_result)
        cycle_result["roles"]["critic"] = {
            "status": "completed",
            "verdict": critique.get("verdict", ""),
            "score": critique.get("score", 0),
            "approved": critique.get("approved", False)
        }
        
        cycle_result["overall_status"] = "APPROVED" if critique.get("approved") else "NEEDS_ATTENTION"
        cycle_result["reflections"] = critique.get("recommendations", [])
        
        self.execution_log.append(cycle_result)
        
        return cycle_result
    
    def get_status(self):
        """Zwraca status wszystkich ról."""
        return {
            "roles_active": {
                "scout": True,
                "architect": True,
                "builder": True,
                "critic": True
            },
            "executor_configured": self.executor is not None,
            "cycles_completed": len(self.execution_log),
            "last_cycle": self.execution_log[-1] if self.execution_log else None
        }
    
    def set_executor(self, executor):
        """Ustawia executor dla Buildiera."""
        self.executor = executor
        self.builder.executor = executor
