import os
import json
from datetime import datetime


class ExecutorLite:
    def __init__(self, state_manager=None, planner=None, learning_engine=None, config=None):
        self.state = state_manager
        self.planner = planner
        self.learning = learning_engine
        self.config = config or {}
        self.suggestions = []

    def generate_suggestions(self, context):
        suggestions = []
        
        focus_task = context.get("focus_task")
        projects = context.get("projects", [])
        work_status = context.get("work_status", "UNKNOWN")

        if focus_task:
            suggestions.append({
                "id": "continue_task",
                "type": "action",
                "label": "Kontynuuj focus task",
                "description": f"Aktualny focus: {focus_task.get('task', 'N/A')}",
                "action": "continue"
            })

        if work_status == "STAGNATION":
            suggestions.append({
                "id": "break_task",
                "type": "breakdown",
                "label": "Rozbij zadanie",
                "description": "Stagnacja wykryta. Rozważ mniejsze kroki.",
                "action": "breakdown"
            })

        if projects:
            for project in projects[:3]:
                changed = len(project.get("changed_files", [])) > 0
                if changed:
                    suggestions.append({
                        "id": f"review_{project['name']}",
                        "type": "review",
                        "label": f"Przejrzyj zmiany",
                        "description": f"{project['name']}: {len(project.get('changed_files', []))} zmienionych plików",
                        "action": "review",
                        "project": project["name"]
                    })

        suggestions.append({
            "id": "run_tests",
            "type": "tool",
            "label": "Uruchom testy",
            "description": "Sprawdź czy kod działa poprawnie",
            "action": "tool_suggestion",
            "tool": "pytest"
        })

        self.suggestions = suggestions
        return suggestions

    def handle_continue(self):
        return {
            "message": "Świetnie! Kontynuuj pracę nad focus task.",
            "action": "continue",
            "tip": "Zapisuj zmiany regularnie."
        }

    def handle_breakdown(self, task):
        if not task:
            return {"message": "Brak aktywnego taska do rozbicia."}

        task_name = task.get("task", "")
        project = task.get("project", "")

        steps = self._generate_steps(task_name)
        
        return {
            "message": f"Rozbijam '{task_name}' na mniejsze kroki:",
            "action": "breakdown",
            "steps": steps,
            "project": project
        }

    def _generate_steps(self, task_name):
        task_lower = task_name.lower()
        
        if "create" in task_lower and "folder" in task_lower:
            return [
                {"step": 1, "task": "mkdir -p nazwa"},
                {"step": 2, "task": "Dodaj placeholder file"},
                {"step": 3, "task": "Sprawdź strukturę"}
            ]
        elif "setup" in task_lower or "init" in task_lower:
            return [
                {"step": 1, "task": "Inicjalizuj projekt"},
                {"step": 2, "task": "Skonfiguruj podstawy"},
                {"step": 3, "task": "Uruchom pierwszy test"}
            ]
        elif "write" in task_lower or "add" in task_lower:
            return [
                {"step": 1, "task": "Napisz szkielet"},
                {"step": 2, "task": "Dodaj podstawową logikę"},
                {"step": 3, "task": "Przetestuj"}
            ]
        elif "test" in task_lower:
            return [
                {"step": 1, "task": "Napisz jeden test"},
                {"step": 2, "task": "Uruchom testy"},
                {"step": 3, "task": "Popraw błędy"}
            ]
        else:
            return [
                {"step": 1, "task": f"Część 1: {task_name}"},
                {"step": 2, "task": f"Część 2: {task_name}"},
                {"step": 3, "task": "Finalizacja"}
            ]

    def handle_review(self, project_name):
        return {
            "message": f"Zmiany w projekcie '{project_name}':",
            "action": "review",
            "suggestion": "Uruchom: git diff lub przejrzyj pliki w edytorze",
            "project": project_name
        }

    def handle_tool_suggestion(self, tool_name):
        tool_commands = {
            "pytest": "pytest tests/ -v",
            "lint": "ruff check .",
            "format": "black .",
            "typecheck": "mypy src/",
            "build": "python -m build"
        }
        
        command = tool_commands.get(tool_name, f"# Nie znany tool: {tool_name}")
        
        return {
            "message": f"Sugestia: Uruchom {tool_name}",
            "action": "tool_suggestion",
            "command": command,
            "tool": tool_name,
            "note": "Executor Lite - uruchom ręcznie jeśli chcesz."
        }

    def execute_suggestion(self, suggestion_id):
        for suggestion in self.suggestions:
            if suggestion["id"] == suggestion_id:
                action = suggestion.get("action")
                
                if action == "continue":
                    return self.handle_continue()
                elif action == "breakdown":
                    return self.handle_breakdown(self.state.state.get("current_focus_task") if self.state else None)
                elif action == "review":
                    return self.handle_review(suggestion.get("project"))
                elif action == "tool_suggestion":
                    return self.handle_tool_suggestion(suggestion.get("tool"))
                
        return {"message": "Nieznana sugestia."}

    def format_suggestions(self):
        if not self.suggestions:
            return "Brak sugestii."
        
        lines = ["## Sugestie akcji\n"]
        for i, s in enumerate(self.suggestions, 1):
            lines.append(f"{i}. **[{s['type'].upper()}]** {s['label']}")
            lines.append(f"   {s['description']}\n")
        
        return "\n".join(lines)
