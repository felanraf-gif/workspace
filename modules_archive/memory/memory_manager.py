import json
import os
from datetime import datetime, timedelta
from core.config import MEMORY_PATH, SYSTEM_PATH

class MemoryManager:
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
        
        self.state_file = os.path.join(self.system_path, "state.json")
        self.history_file = os.path.join(self.decisions_path, "work_history.json")
        
        os.makedirs(self.decisions_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
        
        self._ensure_files()
        self._initialized = True
    
    def _ensure_files(self):
        if not os.path.exists(self.state_file):
            self.save_state({"status": "initialized", "last_update": datetime.now().isoformat()})
        
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def get_state(self):
        """Pobiera aktualny stan systemu."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {"status": "error", "error": "Could not load state"}
    
    def save_state(self, updates):
        """Aktualizuje stan systemu."""
        state = self.get_state()
        state.update(updates)
        state["last_update"] = datetime.now().isoformat()
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return state
    
    def add_history_entry(self, status, score, tasks=None, projects=None):
        """Dodaje wpis do historii pracy."""
        history = self.get_history(days=365)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": status,
            "score": score,
            "tasks_count": len(tasks) if tasks else 0,
            "projects": list(projects) if projects else []
        }
        
        history.append(entry)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return entry
    
    def get_history(self, days=30):
        """Pobiera historię pracy z ostatnich N dni."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        except:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return [h for h in history if h.get("timestamp", "") >= cutoff_str]
    
    def get_work_trends(self):
        """Analizuje trendy pracy."""
        history = self.get_history(days=30)
        
        if not history:
            return {"trend": "unknown", "avg_score": 0, "days_active": 0}
        
        scores = [h.get("score", 0) for h in history]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        real_work_days = len([h for h in history if h.get("status") == "REAL_WORK"])
        stagnation_days = len([h for h in history if h.get("status") == "STAGNATION"])
        
        trend = "stable"
        if len(scores) >= 3:
            recent_avg = sum(scores[-3:]) / 3
            older_avg = sum(scores[:-3]) / (len(scores) - 3) if len(scores) > 3 else recent_avg
            if recent_avg > older_avg + 1:
                trend = "improving"
            elif recent_avg < older_avg - 1:
                trend = "declining"
        
        return {
            "trend": trend,
            "avg_score": round(avg_score, 2),
            "days_active": len(history),
            "real_work_days": real_work_days,
            "stagnation_days": stagnation_days,
            "total_tasks": sum(h.get("tasks_count", 0) for h in history)
        }
    
    def get_daily_summary(self, date_str=None):
        """Pobiera podsumowanie dnia."""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        history = self.get_history(days=365)
        today_entries = [h for h in history if h.get("date") == date_str]
        
        if not today_entries:
            return None
        
        return {
            "date": date_str,
            "entries_count": len(today_entries),
            "status": today_entries[-1].get("status"),
            "score": today_entries[-1].get("score"),
            "tasks": today_entries[-1].get("tasks_count", 0)
        }
    
    def get_last_work_status(self):
        """Pobiera ostatni status pracy."""
        history = self.get_history(days=1)
        if history:
            return history[-1].get("status", "UNKNOWN")
        return "NO_DATA"
    
    def archive_old_files(self, days=30):
        """Archiwizuje stare plany i trackingi."""
        if not os.path.exists(self.decisions_path):
            return {"archived": 0}
        
        cutoff = datetime.now() - timedelta(days=days)
        archived = []
        
        for filename in os.listdir(self.decisions_path):
            if filename.startswith("plan_") or filename.startswith("tracking_"):
                filepath = os.path.join(self.decisions_path, filename)
                
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff:
                        archive_subdir = os.path.join(self.archive_path, mtime.strftime("%Y-%m"))
                        os.makedirs(archive_subdir, exist_ok=True)
                        
                        new_path = os.path.join(archive_subdir, filename)
                        os.rename(filepath, new_path)
                        archived.append(filename)
                except:
                    pass
        
        return {"archived": len(archived), "files": archived}
    
    def get_stats(self):
        """Zwraca statystyki systemu."""
        history = self.get_history(days=365)
        trends = self.get_work_trends()
        
        return {
            "total_history_entries": len(history),
            "days_tracked": len(set(h.get("date") for h in history)),
            "work_trends": trends,
            "last_update": self.get_state().get("last_update"),
            "active_projects": self.get_state().get("projects", [])
        }
    
    def clear_old_cache(self, max_age_days=7):
        """Czyści stary cache tasków."""
        cache_file = os.path.join(self.decisions_path, "task_cache.json")
        
        if not os.path.exists(cache_file):
            return {"cleared": False}
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            updated = data.get("updated", "")
            if updated:
                cache_date = datetime.fromisoformat(updated)
                age_days = (datetime.now() - cache_date).days
                
                if age_days > max_age_days:
                    data = {"tasks": [], "updated": datetime.now().isoformat()}
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                    return {"cleared": True, "reason": f"cache_age_{age_days}_days"}
        except:
            pass
        
        return {"cleared": False}
    
    def log(self, module, action, details=None):
        """Loguje akcję do globalnego loga."""
        log_file = os.path.join(self.system_path, "global_log.txt")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {module}: {action}"
        if details:
            entry += f" - {details}"
        entry += "\n"
        
        with open(log_file, 'a') as f:
            f.write(entry)

if __name__ == "__main__":
    mm = MemoryManager()
    
    print("=== MemoryManager Test ===")
    print(f"State: {mm.get_state()}")
    print(f"Stats: {mm.get_stats()}")
    print(f"Trends: {mm.get_work_trends()}")
    
    state = mm.get_state()
    mm.save_state({**state, "test": True})
    print("State updated")
    
    print(f"Last status: {mm.get_last_work_status()}")
