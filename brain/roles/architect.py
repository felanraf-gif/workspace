"""
brain/roles/architect.py - Architect Role
Planuje rozwiązania na podstawie danych od Scout
"""

from datetime import datetime
from core.constants import PRIORITY_ORDER


class Architect:
    """Architect - planuje rozwiązania."""

    ACTIONABLE_ISSUE_TYPES = {"security", "structure", "code_quality", "dependency"}
    
    def __init__(self):
        self.planning_history = []
    
    def design(self, scout_report, context=None):
        """
        Projektuje plan na podstawie raportu Scouta.
        
        Args:
            scout_report: Dane od Scouta
            context: Dodatkowy kontekst (opcjonalny)
            
        Returns:
            dict: Plan działania
        """
        plan = {
            "timestamp": datetime.now().isoformat(),
            "architect_role": "Architect",
            "goals": [],
            "tasks": [],
            "strategy": ""
        }
        
        findings = scout_report.get("findings", {})
        changes = scout_report.get("changes_detected", [])
        
        if changes:
            plan["goals"].append({
                "id": "handle_changes",
                "description": "Zajmij się wykrytymi zmianami",
                "priority": "HIGH"
            })
            
            for change in changes[:5]:
                if change["type"] == "new_file":
                    plan["tasks"].append({
                        "goal_id": "handle_changes",
                        "action": "analyze",
                        "target": change["path"],
                        "priority": "MEDIUM"
                    })
                elif change["type"] == "modified_file":
                    plan["tasks"].append({
                        "goal_id": "handle_changes",
                        "action": "review",
                        "target": change["path"],
                        "priority": "HIGH"
                    })
        
        agent_data = findings.get("agent", {})
        if agent_data:
            issues = self._analyze_code_quality(agent_data)
            if issues:
                plan["goals"].append({
                    "id": "improve_quality",
                    "description": "Popraw jakość kodu",
                    "priority": "MEDIUM"
                })
                for issue in issues[:3]:
                    plan["tasks"].append({
                        "goal_id": "improve_quality",
                        "action": issue["action"],
                        "target": issue["target"],
                        "priority": issue["priority"]
                    })
        
        # Findings z głębokiej analizy przekazujemy Builderowi
        # jako jawne zadania naprawcze.
        agent_intel = (context or {}).get("agent_intel") or {}
        deep_issues = agent_intel.get("issues", [])
        project = (context or {}).get("project") or {}
        project_root = project.get("path")

        repair_tasks = []

        for issue in deep_issues:
            issue_type = issue.get("type", "")
            priority = issue.get("priority", "LOW")

            if priority not in ("HIGH", "MEDIUM"):
                continue

            if issue_type not in self.ACTIONABLE_ISSUE_TYPES:
                continue

            # Dependency jest automatycznie naprawialne wyłącznie
            # dla jawnie wykrytych nieużywanych importów.
            if issue_type == "dependency":
                suggestions = issue.get("suggestions") or []
                if not any(
                    s.get("type") == "unused_import"
                    and s.get("file")
                    and s.get("unused_names")
                    for s in suggestions
                ):
                    continue

            repair_task = {
                "goal_id": "auto_repair",
                "action": "patch",
                "target": self._issue_target(issue),
                "priority": priority,
                "issue": issue,
                "project": issue.get("project", "towarzysz"),
                "reason": issue.get("issue", "")
            }
            if project_root:
                repair_task["project_root"] = project_root

            repair_tasks.append(repair_task)

        if repair_tasks:
            plan["goals"].append({
                "id": "auto_repair",
                "description": "Automatycznie napraw wykryte problemy",
                "priority": "HIGH"
            })
            plan["tasks"].extend(repair_tasks[:5])

        plan["tasks"].sort(key=lambda t: PRIORITY_ORDER.get(t.get("priority", "LOW"), 3))
        plan["strategy"] = self._determine_strategy(plan)
        
        self.planning_history.append(plan)
        
        return plan
    
    @staticmethod
    def _issue_target(issue):
        if issue.get("file"):
            return issue["file"]

        secrets = issue.get("secrets") or []
        if secrets and secrets[0].get("file"):
            return secrets[0]["file"]

        return ""

    def _analyze_code_quality(self, agent_data):
        """Analizuje jakość kodu."""
        issues = []
        
        for f in agent_data.get("files", []):
            if f.get("lines", 0) > 200:
                issues.append({
                    "action": "review",
                    "target": f["path"],
                    "priority": "MEDIUM",
                    "reason": f"Wielki plik ({f['lines']} linii)"
                })
        
        return issues
    
    def _determine_strategy(self, plan):
        """Określa strategię działania."""
        if len(plan.get("tasks", [])) > 5:
            return "sequential"
        elif len(plan.get("tasks", [])) > 2:
            return "focused"
        else:
            return "quick"
