import time
import os
from datetime import datetime, timedelta
from core.config import SCAN_INTERVAL, MEMORY_PATH

class Scheduler:
    def __init__(self):
        self.daily_report_time = 22  # 22:00
        self.last_daily_report = None
        
    def should_generate_daily_report(self):
        """Sprawdza, czy nadszedł czas na generowanie raportu dziennego."""
        current_hour = datetime.now().hour
        
        # Jeśli jest godzina 22:00 i nie było raportu dzisiaj
        if current_hour == self.daily_report_time:
            today = datetime.now().date()
            if self.last_daily_report != today:
                self.last_daily_report = today
                return True
        
        return False
    
    def get_seconds_until_next_check(self):
        """Oblicza sekundy do następnego sprawdzenia."""
        now = datetime.now()
        next_check = now + timedelta(minutes=1)
        next_check = next_check.replace(second=0, microsecond=0)
        
        return (next_check - now).total_seconds()
    
    def get_seconds_until_daily_report(self):
        """Oblicza sekundy do raportu dziennego."""
        now = datetime.now()
        
        # Jeśli już po 22:00, zaplanuj na jutro
        if now.hour >= self.daily_report_time:
            target = now + timedelta(days=1)
            target = target.replace(hour=self.daily_report_time, minute=0, second=0, microsecond=0)
        else:
            target = now.replace(hour=self.daily_report_time, minute=0, second=0, microsecond=0)
        
        return (target - now).total_seconds()
    
    def is_time_for_daily_cycle(self):
        """Sprawdza, czy to czas na wieczorny cykl (22:00)."""
        now = datetime.now()
        return now.hour == self.daily_report_time and now.minute < 5
    
    def log_schedule(self, message):
        """Loguje działania scheduler."""
        log_file = os.path.join(MEMORY_PATH, "scheduler_log.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

if __name__ == "__main__":
    scheduler = Scheduler()
    
    print(f"Godzina raportu dziennego: {scheduler.daily_report_time}:00")
    print(f"Sekundy do następnego sprawdzenia: {scheduler.get_seconds_until_next_check()}")
    print(f"Sekundy do raportu dziennego: {scheduler.get_seconds_until_daily_report()}")
    
    # Test logowania
    scheduler.log_schedule("Test scheduler")
    print("Log zapisany w memory/scheduler_log.txt")