"""
reports/reporter.py - Generowanie raportów
"""

import os
from datetime import datetime


class Reporter:
    """Generuje raporty dzienne i podsumowania."""
    
    def __init__(self, obsidian_path=None, memory_path="memory"):
        self.obsidian_path = obsidian_path or "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant"
        self.memory_path = memory_path
        self.daily_dir = os.path.join(self.obsidian_path, "Daily")
        os.makedirs(self.daily_dir, exist_ok=True)

    def generate_daily_report(self, focus_task, tasks, work_data, projects):
        """Generuje raport dzienny."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.daily_dir, f"{today}_report.md")
        
        status = work_data.get("overall_status", "UNKNOWN")
        status_icon = {"REAL_WORK": "🟢", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(status, "⚪")
        
        content = f"""# Raport Dzień {today}

## Status Pracy
{status_icon} **{status}** (score: {work_data.get('overall_score', 0)})

## Focus
"""
        if focus_task:
            content += f"- **[{focus_task.get('project', '')}]** {focus_task.get('task', '')} ({focus_task.get('priority', 'LOW')})\n"
        else:
            content += "- *Brak focus taska*\n"
        
        content += "\n## Projekty\n"
        for p, data in work_data.get("projects", {}).items():
            icon = {"REAL_WORK": "🟢", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(data.get("status", ""), "⚪")
            content += f"{icon} {p}: {data.get('status', '?')} (score: {data.get('score', 0)})\n"
        
        content += f"\n## Zadania ({len(tasks)})\n"
        for t in tasks[:5]:
            content += f"- [ ] [{t.get('project', '')}] {t.get('task', '')}\n"
        
        content += f"\n## Produktywność\n"
        content += f"- Ukończone dziś: {work_data.get('completed_today', 0)}\n"
        content += f"- Aktywne projekty: {len(projects)}\n"
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except:
            pass
        
        return {"filename": filename, "date": today}

    def generate_dashboard_md(self, work_data, memory_stats):
        """Generuje dashboard Markdown."""
        content = """## Dashboard

| Metryka | Wartość |
|---------|---------|
"""
        content += f"| Score | {work_data.get('overall_score', 0)} |\n"
        content += f"| Status | {work_data.get('overall_status', '?')} |\n"
        content += f"| Projekty | {memory_stats.get('projects_count', 0)} |\n"
        content += f"| Zadania | {memory_stats.get('tasks_today', 0)} |\n"
        
        return content
