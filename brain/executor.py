"""
brain/executor.py - Executor
Główny executor dla zadań
"""

from datetime import datetime
from tools.executor import ToolExecutor


class Executor:
    """
    Executor - wykonuje zadania.
    
    Przepływ:
    1. Przygotuj zadanie
    2. Wykonaj narzędziami
    3. Zwróć wynik
    """
    
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.execution_log = []
    
    def execute(self, task):
        """
        Wykonuje zadanie.
        
        Args:
            task: Dict z {"tool", "args", "description"}
            
        Returns:
            dict: Wynik wykonania
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "success": False,
            "output": None,
            "error": None
        }
        
        tool = task.get("tool")
        args = task.get("args", {})
        description = task.get("description", "")
        
        if not tool:
            result["error"] = "Brak narzędzia"
            return result
        
        try:
            output = self.tool_executor.execute_tool(tool, args)
            
            result["success"] = output.get("success", False)
            result["output"] = output.get("output") or output.get("content")
            result["error"] = output.get("error")
            result["tool_result"] = output
            
        except Exception as e:
            result["error"] = str(e)
        
        self.execution_log.append(result)
        
        return result
    
    def execute_sequence(self, tasks):
        """
        Wykonuje sekwencję zadań.
        
        Args:
            tasks: Lista zadań
            
        Returns:
            list: Lista wyników
        """
        results = []
        for task in tasks:
            result = self.execute(task)
            results.append(result)
            
            if not result.get("success") and task.get("critical", False):
                break
        
        return results
    
    def get_stats(self):
        """Zwraca statystyki wykonań."""
        total = len(self.execution_log)
        success = sum(1 for r in self.execution_log if r.get("success"))
        
        return {
            "total_executions": total,
            "successful": success,
            "failed": total - success,
            "success_rate": success / total if total > 0 else 0
        }
