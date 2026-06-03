import json
import os
import requests
from datetime import datetime, timedelta
from core.config import TODOIST_API_TOKEN, INTEGRATE_TODOIST, MEMORY_PATH, STAGNATION_DAYS

class WorkDetector:
    REAL_WORK = "REAL_WORK"
    LOW_PROGRESS = "LOW_PROGRESS"
    STAGNATION = "STAGNATION"
    
    def __init__(self):
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.work_history_file = os.path.join(self.decisions_path, "work_history.json")
        self.stagnation_log_file = os.path.join(self.decisions_path, "stagnation_log.json")
        self.sync_api_url = "https://api.todoist.com/sync/v9"
        self.headers = {
            "Authorization": f"Bearer {TODOIST_API_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def analyze_file_changes(self, projects):
        """Analizuje zmiany w plikach projektów."""
        result = {}
        
        for project in projects:
            name = project["name"]
            new_files = project.get("new_files", [])
            changed_files = project.get("changed_files", [])
            
            total_growth = 0
            for file_info in project.get("files", []):
                if file_info.get("type") == "file":
                    try:
                        size = os.path.getsize(file_info["full_path"])
                        total_growth += size
                    except:
                        pass
            
            result[name] = {
                "new_files_count": len(new_files),
                "changed_files_count": len(changed_files),
                "total_size": total_growth,
                "only_small_edits": len(changed_files) > 0 and len(new_files) == 0 and total_growth < 5000
            }
        
        return result
    
    def get_todoist_completed(self, since_days=7):
        """Pobiera ukończone taski z Todoist Sync API."""
        if not INTEGRATE_TODOIST:
            return []
        
        try:
            since = (datetime.now() - timedelta(days=since_days)).isoformat()
            response = requests.post(
                f"{self.sync_api_url}/completed/get_all",
                headers=self.headers,
                data=f"since={since}&limit=100"
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                completed = []
                for item in items:
                    content = item.get("content", "")
                    if "[" in content and "]" in content:
                        start = content.find("[") + 1
                        end = content.find("]")
                        project_name = content[start:end]
                        task_desc = content[end+1:].strip()
                    else:
                        project_name = "unknown"
                        task_desc = content
                    
                    completed.append({
                        "project": project_name,
                        "task": task_desc,
                        "completed_date": item.get("completed_date"),
                        "item_id": item.get("id")
                    })
                
                return completed
        except Exception as e:
            print(f"Błąd pobierania ukończonych tasków: {e}")
        
        return []
    
    def calculate_work_score(self, file_analysis, completed_tasks, project_name):
        """Oblicza wynik pracy dla projektu."""
        score = 0
        details = []
        
        file_data = file_analysis.get(project_name, {})
        
        if file_data.get("new_files_count", 0) > 0:
            count = file_data["new_files_count"]
            score += 3
            details.append(f"+3 nowe pliki ({count})")
        
        if file_data.get("total_size", 0) > 500:
            score += 2
            details.append(f"+2 większe zmiany ({file_data['total_size']}B)")
        
        project_tasks = [t for t in completed_tasks if t["project"] == project_name]
        if len(project_tasks) > 0:
            score += 3 * min(len(project_tasks), 2)
            details.append(f"+{3 * min(len(project_tasks), 2)} ukończone taski ({len(project_tasks)})")
        
        if file_data.get("only_small_edits", False):
            score -= 1
            details.append("-1 tylko drobne zmiany")
        
        return max(0, score), details
    
    def get_stagnation_days(self, project_name):
        """Sprawdza ile dni bez postępu."""
        history = self._load_work_history()
        
        last_real_work = None
        for entry in reversed(history):
            if entry.get("project") == project_name and entry.get("score", 0) >= 3:
                last_real_work = datetime.fromisoformat(entry["timestamp"])
                break
        
        if not last_real_work:
            return STAGNATION_DAYS + 1
        
        days = (datetime.now() - last_real_work).days
        return days
    
    def get_work_status(self, score):
        """Określa status pracy na podstawie wyniku."""
        if score >= 5:
            return self.REAL_WORK
        elif score >= 1:
            return self.LOW_PROGRESS
        else:
            return self.STAGNATION
    
    def evaluate_work(self, projects, trends_data=None):
        """Główna funkcja - ocenia pracę we wszystkich projektach."""
        completed_tasks = self.get_todoist_completed()
        file_analysis = self.analyze_file_changes(projects)
        
        results = {}
        overall_score = 0
        
        for project in projects:
            name = project["name"]
            score, details = self.calculate_work_score(file_analysis, completed_tasks, name)
            
            stagnation_days = self.get_stagnation_days(name)
            if stagnation_days >= STAGNATION_DAYS:
                score -= 3
                details.append(f"-3 stagnacja ({stagnation_days} dni)")
            
            status = self.get_work_status(score)
            overall_score += score
            
            results[name] = {
                "score": max(0, score),
                "status": status,
                "details": details,
                "stagnation_days": stagnation_days,
                "new_files": file_analysis.get(name, {}).get("new_files_count", 0),
                "completed_tasks": len([t for t in completed_tasks if t["project"] == name])
            }
            
            self._save_work_entry(name, max(0, score), status, details)
        
        return {
            "projects": results,
            "overall_score": overall_score,
            "overall_status": self.get_work_status(overall_score),
            "completed_tasks": completed_tasks
        }
    
    def should_create_breakthrough_task(self, project_name, status, stagnation_days):
        """Sprawdza czy należy utworzyć task przełamania stagnacji."""
        if status != self.STAGNATION:
            return False
        
        log = self._load_stagnation_log()
        
        last_task_date = log.get(project_name, {}).get("last_task_date")
        if last_task_date:
            days_since = (datetime.now() - datetime.fromisoformat(last_task_date)).days
            if days_since < 3:
                return False
        
        return True
    
    def create_breakthrough_task(self, project_name, planner):
        """Tworzy task przełamania stagnacji."""
        task = {
            "project": project_name,
            "task": "Przełamać stagnację - zrób coś widocznego",
            "priority": "HIGH",
            "type": "breakthrough"
        }
        
        planner._add_to_cache(task)
        
        log = self._load_stagnation_log()
        log[project_name] = {
            "last_task_date": datetime.now().isoformat(),
            "stagnation_days": self.get_stagnation_days(project_name)
        }
        self._save_stagnation_log(log)
        
        return task
    
    def _load_work_history(self):
        """Wczytuje historię pracy."""
        if os.path.exists(self.work_history_file):
            try:
                with open(self.work_history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_work_entry(self, project, score, status, details):
        """Zapisuje wpis do historii pracy."""
        history = self._load_work_history()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "score": score,
            "status": status,
            "details": details
        }
        
        history.append(entry)
        
        if len(history) > 500:
            history = history[-500:]
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(self.work_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_stagnation_log(self):
        """Wczytuje log stagnacji."""
        if os.path.exists(self.stagnation_log_file):
            try:
                with open(self.stagnation_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_stagnation_log(self, log):
        """Zapisuje log stagnacji."""
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(self.stagnation_log_file, 'w') as f:
            json.dump(log, f, indent=2)

if __name__ == "__main__":
    detector = WorkDetector()
    
    print("=== WorkDetector Test ===")
    
    from modules.analyzer.analyzer import Analyzer
    analyzer = Analyzer()
    projects, _ = analyzer.scan_projects()
    
    result = detector.evaluate_work(projects)
    
    print(f"\nOverall Status: {result['overall_status']}")
    print(f"Overall Score: {result['overall_score']}")
    
    for name, data in result["projects"].items():
        icon = {"REAL_WORK": "✅", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(data["status"], "?")
        print(f"\n{icon} {name}:")
        print(f"   Score: {data['score']}")
        print(f"   Status: {data['status']}")
        print(f"   Details: {', '.join(data['details']) if data['details'] else 'brak'}")
        print(f"   Stagnation: {data['stagnation_days']} dni")
