"""
brain/planner.py - Planowanie zadań i zarządzanie fokusem
Używa integrations/todoist.py zamiast własnej implementacji
"""

import json
import os
from datetime import datetime
from core.config import INTEGRATE_TODOIST, MEMORY_PATH
from core.constants import PRIORITY_ICONS, PRIORITY_ORDER, MAX_TASKS_PER_DAY, FOCUS_LABEL, TODOIST_LABELS
from integrations.todoist import Todoist


class Planner:
    """Planuje zadania i zarządza fokusem."""
    
    def __init__(self, max_tasks_per_project=5, max_tasks_per_day=5):
        self.max_tasks_per_project = max_tasks_per_project
        self.max_tasks_per_day = max_tasks_per_day
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.todoist = Todoist()
        self.focus_log_file = os.path.join(self.decisions_path, "focus_history.json")
        self.sent_tasks_file = os.path.join(self.decisions_path, "sent_tasks.json")
        os.makedirs(self.decisions_path, exist_ok=True)

    def create_tomorrow_plan(self, projects, issues):
        """Generuje plan zadań na podstawie problemów z analizatora."""
        tasks = []
        
        for issue in issues:
            if issue.get("priority") in ["HIGH", "MEDIUM"]:
                task_desc = self._issue_to_task(issue)
                reason = issue.get("reason", "")
                
                value_score = 1.0 if issue.get("priority") == "HIGH" else 0.6
                
                task = {
                    "project": issue["project"],
                    "task": task_desc,
                    "priority": issue.get("priority", "MEDIUM"),
                    "type": issue.get("type", "fix"),
                    "value_score": value_score,
                    "reason": reason,
                    "source": "intelligence"
                }
                
                if issue.get("type") == "technical_debt" and issue.get("todos"):
                    task["details"] = issue.get("todos")[:2]
                
                tasks.append(task)
        
        for project in projects:
            if project.get("new_files") or project.get("changed_files"):
                has_project_task = any(t["project"] == project["name"] for t in tasks)
                if not has_project_task:
                    tasks.append({
                        "project": project["name"],
                        "task": f"Rozwijaj {project['name']}",
                        "priority": "MEDIUM",
                        "type": "development",
                        "value_score": 0.5,
                        "reason": "Projekt ma nowe/zmienione pliki - kontynuuj pracę"
                    })
        
        limited_tasks = []
        project_counts = {}
        for task in tasks:
            proj = task["project"]
            project_counts[proj] = project_counts.get(proj, 0) + 1
            if project_counts[proj] <= self.max_tasks_per_project:
                limited_tasks.append(task)
        
        return limited_tasks[:self.max_tasks_per_day]
    
    def create_tomorrow_plan_from_intelligence(self, intel: dict) -> list:
        """Tworzy plan zadań na podstawie Project Intelligence."""
        if not intel:
            return []
        
        tasks = []
        issues = intel.get("issues", [])
        architecture = intel.get("architecture", {})
        project_name = intel.get("project", "towarzysz")
        
        for issue in issues:
            if issue.get("priority") in ["HIGH", "MEDIUM"]:
                task_desc = self._issue_to_task(issue)
                reason = issue.get("reason", "") or f"Znaleziono w: {issue.get('type', 'unknown')}"
                
                tasks.append({
                    "project": project_name,
                    "task": task_desc,
                    "priority": issue.get("priority", "MEDIUM"),
                    "type": issue.get("type", "fix"),
                    "value_score": 1.0 if issue.get("priority") == "HIGH" else 0.6,
                    "reason": reason,
                    "source": "intelligence",
                    "issue_details": issue
                })
        
        missing = architecture.get("missing", [])
        for item in missing[:2]:
            task_name = item.split(" - ")[0] if " - " in item else item
            tasks.append({
                "project": project_name,
                "task": f"Utwórz: {task_name}",
                "priority": "MEDIUM",
                "type": "structure",
                "value_score": 0.4,
                "reason": "Brakujący element architektury",
                "source": "architecture"
            })
        
        security_tasks = [t for t in tasks if t.get("type") == "security"]
        if security_tasks:
            security_tasks[0]["priority"] = "HIGH"
            security_tasks[0]["value_score"] = 1.0
        
        tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "LOW"), 3), -t.get("value_score", 0)))
        
        return tasks[:self.max_tasks_per_day]

    def _issue_to_task(self, issue):
        """Konwertuje issue na szczegółowy opis tasku."""
        issue_type = issue.get("type", "")
        issue_text = issue.get("issue", "")
        secrets = issue.get("secrets", [])
        todos = issue.get("todos", [])
        functions = issue.get("functions", [])
        
        if issue_type == "security" and secrets:
            files = [s.get("file", "?") for s in secrets[:3]]
            types = [s.get("type", "?") for s in secrets[:3]]
            return f"SECURITY: {types[0]} w {files[0]} (+ {len(secrets)-1} więcej)"
        
        elif issue_type == "syntax_error":
            return f"FIX: {issue_text}"
        
        elif issue_type == "technical_debt" and todos:
            first_todo = todos[0]
            file_path = first_todo.get("file", "?")
            marker = first_todo.get("type", "TODO")
            content = first_todo.get("content", "?")
            return f"{marker}: {content} [{file_path}]"
        
        elif issue_type == "code_quality" and functions:
            func_info = [f"{f.get('function')}() [{f.get('lines')}ln]" for f in functions[:2]]
            return f"Refaktoryzacja: {', '.join(func_info)}"
        
        elif issue_type == "structure":
            if "pusty" in issue_text.lower():
                return "Zacznij projekt - napisz pierwszy kod"
            return f"Struktura: {issue_text}"
        
        return issue_text

    def select_focus_task(self, tasks):
        """Wybiera 1 najważniejszy task."""
        if not tasks:
            return None
        
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "LOW"), 3), -t.get("value_score", 0))
        )
        return sorted_tasks[0]

    def generate_message(self, status, work_data=None, tasks=None):
        """Generuje komunikat systemowy z kontekstem."""
        projects = work_data.get("projects", {}) if work_data else {}
        
        if status == "STAGNATION":
            stagnant = [p for p, d in projects.items() if d.get("status") == "STAGNATION"]
            if stagnant:
                return f"⚠️ Stagnacja: {', '.join(stagnant)}\nZrób jedną konkretną rzecz - najpierw security issues."
            return "⚠️ Brak realnego postępu. Zrób jedną konkretną rzecz."
        elif status == "LOW_PROGRESS":
            return "🟡 Za mało postępu. Skup się na jednym zadaniu z HIGH priority."
        elif status == "REAL_WORK":
            best = max(projects.items(), key=lambda x: x[1].get("score", 0)) if projects else None
            if best:
                return f"✅ Dobrze idziesz! Kontynuuj nad **{best[0]}**."
            return "✅ Dobrze idziesz. Kontynuuj."
        
        if tasks:
            security = [t for t in tasks if t.get("type") == "security"]
            if security:
                return f"🚨 Masz {len(security)} security issues do naprawienia!"
        
        return "📋 Masz zadania. Wybierz jeden task."

    def get_focus_section_md(self, focus_task, message):
        """Generuje sekcję Focus dla raportu."""
        if not focus_task:
            return ""
        
        project = focus_task.get("project", "N/A")
        task = focus_task.get("task", "Brak")
        priority = focus_task.get("priority", "LOW")
        icon = PRIORITY_ICONS.get(priority, "⚪")
        reason = focus_task.get("reason", "")
        
        result = f"""## 🎯 Focus na dziś

{icon} **[{project}]** {task}
"""
        if reason:
            result += f"\n_Dlaczego: {reason}_"
        
            result += f"""
## ⚠️ Komunikat

{message}
"""
        return result

    def send_to_todoist(self, tasks, due_date=None):
        """Wysyła szczegółowe zadania do Todoist z deduplikacją."""
        if not INTEGRATE_TODOIST:
            return []
        
        project_id = self.todoist.get_project_id()
        if not project_id:
            return []
        
        active_tasks = self.todoist.get_active_tasks()
        existing_contents = {self._normalize_content(t.get("content", "")) for t in active_tasks}
        
        sent = []
        skipped = 0
        
        for task in tasks:
            if not self._should_create_task(task):
                continue
            
            content = self._build_detailed_task_content(task)
            normalized = self._normalize_content(content)
            
            if normalized in existing_contents:
                skipped += 1
                continue
            
            priority = 4 if task.get("priority") == "HIGH" else 3 if task.get("priority") == "MEDIUM" else 2
            task_id = self.todoist.create_task(content, project_id, priority, TODOIST_LABELS)
            if task_id:
                sent.append({"todoist_id": task_id, "task_data": task})
                existing_contents.add(normalized)
        
        if skipped > 0:
            print(f"[TODOIST] Pominięto {skipped} duplikatów")
        
        if sent:
            self._save_sent_tasks(sent)
        
        return sent
    
    def _normalize_content(self, content):
        """Normalizuje treść tasku do porównania - ignoruje prefix projektu i emoji."""
        import re
        normalized = content.lower().strip()
        normalized = re.sub(r'\[.*?\]', '', normalized)
        normalized = re.sub(r'[\U0001F300-\U0001F9FF]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
    
    def _should_create_task(self, task):
        """Sprawdza czy task powinien być utworzony (plik nie istnieje)."""
        task_desc = task.get("task", "")
        task_type = task.get("type", "")
        
        if task_type == "structure":
            for keyword in ["Utwórz:", "Create:", "Dodaj:", "Add:"]:
                if keyword in task_desc:
                    filepath = task_desc.split(keyword)[-1].strip()
                    filepath = filepath.split("[")[0].strip()
                    if os.path.exists(filepath):
                        return False
                    return True
        
        if task_type in ["security", "technical_debt", "code_quality"]:
            file_path = task.get("issue_details", {}).get("secrets", [{}])
            if file_path:
                for secret in file_path:
                    if os.path.exists(secret.get("file", "")):
                        return False
            
            todos = task.get("issue_details", {}).get("todos", [])
            for todo in todos:
                if os.path.exists(todo.get("file", "")):
                    pass
            
        return True
    
    def _build_detailed_task_content(self, task):
        """Buduje szczegółową treść tasku dla Todoist."""
        project = task.get('project', '?')
        task_type = task.get('type', '')
        issue_details = task.get('issue_details', {})
        
        content = f"[{project}] "
        
        if task_type == 'security':
            secrets = issue_details.get('secrets', [])
            if secrets:
                s = secrets[0]
                content += f"🔐 {s.get('type', 'SECRET')} w `{s.get('file', '?')}`"
                if len(secrets) > 1:
                    content += f" (+{len(secrets)-1} więcej)"
            else:
                content += task.get('task', 'Napraw security')
        
        elif task_type == 'technical_debt':
            todos = issue_details.get('todos', [])
            if todos:
                t = todos[0]
                marker = t.get('type', 'TODO')
                content += f"📝 {marker}: {t.get('content', '?')[:50]}"
                content += f" [plik: {t.get('file', '?')}]"
            else:
                content += task.get('task', 'Napraw TODO/FIXME')
        
        elif task_type == 'code_quality':
            funcs = issue_details.get('functions', [])
            if funcs:
                f = funcs[0]
                content += f"⚡ Refaktoryzuj `{f.get('function', '?')}()` ({f.get('lines', '?')}ln)"
                if len(funcs) > 1:
                    content += f" (+{len(funcs)-1} więcej)"
            else:
                content += task.get('task', 'Refaktoryzacja')
        
        elif task_type == 'structure':
            content += f"📁 {task.get('task', 'Struktura')}"
        
        else:
            content += task.get('task', 'Do zrobienia')
        
        return content[:500]

    def close_task(self, task_content):
        """Zamyka zadanie w Todoist."""
        if not INTEGRATE_TODOIST:
            return False
        
        active = self.todoist.get_active_tasks()
        for task in active:
            if task.get("content") == task_content:
                return self.todoist.close_task(task.get("id"))
        return False

    def mark_focus(self, task_content):
        """Oznacza task jako FOCUS."""
        if not INTEGRATE_TODOIST:
            return False
        
        active = self.todoist.get_active_tasks()
        for task in active:
            if task.get("content") == task_content:
                return self.todoist.add_label(task.get("id"), FOCUS_LABEL)
        return False

    def save_focus_log(self, focus_task, message, status):
        """Zapisuje log focus."""
        log = self._load_focus_log()
        log.append({
            "timestamp": datetime.now().isoformat(),
            "focus_task": focus_task,
            "message": message,
            "status": status
        })
        if len(log) > 100:
            log = log[-100:]
        
        os.makedirs(self.decisions_path, exist_ok=True)
        with open(self.focus_log_file, 'w') as f:
            json.dump(log, f, indent=2)

    def get_today_focus(self):
        """Pobiera focus z dzisiaj."""
        log = self._load_focus_log()
        today = datetime.now().strftime("%Y-%m-%d")
        for entry in reversed(log):
            if entry.get("timestamp", "").startswith(today):
                return entry
        return None

    def get_task_content(self, task):
        """Tworzy treść tasku do wyszukiwania w Todoist."""
        if not task:
            return ""
        project = task.get("project", "")
        task_text = task.get("task", "")
        if project and project != "unknown":
            return f"[{project}] {task_text}"
        return task_text

    def _load_focus_log(self):
        if os.path.exists(self.focus_log_file):
            try:
                with open(self.focus_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_sent_tasks(self, sent_tasks):
        """Zapisuje wysłane taski do pamięci."""
        all_sent = self._load_sent_tasks()
        
        for sent in sent_tasks:
            content = self._build_detailed_task_content(sent.get("task_data", {}))
            task_entry = {
                "content": content,
                "normalized": self._normalize_content(content),
                "todoist_id": sent.get("todoist_id"),
                "timestamp": datetime.now().isoformat(),
                "task_data": sent.get("task_data", {})
            }
            all_sent.append(task_entry)
        
        try:
            with open(self.sent_tasks_file, 'w') as f:
                json.dump(all_sent, f, indent=2)
        except Exception as e:
            print(f"[PLANNER] Błąd zapisu sent_tasks: {e}")
    
    def _load_sent_tasks(self):
        """Ładuje historię wysłanych tasków."""
        if os.path.exists(self.sent_tasks_file):
            try:
                with open(self.sent_tasks_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _is_task_completed(self, task):
        """Sprawdza czy task został wykonany (plik istnieje / TODO naprawione)."""
        task_type = task.get("type", "")
        issue_details = task.get("issue_details", {})
        
        if task_type == "structure":
            task_desc = task.get("task", "")
            for keyword in ["Utwórz:", "Create:", "Dodaj:", "Add:"]:
                if keyword in task_desc:
                    filepath = task_desc.split(keyword)[-1].strip()
                    filepath = filepath.split("[")[0].strip()
                    return os.path.exists(filepath)
        
        if task_type == "security":
            secrets = issue_details.get("secrets", [])
            if not secrets:
                return False
            return False
        
        if task_type == "technical_debt":
            todos = issue_details.get("todos", [])
            if not todos:
                return False
            return False
        
        return False
