"""
brain/alerts.py - Productivity Alerts
Jedyna jednostka odpowiedzialna za sprawdzanie i raportowanie alertów produktywności
"""

from datetime import datetime
from core.constants import STAGNATION_CRITICAL_DAYS, STAGNATION_WARNING_DAYS, OVERDUE_DAYS


class Alerts:
    """Sprawdza i generuje alerty produktywności."""
    
    def __init__(self):
        self.alert_history = []
    
    def check(self, work_data, focus_task, state):
        """Sprawdza warunki alertów."""
        alerts = []
        
        stagnation = self._check_stagnation(work_data)
        if stagnation:
            alerts.append(stagnation)
        
        overdue = self._check_overdue(focus_task, state)
        if overdue:
            alerts.append(overdue)
        
        no_focus = self._check_no_focus(focus_task)
        if no_focus:
            alerts.append(no_focus)
        
        good_progress = self._check_good_progress(work_data)
        if good_progress:
            alerts.append(good_progress)
        
        self.alert_history.extend(alerts)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        return alerts
    
    def _check_stagnation(self, work_data):
        """Sprawdza stagnację projektów (JEDYNE miejsce sprawdzania)."""
        stagnant_projects = []
        
        for name, data in work_data.get("projects", {}).items():
            if data.get("status") == "STAGNATION":
                days = data.get("stagnation_days", 0)
                stagnant_projects.append((name, days))
        
        if stagnant_projects:
            if any(days >= STAGNATION_CRITICAL_DAYS for _, days in stagnant_projects):
                names = ", ".join([f"{n} ({d}d)" for n, d in stagnant_projects[:2]])
                return {
                    "type": "critical",
                    "priority": 1,
                    "message": f"🚨 KRYTYCZNE: {names} - {STAGNATION_CRITICAL_DAYS}+ dni stagnacji!",
                    "action": "break_task"
                }
            elif any(days >= STAGNATION_WARNING_DAYS for _, days in stagnant_projects):
                names = ", ".join([n for n, _ in stagnant_projects[:2]])
                return {
                    "type": "warning",
                    "priority": 2,
                    "message": f"⚠️ Stagnacja: {names} - {STAGNATION_WARNING_DAYS}+ dni bez postępu",
                    "action": "consider_skip"
                }
        
        return None
    
    def _check_overdue(self, focus_task, state):
        """Sprawdza overdue taski."""
        if not focus_task:
            return None
        
        last_completion = state.get("last_completion")
        if last_completion:
            try:
                last = datetime.fromisoformat(last_completion)
                days_since = (datetime.now() - last).days
                
                if days_since >= OVERDUE_DAYS:
                    return {
                        "type": "warning",
                        "priority": 3,
                        "message": f"📋 {focus_task.get('task', '')} - {days_since} dni bez zamknięcia",
                        "action": "review_task"
                    }
            except:
                pass
        
        return None
    
    def _check_no_focus(self, focus_task):
        """Sprawdza brak focusa."""
        if not focus_task:
            return {
                "type": "info",
                "priority": 5,
                "message": "🎯 Ustaw focus na dziś!",
                "action": "select_focus"
            }
        return None
    
    def _check_good_progress(self, work_data):
        """Sprawdza dobry postęp."""
        if work_data.get("overall_status") == "REAL_WORK":
            return {
                "type": "positive",
                "priority": 6,
                "message": "🟢 Świetnie! REAL_WORK - kontynuuj!",
                "action": "keep_going"
            }
        return None
    
    def format_alerts(self, alerts):
        """Formatuje alerty do wyświetlenia."""
        if not alerts:
            return ""
        
        lines = ["\n" + "=" * 40]
        lines.append("📊 ALERTY")
        lines.append("=" * 40)
        
        sorted_alerts = sorted(alerts, key=lambda x: x.get("priority", 99))
        
        for alert in sorted_alerts[:3]:
            lines.append(alert.get("message", ""))
        
        return "\n".join(lines)
