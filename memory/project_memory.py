"""
memory/project_memory.py - Pamięć per-projekt dla multi-project V9
Przechowuje historię, rekomendacje i stan dla każdego projektu osobno
"""

import os
import json
from datetime import datetime
from pathlib import Path


class ProjectMemory:
    """
    Pamięć per-projekt.
    
    Struktura katalogów:
    memory/projects/{project_name}/
    ├── state.json         # Aktualny stan projektu
    ├── history.json       # Historia cykli i tasków
    ├── recommendations.json # Historia rekomendacji
    └── patterns.json      # Wyuczone wzorce
    """
    
    def __init__(self, project_name):
        self.project_name = project_name
        self.base_path = f"memory/projects/{project_name}"
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Upewnia się że katalog istnieje."""
        os.makedirs(self.base_path, exist_ok=True)
    
    @property
    def state_file(self):
        return os.path.join(self.base_path, "state.json")
    
    @property
    def history_file(self):
        return os.path.join(self.base_path, "history.json")
    
    @property
    def recommendations_file(self):
        return os.path.join(self.base_path, "recommendations.json")
    
    @property
    def patterns_file(self):
        return os.path.join(self.base_path, "patterns.json")
    
    def save_state(self, state):
        """Zapisuje stan projektu."""
        full_state = {
            "project": self.project_name,
            "timestamp": datetime.now().isoformat(),
            **state
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(full_state, f, indent=2)
            return True
        except Exception as e:
            print(f"[PROJECT_MEMORY] Błąd zapisu stanu {self.project_name}: {e}")
            return False
    
    def load_state(self):
        """Ładuje stan projektu."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"project": self.project_name}
    
    def add_history_entry(self, entry):
        """Dodaje wpis do historii projektu."""
        history = self.load_history()
        
        full_entry = {
            "timestamp": datetime.now().isoformat(),
            **entry
        }
        
        history.append(full_entry)
        
        history = history[-100:]
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        except Exception as e:
            print(f"[PROJECT_MEMORY] Błąd zapisu historii {self.project_name}: {e}")
            return False
    
    def load_history(self, days=None):
        """Ładuje historię projektu."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    
                    if days:
                        cutoff = datetime.now().timestamp() - (days * 86400)
                        history = [h for h in history if datetime.fromisoformat(h["timestamp"]).timestamp() > cutoff]
                    
                    return history
            except:
                pass
        return []
    
    def save_recommendation(self, recommendation):
        """Zapisuje rekomendację."""
        recs = self.load_recommendations()
        
        full_rec = {
            "timestamp": datetime.now().isoformat(),
            **recommendation
        }
        
        recs.append(full_rec)
        
        recs = recs[-50:]
        
        try:
            with open(self.recommendations_file, 'w') as f:
                json.dump(recs, f, indent=2)
            return True
        except Exception as e:
            print(f"[PROJECT_MEMORY] Błąd zapisu rekomendacji {self.project_name}: {e}")
            return False
    
    def load_recommendations(self, days=None):
        """Ładuje rekomendacje projektu."""
        if os.path.exists(self.recommendations_file):
            try:
                with open(self.recommendations_file, 'r') as f:
                    recs = json.load(f)
                    
                    if days:
                        cutoff = datetime.now().timestamp() - (days * 86400)
                        recs = [r for r in recs if datetime.fromisoformat(r["timestamp"]).timestamp() > cutoff]
                    
                    return recs
            except:
                pass
        return []
    
    def get_patterns(self):
        """Ładuje wyuczone wzorce."""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"completed_tasks": [], "focus_tasks": [], "patterns": []}
    
    def save_pattern(self, pattern_type, pattern_data):
        """Zapisuje wzorzec."""
        patterns = self.get_patterns()
        
        if pattern_type == "completed_task":
            patterns["completed_tasks"].append({
                "timestamp": datetime.now().isoformat(),
                **pattern_data
            })
            patterns["completed_tasks"] = patterns["completed_tasks"][-50:]
        
        elif pattern_type == "focus_task":
            patterns["focus_tasks"].append({
                "timestamp": datetime.now().isoformat(),
                **pattern_data
            })
            patterns["focus_tasks"] = patterns["focus_tasks"][-20:]
        
        elif pattern_type == "pattern":
            patterns["patterns"].append({
                "timestamp": datetime.now().isoformat(),
                **pattern_data
            })
            patterns["patterns"] = patterns["patterns"][-30:]
        
        try:
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns, f, indent=2)
            return True
        except Exception as e:
            print(f"[PROJECT_MEMORY] Błąd zapisu wzorców {self.project_name}: {e}")
            return False
    
    def get_productivity_stats(self):
        """Zwraca statystyki produktywności projektu."""
        history = self.load_history(days=30)
        recommendations = self.load_recommendations(days=30)
        patterns = self.get_patterns()
        
        completed_tasks = len(patterns.get("completed_tasks", []))
        focus_tasks = len(patterns.get("focus_tasks", []))
        
        completion_rate = 0
        if focus_tasks > 0:
            completion_rate = completed_tasks / focus_tasks * 100
        
        avg_cycle_time = 0
        if len(history) > 1:
            total_time = 0
            count = 0
            for i in range(1, len(history)):
                try:
                    t1 = datetime.fromisoformat(history[i-1]["timestamp"])
                    t2 = datetime.fromisoformat(history[i]["timestamp"])
                    total_time += (t2 - t1).total_seconds()
                    count += 1
                except:
                    pass
            if count > 0:
                avg_cycle_time = total_time / count / 3600
        
        return {
            "project": self.project_name,
            "period_days": 30,
            "cycles_count": len(history),
            "completed_tasks": completed_tasks,
            "focus_tasks": focus_tasks,
            "completion_rate": round(completion_rate, 1),
            "avg_cycle_hours": round(avg_cycle_time, 2),
            "recommendations_count": len(recommendations),
            "high_priority_recs": len([r for r in recommendations if r.get("priority") == "HIGH"])
        }


class MultiProjectMemory:
    """
    Zarządza pamięcią wielu projektów.
    """
    
    def __init__(self):
        self.projects_base = "memory/projects"
        os.makedirs(self.projects_base, exist_ok=True)
    
    def get_project_memory(self, project_name):
        """Pobiera pamięć dla projektu."""
        return ProjectMemory(project_name)
    
    def list_projects(self):
        """Lista projektów z pamięcią."""
        if not os.path.exists(self.projects_base):
            return []
        
        projects = []
        for name in os.listdir(self.projects_base):
            path = os.path.join(self.projects_base, name)
            if os.path.isdir(path):
                projects.append(name)
        
        return sorted(projects)
    
    def get_all_stats(self):
        """Zwraca statystyki wszystkich projektów."""
        stats = []
        for project_name in self.list_projects():
            pm = ProjectMemory(project_name)
            stats.append(pm.get_productivity_stats())
        return stats
    
    def cleanup_old_projects(self, max_age_days=90):
        """Usuwa stare projekty bez aktywności."""
        projects = self.list_projects()
        removed = []
        
        for project_name in projects:
            pm = ProjectMemory(project_name)
            state = pm.load_state()
            last_update = state.get("timestamp")
            
            if last_update:
                try:
                    dt = datetime.fromisoformat(last_update)
                    days_old = (datetime.now() - dt).days
                    
                    if days_old > max_age_days:
                        import shutil
                        project_path = os.path.join(self.projects_base, project_name)
                        shutil.rmtree(project_path)
                        removed.append(project_name)
                except:
                    pass
        
        return removed
