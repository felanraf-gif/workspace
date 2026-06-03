import json
import os
from datetime import datetime
from core.config import MEMORY_PATH

class Guidance:
    """Moduł prowadzenia - wybiera 1 focus task i generuje komunikaty."""
    
    FOCUS_LABEL = "FOCUS"
    REAL_WORK = "REAL_WORK"
    LOW_PROGRESS = "LOW_PROGRESS"
    STAGNATION = "STAGNATION"
    
    def __init__(self):
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.focus_log_file = os.path.join(self.decisions_path, "focus_history.json")
    
    def select_focus_task(self, tasks):
        """Wybiera 1 najważniejszy task do realizacji."""
        if not tasks:
            return None
        
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_tasks = sorted(
            tasks, 
            key=lambda t: (
                priority_order.get(t.get("priority", "LOW"), 3),
                -t.get("value_score", 0),
                -t.get("trend_score", 0)
            )
        )
        
        return sorted_tasks[0]
    
    def generate_message(self, status, work_data):
        """Generuje komunikat systemowy dla użytkownika."""
        project_status = {}
        if work_data and "projects" in work_data:
            project_status = work_data["projects"]
        
        if status == self.STAGNATION:
            stagnant_projects = [p for p, d in project_status.items() if d.get("status") == self.STAGNATION]
            if stagnant_projects:
                msg = f"⚠️ **Stagnacja wykryta** w: {', '.join(stagnant_projects)}\n\n"
                msg += "Zrób jedną konkretną rzecz:\n"
                msg += "→ stwórz plik\n"
                msg += "→ zamknij task\n"
                msg += "→ zrób commit"
                return msg
            return "⚠️ Brak realnego postępu. Zrób jedną konkretną rzecz."
        
        elif status == self.LOW_PROGRESS:
            return "🟡 Za mało postępu. Skup się na jednym zadaniu i doprowadź je do końca."
        
        elif status == self.REAL_WORK:
            if project_status:
                best_project = max(project_status.items(), key=lambda x: x[1].get("score", 0))
                return f"✅ Dobrze idziesz! Kontynuuj pracę nad **{best_project[0]}**."
            return "✅ Dobrze idziesz. Kontynuuj."
        
        return "📋 Masz zadania do wykonania. Wybierz jeden task."
    
    def get_stagnation_warning(self, work_data):
        """Generuje ostrzeżenie dla stagnacji."""
        if not work_data or "projects" not in work_data:
            return None
        
        stagnant = []
        for project, data in work_data["projects"].items():
            if data.get("status") == self.STAGNATION:
                stagnant.append({
                    "project": project,
                    "days": data.get("stagnation_days", 0)
                })
        
        if stagnant:
            return {
                "type": "warning",
                "projects": stagnant,
                "message": "Wykryto stagnację w projektach"
            }
        
        return None
    
    def should_send_reminder(self, last_reminder_date):
        """Sprawdza czy minęło достаточно czasu od ostatniego przypomnienia."""
        if not last_reminder_date:
            return True
        
        try:
            last = datetime.fromisoformat(last_reminder_date)
            hours_since = (datetime.now() - last).total_seconds() / 3600
            return hours_since >= 2
        except:
            return True
    
    def get_focus_section_md(self, focus_task, message):
        """Generuje sekcję Focus dla raportu Markdown."""
        if not focus_task:
            return ""
        
        project = focus_task.get("project", "N/A")
        task = focus_task.get("task", "Brak zadania")
        priority = focus_task.get("priority", "LOW")
        
        priority_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
        
        return f"""## 🎯 Focus na dziś

{priority_icon} **[{project}]** {task}

## ⚠️ Komunikat systemu

{message}
"""
    
    def mark_task_as_focus(self, task_content, planner):
        """Oznacza task jako FOCUS w Todoist dodając etykietę."""
        try:
            todoist_tools = __import__('modules.tools.todoist_tools', fromlist=['TodoistTools']).TodoistTools()
            
            tasks = todoist_tools.get_active_tasks(force_refresh=True)
            for task in tasks:
                if task.get("content") == task_content:
                    task_id = task.get("id")
                    
                    existing_labels = task.get("labels", [])
                    if self.FOCUS_LABEL not in existing_labels:
                        new_labels = existing_labels + [self.FOCUS_LABEL]
                        
                        import requests
                        response = requests.post(
                            f"{todoist_tools.REST_API_URL}/tasks/{task_id}",
                            headers=todoist_tools.rest_headers,
                            json={"labels": new_labels}
                        )
                        
                        if response.status_code == 200:
                            return True
            return False
        except Exception as e:
            print(f"Błąd oznaczania FOCUS: {e}")
            return False
    
    def get_task_content(self, task):
        """Tworzy treść tasku do wyszukiwania w Todoist."""
        project = task.get("project", "")
        task_text = task.get("task", "")
        
        if project and project != "unknown":
            return f"[{project}] {task_text}"
        return task_text
    
    def save_focus_log(self, focus_task, message, status):
        """Zapisuje log focus taska."""
        log = self._load_focus_log()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "focus_task": focus_task,
            "message": message,
            "status": status
        }
        
        log.append(entry)
        
        if len(log) > 100:
            log = log[-100:]
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(self.focus_log_file, 'w') as f:
            json.dump(log, f, indent=2)
    
    def _load_focus_log(self):
        """Wczytuje log focus."""
        if os.path.exists(self.focus_log_file):
            try:
                with open(self.focus_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def get_today_focus(self):
        """Pobiera focus task z dzisiaj."""
        log = self._load_focus_log()
        today = datetime.now().strftime("%Y-%m-%d")
        
        for entry in reversed(log):
            if entry.get("timestamp", "").startswith(today):
                return entry
        
        return None

if __name__ == "__main__":
    guidance = Guidance()
    
    print("=== Guidance Test ===")
    
    mock_tasks = [
        {"project": "towarzysz", "task": "Utwórz src/", "priority": "HIGH", "value_score": 0.8},
        {"project": "scraper_1", "task": "Dodaj testy", "priority": "MEDIUM", "value_score": 0.5},
        {"project": "content_bot", "task": "Refaktoryzuj kod", "priority": "LOW", "value_score": 0.3},
    ]
    
    focus = guidance.select_focus_task(mock_tasks)
    print(f"Focus task: [{focus['project']}] {focus['task']}")
    
    message = guidance.generate_message("STAGNATION", {
        "projects": {
            "towarzysz": {"status": "STAGNATION", "days": 3}
        }
    })
    print(f"Message: {message}")
    
    section = guidance.get_focus_section_md(focus, message)
    print(f"\nFocus section:\n{section}")
