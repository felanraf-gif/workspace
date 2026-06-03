import json
import os
from datetime import datetime, timedelta
from core.config import MEMORY_PATH, INTEGRATE_TODOIST

class PressureManager:
    """Moduł wymuszania zamykania tasków."""
    
    LEVEL_NONE = 0
    LEVEL_GENTLE = 1
    LEVEL_REMINDER = 2
    LEVEL_URGENT = 3
    LEVEL_CRITICAL = 4
    
    REMINDER_MESSAGES = {
        LEVEL_GENTLE: "Przypomnienie: masz otwarte zadanie.",
        LEVEL_REMINDER: "Zadanie jest otwarte od {} dni. Czy możesz je zamknąć?",
        LEVEL_URGENT: "⚠️ Zadanie zalega! Rozważ zamknięcie lub usunięcie.",
        LEVEL_CRITICAL: "🚨 CRITICAL: {} dni bez postępu. Zamknij lub wyrzuć."
    }
    
    def __init__(self):
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.pressure_log_file = os.path.join(self.decisions_path, "pressure_log.json")
        self.enabled = INTEGRATE_TODOIST
    
    def get_pressure_level(self, days_open):
        """Określa poziom presji na podstawie dni."""
        if days_open < 1:
            return self.LEVEL_NONE
        elif days_open < 2:
            return self.LEVEL_GENTLE
        elif days_open < 4:
            return self.LEVEL_REMINDER
        elif days_open < 7:
            return self.LEVEL_URGENT
        else:
            return self.LEVEL_CRITICAL
    
    def get_message(self, level, days):
        """Generuje komunikat dla poziomu presji."""
        template = self.REMINDER_MESSAGES.get(level, "")
        if "{}" in template:
            return template.format(days)
        return template
    
    def check_stale_tasks(self, todoist_tools):
        """Sprawdza stare taski i zwraca listę wymagającą uwagi."""
        if not self.enabled:
            return []
        
        stale_tasks = []
        
        try:
            active_tasks = todoist_tools.get_active_tasks(force_refresh=True)
            completed = todoist_tools.get_completed_tasks(since_days=30)
            
            completed_content = {c.get("content") for c in completed}
            
            for task in active_tasks:
                task_id = task.get("id")
                content = task.get("content", "")
                created = task.get("created_at", "")
                priority = task.get("priority", 3)
                
                if not created:
                    continue
                
                try:
                    created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    days_open = (datetime.now() - created_date).days
                except:
                    days_open = 7
                
                level = self.get_pressure_level(days_open)
                
                if level > self.LEVEL_GENTLE:
                    stale_tasks.append({
                        "id": task_id,
                        "content": content,
                        "days_open": days_open,
                        "level": level,
                        "message": self.get_message(level, days_open),
                        "priority": priority
                    })
            
            stale_tasks.sort(key=lambda x: (-x["level"], -x["days_open"]))
            
        except Exception as e:
            print(f"Błąd sprawdzania starych tasków: {e}")
        
        return stale_tasks
    
    def should_archive_task(self, task_info):
        """Sprawdza czy task powinien być archiwizowany."""
        if task_info["level"] >= self.LEVEL_CRITICAL and task_info["days_open"] >= 14:
            return True
        return False
    
    def archive_task(self, task_id, todoist_tools):
        """Archiwizuje (zamyka) stary task."""
        if not self.enabled:
            return False
        
        try:
            return todoist_tools.close_task(task_id)
        except:
            return False
    
    def generate_pressure_summary(self, stale_tasks):
        """Generuje podsumowanie presji dla raportu."""
        if not stale_tasks:
            return ""
        
        summary = "## 🔥 Presja na zamykanie\n\n"
        
        by_level = {self.LEVEL_REMINDER: [], self.LEVEL_URGENT: [], self.LEVEL_CRITICAL: []}
        
        for task in stale_tasks:
            if task["level"] >= self.LEVEL_REMINDER:
                by_level[task["level"]].append(task)
        
        if by_level[self.LEVEL_CRITICAL]:
            summary += "### 🚨 Krytyczne (14+ dni)\n\n"
            for task in by_level[self.LEVEL_CRITICAL][:3]:
                summary += f"- **{task['content']}** ({task['days_open']} dni)\n"
            summary += "\n"
        
        if by_level[self.LEVEL_URGENT]:
            summary += "### ⚠️ Pilne (4-13 dni)\n\n"
            for task in by_level[self.LEVEL_URGENT][:5]:
                summary += f"- {task['content']} ({task['days_open']} dni)\n"
            summary += "\n"
        
        if by_level[self.LEVEL_REMINDER]:
            summary += "### 💡 Przypomnienie (2-3 dni)\n\n"
            for task in by_level[self.LEVEL_REMINDER][:3]:
                summary += f"- {task['content']} ({task['days_open']} dni)\n"
            summary += "\n"
        
        return summary
    
    def log_pressure_action(self, task_content, action, level):
        """Loguje akcję presji."""
        log = self._load_pressure_log()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task_content,
            "action": action,
            "level": level
        }
        
        log.append(entry)
        
        if len(log) > 200:
            log = log[-200:]
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(self.pressure_log_file, 'w') as f:
            json.dump(log, f, indent=2)
    
    def _load_pressure_log(self):
        """Wczytuje log presji."""
        if os.path.exists(self.pressure_log_file):
            try:
                with open(self.pressure_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def get_pressure_stats(self):
        """Zwraca statystyki presji."""
        log = self._load_pressure_log()
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_actions = [e for e in log if e.get("timestamp", "").startswith(today)]
        
        return {
            "total_actions": len(log),
            "today_actions": len(today_actions),
            "last_action": log[-1] if log else None
        }

if __name__ == "__main__":
    pm = PressureManager()
    
    print("=== PressureManager Test ===")
    
    for days in [0, 1, 3, 5, 10, 20]:
        level = pm.get_pressure_level(days)
        msg = pm.get_message(level, days)
        print(f"{days} dni: {level} - {msg}")
