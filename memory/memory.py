"""
memory/memory.py - Uproszczony system pamięci
Konsolidacja: memory_manager + time tracking
"""

import os
import json
from datetime import datetime, timedelta
from core.config import MEMORY_PATH, SYSTEM_PATH


class Memory:
    """Centralna pamięć systemu - stan, historia, time tracking."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.memory_path = MEMORY_PATH
        self.system_path = SYSTEM_PATH
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.archive_path = os.path.join(MEMORY_PATH, "archive")
        self.analytics_path = os.path.join(MEMORY_PATH, "analytics")
        
        self.state_file = os.path.join(self.system_path, "state.json")
        self.history_file = os.path.join(self.decisions_path, "work_history.json")
        self.time_log_file = os.path.join(MEMORY_PATH, "time_tracking.json")
        
        os.makedirs(self.decisions_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
        os.makedirs(self.analytics_path, exist_ok=True)
        
        self._ensure_files()
        self._initialized = True
    
    def _ensure_files(self):
        if not os.path.exists(self.state_file):
            self.save_state({"status": "initialized"})
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
        if not os.path.exists(self.time_log_file):
            with open(self.time_log_file, 'w') as f:
                json.dump([], f)

    def get_state(self):
        """Pobiera aktualny stan."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {"status": "error"}

    def save_state(self, updates):
        """Aktualizuje stan."""
        state = self.get_state()
        state.update(updates)
        state["last_update"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        return state

    def add_history_entry(self, status, score, tasks=None, projects=None):
        """Dodaje wpis do historii."""
        history = self.get_history(days=365)
        history.append({
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": status,
            "score": score,
            "tasks_count": len(tasks) if tasks else 0,
            "projects": list(projects) if projects else []
        })
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        return history[-1]

    def get_history(self, days=30):
        """Pobiera historię pracy."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        except:
            return []
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [e for e in history if e.get("date", "") >= cutoff]

    def get_work_trends(self):
        """Analizuje trendy pracy."""
        history = self.get_history(days=30)
        if not history:
            return {"trend": "unknown", "avg_score": 0}
        
        recent = history[-7:] if len(history) >= 7 else history
        avg_score = sum(e.get("score", 0) for e in recent) / len(recent)
        
        if len(history) >= 14:
            older = history[-14:-7]
            older_avg = sum(e.get("score", 0) for e in older) / len(older) if older else 0
            if avg_score > older_avg * 1.2:
                trend = "improving"
            elif avg_score < older_avg * 0.8:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {"trend": trend, "avg_score": round(avg_score, 1), "entries": len(history)}

    def archive_old_files(self):
        """Archiwizuje stare plany."""
        if not os.path.exists(self.decisions_path):
            return
        
        today = datetime.now()
        archive_month = os.path.join(self.archive_path, today.strftime("%Y-%m"))
        os.makedirs(archive_month, exist_ok=True)
        
        for filename in os.listdir(self.decisions_path):
            if filename.startswith("plan_") and filename.endswith(".json"):
                filepath = os.path.join(self.decisions_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        date = data.get("created", "")[:10]
                        if date and date < today.strftime("%Y-%m-%d"):
                            import shutil
                            shutil.move(filepath, os.path.join(archive_month, filename))
                except:
                    pass

    def clear_old_cache(self):
        """Czyści stary cache."""
        cache_files = [
            os.path.join(self.decisions_path, f"task_cache_{d}.json")
            for d in range(1, 8)
        ]
        for f in cache_files:
            if os.path.exists(f):
                os.remove(f)

    def get_daily_time(self, date_str=None):
        """Pobiera czas pracy dla dnia."""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        daily_file = os.path.join(self.decisions_path, f"time_{date_str}.json")
        if os.path.exists(daily_file):
            try:
                with open(daily_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_daily_time(self, project, duration):
        """Zapisuje czas pracy projektu."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_file = os.path.join(self.decisions_path, f"time_{date_str}.json")
        
        data = {}
        if os.path.exists(daily_file):
            try:
                with open(daily_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        data[project] = data.get(project, 0) + duration
        
        with open(daily_file, 'w') as f:
            json.dump(data, f, indent=2)

    def log_time_event(self, event_type, task):
        """Loguje zdarzenie czasowe."""
        try:
            with open(self.time_log_file, 'r') as f:
                log = json.load(f)
        except:
            log = []
        
        log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "task": task
        })
        
        if len(log) > 1000:
            log = log[-1000:]
        
        with open(self.time_log_file, 'w') as f:
            json.dump(log, f, indent=2)

    def get_cycles_without_progress(self):
        """Pobiera licznik cykli bez postępu."""
        state = self.get_state()
        return state.get("cycles_without_progress", 0)

    def increment_cycles_without_progress(self):
        """Zwiększa licznik cykli bez postępu."""
        state = self.get_state()
        cycles = state.get("cycles_without_progress", 0) + 1
        self.save_state({"cycles_without_progress": cycles})
        return cycles

    def reset_cycles_without_progress(self):
        """Resetuje licznik."""
        self.save_state({"cycles_without_progress": 0})

    def get_last_completed_task(self):
        """Pobiera ostatni ukończony task."""
        state = self.get_state()
        return state.get("last_completed_task")

    def set_last_completed_task(self, task):
        """Ustawia ostatni ukończony task."""
        self.save_state({"last_completed_task": task, "last_completion": datetime.now().isoformat()})

    def get_last_todoist_check(self):
        """Czas ostatniego sprawdzenia Todoist."""
        state = self.get_state()
        return state.get("last_todoist_check")

    def set_last_todoist_check(self):
        """Ustawia czas sprawdzenia Todoist."""
        self.save_state({"last_todoist_check": datetime.now().isoformat()})

    def can_check_todoist_again(self, minutes=15):
        """Sprawdza czy można znów sprawdzić Todoist."""
        last = self.get_last_todoist_check()
        if not last:
            return True
        elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
        return elapsed >= minutes

    def get_tasks_sent_today(self):
        """Liczba tasków wysłanych dziś."""
        state = self.get_state()
        today = datetime.now().strftime("%Y-%m-%d")
        sent_today = state.get("tasks_sent_today", [])
        if sent_today and sent_today[0].get("date") == today:
            return sent_today[0].get("count", 0)
        return 0

    def set_daily_tasks_sent(self, count):
        """Ustawia liczbę wysłanych tasków."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.save_state({"tasks_sent_today": [{"date": today, "count": count}]})

    def can_send_more_tasks(self, max_daily=5):
        """Sprawdza czy można wysłać więcej tasków."""
        return self.get_tasks_sent_today() < max_daily
