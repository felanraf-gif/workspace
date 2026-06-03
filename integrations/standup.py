"""
integrations/standup.py - Daily Standup o 6:00
"""

import os
from datetime import datetime
from core.constants import STATUS_ICONS, PRIORITY_ICONS


class Standup:
    """Generuje poranny standup w Obsidian."""
    
    STANDUP_HOUR = 6
    
    def __init__(self, vault_path=None):
        self.vault_path = vault_path or "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant"
        self.daily_dir = os.path.join(self.vault_path, "Daily")
        os.makedirs(self.daily_dir, exist_ok=True)
    
    def should_run(self):
        """Sprawdza czy to czas na standup."""
        return datetime.now().hour == self.STANDUP_HOUR
    
    def was_run_today(self):
        """Sprawdza czy standup był już dziś."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.daily_dir, f"{today}_standup.md")
        return os.path.exists(filename)
    
    def generate(self, focus_task, projects, work_data, planner):
        """Generuje standup report."""
        if self.was_run_today():
            return None
        
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.daily_dir, f"{today}_standup.md")
        
        content = self._build_header()
        content += self._build_focus_section(focus_task)
        content += self._build_projects_status_section(work_data)
        content += self._build_suggestions_section(work_data.get("overall_status"))
        content += self._build_footer()
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except:
            pass
        
        return filename
    
    def _build_header(self):
        """Buduje nagłówek standup."""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""# 🌅 Standup - {today}

## Dzień dobry!

**Godzina:** {datetime.now().strftime("%H:%M")}

## 🎯 Twój Focus na dziś

"""
    
    def _build_focus_section(self, focus_task):
        """Buduje sekcję focus taska."""
        if focus_task:
            project = focus_task.get('project', 'N/A')
            task = focus_task.get('task', 'Brak')
            priority = focus_task.get('priority', 'LOW')
            icon = PRIORITY_ICONS.get(priority, "⚪")
            return f"{icon} **[{project}]** {task}\n\n"
        return "_Brak ustalonego focus taska_\n\n"
    
    def _build_projects_status_section(self, work_data):
        """Buduje sekcję statusu projektów."""
        content = "## 📊 Status projektów\n\n"
        for name, data in work_data.get("projects", {}).items():
            icon = STATUS_ICONS.get(data.get("status", "UNKNOWN"), "⚪")
            stagnation = data.get("stagnation_days", 0)
            stagnation_text = f" ({stagnation} dni stagnacji)" if stagnation >= 2 else ""
            content += f"| {icon} | {name} | {data.get('status', '?')} | {data.get('score', 0)} pkt |{stagnation_text}\n"
        return content + "\n"
    
    def _build_suggestions_section(self, overall_status):
        """Buduje sekcję sugestii."""
        content = "## 💡 Sugestie\n\n"
        if overall_status == "STAGNATION":
            content += "- ⚠️ Zacznij od małego kroka\n"
            content += "- 🔨 Podziel zadanie na mniejsze części\n"
            content += "- ✅ Zrób jeden commit\n"
        elif overall_status == "LOW_PROGRESS":
            content += "- 🟡 Skup się na jednym zadaniu\n"
            content += "- ⏱️ Ustaw timer na 25 min\n"
        else:
            content += "- 🟢 Świetnie! Kontynuuj!\n"
            content += "- 🔥 Utrzymaj tempo\n"
        return content
    
    def _build_footer(self):
        """Buduje stopkę standup."""
        return """
## 📋 Plan na dziś

_Taski zostaną wysłane do Todoist_

---
*Wygenerowano automatycznie o {time}*
""".format(time=datetime.now().strftime('%H:%M'))
