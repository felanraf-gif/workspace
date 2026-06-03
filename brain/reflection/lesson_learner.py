"""
brain/reflection/lesson_learner.py - Lesson Learner
Wyciąga wnioski z wyników i zapisuje do pamięci
"""

import os
import json
from datetime import datetime


class LessonLearner:
    """Uczy się z każdego wyniku i zapisuje wnioski."""
    
    def __init__(self, lessons_path="memory/lessons"):
        self.lessons_path = lessons_path
        os.makedirs(lessons_path, exist_ok=True)
        self.lessons_file = os.path.join(lessons_path, "lessons.json")
        self._ensure_file()
    
    def _ensure_file(self):
        """Upewnia się, że plik istnieje."""
        if not os.path.exists(self.lessons_file):
            with open(self.lessons_file, 'w') as f:
                json.dump([], f)
    
    def learn(self, task, result):
        """
        Zapisuje naukę z wyniku.
        
        Args:
            task: Wykonane zadanie
            result: Wynik wykonania
            
        Returns:
            dict: Zapisana lekcja
        """
        lesson = {
            "id": self._generate_id(),
            "timestamp": datetime.now().isoformat(),
            "task_type": task.get("type") or task.get("action", "unknown"),
            "task_target": task.get("target", task.get("task", "")),
            "success": result.get("success", False),
            "approach": task.get("approach", ""),
            "output_summary": self._summarize_output(result.get("output")),
            "error": result.get("error"),
            "what_worked": self._extract_success(result),
            "what_failed": self._extract_failure(result),
            "tags": self._generate_tags(task, result)
        }
        
        lessons = self._load_lessons()
        lessons.append(lesson)
        
        if len(lessons) > 1000:
            lessons = lessons[-500:]
        
        with open(self.lessons_file, 'w') as f:
            json.dump(lessons, f, indent=2)
        
        return lesson
    
    def get_lessons(self, task_type=None, limit=50):
        """
        Pobiera nagrane lekcje.
        
        Args:
            task_type: Filtruj po typie zadania
            limit: Maksymalna liczba lekcji
            
        Returns:
            list: Lista lekcji
        """
        lessons = self._load_lessons()
        
        if task_type:
            lessons = [l for l in lessons if l.get("task_type") == task_type]
        
        return lessons[-limit:]
    
    def get_success_rate(self, task_type=None):
        """Oblicza wskaźnik sukcesu."""
        lessons = self.get_lessons(task_type, limit=100)
        if not lessons:
            return {"rate": 0, "count": 0}
        
        successful = sum(1 for l in lessons if l.get("success"))
        return {
            "rate": successful / len(lessons) if lessons else 0,
            "count": len(lessons),
            "successful": successful
        }
    
    def _load_lessons(self):
        """Ładuje lekcje z pliku."""
        try:
            with open(self.lessons_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _generate_id(self):
        """Generuje unikalne ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _summarize_output(self, output):
        """Skraca output do podsumowania."""
        if not output:
            return None
        output = str(output)
        if len(output) > 200:
            return output[:200] + "..."
        return output
    
    def _extract_success(self, result):
        """Wyciąga co zadziałało."""
        if result.get("success"):
            return "Zadanie wykonane pomyślnie"
        return None
    
    def _extract_failure(self, result):
        """Wyciąga co zawiodło."""
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return str(error)[:100] if error else "Unknown failure"
        return None
    
    def _generate_tags(self, task, result):
        """Generuje tagi dla lekcji."""
        tags = []
        
        task_type = task.get("type") or task.get("action", "")
        if "bash" in task_type.lower():
            tags.append("shell")
        elif "file" in task_type.lower():
            tags.append("filesystem")
        elif "git" in task_type.lower():
            tags.append("git")
        
        if result.get("success"):
            tags.append("success")
        else:
            tags.append("failure")
        
        return tags
