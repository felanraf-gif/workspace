"""
brain/project_manager.py - Zarządzanie projektami w multi-project V9
Koordynuje cykl pracy per-projekt
"""

import os
import json
from datetime import datetime
from pathlib import Path


class ProjectManager:
    """
    Zarządza listą projektów i ich cyklami pracy.
    
    Każdy projekt ma własny PROJECT_STATE:
    - name: nazwa projektu
    - path: ścieżka do projektu
    - type: typ projektu (python, javascript, etc.)
    - last_analysis: timestamp ostatniej analizy
    - last_cycle: timestamp ostatniego cyklu V9
    - focus_task: aktualny fokus task
    - v9_status: status cyklu V9
    - tasks_sent_today: liczba wysłanych tasków
    - recommendations: lista rekomendacji
    """
    
    def __init__(self, projects_cache=None):
        self.projects_cache = projects_cache or []
        self.states_file = "memory/project_states.json"
        self.project_states = self._load_states()
    
    def get_projects(self):
        """Zwraca listę projektów z ich stanami."""
        projects = []
        
        for project_data in self.projects_cache:
            name = project_data.get("name")
            state = self.project_states.get(name, self._create_default_state(name, project_data))
            
            projects.append({
                **project_data,
                **state
            })
        
        return projects
    
    def get_project(self, name):
        """Pobiera pojedynczy projekt."""
        for project_data in self.projects_cache:
            if project_data.get("name") == name:
                state = self.project_states.get(name, self._create_default_state(name, project_data))
                return {**project_data, **state}
        return None
    
    def update_project_state(self, name, updates):
        """Aktualizuje stan projektu."""
        if name not in self.project_states:
            project_data = self.get_project(name)
            self.project_states[name] = self._create_default_state(name, project_data or {})
        
        self.project_states[name].update(updates)
        self.project_states[name]["last_update"] = datetime.now().isoformat()
        self._save_states()
    
    def get_project_focus_order(self):
        """
        Zwraca projekty w kolejności priorytetu fokusu.
        
        Priorytety:
        1. Projekty z nieukończonym fokus taskiem
        2. Projekty z wysokimi rekomendacjami
        3. Projekty z brakiem aktywności
        4. Projekty starsze niż 24h bez cyklu
        """
        projects = self.get_projects()
        
        scored = []
        for project in projects:
            score = 0
            
            if project.get("focus_task"):
                score += 100
            
            recs = project.get("recommendations", [])
            high_recs = [r for r in recs if r.get("priority") == "HIGH"]
            score += len(high_recs) * 20
            
            days_since = self._days_since(project.get("last_cycle"))
            if days_since and days_since > 24:
                score += (days_since - 24) * 5
            
            if not project.get("last_cycle"):
                score += 50
            
            scored.append({
                "project": project,
                "score": score,
                "name": project.get("name")
            })
        
        scored.sort(key=lambda x: -x["score"])
        return [s["project"] for s in scored]
    
    def should_run_cycle(self, name, interval_hours=24):
        """Sprawdza czy projekt powinien mieć uruchomiony cykl."""
        project = self.get_project(name)
        if not project:
            return True
        
        last_cycle = project.get("last_cycle")
        if not last_cycle:
            return True
        
        days_since = self._days_since(last_cycle)
        return days_since is None or days_since >= interval_hours
    
    def get_projects_needing_attention(self):
        """Zwraca projekty wymagające uwagi."""
        projects = self.get_projects()
        attention = []
        
        for project in projects:
            recs = project.get("recommendations", [])
            
            high_recs = [r for r in recs if r.get("priority") == "HIGH"]
            if high_recs:
                attention.append({
                    "name": project.get("name"),
                    "type": "high_priority_recommendations",
                    "count": len(high_recs),
                    "recommendations": high_recs
                })
            
            status = project.get("status")
            if status in ["stagnant", "abandoned"]:
                attention.append({
                    "name": project.get("name"),
                    "type": "project_status",
                    "status": status,
                    "days_since_edit": project.get("days_since_edit")
                })
            
            if project.get("focus_task") and not project.get("focus_completed"):
                attention.append({
                    "name": project.get("name"),
                    "type": "incomplete_focus",
                    "focus_task": project.get("focus_task")
                })
        
        return attention
    
    def add_project(self, project_data):
        """Dodaje nowy projekt."""
        name = project_data.get("name")
        if not any(p.get("name") == name for p in self.projects_cache):
            self.projects_cache.append(project_data)
            self.project_states[name] = self._create_default_state(name, project_data)
            self._save_states()
            return True
        return False
    
    def remove_project(self, name):
        """Usuwa projekt."""
        self.projects_cache = [p for p in self.projects_cache if p.get("name") != name]
        if name in self.project_states:
            del self.project_states[name]
            self._save_states()
            return True
        return False
    
    def get_summary(self):
        """Zwraca podsumowanie wszystkich projektów."""
        projects = self.get_projects()
        
        return {
            "total": len(projects),
            "active": len([p for p in projects if p.get("status") == "active"]),
            "stagnant": len([p for p in projects if p.get("status") == "stagnant"]),
            "abandoned": len([p for p in projects if p.get("status") == "abandoned"]),
            "needs_attention": len(self.get_projects_needing_attention()),
            "projects": [
                {
                    "name": p.get("name"),
                    "type": p.get("type"),
                    "status": p.get("status", "unknown"),
                    "has_focus": bool(p.get("focus_task")),
                    "recommendations_count": len(p.get("recommendations", []))
                }
                for p in projects
            ]
        }
    
    def _create_default_state(self, name, project_data):
        """Tworzy domyślny stan projektu."""
        return {
            "name": name,
            "path": project_data.get("path", ""),
            "type": project_data.get("type", "unknown"),
            "last_analysis": None,
            "last_cycle": None,
            "focus_task": None,
            "focus_completed": True,
            "v9_status": "PENDING",
            "tasks_sent_today": 0,
            "tasks_sent_dates": {},
            "recommendations": [],
            "status": "unknown",
            "last_update": datetime.now().isoformat()
        }
    
    def _load_states(self):
        """Ładuje stany projektów z pliku."""
        if os.path.exists(self.states_file):
            try:
                with open(self.states_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_states(self):
        """Zapisuje stany projektów do pliku."""
        os.makedirs(os.path.dirname(self.states_file), exist_ok=True)
        try:
            with open(self.states_file, 'w') as f:
                json.dump(self.project_states, f, indent=2)
        except Exception as e:
            print(f"[PROJECT_MANAGER] Błąd zapisu: {e}")
    
    def _days_since(self, timestamp):
        """Oblicza dni od timestamp."""
        if not timestamp:
            return None
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            delta = datetime.now() - dt
            return delta.total_seconds() / 86400
        except:
            return None
