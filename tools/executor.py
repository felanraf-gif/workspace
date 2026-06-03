"""
tools/executor.py - Tool Executor
Wykonuje wybrane narzędzia z rejestru
"""

from datetime import datetime


class ToolExecutor:
    """
    Executor - wykonuje narzędzia z rejestru.
    
    Przepływ:
    1. Wybierz narzędzie z rejestru
    2. Wykonaj z argumentami
    3. Zaloguj wynik
    4. Zwróć rezultat
    """
    
    def __init__(self):
        from .registry import ToolRegistry
        self.registry = ToolRegistry()
        self.registry.register_all()
        self.execution_history = []
    
    def execute_tool(self, tool_name, args):
        """
        Wykonuje narzędzie.
        
        Args:
            tool_name: Nazwa narzędzia
            args: Słownik argumentów
            
        Returns:
            dict: Wynik wykonania
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": args,
            "success": False,
            "output": None,
            "error": None
        }
        
        tool = self.registry.get(tool_name)
        if not tool:
            result["error"] = f"Narzędzie '{tool_name}' nie znalezione"
            self.registry.log_usage(tool_name, args, result)
            return result
        
        try:
            output = tool(**args) if isinstance(args, dict) else tool(args)
            
            if isinstance(output, dict):
                result.update(output)
            else:
                result["output"] = output
                result["success"] = True
                
        except TypeError as e:
            result["error"] = f"Błędne argumenty: {e}"
        except FileNotFoundError as e:
            result["error"] = f"Plik nie znaleziony: {e}"
        except PermissionError as e:
            result["error"] = f"Brak uprawnień: {e}"
        except Exception as e:
            result["error"] = f"Błąd wykonania: {str(e)}"
        
        self.registry.log_usage(tool_name, args, result)
        self.execution_history.append(result)
        
        return result
    
    def execute_sequence(self, commands):
        """
        Wykonuje sekwencję poleceń.
        
        Args:
            commands: Lista [{"tool": "name", "args": {...}}, ...]
            
        Returns:
            list: Lista wyników
        """
        results = []
        for cmd in commands:
            result = self.execute_tool(cmd.get("tool"), cmd.get("args", {}))
            results.append(result)
            
            if not result.get("success") and cmd.get("stop_on_error", False):
                break
        
        return results
    
    def get_history(self, limit=50):
        """Zwraca historię wykonań."""
        return self.execution_history[-limit:]
