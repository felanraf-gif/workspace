"""
brain/roles/builder.py - Builder Role
Wykonuje zadania z planu Architecta
"""

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
        results = {
            "timestamp": datetime.now().isoformat(),
            "builder_role": "Builder",
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
        
        if executor:
            try:
                if action == "analyze":
                    output = executor.execute_tool("file_read", {"path": target})
                    result["success"] = output.get("success", False)
                    result["output"] = output.get("content", "")[:200] if output.get("content") else None
                elif action == "review":
                    output = executor.execute_tool("file_read", {"path": target})
                    result["success"] = output.get("success", False)
                    result["output"] = "Reviewed"
                elif action == "refactor":
                    result["success"] = True
                    result["output"] = "Refactoring scheduled"
                elif action == "execute":
                    output = executor.execute_tool("bash_run", {"command": target})
                    result["success"] = output.get("success", False)
                    result["output"] = output.get("stdout", "")[:200]
                    result["error"] = output.get("stderr", "")
            except Exception as e:
                result["error"] = str(e)
        else:
            result["output"] = "No executor available"
            result["error"] = "Executor not configured"
        
        return result
    
    def get_current_status(self):
        """Zwraca status bieżącego wykonania."""
        if self.current_execution:
            return {
                "in_progress": True,
                "execution": self.current_execution
            }
        return {"in_progress": False}
