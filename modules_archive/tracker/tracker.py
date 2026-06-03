import json
import os
import time
from datetime import datetime, timedelta
from core.config import PROJECTS_PATH, MEMORY_PATH, OBSIDIAN_PATH, STAGNATION_DAYS

class Tracker:
    def __init__(self):
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.lessons_dir = os.path.join(OBSIDIAN_PATH, "lessons")
        self.projects_path = PROJECTS_PATH
        self.time_log_file = os.path.join(MEMORY_PATH, "time_tracking.json")
        
        # Inicjalizacja time tracking
        self.task_start_time = {}
        self.current_task = None
        
        # Utwórz folder lessons w Obsidian
        os.makedirs(self.lessons_dir, exist_ok=True)

    def start_task_tracking(self, task):
        """Rozpocznij śledzenie czasu dla zadania."""
        self.current_task = task
        self.task_start_time[task["project"]] = time.time()
        
        # Zapisz do time log
        self._log_time_event("START", task)

    def stop_task_tracking(self, project):
        """Zakończ śledzenie czasu dla projektu."""
        if project in self.task_start_time:
            duration = time.time() - self.task_start_time[project]
            task = {"project": project, "duration": duration}
            self._log_time_event("STOP", task)
            
            # Zapisz do daily time log
            self._save_daily_time(project, duration)
            
            del self.task_start_time[project]
            
            if self.current_task and self.current_task["project"] == project:
                self.current_task = None

    def _log_time_event(self, event_type, task):
        """Zapisz zdarzenie time tracking."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "task": task
        }
        
        time_log = self._load_time_log()
        time_log.append(log_entry)
        
        # Ogranicz do ostatnich 1000 wpisów
        if len(time_log) > 1000:
            time_log = time_log[-1000:]
        
        with open(self.time_log_file, 'w') as f:
            json.dump(time_log, f, indent=2)

    def _load_time_log(self):
        """Wczytaj log time tracking."""
        if os.path.exists(self.time_log_file):
            try:
                with open(self.time_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_daily_time(self, project, duration):
        """Zapisz czas pracy dla danego dnia."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_file = os.path.join(self.decisions_path, f"time_{date_str}.json")
        
        os.makedirs(self.decisions_path, exist_ok=True)
        
        daily_data = {}
        if os.path.exists(daily_file):
            try:
                with open(daily_file, 'r') as f:
                    daily_data = json.load(f)
            except:
                pass
        
        if project not in daily_data:
            daily_data[project] = 0
        
        daily_data[project] += duration
        
        with open(daily_file, 'w') as f:
            json.dump(daily_data, f, indent=2)

    def monitor_progress(self, projects):
        """Monitoruje postęp projektów."""
        status = {}
        current_time = datetime.now()
        
        for project in projects:
            project_name = project["name"]
            project_dir = os.path.join(self.projects_path, project_name)
            
            try:
                mod_time = os.path.getmtime(project_dir)
                last_modified = datetime.fromtimestamp(mod_time)
                hours_diff = (current_time - last_modified).total_seconds() / 3600
                
                status[project_name] = {
                    "last_modified": last_modified.isoformat(),
                    "hours_since_change": round(hours_diff, 2),
                    "active": hours_diff < 24
                }
            except OSError:
                status[project_name] = {
                    "last_modified": None,
                    "hours_since_change": None,
                    "active": False
                }
        
        return status

    def detect_stagnation(self, status, threshold_days=None):
        """Wykrywa stagnację projektów."""
        if threshold_days is None:
            threshold_days = STAGNATION_DAYS
            
        stagnation_report = []
        current_time = datetime.now()
        threshold_hours = threshold_days * 24
        
        for project_name, info in status.items():
            if info["active"] and info["last_modified"]:
                last_mod = datetime.fromisoformat(info["last_modified"])
                hours_diff = (current_time - last_mod).total_seconds() / 3600
                
                if hours_diff > threshold_hours:
                    stagnation_report.append({
                        "project": project_name,
                        "last_active": info["last_modified"],
                        "stagnation_hours": round(hours_diff, 2),
                        "stagnation_days": round(hours_diff / 24, 1),
                        "alert": "STAGNATION_DETECTED"
                    })
        
        return stagnation_report

    def generate_daily_lesson(self, projects, issues, tasks, time_data):
        """Generuje czytelną lekcję dnia w formacie Markdown."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        lesson_file = os.path.join(self.lessons_dir, f"{date_str}_lekcja.md")
        
        # Przygotuj dane czasowe
        total_time = 0
        project_time = {}
        for project, duration in time_data.items():
            total_time += duration
            project_time[project] = round(duration / 3600, 2)  # w godzinach
        
        # Przygotuj treść lekcji
        content = f"# Lekcja dnia - {date_str}\n\n"
        content += "---\n\n"
        
        # Sekcja: Podsumowanie czasu
        content += "## ⏱️ Czas pracy\n\n"
        content += f"- **Czas całkowity:** {round(total_time / 3600, 2)} godz.\n"
        if project_time:
            content += "- **Czas per projekt:**\n"
            for project, hours in project_time.items():
                content += f"  - {project}: {hours} godz.\n"
        content += "\n"
        
        # Sekcja: Wykonane zadania
        content += "## ✅ Wykonane zadania\n\n"
        completed_tasks = [t for t in tasks if t.get("completed", False)]
        if completed_tasks:
            for task in completed_tasks:
                content += f"- [{task['priority']}] **{task['project']}**: {task['task']}\n"
        else:
            content += "Brak zakończonych zadań (zadania aktywne)\n"
        content += "\n"
        
        # Sekcja: Problemy i wyzwania
        content += "## ⚠️ Problemy i wyzwania\n\n"
        if issues:
            for issue in issues:
                content += f"- **{issue['project']}**: {issue['issue']}\n"
        else:
            content += "Brak problemów\n"
        content += "\n"
        
        # Sekcja: Refleksje i wnioski
        content += "## 💡 Refleksje i wnioski\n\n"
        content += "### Co poszło dobrze:\n"
        content += "- \n\n"
        content += "### Co można poprawić:\n"
        content += "- \n\n"
        content += "### Plan na jutro:\n"
        content += "- \n\n"
        
        # Sekcja: Sugestie agenta
        content += "## 🤖 Sugestie agenta\n\n"
        if total_time > 0:
            avg_time = total_time / len(time_data) if time_data else 0
            content += f"- Średni czas na projekt: {round(avg_time / 3600, 2)} godz.\n"
        
        if len(completed_tasks) == 0 and len(tasks) > 0:
            content += "- Brak zakończonych zadań - rozważ skupienie się na priorytetach HIGH\n"
        
        content += "\n---\n"
        content += f"*Wygenerowane przez Development Assistant V4 - {datetime.now().strftime('%H:%M')}*\n"
        
        # Zapis do pliku
        with open(lesson_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return lesson_file

    def save_tracking(self, status, stagnation_report):
        """Zapisuje wyniki śledzenia."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tracking_file = os.path.join(self.decisions_path, f"tracking_{timestamp}.json")
        
        tracking_data = {
            "timestamp": timestamp,
            "status": status,
            "stagnation_report": stagnation_report
        }
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        
        return tracking_file

    def check_todoist_completed(self):
        """Sprawdza ukończone taski w Todoist i zwraca ile zostało."""
        try:
            from modules.tools.todoist_tools import TodoistTools
            
            todoist = TodoistTools()
            active_tasks = todoist.get_active_tasks()
            completed_tasks = todoist.get_completed_tasks(since_days=1)
            
            return {
                "active_count": len(active_tasks),
                "completed_today": len(completed_tasks),
                "remaining": len(active_tasks),
                "completed": completed_tasks
            }
        except Exception as e:
            print(f"Błąd sprawdzania Todoist: {e}")
            return {
                "active_count": 0,
                "completed_today": 0,
                "remaining": 0,
                "completed": [],
                "error": str(e)
            }
    
    def get_recently_completed_tasks(self, hours=24):
        """Zwraca listę zamkniętych tasków z ostatnich N godzin.
        
        Używane przez CompletionGuard do sprawdzenia czy focus task został zamknięty.
        """
        try:
            from modules.tools.todoist_tools import TodoistTools
            
            todoist = TodoistTools()
            completed_tasks = todoist.get_completed_tasks(since_days=1)
            
            if not completed_tasks:
                return []
            
            now = datetime.now()
            recent_tasks = []
            
            for task in completed_tasks:
                completed_at = task.get("completed_at")
                if completed_at:
                    try:
                        completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        completed_time = completed_time.replace(tzinfo=None)
                        hours_diff = (now - completed_time).total_seconds() / 3600
                        
                        if hours_diff <= hours:
                            recent_tasks.append({
                                "content": task.get("content", ""),
                                "completed_at": completed_at,
                                "hours_ago": round(hours_diff, 1)
                            })
                    except Exception:
                        continue
            
            return recent_tasks
        except Exception as e:
            print(f"Błąd pobierania zamkniętych tasków: {e}")
            return []

if __name__ == "__main__":
    tracker = Tracker()
    
    # Test time tracking
    test_task = {"project": "test_project", "task": "Test task", "priority": "MEDIUM"}
    tracker.start_task_tracking(test_task)
    time.sleep(2)
    tracker.stop_task_tracking("test_project")
    
    # Test daily lesson
    time_data = {"test_project": 7200, "another_project": 3600}
    lesson_file = tracker.generate_daily_lesson([], [], [], time_data)
    print(f"Lekcja zapisana w: {lesson_file}")