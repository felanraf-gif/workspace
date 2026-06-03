"""
brain/assistant.py - Asystent: interakcja, nauka i sugestie
Konsolidacja: learning_engine + interaction_engine + executor_lite
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict
from core.constants import PRIORITY_ICONS, CHECKIN_INTERVAL_MINUTES


def safe_print(*args, **kwargs):
    """Bezpieczne printowanie - ignoruje BrokenPipeError."""
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        pass
    except OSError as e:
        if e.errno == 32:
            pass


class Assistant:
    """Asystent - interakcja z użytkownikiem, nauka wzorców, sugestie."""
    
    def __init__(self, memory_path="memory", obsidian_path=None, use_llm=True):
        self.memory_path = memory_path
        self.obsidian_path = obsidian_path or "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant"
        self.decisions_path = os.path.join(memory_path, "decisions")
        self.analytics_path = os.path.join(memory_path, "analytics")
        self.interactions_dir = os.path.join(self.obsidian_path, "Interactions")
        
        self.learning_file = os.path.join(self.analytics_path, "learning_data.json")
        self.patterns_file = os.path.join(self.decisions_path, "user_patterns.json")
        
        os.makedirs(self.analytics_path, exist_ok=True)
        os.makedirs(self.decisions_path, exist_ok=True)
        os.makedirs(self.interactions_dir, exist_ok=True)
        
        self._ensure_files()
        self.state = {}
        
        self.llm = None
        if use_llm:
            try:
                from integrations.llm import SmartAdvisor, LLM
                self.llm = SmartAdvisor()
                if self.llm.llm.is_available():
                    print(f"[ASSISTANT] 🤖 LLM aktywny ({self.llm.llm.provider})")
                else:
                    print("[ASSISTANT] ⚠️ LLM niedostępny - używam fallback")
            except ImportError:
                print("[ASSISTANT] ⚠️ Moduł LLM niedostępny")

    def _ensure_files(self):
        if not os.path.exists(self.learning_file):
            self._save_learning({"history": [], "stats": {}})
        if not os.path.exists(self.patterns_file):
            self._save_patterns({})

    def record_task_completion(self, task, project, duration_minutes=0):
        """Zapisuje ukończenie taska."""
        data = self._load_learning()
        data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "project": project,
            "duration_minutes": duration_minutes,
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday()
        })
        if len(data["history"]) > 1000:
            data["history"] = data["history"][-1000:]
        self._save_learning(data)
        self._update_patterns()

    def record_task_skipped(self, task, project):
        """Zapisuje pominięcie taska."""
        data = self._load_learning()
        data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "project": project,
            "action": "skipped",
            "hour": datetime.now().hour
        })
        self._save_learning(data)

    def get_recommendations(self):
        """Zwraca rekomendacje na podstawie wzorców i LLM."""
        patterns = self._load_patterns()
        recs = []
        
        current_hour = datetime.now().hour
        best_hours = patterns.get("best_working_hours", [])
        
        if best_hours:
            if current_hour in best_hours:
                recs.append({"type": "good_time", "message": "Teraz dobry czas na pracę.", "priority": "high"})
            else:
                next_good = min([h for h in best_hours if h > current_hour] or best_hours)
                recs.append({"type": "optimal_time", "message": f"Następny szczyt: {next_good}:00", "priority": "medium"})
        
        avg_duration = patterns.get("avg_task_duration_minutes", 0)
        if avg_duration > 120:
            recs.append({"type": "task_size", "message": "Rozważ mniejsze taski.", "priority": "medium"})
        
        if self.llm and self.llm.llm.is_available():
            llm_rec = self._get_llm_recommendation()
            if llm_rec:
                recs.append(llm_rec)
        
        return recs
    
    def _get_llm_recommendation(self):
        """Pobiera rekomendację z LLM."""
        if not self.llm:
            return None
        
        try:
            context = {
                "project_type": "AI Agent",
                "issues": [],
                "progress": {"status": "active"},
                "goals": "Budowa autonomicznego agenta AI"
            }
            
            result = self.llm.get_daily_recommendation(context)
            
            if result and "ACC:" in result:
                lines = result.strip().split("\n")
                action = ""
                why = ""
                for line in lines:
                    if line.startswith("ACC:"):
                        action = line.replace("ACC:", "").strip()
                    elif line.startswith("DLACZEGO:"):
                        why = line.replace("DLACZEGO:", "").strip()
                
                if action:
                    return {
                        "type": "llm",
                        "message": f"🤖 {action}",
                        "why": why,
                        "priority": "high"
                    }
        except Exception as e:
            print(f"[ASSISTANT] LLM error: {e}")
        
        return None

    def get_productivity_score(self, days=7):
        """Oblicza wynik produktywności 0-100."""
        history = self._load_learning().get("history", [])
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in history if datetime.fromisoformat(e["timestamp"]) > cutoff]
        
        if not recent:
            return {"score": 0, "tasks_completed": 0, "message": "Brak danych"}
        
        completed = len([e for e in recent if e.get("duration_minutes", 0) > 0])
        skipped = len([e for e in recent if e.get("action") == "skipped"])
        stagnations = len([e for e in recent if e.get("type") == "stagnation"])
        
        score = 50 + completed * 10 - skipped * 5 - stagnations * 15
        score = max(0, min(100, score))
        
        msg = "Świetnie!" if score >= 80 else "Dobra praca." if score >= 60 else "Przeciętnie." if score >= 40 else "Niski wynik."
        
        return {"score": score, "tasks_completed": completed, "tasks_skipped": skipped, "stagnations": stagnations, "message": msg}

    def suggest_daily_limit(self):
        """Sugeruje realistyczny limit tasków na dzień."""
        patterns = self._load_patterns()
        avg_duration = patterns.get("avg_task_duration_minutes", 60)
        hours_left = max(0, 22 - datetime.now().hour)
        return min(max(1, int(hours_left / (avg_duration / 60))), 5)
    
    def get_proactive_suggestions(self, project_state: dict) -> list:
        """Zwraca proaktywne sugestie oparte na wzorcach."""
        suggestions = []
        patterns = self._load_patterns()
        history = self._load_learning().get("history", [])
        
        recent_history = [e for e in history[-50:] if e.get("timestamp")]
        
        if len(recent_history) >= 10:
            completion_rate = len([e for e in recent_history if e.get("duration_minutes", 0) > 0]) / len(recent_history)
            
            if completion_rate < 0.5:
                suggestions.append({
                    "type": "completion_rate",
                    "priority": "high",
                    "message": "📉 Niski wskaźnik ukończenia ({}%). Rozważ mniejsze taski.".format(int(completion_rate * 100))
                })
        
        if patterns.get("best_working_hours"):
            current_hour = datetime.now().hour
            best_hours = patterns["best_working_hours"]
            if current_hour not in best_hours and len(best_hours) >= 1:
                suggestions.append({
                    "type": "timing",
                    "priority": "medium",
                    "message": f"⏰ Twoje najlepsze godziny pracy to {best_hours}. Rozważ planowanie ważnych zadań wtedy."
                })
        
        avg_duration = patterns.get("avg_task_duration_minutes", 0)
        if avg_duration > 90:
            suggestions.append({
                "type": "task_size",
                "priority": "medium",
                "message": f"📊 Średni czas taska: {avg_duration} min. Sugeruję podzielić na mniejsze."
            })
        
        skipped_recently = [e for e in recent_history if e.get("action") == "skipped"]
        if len(skipped_recently) >= 3:
            suggestions.append({
                "type": "pattern",
                "priority": "medium",
                "message": "⚠️ Ostatnio dużo pomijasz. Może warto przemyśleć plan?"
            })
        
        return suggestions
    
    def detect_context_switches(self) -> int:
        """Wykrywa częste zmiany między projektami."""
        history = self._load_learning().get("history", [])
        recent = history[-20:]
        
        if len(recent) < 5:
            return 0
        
        projects = [e.get("project") for e in recent if e.get("project")]
        if len(projects) != len(set(projects)):
            return len(projects) - len(set(projects))
        
        return 0
    
    def suggest_project_focus(self) -> str:
        """Sugeruje na którym projekcie się skupić."""
        history = self._load_learning().get("history", [])
        recent = [e for e in history[-30:] if e.get("project")]
        
        if not recent:
            return "Wybierz projekt samodzielnie"
        
        project_counts = defaultdict(int)
        for e in recent:
            project_counts[e["project"]] += 1
        
        most_active = max(project_counts.items(), key=lambda x: x[1]) if project_counts else None
        
        if most_active:
            return f"Kontynuuj nad {most_active[0]} - to Twój najbardziej aktywny projekt"
        
        return "Wybierz projekt samodzielnie"

    def should_checkin(self, last_check=None, interval_minutes=30):
        """Sprawdza czy czas na check-in."""
        if not last_check:
            return True
        elapsed = (datetime.now() - datetime.fromisoformat(last_check)).total_seconds() / 60
        return elapsed >= interval_minutes

    def prompt_checkin(self, focus_task, work_data=None, cycles_without_progress=0):
        """Smart check-in - kontekstowy prompt. Zwraca None jeśli stdin niedostępny (daemon mode)."""
        safe_print("\n" + "=" * 50)
        
        if focus_task:
            project = focus_task.get('project', '')
            task = focus_task.get('task', '')
            priority = focus_task.get('priority', 'LOW')
            icon = PRIORITY_ICONS.get(priority, "⚪")
            safe_print(f"🎯 FOCUS: {icon} [{project}] {task}")
        
        if cycles_without_progress >= 3:
            safe_print("⚠️ 3+ cykli bez postępu - coś nie tak?")
        elif cycles_without_progress >= 2:
            safe_print("💡 Stagnacja zbliża się...")
        
        if work_data and work_data.get('overall_status') == 'STAGNATION':
            safe_print("🔴 Status: Stagnacja - spróbuj mniejszego kroku")
        elif work_data and work_data.get('overall_status') == 'REAL_WORK':
            safe_print("🟢 Świetnie! Kontynuuj!")
        
        safe_print("=" * 50)
        safe_print("Co słychać?")
        safe_print("1. Zrobiłem ✓")
        safe_print("2. Pracuję...")
        safe_print("3. Utknąłem")
        safe_print("4. Pomijam")
        
        try:
            safe_print("> ", end="", flush=True)
            return input().strip().lower()
        except (EOFError, OSError, BrokenPipeError):
            return None
        except:
            return None

    def process_status(self, status, focus_task):
        """Przetwarza odpowiedź użytkownika."""
        status_map = {
            "1": "done", "done": "done",
            "2": "working", "working": "working",
            "3": "blocked", "blocked": "blocked",
            "4": "skip", "skip": "skip"
        }
        
        status = status_map.get(status.lower(), status.lower())
        
        if status not in status_map.values():
            return {"action": "invalid", "message": f"Nieznany: '{status}'. Użyj 1-4 lub done/working/blocked/skip"}
        
        result = {"action": status, "task": focus_task, "timestamp": datetime.now().isoformat()}
        
        if status == "done":
            result["message"] = f"✅ Zamknięto: {focus_task.get('task', '')}"
            if focus_task:
                self.record_task_completion(focus_task.get("task", ""), focus_task.get("project", ""))
        
        elif status == "working":
            result["message"] = "📝 Postęp zapisany. Kontynuuj!"
            self.state["progress_cycles"] = self.state.get("progress_cycles", 0) + 1
        
        elif status == "blocked":
            smaller = self._generate_smaller_step(focus_task)
            result["message"] = f"🔧 Spróbuj: {smaller}"
            result["smaller_step"] = smaller
        
        elif status == "skip":
            result["message"] = "⏭️ Focus zmieniony."
            if focus_task:
                self.record_task_skipped(focus_task.get("task", ""), focus_task.get("project", ""))
        
        self._log_interaction(result)
        return result

    def generate_suggestions(self, focus_task, work_status):
        """Generuje sugestie akcji."""
        suggestions = []
        
        if focus_task:
            suggestions.append({"id": "continue", "type": "action", "label": "Kontynuuj", "description": focus_task.get("task", "")})
        
        if work_status == "STAGNATION":
            suggestions.append({"id": "breakdown", "type": "breakdown", "label": "Rozbij zadanie", "description": "Stagnacja - mniejsze kroki"})
        
        suggestions.append({"id": "tool", "type": "tool", "label": "Uruchom testy", "description": "Sprawdź kod"})
        
        return suggestions

    def handle_breakdown(self, task):
        """Rozbija task na mniejsze kroki."""
        if not task:
            return {"message": "Brak taska."}
        
        task_name = task.get("task", "").lower()
        steps = []
        
        if "create" in task_name:
            steps = [{"step": 1, "task": "mkdir -p nazwa"}, {"step": 2, "task": "Dodaj placeholder"}, {"step": 3, "task": "Sprawdź strukturę"}]
        elif "test" in task_name:
            steps = [{"step": 1, "task": "Napisz jeden test"}, {"step": 2, "task": "Uruchom"}, {"step": 3, "task": "Popraw"}]
        else:
            steps = [{"step": 1, "task": "Część 1"}, {"step": 2, "task": "Część 2"}, {"step": 3, "task": "Finalizacja"}]
        
        return {"message": f"Rozbijam '{task_name}'", "steps": steps}

    def _generate_smaller_step(self, task):
        """Generuje mniejszy krok."""
        if not task:
            return "Zrób mniejszą część zadania."
        return f"Smaller: {task.get('task', '')}"

    def _update_patterns(self):
        """Aktualizuje wyuczone wzorce."""
        history = self._load_learning().get("history", [])
        if len(history) < 5:
            return
        
        patterns = {}
        
        hour_counts = defaultdict(int)
        for e in history:
            if "hour" in e:
                hour_counts[e["hour"]] += 1
        if hour_counts:
            patterns["best_working_hours"] = [h for h, _ in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
        
        recent = [e for e in history if e.get("duration_minutes", 0) > 0][-50:]
        if recent:
            patterns["avg_task_duration_minutes"] = round(sum(e.get("duration_minutes", 30) for e in recent) / len(recent))
        
        patterns["last_updated"] = datetime.now().isoformat()
        self._save_patterns(patterns)

    def _log_interaction(self, result):
        """Zapisuje interakcję do Obsidian."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.interactions_dir, f"{today}_interactions.md")
        
        task = result.get("task", {})
        content = f"""## {result.get("timestamp", "")}

**Akcja:** {result.get("action", "").upper()}
**Task:** {task.get("task", "N/A")} ({task.get("project", "N/A")})
**Wiadomość:** {result.get("message", "")}

"""
        try:
            with open(log_file, 'a') as f:
                f.write(content)
        except:
            pass

    def _load_learning(self):
        try:
            with open(self.learning_file, 'r') as f:
                return json.load(f)
        except:
            return {"history": [], "stats": {}}

    def _save_learning(self, data):
        with open(self.learning_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_patterns(self):
        try:
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_patterns(self, patterns):
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)
