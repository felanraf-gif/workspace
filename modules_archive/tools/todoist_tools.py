import requests
from datetime import datetime, timedelta
from core.config import TODOIST_API_TOKEN, TODOIST_PROJECT, INTEGRATE_TODOIST

class TodoistTools:
    """Narzędzia do integracji z Todoist API."""
    
    REST_API_URL = "https://api.todoist.com/rest/v2"
    SYNC_API_URL = "https://api.todoist.com/sync/v9"
    
    def __init__(self):
        self.api_token = TODOIST_API_TOKEN
        self.project_name = TODOIST_PROJECT
        self.enabled = INTEGRATE_TODOIST
        
        self.rest_headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        self.sync_headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        self._project_id = None
        self._active_tasks_cache = []
        self._cache_timestamp = None
    
    @property
    def project_id(self):
        """Lazy loading project ID."""
        if self._project_id is None:
            self._project_id = self._get_or_create_project()
        return self._project_id
    
    def _get_or_create_project(self):
        """Pobiera lub tworzy projekt Todoist."""
        if not self.enabled:
            return None
        
        try:
            response = requests.get(
                f"{self.REST_API_URL}/projects",
                headers=self.rest_headers
            )
            
            if response.status_code == 200:
                projects = response.json()
                for proj in projects:
                    if proj["name"] == self.project_name:
                        return proj["id"]
                
                create_resp = requests.post(
                    f"{self.REST_API_URL}/projects",
                    headers=self.rest_headers,
                    json={"name": self.project_name}
                )
                
                if create_resp.status_code == 200:
                    return create_resp.json()["id"]
        except Exception as e:
            print(f"Błąd pobierania projektu: {e}")
        
        return None
    
    def create_task(self, title, project=None, priority=3, description="", due_date=None, labels=None):
        """Tworzy nowe zadanie w Todoist."""
        if not self.enabled:
            return None
        
        project_id = self._project_id
        if project and project != self.project_name:
            project_id = self._get_or_create_project()
        
        content = title
        if project and project != "unknown":
            content = f"[{project}] {title}"
        
        task_data = {
            "content": content,
            "priority": priority,
            "description": description
        }
        
        if project_id:
            task_data["project_id"] = project_id
        
        if due_date:
            task_data["due_date"] = due_date
        
        if labels:
            task_data["labels"] = labels
        
        try:
            response = requests.post(
                f"{self.REST_API_URL}/tasks",
                headers=self.rest_headers,
                json=task_data
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Błąd tworzenia taska: {e}")
        
        return None
    
    def get_active_tasks(self, force_refresh=False):
        """Pobiera aktywne zadania."""
        if not self.enabled:
            return []
        
        now = datetime.now()
        if not force_refresh and self._cache_timestamp:
            if (now - self._cache_timestamp).seconds < 60:
                return self._active_tasks_cache
        
        try:
            params = {"project_id": self.project_id} if self.project_id else {}
            response = requests.get(
                f"{self.REST_API_URL}/tasks",
                headers=self.rest_headers,
                params=params
            )
            
            if response.status_code == 200:
                tasks = response.json()
                self._active_tasks_cache = tasks
                self._cache_timestamp = now
                return tasks
        except Exception as e:
            print(f"Błąd pobierania tasków: {e}")
        
        return self._active_tasks_cache
    
    def get_completed_tasks(self, since_days=7):
        """Pobiera ukończone zadania (wymaga Sync API)."""
        if not self.enabled:
            return []
        
        since = (datetime.now() - timedelta(days=since_days)).isoformat()
        
        try:
            response = requests.post(
                f"{self.SYNC_API_URL}/completed/get_all",
                headers=self.sync_headers,
                data=f"since={since}&limit=100"
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                completed = []
                for item in items:
                    content = item.get("content", "")
                    project_name = "unknown"
                    task_desc = content
                    
                    if "[" in content and "]" in content:
                        start = content.find("[") + 1
                        end = content.find("]")
                        project_name = content[start:end]
                        task_desc = content[end+1:].strip()
                    
                    completed.append({
                        "id": item.get("id"),
                        "project": project_name,
                        "task": task_desc,
                        "completed_date": item.get("completed_date"),
                        "content": content
                    })
                
                return completed
        except Exception as e:
            print(f"Błąd pobierania ukończonych tasków: {e}")
        
        return []
    
    def task_exists(self, title, project=None):
        """Sprawdza czy task istnieje."""
        if not self.enabled:
            return False
        
        tasks = self.get_active_tasks()
        
        search_content = title
        if project and project != "unknown":
            search_content = f"[{project}] {title}"
        
        for task in tasks:
            if task.get("content") == search_content:
                return True
        
        return False
    
    def get_task_by_content(self, content):
        """Pobiera task po treści."""
        if not self.enabled:
            return None
        
        tasks = self.get_active_tasks()
        
        for task in tasks:
            if task.get("content") == content:
                return task
        
        return None
    
    def close_task(self, task_id):
        """Zamyka (ukończa) task."""
        if not self.enabled:
            return False
        
        try:
            response = requests.post(
                f"{self.REST_API_URL}/tasks/{task_id}/close",
                headers=self.rest_headers
            )
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Błąd zamykania taska: {e}")
        
        return False
    
    def delete_task(self, task_id):
        """Usuwa task."""
        if not self.enabled:
            return False
        
        try:
            response = requests.delete(
                f"{self.REST_API_URL}/tasks/{task_id}",
                headers=self.rest_headers
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Błąd usuwania taska: {e}")
        
        return False
    
    def get_tasks_by_project(self, project_name):
        """Pobiera taski dla danego projektu."""
        if not self.enabled:
            return []
        
        tasks = self.get_active_tasks()
        
        project_tasks = []
        for task in tasks:
            content = task.get("content", "")
            
            if "[" in content and "]" in content:
                start = content.find("[") + 1
                end = content.find("]")
                task_project = content[start:end]
                
                if task_project == project_name:
                    project_tasks.append(task)
            elif project_name == "unknown":
                project_tasks.append(task)
        
        return project_tasks
    
    def get_stats(self):
        """Zwraca statystyki Todoist."""
        if not self.enabled:
            return {"enabled": False}
        
        tasks = self.get_active_tasks()
        completed = self.get_completed_tasks(since_days=7)
        
        by_priority = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}
        by_project = {}
        
        for task in tasks:
            priority = task.get("priority", 3)
            p_key = f"p{priority}"
            if p_key in by_priority:
                by_priority[p_key] += 1
            
            content = task.get("content", "")
            project = "unknown"
            if "[" in content and "]" in content:
                start = content.find("[") + 1
                end = content.find("]")
                project = content[start:end]
            
            if project not in by_project:
                by_project[project] = 0
            by_project[project] += 1
        
        return {
            "enabled": True,
            "active_tasks": len(tasks),
            "completed_this_week": len(completed),
            "by_priority": by_priority,
            "by_project": by_project
        }

if __name__ == "__main__":
    tt = TodoistTools()
    
    print("=== TodoistTools Test ===")
    print(f"Stats: {tt.get_stats()}")
    
    active = tt.get_active_tasks()
    print(f"Active tasks: {len(active)}")
    
    completed = tt.get_completed_tasks()
    print(f"Completed this week: {len(completed)}")
