"""
brain/project_tracker.py - Śledzenie postępów projektów
Śledzi zmiany, commity i aktywność projektów
"""

import os
import json
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path


class ProjectTracker:
    """Śledzi postępy i aktywność projektów."""
    
    def __init__(self, projects=None):
        self.projects = projects or []
        self.history_file = "memory/project_history.json"
        self.state_file = "memory/project_state.json"
        self.history = self._load_history()
        self.state = self._load_state()
    
    def track_projects(self, discovered_projects):
        """Śledzi listę projektów i wykrywa zmiany."""
        self.projects = discovered_projects
        results = []
        
        for project in discovered_projects:
            progress = self._track_single_project(project)
            results.append(progress)
        
        self._save_history(results)
        self._save_state()
        
        return results
    
    def _track_single_project(self, project):
        """Śledzi pojedynczy projekt."""
        project_path = project.get("path")
        project_name = project.get("name")
        
        progress = {
            "name": project_name,
            "path": project_path,
            "type": project.get("type"),
            "timestamp": datetime.now().isoformat(),
            "git_metrics": {},
            "code_metrics": {},
            "activity_metrics": {},
            "status": "unknown"
        }
        
        if project.get("has_git"):
            progress["git_metrics"] = self._get_git_metrics(project_path)
        
        progress["code_metrics"] = self._get_code_metrics(project_path)
        progress["activity_metrics"] = self._get_activity_metrics(project_name, project_path)
        progress["status"] = self._calculate_status(progress)
        
        return progress
    
    def _get_git_metrics(self, project_path):
        """Pobiera metryki Git."""
        metrics = {
            "commits_last_7d": 0,
            "commits_last_30d": 0,
            "last_commit_date": None,
            "branches": [],
            "has_uncommitted": False
        }
        
        try:
            os.chdir(project_path)
            
            log_7d = subprocess.run(
                ["git", "log", "--oneline", f"--since={datetime.now() - timedelta(days=7)}"],
                capture_output=True, text=True, timeout=3
            )
            if log_7d.returncode == 0:
                metrics["commits_last_7d"] = len(log_7d.stdout.strip().split('\n')) if log_7d.stdout.strip() else 0
            
            log_30d = subprocess.run(
                ["git", "log", "--oneline", f"--since={datetime.now() - timedelta(days=30)}"],
                capture_output=True, text=True, timeout=3
            )
            if log_30d.returncode == 0:
                metrics["commits_last_30d"] = len(log_30d.stdout.strip().split('\n')) if log_30d.stdout.strip() else 0
            
            last_commit = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                capture_output=True, text=True, timeout=3
            )
            if last_commit.returncode == 0 and last_commit.stdout.strip():
                metrics["last_commit_date"] = last_commit.stdout.strip()[:10]
            
            branches = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True, text=True, timeout=3
            )
            if branches.returncode == 0:
                metrics["branches"] = [b.strip().replace("* ", "") for b in branches.stdout.strip().split('\n') if b.strip()]
            
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=3
            )
            metrics["has_uncommitted"] = bool(status.stdout.strip())
            
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    def _get_code_metrics(self, project_path):
        """Pobiera metryki kodu."""
        metrics = {
            "files_count": 0,
            "total_lines": 0,
            "file_types": {},
            "largest_file": None
        }
        
        skip_dirs = {'__pycache__', '.git', 'venv', 'node_modules', '.venv'}
        largest_size = 0
        largest_file = None
        
        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
                
                for f in files:
                    if f.startswith('.'):
                        continue
                    
                    metrics["files_count"] += 1
                    
                    ext = os.path.splitext(f)[1] or "no_ext"
                    metrics["file_types"][ext] = metrics["file_types"].get(ext, 0) + 1
                    
                    file_path = os.path.join(root, f)
                    try:
                        size = os.path.getsize(file_path)
                        if size > largest_size:
                            largest_size = size
                            largest_file = f
                    except:
                        pass
                    
                    if f.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.md', '.txt')):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                                lines = len(fp.readlines())
                                metrics["total_lines"] += lines
                        except:
                            pass
            
            if largest_file:
                metrics["largest_file"] = {"name": largest_file, "size": largest_size}
        
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    def _get_activity_metrics(self, project_name, project_path):
        """Pobiera metryki aktywności."""
        metrics = {
            "days_since_edit": None,
            "edit_frequency_7d": 0,
            "focus_time_minutes": 0,
            "tasks_completed": 0,
            "tasks_total": 0
        }
        
        try:
            mtime = os.path.getmtime(project_path)
            last_edit = datetime.fromtimestamp(mtime)
            metrics["days_since_edit"] = (datetime.now() - last_edit).days
        except:
            pass
        
        history_key = f"{project_name}_{datetime.now().strftime('%Y-%m-%d')}"
        today_history = self.history.get(history_key, {})
        
        metrics["focus_time_minutes"] = today_history.get("focus_time", 0)
        metrics["tasks_completed"] = today_history.get("tasks_completed", 0)
        metrics["tasks_total"] = today_history.get("tasks_total", 0)
        
        edits_7d = 0
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            key = f"{project_name}_{day}"
            if key in self.history:
                edits_7d += self.history[key].get("edits", 0)
        metrics["edit_frequency_7d"] = edits_7d
        
        return metrics
    
    def _calculate_status(self, progress):
        """Oblicza status projektu."""
        days_since = progress.get("activity_metrics", {}).get("days_since_edit")
        commits_7d = progress.get("git_metrics", {}).get("commits_last_7d", 0)
        has_uncommitted = progress.get("git_metrics", {}).get("has_uncommitted", False)
        
        if days_since is not None and days_since > 30:
            return "abandoned"
        elif days_since is not None and days_since > 14:
            return "stagnant"
        elif days_since is not None and days_since > 7:
            return "idle"
        elif commits_7d > 0:
            return "active"
        elif has_uncommitted:
            return "in_progress"
        else:
            return "stable"
    
    def get_progress_report(self):
        """Generuje raport postępów dla wszystkich projektów."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "projects": [],
            "summary": {
                "total": len(self.projects),
                "active": 0,
                "stagnant": 0,
                "abandoned": 0,
                "needs_attention": []
            }
        }
        
        for project in self.projects:
            progress = self._track_single_project(project)
            report["projects"].append(progress)
            
            status = progress.get("status")
            if status == "active":
                report["summary"]["active"] += 1
            elif status in ["stagnant", "abandoned"]:
                report["summary"]["stagnant"] += 1
                if status == "abandoned":
                    report["summary"]["abandoned"] += 1
            
            if status in ["stagnant", "abandoned", "idle"]:
                report["summary"]["needs_attention"].append({
                    "name": project.get("name"),
                    "status": status,
                    "days_since_edit": progress.get("activity_metrics", {}).get("days_since_edit")
                })
        
        return report
    
    def get_project_focus(self):
        """Zwraca projekt który powinien mieć fokus."""
        priorities = []
        
        for project in self.projects:
            name = project.get("name")
            progress = self._track_single_project(project)
            
            score = 0
            if progress.get("git_metrics", {}).get("has_uncommitted"):
                score += 10
            if progress.get("git_metrics", {}).get("commits_last_7d", 0) > 0:
                score += 5
            days = progress.get("activity_metrics", {}).get("days_since_edit", 999)
            if days < 3:
                score += 8
            elif days < 7:
                score += 4
            
            priorities.append({
                "name": name,
                "path": project.get("path"),
                "score": score,
                "status": progress.get("status"),
                "days_since_edit": days
            })
        
        priorities.sort(key=lambda x: -x["score"])
        return priorities[:3] if priorities else []
    
    def _load_history(self):
        """Ładuje historię aktywności."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_history(self, results):
        """Zapisuje historię aktywności."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for result in results:
            key = f"{result['name']}_{today}"
            if key not in self.history:
                self.history[key] = {"edits": 0, "focus_time": 0, "tasks_completed": 0}
            self.history[key]["last_status"] = result.get("status")
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[TRACKER] Błąd zapisu historii: {e}")
    
    def _load_state(self):
        """Ładuje stan projektów."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"projects": {}, "last_scan": None}
    
    def _save_state(self):
        """Zapisuje stan projektów."""
        state = {
            "last_scan": datetime.now().isoformat(),
            "projects": {}
        }
        
        for project in self.projects:
            name = project.get("name")
            state["projects"][name] = {
                "path": project.get("path"),
                "type": project.get("type"),
                "last_modified": project.get("last_modified")
            }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[TRACKER] Błąd zapisu stanu: {e}")
    
    def record_task_completion(self, project_name):
        """Rejestruje ukończenie taska dla projektu."""
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{project_name}_{today}"
        
        if key not in self.history:
            self.history[key] = {"edits": 0, "focus_time": 0, "tasks_completed": 0}
        
        self.history[key]["tasks_completed"] = self.history[key].get("tasks_completed", 0) + 1
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except:
            pass
