"""
brain/roles/manager.py - Role Manager
Koordynuje wszystkie role
"""

from datetime import datetime
from .scout import Scout
from .architect import Architect
from .builder import Builder
from .critic import Critic


class RoleManager:
    """
    RoleManager - koordynuje wszystkie role agenta.
    
    Przepływ:
    Scout → Architect → Builder → Critic
    """
    
    def __init__(self, executor=None):
        self.scout = Scout()
        self.architect = Architect()
        self.builder = Builder(executor)
        self.critic = Critic()
        self.executor = executor
        self.execution_log = []
    
    def run_cycle(self, focus_on_agent=True):
        """
        Uruchamia pełny cykl wszystkich ról.
        
        Args:
            focus_on_agent: Czy skupić się na kodzie agenta
            
        Returns:
            dict: Wynik całego cyklu
        """
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "cycle_id": len(self.execution_log) + 1,
            "roles": {},
            "overall_status": "",
            "reflections": []
        }
        
        scout_report = self.scout.scout(focus_on_agent=focus_on_agent)
        cycle_result["roles"]["scout"] = {
            "status": "completed",
            "changes_found": len(scout_report.get("changes_detected", [])),
            "files_scanned": scout_report.get("findings", {}).get("agent", {}).get("files_count", 0)
        }
        
        plan = self.architect.design(scout_report)
        cycle_result["roles"]["architect"] = {
            "status": "completed",
            "goals_count": len(plan.get("goals", [])),
            "tasks_count": len(plan.get("tasks", [])),
            "strategy": plan.get("strategy", "")
        }
        
        build_result = self.builder.build(plan, executor=self.executor)
        cycle_result["roles"]["builder"] = {
            "status": build_result.get("status", "unknown"),
            "success_rate": build_result.get("summary", {}).get("success", 0),
            "failed_count": build_result.get("summary", {}).get("failed", 0)
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
