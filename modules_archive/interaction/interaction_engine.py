import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class InteractionEngine:
    def __init__(self, state_manager=None, planner=None, guidance=None, config=None):
        self.state = state_manager
        self.planner = planner
        self.guidance = guidance
        self.config = config or {}
        self.obsidian_path = self.config.get("OBSIDIAN_PATH", "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant")
        self.interactions_dir = os.path.join(self.obsidian_path, "Interactions")
        
        os.makedirs(self.interactions_dir, exist_ok=True)

    def should_checkin(self):
        if not self.state:
            return False
        
        last_check = self.state.state.get("last_interaction_check", None)
        if not last_check:
            return True
        
        interval_minutes = self.config.get("INTERACTION_INTERVAL_MINUTES", 30)
        last_time = datetime.fromisoformat(last_check)
        elapsed = (datetime.now() - last_time).total_seconds() / 60
        
        return elapsed >= interval_minutes

    def update_last_check(self):
        if self.state:
            self.state.update_state({"last_interaction_check": datetime.now().isoformat()})

    def get_current_focus(self):
        if not self.state:
            return None
        return self.state.state.get("current_focus_task")

    def prompt_checkin(self):
        focus = self.get_current_focus()
        
        if focus:
            print("\n" + "=" * 50)
            print(f"🎯 FOCUS TASK: {focus.get('task', 'N/A')}")
            print(f"📁 Project: {focus.get('project', 'N/A')}")
            print("=" * 50)
        
        print("\nStatus zadania? (done / working / blocked / skip)")
        print("> ", end="", flush=True)
        
        try:
            status = input().strip().lower()
        except EOFError:
            return None
        
        return status

    def parse_response(self, status):
        valid = ["done", "working", "blocked", "skip"]
        if status in valid:
            return status
        return None

    def handle_done(self, focus_task):
        result = {
            "action": "done",
            "task": focus_task,
            "timestamp": datetime.now().isoformat(),
            "message": None,
            "new_focus": None
        }
        
        if focus_task:
            task_content = f"[{focus_task.get('project', '')}] {focus_task.get('task', '')}"
            result["message"] = f"✅ Zadanie zamknięte: {task_content}"
            
            if self.planner:
                self._close_task_in_todoist(focus_task)
            
            new_focus = self._select_new_focus()
            result["new_focus"] = new_focus
            if new_focus:
                result["message"] += f"\n🔄 Nowy focus: {new_focus.get('task', 'N/A')}"
        else:
            result["message"] = "Brak aktywnego focus taska."
        
        self._log_interaction(result)
        return result

    def handle_working(self, focus_task):
        result = {
            "action": "working",
            "task": focus_task,
            "timestamp": datetime.now().isoformat(),
            "message": None
        }
        
        if focus_task and self.state:
            self.state.update_state({
                "last_progress_update": datetime.now().isoformat(),
                "progress_cycles": self.state.state.get("progress_cycles", 0) + 1
            })
            result["message"] = f"📝 Postęp zapisany. Kontynuuj: {focus_task.get('task', 'N/A')}"
        elif focus_task:
            result["message"] = f"📝 Postęp zapisany. Kontynuuj: {focus_task.get('task', 'N/A')}"
        else:
            result["message"] = "Brak aktywnego focus taska."
        
        self._log_interaction(result)
        return result

    def handle_blocked(self, focus_task):
        result = {
            "action": "blocked",
            "task": focus_task,
            "timestamp": datetime.now().isoformat(),
            "message": None,
            "smaller_step": None
        }
        
        if focus_task and self.planner:
            smaller_task = self._generate_smaller_step(focus_task)
            result["smaller_step"] = smaller_task
            if smaller_task:
                result["message"] = f"🔧 Zgenerowano mniejszy krok:\n   {smaller_task.get('content', 'N/A')}"
                self._create_blocking_task(smaller_task, focus_task)
            else:
                result["message"] = "⚠️ Nie udało się zgenerować mniejszego kroku."
        else:
            result["message"] = "Brak aktywnego focus taska."
        
        self._log_interaction(result)
        return result

    def handle_skip(self, focus_task):
        result = {
            "action": "skip",
            "task": focus_task,
            "timestamp": datetime.now().isoformat(),
            "message": None,
            "new_focus": None
        }
        
        if focus_task and self.state:
            self.state.update_state({"skipped_tasks": self.state.state.get("skipped_tasks", 0) + 1})
        
        new_focus = self._select_new_focus()
        result["new_focus"] = new_focus
        
        if new_focus:
            result["message"] = f"⏭️ Focus zmieniony na: {new_focus.get('task', 'N/A')}"
            if self.state:
                self.state.update_state({"current_focus_task": new_focus})
        else:
            result["message"] = "⏭️ Focus task pominięty. Brak nowego zadania."
        
        self._log_interaction(result)
        return result

    def process_status(self, status):
        valid = self.parse_response(status)
        if not valid:
            return {
                "action": "invalid",
                "message": f"Nieznany status: '{status}'. Użyj: done/working/blocked/skip"
            }
        
        focus_task = self.get_current_focus()
        
        handlers = {
            "done": self.handle_done,
            "working": self.handle_working,
            "blocked": self.handle_blocked,
            "skip": self.handle_skip
        }
        
        return handlers[valid](focus_task)

    def _select_new_focus(self):
        if self.guidance and self.planner:
            pending_tasks = self._get_pending_tasks()
            if pending_tasks:
                new_focus = self.guidance.select_focus_task(pending_tasks)
                if new_focus and self.state:
                    self.state.update_state({"current_focus_task": new_focus})
                return new_focus
        return None

    def _get_pending_tasks(self):
        pending_file = os.path.join(self.config.get("MEMORY_PATH", "memory"), "decisions", "pending_tasks.json")
        if os.path.exists(pending_file):
            try:
                with open(pending_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def _close_task_in_todoist(self, task):
        if not self.planner:
            return
        
        task_id = task.get("todoist_id")
        if task_id:
            try:
                self.planner.api.close_task(task_id)
            except:
                pass
        
        if self.state:
            completed = self.state.state.get("completed_tasks_today", 0) + 1
            self.state.update_state({
                "completed_tasks_today": completed,
                "current_focus_task": None
            })

    def _generate_smaller_step(self, focus_task):
        project = focus_task.get("project", "")
        task = focus_task.get("task", "")
        
        smaller_steps = {
            "Create src folder": "Create empty file in src",
            "Setup database": "Create database connection file",
            "Write tests": "Write one test function",
            "Refactor code": "Rename one variable",
            "Add tests": "Add one unit test",
        }
        
        smaller = smaller_steps.get(task, f"Smaller part of: {task}")
        
        return {
            "content": smaller,
            "project": project,
            "priority": 4,
            "parent": task
        }

    def _create_blocking_task(self, smaller_task, parent_task):
        if not self.planner:
            return
        
        try:
            self.planner.create_task(
                content=f"[BLOCKER] {smaller_task.get('content', '')}",
                project_name=smaller_task.get("project", ""),
                priority=4,
                labels=["BLOCKER"]
            )
        except:
            pass

    def _log_interaction(self, result):
        if not self.state:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.interactions_dir, f"{today}_interactions.md")
        
        action = result.get("action", "unknown")
        task = result.get("task", {})
        timestamp = result.get("timestamp", datetime.now().isoformat())
        
        content = f"""## Interakcja {timestamp}

**Akcja:** {action.upper()}
**Task:** {task.get('task', 'N/A')} ({task.get('project', 'N/A')})
**Wiadomość:** {result.get('message', '')}

"""
        if result.get("new_focus"):
            nf = result.get("new_focus")
            content += f"**Nowy focus:** {nf.get('task', 'N/A')} ({nf.get('project', 'N/A')})\n\n"
        
        if result.get("smaller_step"):
            st = result.get("smaller_step")
            content += f"**Mniejszy krok:** {st.get('content', 'N/A')}\n\n"
        
        try:
            with open(log_file, 'a') as f:
                f.write(content)
        except:
            pass

    def run_checkin_cycle(self):
        if not self.should_checkin():
            return None
        
        self.update_last_check()
        status = self.prompt_checkin()
        
        if not status:
            return None
        
        return self.process_status(status)

    def get_interaction_summary(self, days=7):
        summary = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            log_file = os.path.join(self.interactions_dir, f"{date_str}_interactions.md")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                    summary.append({
                        "date": date_str,
                        "content": content
                    })
                except:
                    pass
        
        return summary
