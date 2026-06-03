from datetime import datetime

class CompletionGuard:
    def __init__(self):
        self.WARNING_THRESHOLD = 2
        self.CRITICAL_THRESHOLD = 4
        
        self.MESSAGES = {
            "OK": None,
            "WARNING": "Nie zamknąłeś zadania. Dokończ je.",
            "CRITICAL": "Pracujesz bez efektu. Zamknij task albo zmień podejście."
        }
    
    def check_completion(self, focus_task, completed_tasks, cycles_without_progress):
        """Sprawdza status ukończenia focus taska.
        
        Args:
            focus_task: Dict z kluczami 'project' i 'task' lub None
            completed_tasks: Lista zamkniętych tasków z Todoist
            cycles_without_progress: Liczba cykli bez postępu (z state)
        
        Returns:
            Dict z kluczami: status, message, cycles, needs_urgent_task
        """
        if not focus_task:
            return {
                "status": "OK",
                "message": None,
                "cycles": 0,
                "needs_urgent_task": False
            }
        
        focus_content = f"[{focus_task['project']}] {focus_task['task']}"
        
        is_completed = self._is_task_completed(focus_content, completed_tasks)
        
        if is_completed:
            cycles = 0
            status = "DONE"
            message = "Focus task zamknięty! Dobra robota."
        else:
            cycles = cycles_without_progress + 1
            
            if cycles >= self.CRITICAL_THRESHOLD:
                status = "CRITICAL"
            elif cycles >= self.WARNING_THRESHOLD:
                status = "WARNING"
            else:
                status = "OK"
            
            message = self.MESSAGES[status]
        
        needs_urgent = status == "CRITICAL"
        
        return {
            "status": status,
            "message": message,
            "cycles": cycles,
            "focus_task": focus_task,
            "needs_urgent_task": needs_urgent,
            "is_completed": is_completed
        }
    
    def _is_task_completed(self, focus_content, completed_tasks):
        """Sprawdza czy focus task jest na liście zamkniętych."""
        if not completed_tasks:
            return False
        
        for task in completed_tasks:
            task_content = task.get("content", "")
            if focus_content == task_content:
                return True
        
        return False
    
    def get_urgency_level(self, cycles_without_progress):
        """Zwraca poziom pilności dla UI."""
        if cycles_without_progress >= self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif cycles_without_progress >= self.WARNING_THRESHOLD:
            return "WARNING"
        else:
            return "OK"
    
    def should_create_urgent_task(self, cycles_without_progress):
        """Czy należy utworzyć URGENT task."""
        return cycles_without_progress >= self.CRITICAL_THRESHOLD


if __name__ == "__main__":
    guard = CompletionGuard()
    
    print("=== Test CompletionGuard ===\n")
    
    focus_task = {"project": "scraper_1", "task": "Utwórz src/"}
    completed_tasks = [
        {"content": "[towarzysz] Inne zadanie"},
        {"content": "[content_bot] Jeszcze jedno"}
    ]
    
    print(f"Focus: {focus_task}")
    print(f"Ukończone: {completed_tasks}\n")
    
    for cycles in range(5):
        result = guard.check_completion(focus_task, completed_tasks, cycles)
        print(f"Cycli bez postępu: {cycles}")
        print(f"  Status: {result['status']}")
        print(f"  Komunikat: {result['message']}")
        print(f"  Needs URGENT: {result['needs_urgent_task']}")
        print()
