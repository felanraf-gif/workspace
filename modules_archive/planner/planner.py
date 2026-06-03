import json
import os
import requests
from datetime import datetime
from core.config import TODOIST_API_TOKEN, TODOIST_PROJECT, INTEGRATE_TODOIST, MEMORY_PATH

class Planner:
    def __init__(self, max_tasks_per_project=5, max_tasks_per_day=5):
        self.max_tasks_per_project = max_tasks_per_project
        self.max_tasks_per_day = max_tasks_per_day
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.todoist_api_url = "https://api.todoist.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {TODOIST_API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.cache_file = os.path.join(self.decisions_path, "task_cache.json")
        self.existing_tasks_cache = self._load_cache()

    def _load_cache(self):
        """Wczytuje cache z pliku JSON, usuwa stare wpisy (TTL 7 dni)."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    tasks = data.get("tasks", [])
                    updated = data.get("updated", "")
                    if updated:
                        cache_age = (datetime.now() - datetime.fromisoformat(updated)).days
                        if cache_age > 7:
                            return set()
                    return set(tasks)
            except:
                pass
        return set()

    def _save_cache(self):
        """Zapisuje cache do pliku JSON z timestamp."""
        os.makedirs(self.decisions_path, exist_ok=True)
        cache_data = {
            "tasks": list(self.existing_tasks_cache),
            "updated": datetime.now().isoformat()
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def _get_todoist_project_id(self):
        """Pobiera ID projektu z Todoist."""
        if not INTEGRATE_TODOIST:
            return None
            
        try:
            response = requests.get(f"{self.todoist_api_url}/projects", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                projects = data.get("results", [])
                for proj in projects:
                    if proj["name"] == TODOIST_PROJECT:
                        return proj["id"]
                
                # Jeśli projekt nie istnieje, utwórz go
                create_response = requests.post(
                    f"{self.todoist_api_url}/projects",
                    headers=self.headers,
                    json={"name": TODOIST_PROJECT}
                )
                if create_response.status_code == 200:
                    return create_response.json()["id"]
        except Exception as e:
            print(f"Błąd połączenia z Todoist: {e}")
        
        return None

    def _create_todoist_task(self, project_id, task_data, due_date=None):
        """Tworzy zadanie w Todoist."""
        if not INTEGRATE_TODOIST or not project_id:
            return None
            
        content = f"[{task_data['project']}] {task_data['task']}"
        priority = 4 if task_data["priority"] == "HIGH" else 3 if task_data["priority"] == "MEDIUM" else 2
        
        # Przygotuj opis zadania
        description = f"Wykryto przez Analyzer:\n"
        description += f"- Typ: {task_data.get('type', 'unknown')}\n"
        description += f"- Priorytet: {task_data['priority']}\n"
        if 'value_score' in task_data:
            description += f"- Wartość: {task_data['value_score']:.2f}\n"
        
        # Przygotuj dane zadania
        task_json = {
            "content": content,
            "project_id": project_id,
            "priority": priority,
            "labels": ["development", "assistant"],
            "description": description
        }
        
        # Dodaj datę jeśli podano
        if due_date:
            task_json["due_date"] = due_date
        
        try:
            response = requests.post(
                f"{self.todoist_api_url}/tasks",
                headers=self.headers,
                json=task_json
            )
            if response.status_code == 200:
                return response.json()["id"]
        except Exception as e:
            print(f"Błąd tworzenia zadania w Todoist: {e}")
        
        return None

    def _check_duplicate_task(self, task_data):
        """Sprawdza, czy task już istnieje w cache."""
        task_key = f"{task_data['project']}:{task_data['task']}"
        return task_key in self.existing_tasks_cache

    def _add_to_cache(self, task_data):
        """Dodaje task do cache i zapisuje na dysk."""
        task_key = f"{task_data['project']}:{task_data['task']}"
        self.existing_tasks_cache.add(task_key)
        self._save_cache()

    def _load_existing_tasks(self):
        """Wczytuje istniejące taski z Todoist do cache."""
        if not INTEGRATE_TODOIST:
            return
            
        try:
            project_id = self._get_todoist_project_id()
            if project_id:
                response = requests.get(
                    f"{self.todoist_api_url}/tasks",
                    headers=self.headers,
                    params={"project_id": project_id}
                )
                if response.status_code == 200:
                    data = response.json()
                    tasks = data.get("results", [])
                    for task in tasks:
                        # Extract project name from task content
                        content = task.get("content", "")
                        if "[" in content and "]" in content:
                            start = content.find("[") + 1
                            end = content.find("]")
                            project_name = content[start:end]
                            task_desc = content[end+1:].strip()
                            task_key = f"{project_name}:{task_desc}"
                            self.existing_tasks_cache.add(task_key)
        except Exception as e:
            print(f"Błąd wczytywania istniejących tasków: {e}")

    def create_plan(self, projects, issues):
        """Generuje plan zadań."""
        tasks = []
        
        # Zadania HIGH (krytyczne braki)
        for issue in issues:
            if issue["priority"] == "HIGH":
                task_desc = ""
                if "src/" in issue["issue"]:
                    task_desc = "Utwórz katalog src/"
                elif "config.json" in issue["issue"]:
                    task_desc = "Utwórz lub napraw plik config.json"
                else:
                    task_desc = f"Rozwiąż problem: {issue['issue']}"
                
                tasks.append({
                    "project": issue["project"],
                    "task": task_desc,
                    "priority": "HIGH",
                    "type": issue.get("type", "fix"),
                    "value_score": 1.0,
                    "trend_score": 0.8
                })
        
        # Zadania MEDIUM (nowe pliki i rozwój)
        for project in projects:
            project_name = project["name"]
            
            # Nowe pliki
            for new_file in project.get("new_files", []):
                tasks.append({
                    "project": project_name,
                    "task": f"Przejrzeć nowy plik: {new_file}",
                    "priority": "MEDIUM",
                    "type": "new_file",
                    "value_score": 0.6,
                    "trend_score": 0.6
                })
            
            # Rozwój (jeśli brak HIGH)
            high_tasks = [t for t in tasks if t["project"] == project_name and t["priority"] == "HIGH"]
            if len(high_tasks) == 0:
                tasks.append({
                    "project": project_name,
                    "task": "Przeglądaj i aktualizuj kod",
                    "priority": "MEDIUM",
                    "type": "development",
                    "value_score": 0.6,
                    "trend_score": 0.6
                })
        
        # Ogranicz liczbę zadań na projekt
        limited_tasks = []
        project_counts = {}
        
        for task in tasks:
            proj = task["project"]
            if proj not in project_counts:
                project_counts[proj] = 0
            
            if project_counts[proj] < self.max_tasks_per_project:
                limited_tasks.append(task)
                project_counts[proj] += 1
        
        return limited_tasks

    def send_to_todoist(self, tasks, due_date=None):
        """Wysyła zadania do Todoist."""
        if not INTEGRATE_TODOIST:
            return []
            
        project_id = self._get_todoist_project_id()
        if not project_id:
            return []
        
        sent_tasks = []
        for task in tasks:
            task_id = self._create_todoist_task(project_id, task, due_date)
            if task_id:
                self._add_to_cache(task)
                sent_tasks.append({
                    "todoist_id": task_id,
                    "task_data": task
                })
        
        return sent_tasks

    def create_tomorrow_plan(self, projects, issues, trends):
        """Generuje plan na jutro na podstawie trendów i problemów."""
        # Wczytaj istniejące taski
        self._load_existing_tasks()
        
        tasks = self.create_plan(projects, issues)
        
        # Dodaj rekomendacje z trendów
        if trends:
            for project, data in trends.items():
                if data.get("current_trend", 0) < -0.1:
                    tasks.append({
                        "project": project,
                        "task": f"Analiza spadku wartości (trend: {data['current_trend']:.2f})",
                        "priority": "MEDIUM",
                        "type": "trend_review",
                        "value_score": 0.5,
                        "trend_score": 0.3
                    })
        
        # Sortuj według priorytetu, value_score i trend_score
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        tasks.sort(key=lambda t: (
            priority_order[t["priority"]],
            -t.get("value_score", 0),
            -t.get("trend_score", 0)
        ))
        
        # Usuń duplikaty i ogranicz do limitu dziennego
        unique_tasks = []
        seen_tasks = set()
        
        for task in tasks:
            task_key = f"{task['project']}:{task['task']}"
            
            # Sprawdź czy task już istnieje w Todoist lub został dodany
            if task_key in seen_tasks or self._check_duplicate_task(task):
                continue
                
            seen_tasks.add(task_key)
            unique_tasks.append(task)
            
            # Ogranicz do limitu dziennego
            if len(unique_tasks) >= self.max_tasks_per_day:
                break
        
        return unique_tasks

    def save_plan(self, tasks, todoist_sent=None):
        """Zapisuje plan do pliku."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        plan_file = os.path.join(self.decisions_path, f"plan_{timestamp}.json")
        
        plan_data = {
            "timestamp": timestamp,
            "tasks_count": len(tasks),
            "tasks": tasks,
            "todoist_sent": todoist_sent or []
        }
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(plan_file, 'w') as f:
            json.dump(plan_data, f, indent=2)
        
        return plan_file

    def generate_new_tasks_if_needed(self, projects, issues, current_active, max_daily=5):
        """Generuje nowe zadania jeśli poprzednie zostały wykonane."""
        remaining = max_daily - current_active
        
        if remaining <= 0:
            return []
        
        all_tasks = self.create_plan(projects, issues)
        
        new_tasks = []
        seen_tasks = set()
        
        for task in all_tasks:
            task_key = f"{task['project']}:{task['task']}"
            
            if task_key in seen_tasks or self._check_duplicate_task(task):
                continue
            
            seen_tasks.add(task_key)
            new_tasks.append(task)
            
            if len(new_tasks) >= remaining:
                break
        
        return new_tasks

    def create_urgent_task(self, content):
        """Tworzy URGENT task w Todoist (tylko przy CRITICAL status).
        
        Args:
            content: Treść taska, np. "[URGENT] Zamknij obecne zadanie"
        
        Returns:
            ID utworzonego taska lub None
        """
        if not INTEGRATE_TODOIST:
            return None
        
        project_id = self._get_todoist_project_id()
        if not project_id:
            return None
        
        urgent_task = {
            "content": content,
            "priority": 4,  # P1 - najwyższy priorytet
            "labels": ["urgent", "assistant", "completion-pressure"]
        }
        
        try:
            response = requests.post(
                f"{self.todoist_api_url}/tasks",
                headers=self.headers,
                json={
                    "content": urgent_task["content"],
                    "project_id": project_id,
                    "priority": urgent_task["priority"],
                    "labels": urgent_task["labels"],
                    "description": "⚠️ Task utworzony automatycznie przez CompletionGuard V6.2 - zbyt długo bez postępu!"
                }
            )
            
            if response.status_code == 200:
                task_id = response.json()["id"]
                print(f"UTWORZONO URGENT TASK: {content} (ID: {task_id})")
                return task_id
        except Exception as e:
            print(f"Błąd tworzenia URGENT taska: {e}")
        
        return None

if __name__ == "__main__":
    # Testowanie
    planner = Planner()
    mock_projects = [{"name": "test_project", "new_files": ["src/main.py"]}]
    mock_issues = [{"project": "test_project", "issue": "Brak src/", "priority": "HIGH", "type": "structure"}]
    
    tasks = planner.create_plan(mock_projects, mock_issues)
    todoist_sent = planner.send_to_todoist(tasks)
    plan_file = planner.save_plan(tasks, todoist_sent)
    
    print(f"Plan zapisany w: {plan_file}")
    print(f"Liczba zadań: {len(tasks)}")
    print(f"Wysłano do Todoist: {len(todoist_sent)} zadań")