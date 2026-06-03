"""
integrations/todoist.py - Integracja z Todoist
"""

import requests
from datetime import datetime, timedelta
from core.config import TODOIST_API_TOKEN, TODOIST_PROJECT, INTEGRATE_TODOIST


class Todoist:
    """Komunikuje się z Todoist API."""
    
    def __init__(self):
        self.api_url = "https://api.todoist.com/api/v1"
        self.sync_url = "https://api.todoist.com/sync/v9"
        self.headers = {"Authorization": f"Bearer {TODOIST_API_TOKEN}", "Content-Type": "application/json"}
        self.sync_headers = {"Authorization": f"Bearer {TODOIST_API_TOKEN}", "Content-Type": "application/x-www-form-urlencoded"}
        self.timeout = 30

    def _safe_request(self, method, url, **kwargs):
        """Bezpieczne wykonanie requesta z obsługą błędów."""
        try:
            kwargs.setdefault('timeout', self.timeout)
            kwargs.setdefault('headers', self.headers)
            response = requests.request(method, url, **kwargs)
            return response
        except requests.exceptions.Timeout:
            print(f"[TODOIST] Timeout połączenia z {url}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"[TODOIST] Błąd połączenia: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[TODOIST] Błąd requestu: {e}")
            return None
        except Exception as e:
            print(f"[TODOIST] Nieoczekiwany błąd: {e}")
            return None

    def get_active_tasks(self, project_id=None):
        """Pobiera aktywne taski."""
        if not INTEGRATE_TODOIST:
            return []
        
        resp = self._safe_request("GET", f"{self.api_url}/tasks", params={"project_id": project_id} if project_id else None)
        if resp and resp.status_code == 200:
            return resp.json().get("results", [])
        return []

    def get_completed_tasks(self, since_days=7):
        """Pobiera ukończone taski."""
        if not INTEGRATE_TODOIST:
            return []
        
        since = (datetime.now() - timedelta(days=since_days)).isoformat()
        resp = self._safe_request(
            "POST",
            f"{self.sync_url}/completed/get_all",
            headers=self.sync_headers,
            data=f"since={since}&limit=100"
        )
        if resp and resp.status_code == 200:
            return resp.json().get("items", [])
        return []

    def create_task(self, content, project_id=None, priority=3, labels=None, due_date=None):
        """Tworzy nowy task."""
        if not INTEGRATE_TODOIST:
            return None
        
        if not project_id:
            project_id = self._get_project_id()
        
        task_data = {
            "content": content,
            "project_id": project_id,
            "priority": priority
        }
        if labels:
            task_data["labels"] = labels
        if due_date:
            task_data["due_date"] = due_date
        
        resp = self._safe_request("POST", f"{self.api_url}/tasks", json=task_data)
        if resp and resp.status_code == 200:
            return resp.json().get("id")
        return None

    def close_task(self, task_id):
        """Zamyka task."""
        if not INTEGRATE_TODOIST:
            return False
        
        resp = self._safe_request("POST", f"{self.api_url}/tasks/{task_id}/close")
        return resp is not None and resp.status_code in [200, 204]

    def update_task(self, task_id, updates):
        """Aktualizuje task."""
        if not INTEGRATE_TODOIST:
            return False
        
        resp = self._safe_request("POST", f"{self.api_url}/tasks/{task_id}", json=updates)
        return resp is not None and resp.status_code == 200

    def add_label(self, task_id, label):
        """Dodaje etykietę do taska."""
        task = self._get_task(task_id)
        if not task:
            return False
        
        existing = task.get("labels", [])
        if label not in existing:
            existing.append(label)
            return self.update_task(task_id, {"labels": existing})
        return True

    def get_project_id(self, project_name=None):
        """Pobiera ID projektu."""
        return self._get_project_id(project_name)

    def sync_with_state(self, tasks):
        """Synchronizuje taski ze stanem."""
        active = self.get_active_tasks()
        active_contents = {t.get("content") for t in active}
        
        created = []
        for task in tasks:
            content = f"[{task.get('project', '')}] {task.get('task', '')}"
            if content not in active_contents:
                priority = 4 if task.get("priority") == "HIGH" else 3 if task.get("priority") == "MEDIUM" else 2
                task_id = self.create_task(content, priority=priority)
                if task_id:
                    created.append({"id": task_id, "content": content})
        
        return created

    def get_stats(self):
        """Zwraca statystyki."""
        active = self.get_active_tasks()
        completed = self.get_completed_tasks(since_days=1)
        
        return {
            "active_count": len(active),
            "completed_today": len(completed)
        }

    def _get_project_id(self, project_name=None):
        """Pobiera ID projektu Todoist."""
        if not INTEGRATE_TODOIST:
            return None
        
        name = project_name or TODOIST_PROJECT
        
        resp = self._safe_request("GET", f"{self.api_url}/projects")
        if resp and resp.status_code == 200:
            for proj in resp.json().get("results", []):
                if proj["name"] == name:
                    return proj["id"]
            
            create_resp = self._safe_request("POST", f"{self.api_url}/projects", json={"name": name})
            if create_resp and create_resp.status_code == 200:
                return create_resp.json().get("id")
        return None

    def _get_task(self, task_id):
        """Pobiera pojedynczy task."""
        if not INTEGRATE_TODOIST:
            return None
        
        resp = self._safe_request("GET", f"{self.api_url}/tasks/{task_id}")
        if resp and resp.status_code == 200:
            return resp.json()
        return None
