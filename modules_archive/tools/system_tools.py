import os
import time
import platform
from datetime import datetime, timedelta

class SystemTools:
    """Narzędzia systemowe."""
    
    @staticmethod
    def get_current_time():
        """Zwraca aktualny czas."""
        return datetime.now()
    
    @staticmethod
    def get_uptime():
        """Zwraca uptime systemu."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return {
                "seconds": uptime_seconds,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "formatted": f"{days}d {hours}h {minutes}m"
            }
        except:
            return {"seconds": 0, "days": 0, "hours": 0, "minutes": 0, "formatted": "N/A"}
    
    @staticmethod
    def get_system_info():
        """Zwraca informacje o systemie."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
    
    @staticmethod
    def get_memory_usage():
        """Zwraca użycie pamięci."""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]
                    try:
                        mem[key] = int(value) * 1024
                    except:
                        pass
            
            total = mem.get('MemTotal', 0)
            available = mem.get('MemAvailable', mem.get('MemFree', 0))
            used = total - available
            
            return {
                "total": total,
                "available": available,
                "used": used,
                "percent": round((used / total) * 100, 1) if total > 0 else 0,
                "total_mb": round(total / 1024 / 1024, 1),
                "used_mb": round(used / 1024 / 1024, 1),
                "available_mb": round(available / 1024 / 1024, 1)
            }
        except:
            return {"total": 0, "available": 0, "used": 0, "percent": 0}
    
    @staticmethod
    def get_disk_usage(path="/"):
        """Zwraca użycie dysku."""
        try:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            available = stat.f_bavail * stat.f_frsize
            used = total - available
            
            return {
                "total": total,
                "available": available,
                "used": used,
                "percent": round((used / total) * 100, 1) if total > 0 else 0,
                "total_gb": round(total / 1024 / 1024 / 1024, 2),
                "used_gb": round(used / 1024 / 1024 / 1024, 2),
                "available_gb": round(available / 1024 / 1024 / 1024, 2)
            }
        except:
            return {"total": 0, "available": 0, "used": 0, "percent": 0}
    
    @staticmethod
    def is_weekend():
        """Sprawdza czy jest weekend."""
        weekday = datetime.now().weekday()
        return weekday >= 5
    
    @staticmethod
    def get_time_of_day():
        """Zwraca porę dnia."""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def get_work_hours_left():
        """Zwraca ile godzin pracy zostało (zakładając 22:00 koniec)."""
        now = datetime.now()
        end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0)
        
        if now.hour >= 22:
            return 0
        
        diff = (end_of_day - now).total_seconds() / 3600
        return round(max(0, diff), 1)
    
    @staticmethod
    def format_duration(seconds):
        """Formatuje czas w czytelny sposób."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def get_day_name():
        """Zwraca nazwę dnia tygodnia."""
        days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        return days[datetime.now().weekday()]

if __name__ == "__main__":
    st = SystemTools()
    
    print("=== SystemTools Test ===")
    print(f"Time: {st.get_current_time()}")
    print(f"Day: {st.get_day_name()}")
    print(f"Time of day: {st.get_time_of_day()}")
    print(f"Uptime: {st.get_uptime()}")
    print(f"Memory: {st.get_memory_usage()}")
    print(f"Disk: {st.get_disk_usage()}")
    print(f"System: {st.get_system_info()}")
