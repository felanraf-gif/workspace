"""
brain/roles/builder.py - Builder Role
Wykonuje zadania z planu Architecta
"""

import os
from core.observer_policy import mutation, observer_mode, blocked, authorized_repo
from datetime import datetime


class Builder:
    """Builder - wykonuje zadania."""
    
    def __init__(self, executor=None):
        self.executor = executor
        self.execution_history = []
        self.current_execution = None
    
    def build(self, plan, executor=None):
        """
        Wykonuje plan Architecta.
        
        Args:
            plan: Plan od Architecta
            executor: Executor do wykonania zadań (opcjonalny)
            
        Returns:
            dict: Wyniki wykonania
        """
        if observer_mode():
            return blocked("builder.build", executions=[], summary={
                "total": len(plan.get("tasks", [])), "success": 0,
                "failed": 0, "blocked": len(plan.get("tasks", [])),
            })
        results = {
            "timestamp": datetime.now().isoformat(),
            "builder_role": "Builder",
            "authorized_repo": authorized_repo(),
            "plan_id": plan.get("timestamp"),
            "executions": [],
            "summary": {
                "total": 0,
                "success": 0,
                "failed": 0
            }
        }
        
        tasks = plan.get("tasks", [])
        results["summary"]["total"] = len(tasks)
        
        for task in tasks:
            execution = self._execute_task(task, executor or self.executor)
            results["executions"].append(execution)
            
            if execution.get("success"):
                results["summary"]["success"] += 1
            else:
                results["summary"]["failed"] += 1
            
            self.execution_history.append(execution)
        
        results["status"] = "completed" if results["summary"]["failed"] == 0 else "completed_with_errors"
        
        return results
    
    @mutation("brain/roles/builder.py:_execute_task", controlled=True,
              read_only=lambda v: v["task"].get("action") in {"analyze", "review"})
    def _execute_task(self, task, executor):
        """Wykonuje pojedyncze zadanie."""
        action = task.get("action", "")
        target = task.get("target", "")

        result = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "output": None,
            "error": None
        }

        if action == "patch":
            return self._execute_patch(task)

        if not executor:
            result["output"] = "No executor available"
            result["error"] = "Executor not configured"
            return result

        try:
            if action == "analyze":
                execution = executor.execute({
                    "tool": "file_read",
                    "args": {"path": target}
                })
                tool_result = execution.get("tool_result", execution)

                result["success"] = tool_result.get(
                    "success",
                    execution.get("success", False)
                )
                content = tool_result.get("content", "")
                result["output"] = content[:200] if content else None

            elif action == "review":
                execution = executor.execute({
                    "tool": "file_read",
                    "args": {"path": target}
                })
                tool_result = execution.get("tool_result", execution)

                result["success"] = tool_result.get(
                    "success",
                    execution.get("success", False)
                )
                result["output"] = "Reviewed"

            elif action == "refactor":
                result["error"] = (
                    "Refactor wymaga jawnej operacji patch; "
                    "brak automatycznej implementacji."
                )

            elif action == "execute":
                return blocked("builder.execute")

            else:
                result["error"] = f"Nieznana akcja: {action}"

        except Exception as e:
            result["error"] = str(e)

        return result

    @mutation("brain/roles/builder.py:_execute_patch", controlled=True,
              paths=lambda v: [v["task"].get("project_root") or os.getcwd()])
    def _execute_patch(self, task):
        """Wykonuje jawnie zaplanowaną naprawę przez PatchEngine."""
        result = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "output": None,
            "error": None,
        }

        issue = task.get("issue")
        if not isinstance(issue, dict):
            result["error"] = "Patch task nie zawiera konkretnego findingu."
            return result

        try:
            from brain.patch_engine import PatchEngine

            project_root = task.get("project_root") or os.getcwd()

            engine = PatchEngine()
            engine._project_root = project_root

            project = {
                "name": task.get("project") or issue.get("project", "towarzysz"),
                "path": project_root,
                "files": [],
            }

            patches = engine.suggest([issue], project)

            auto = [
                patch for patch in patches
                if patch.confidence >= PatchEngine.AUTO_CONFIDENCE
            ]

            review = [
                patch for patch in patches
                if patch.confidence < PatchEngine.AUTO_CONFIDENCE
            ]

            applied = engine.apply_patches(auto)

            result["output"] = {
                "suggested": len(patches),
                "auto_candidates": len(auto),
                "applied": len(applied),
                "review_required": len(review),
                "descriptions": [patch.description for patch in applied],
            }

            if not auto:
                result["error"] = "Brak poprawki spełniającej próg auto-apply."
                return result

            if len(applied) != len(auto):
                result["error"] = (
                    f"Aplikowano {len(applied)}/{len(auto)} auto-poprawek."
                )
                return result

            result["success"] = True
            return result

        except Exception as e:
            result["error"] = str(e)
            return result

    def get_current_status(self):
        """Zwraca status bieżącego wykonania."""
        if self.current_execution:
            return {
                "in_progress": True,
                "execution": self.current_execution
            }
        return {"in_progress": False}
