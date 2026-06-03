"""
brain/planning/scheduler.py - Task Scheduler
Planuje i harmonogramuje zadania
"""

from datetime import datetime, timedelta


class TaskScheduler:
    """
    TaskScheduler - planuje i harmonogramuje zadania.
    
    Funkcje:
    - Ustala kolejność zadań
    - Szacuje czas
    - Tworzy harmonogram
    """
    
    def __init__(self):
        self.schedule_history = []
    
    def schedule(self, tasks, constraints=None):
        """
        Tworzy harmonogram zadań.
        
        Args:
            tasks: Lista zadań
            constraints: Ograniczenia (opcjonalne)
            
        Returns:
            dict: Harmonogram
        """
        constraints = constraints or {}
        max_daily_minutes = constraints.get("max_daily_minutes", 480)
        
        schedule = {
            "timestamp": datetime.now().isoformat(),
            "schedule_id": self._generate_id(),
            "tasks": [],
            "daily_schedule": {},
            "total_estimated_minutes": 0
        }
        
        sorted_tasks = self._sort_tasks(tasks)
        
        current_day = datetime.now()
        current_minutes = 0
        day_tasks = []
        
        for task in sorted_tasks:
            duration = task.get("estimated_minutes", 30)
            
            if current_minutes + duration > max_daily_minutes:
                schedule["daily_schedule"][current_day.strftime("%Y-%m-%d")] = day_tasks
                current_day += timedelta(days=1)
                current_minutes = 0
                day_tasks = []
            
            day_tasks.append({
                **task,
                "scheduled_date": current_day.isoformat()
            })
            current_minutes += duration
        
        if day_tasks:
            schedule["daily_schedule"][current_day.strftime("%Y-%m-%d")] = day_tasks
        
        schedule["tasks"] = sorted_tasks
        schedule["total_estimated_minutes"] = sum(
            t.get("estimated_minutes", 30) for t in sorted_tasks
        )
        
        self.schedule_history.append(schedule)
        
        return schedule
    
    def _sort_tasks(self, tasks):
        """Sortuje zadania według priorytetu."""
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        
        return sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.get("priority", "LOW"), 2),
                t.get("estimated_minutes", 30)
            )
        )
    
    def get_today_tasks(self, schedule):
        """Pobiera zadania na dziś."""
        today = datetime.now().strftime("%Y-%m-%d")
        return schedule.get("daily_schedule", {}).get(today, [])
    
    def _generate_id(self):
        import hashlib
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
