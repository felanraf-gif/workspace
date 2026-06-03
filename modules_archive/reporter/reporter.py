import json
import os
from datetime import datetime
from core.config import INTEGRATE_OBSIDIAN, OBSIDIAN_PATH, MEMORY_PATH

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not found, charts disabled")

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not found, interactive dashboards disabled")

class Reporter:
    def __init__(self):
        self.daily_logs_path = os.path.join(MEMORY_PATH, "daily_logs")
        self.obsidian_path = OBSIDIAN_PATH
        self.daily_path = os.path.join(OBSIDIAN_PATH, "Daily")
        os.makedirs(self.daily_path, exist_ok=True)

    def generate_markdown_report(self, projects, issues, tasks, stagnation_report):
        """Generuje raport w formacie Markdown."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        md = f"# Raport Dzienny - Development Assistant V2\n\n"
        md += f"**Data:** {timestamp}\n\n"
        md += "---\n\n"
        
        # Sekcja: Podsumowanie
        md += "## 📊 Podsumowanie\n\n"
        md += f"- **Projekty:** {len(projects)}\n"
        md += f"- **Problemy:** {len(issues)}\n"
        md += f"- **Zadania:** {len(tasks)}\n"
        md += f"- **Stagnacja:** {len(stagnation_report)}\n\n"
        
        # Sekcja: Projekty
        md += "## 📂 Projekty\n\n"
        for p in projects:
            status = "✅" if p.get("new_files") else "📝"
            md += f"- {status} **{p['name']}**\n"
            if p.get("new_files"):
                md += f"  - Nowe pliki: {', '.join(p['new_files'][:3])}...\n"
        md += "\n"
        
        # Sekcja: Problemy
        md += "## ⚠️ Problemy\n\n"
        if issues:
            for i in issues:
                icon = "🔴" if i["priority"] == "HIGH" else "🟡"
                md += f"- {icon} **{i['project']}**: {i['issue']}\n"
        else:
            md += "✅ Brak problemów\n"
        md += "\n"
        
        # Sekcja: Zadania
        md += "## ✅ Zadania do wykonania\n\n"
        if tasks:
            for t in tasks:
                icon = "🔴" if t["priority"] == "HIGH" else "🟡" if t["priority"] == "MEDIUM" else "🟢"
                md += f"- {icon} **{t['project']}**: {t['task']}\n"
        else:
            md += "Brak zaplanowanych zadań\n"
        md += "\n"
        
        # Sekcja: Stagnacja
        md += "## 🕒 Stagnacja\n\n"
        if stagnation_report:
            for s in stagnation_report:
                md += f"- 🔴 **{s['project']}**: {s['stagnation_days']} dni bez aktywności\n"
        else:
            md += "✅ Brak stagnacji\n"
        md += "\n"
        
        # Metadane
        md += "---\n\n"
        md += "> Wygenerowane automatycznie przez Development Assistant V2\n"
        
        return md, date_str

    def save_report(self, report_content, date_str):
        """Zapisuje raport w pamięci lokalnej."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = os.path.join(self.daily_logs_path, f"report_{timestamp}.md")
        
        os.makedirs(self.daily_logs_path, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file

    def save_to_obsidian(self, report_content, date_str):
        """Zapisuje raport w vault Obsidian."""
        if not INTEGRATE_OBSIDIAN:
            return None
            
        obsidian_dir = os.path.join(self.obsidian_path, "daily_logs")
        obsidian_file = os.path.join(obsidian_dir, f"{date_str}_report.md")
        
        os.makedirs(obsidian_dir, exist_ok=True)
        with open(obsidian_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return obsidian_file

    def generate_charts(self, tasks, date_str):
        """Generuje wykresy analityczne."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            # Wykres 1: Rozkład priorytetów
            priorities = [t["priority"] for t in tasks]
            counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for p in priorities:
                if p in counts:
                    counts[p] += 1
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Wykres słupkowy priorytetów
            ax1.bar(counts.keys(), counts.values(), color=['red', 'orange', 'green'])
            ax1.set_title("Rozkład priorytetów zadań")
            ax1.set_xlabel("Priorytet")
            ax1.set_ylabel("Liczba zadań")
            
            # Wykres wartości zadań (value_score)
            value_scores = [t.get("value_score", 0) for t in tasks]
            if value_scores:
                ax2.hist(value_scores, bins=10, color='blue', alpha=0.7)
                ax2.set_title("Rozkład wartości zadań")
                ax2.set_xlabel("Wartość (0-1)")
                ax2.set_ylabel("Liczba zadań")
            
            plt.tight_layout()
            
            # Zapis wykresu
            charts_dir = os.path.join(MEMORY_PATH, "daily_logs", "charts")
            os.makedirs(charts_dir, exist_ok=True)
            chart_file = os.path.join(charts_dir, f"chart_{date_str}.png")
            plt.savefig(chart_file)
            plt.close()
            
            return chart_file
        except Exception as e:
            print(f"Błąd generowania wykresów: {e}")
            return None

    def generate_interactive_dashboard(self, tasks, trends_data, date_str):
        """Generuje interaktywny dashboard Plotly."""
        if not PLOTLY_AVAILABLE:
            return None
        
        # Przygotuj dane
        projects = list(set([t["project"] for t in tasks]))
        
        # Wykres 1: Rozkład priorytetów per projekt
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Rozkład priorytetów", "Wartość zadań", "Trendy projektów", "Zmienność projektów"),
            specs=[[{"type": "pie"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # Wykres 1: Pie chart priorytetów
        priorities = [t["priority"] for t in tasks]
        priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for p in priorities:
            if p in priority_counts:
                priority_counts[p] += 1
        
        fig.add_trace(
            go.Pie(labels=list(priority_counts.keys()), values=list(priority_counts.values()), name="Priorytety"),
            row=1, col=1
        )
        
        # Wykres 2: Histogram value_score
        value_scores = [t.get("value_score", 0) for t in tasks]
        fig.add_trace(
            go.Histogram(x=value_scores, name="Wartość zadań", marker_color='blue'),
            row=1, col=2
        )
        
        # Wykres 3: Trendy projektów (jeśli dostępne)
        project_names = []
        trends = []
        volatilities = []
        
        if trends_data:
            project_names = list(trends_data.keys())
            trends = [trends_data[p]["current_trend"] for p in project_names]
            volatilities = [trends_data[p].get("volatility", 0) for p in project_names]
            
            fig.add_trace(
                go.Scatter(x=project_names, y=trends, mode='markers+lines', name="Trendy"),
                row=2, col=1
            )
            
            # Wykres 4: Zmienność projektów
            fig.add_trace(
                go.Bar(x=project_names, y=volatilities, name="Zmienność", marker_color='orange'),
                row=2, col=2
            )
        
        fig.update_layout(height=800, showlegend=True, title_text=f"Dashboard - {date_str}")
        
        # Zapis dashboardu
        charts_dir = os.path.join(MEMORY_PATH, "daily_logs", "charts")
        os.makedirs(charts_dir, exist_ok=True)
        dashboard_file = os.path.join(charts_dir, f"dashboard_{date_str}.html")
        fig.write_html(dashboard_file)
        
        return dashboard_file

    def generate_readable_report(self, projects, issues, tasks, stagnation_report, trends_data=None, time_data=None, work_data=None, focus_task=None, focus_message=None, completion_data=None):
        """Generuje czytelny raport w formacie Markdown dla Obsidian."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Przygotuj dane
        high_tasks = [t for t in tasks if t["priority"] == "HIGH"]
        medium_tasks = [t for t in tasks if t["priority"] == "MEDIUM"]
        low_tasks = [t for t in tasks if t["priority"] == "LOW"]
        
        completed_tasks = [t for t in tasks if t.get("completed", False)]
        active_tasks = [t for t in tasks if not t.get("completed", False)]
        
        # Oblicz statystyki
        total_time = sum(time_data.values()) if time_data else 0
        project_stats = {}
        if time_data:
            for project, duration in time_data.items():
                project_stats[project] = {
                    "time": round(duration / 3600, 2),
                    "tasks": len([t for t in tasks if t["project"] == project])
                }
        
        # Generuj treść raportu
        content = f"# 📅 {date_str}\n\n"
        content += "---\n\n"
        
        # Sekcja: Najważniejsze zadania
        content += "## 🔥 Najważniejsze zadania\n\n"
        if high_tasks:
            for task in high_tasks:
                content += f"- [ ] **{task['project']}**: {task['task']}\n"
        else:
            content += "- Brak zadań HIGH\n"
        content += "\n"
        
        # Sekcja: Aktywne zadania (MEDIUM/LOW)
        if medium_tasks or low_tasks:
            content += "## 📋 Pozostałe zadania\n\n"
            for task in medium_tasks + low_tasks:
                priority_icon = "🟡" if task["priority"] == "MEDIUM" else "🟢"
                content += f"- {priority_icon} {task['project']}: {task['task']}\n"
            content += "\n"
        
        # Sekcja: Wykonane
        content += "## ✅ Wykonane\n\n"
        if completed_tasks:
            for task in completed_tasks:
                content += f"- {task['project']}: {task['task']}\n"
        else:
            content += "- Brak wykonanych zadań\n"
        content += "\n"
        
        # Sekcja: Problemy
        content += "## ⚠️ Problemy\n\n"
        if issues:
            for issue in issues:
                content += f"- **{issue['project']}**: {issue['issue']}\n"
        else:
            content += "- Brak problemów\n"
        content += "\n"
        
        # Sekcja: Analiza
        content += "## 📊 Analiza\n\n"
        if time_data:
            content += f"- **Czas całkowity**: {round(total_time / 3600, 2)} godz.\n"
            if project_stats:
                content += "- **Czas per projekt**:\n"
                for project, stats in project_stats.items():
                    content += f"  - {project}: {stats['time']} godz. ({stats['tasks']} zadań)\n"
        content += "\n"
        
        # Sekcja: Ocena pracy (Work Detection V5)
        content += "## 🧠 Ocena pracy\n\n"
        if work_data:
            status_icon = {"REAL_WORK": "✅", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(work_data.get("overall_status", ""), "?")
            content += f"**Status ogólny:** {status_icon} {work_data.get('overall_status', 'N/A')}\n"
            content += f"**Wynik:** {work_data.get('overall_score', 0)} pkt.\n\n"
            
            for project_name, project_work in work_data.get("projects", {}).items():
                icon = {"REAL_WORK": "✅", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(project_work.get("status", ""), "?")
                content += f"- {icon} **{project_name}**: {project_work.get('status', 'N/A')}\n"
                if project_work.get("details"):
                    for detail in project_work["details"]:
                        content += f"  - {detail}\n"
                if project_work.get("stagnation_days", 0) >= 2:
                    content += f"  - ⚠️ Stagnacja: {project_work['stagnation_days']} dni bez postępu\n"
            content += "\n"
        else:
            content += "Brak danych\n\n"
        
        # Sekcja: Focus (Guidance)
        if focus_task:
            project = focus_task.get("project", "N/A")
            task = focus_task.get("task", "Brak zadania")
            priority = focus_task.get("priority", "LOW")
            priority_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            
            content += "## 🎯 Focus na dziś\n\n"
            content += f"{priority_icon} **[{project}]** {task}\n\n"
            
            if focus_message:
                content += "## ⚠️ Komunikat systemu\n\n"
                content += f"{focus_message}\n\n"
        else:
            content += "## 🎯 Focus na dziś\n\n"
            content += "Brak aktywnych zadań.\n\n"
        
        # Sekcja: ⏱ Status zadania (CompletionGuard V6.2)
        if completion_data:
            content += "---\n\n"
            content += "## ⏱ Status zadania\n\n"
            
            focus_t = completion_data.get("focus_task", {})
            cycles = completion_data.get("cycles_without_progress", 0)
            status = completion_data.get("status", "OK")
            message = completion_data.get("message")
            last_completed = completion_data.get("last_completed_task")
            last_completed_at = completion_data.get("last_completed_at")
            
            if focus_t:
                content += f"**Focus:** `[{focus_t.get('project', 'N/A')}] {focus_t.get('task', 'Brak')}`\n\n"
            
            status_icon = {"OK": "🟢", "WARNING": "🟡", "CRITICAL": "🔴", "DONE": "✅"}.get(status, "⚪")
            content += f"**Status:** {status_icon} {status}\n"
            
            if cycles > 0:
                content += f"**Cykle bez postępu:** {cycles}\n"
            
            if message:
                content += f"\n**Komunikat:** _{message}_\n"
            
            if last_completed:
                content += f"\n**Ostatni zamknięty:** `{last_completed}`"
                if last_completed_at:
                    try:
                        completed_time = datetime.fromisoformat(last_completed_at)
                        hours_ago = (datetime.now() - completed_time).total_seconds() / 3600
                        content += f" ({hours_ago:.1f}h temu)"
                    except:
                        pass
                content += "\n"
            
            content += "\n"
        
        # Sekcja: Wnioski
        content += "## 🧠 Wnioski\n\n"
        content += "### Co poszło dobrze:\n"
        content += "- \n\n"
        content += "### Co można poprawić:\n"
        content += "- \n\n"
        content += "### Plan na jutro:\n"
        content += "- Skup się na zadaniach HIGH\n"
        content += "\n"
        
        content += "---\n"
        content += f"*Wygenerowane przez Development Assistant V4 - {datetime.now().strftime('%H:%M')}*\n"
        
        return content, date_str

    def generate_report(self, projects, issues, tasks, stagnation_report, trends_data=None, time_data=None, work_data=None, focus_task=None, focus_message=None, completion_data=None):
        """Kompletna generacja raportu."""
        md_content, date_str = self.generate_readable_report(projects, issues, tasks, stagnation_report, trends_data, time_data, work_data, focus_task, focus_message, completion_data=completion_data)
        
        # Zapisz w nowej lokalizacji Daily/
        daily_file = os.path.join(self.daily_path, f"{date_str}.md")
        with open(daily_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Generowanie wykresów statycznych (matplotlib)
        chart_file = self.generate_charts(tasks, date_str)
        
        # Generowanie dashboardu Markdown
        dashboard_content = self.generate_markdown_dashboard(work_data, time_data, tasks)
        dashboard_file = self.save_dashboard(dashboard_content, date_str)
        
        # Dodaj odnośnik do lekcji
        lesson_file = os.path.join(OBSIDIAN_PATH, "lessons", f"{date_str}_lekcja.md")
        
        return {
            "daily_path": daily_file,
            "date": date_str,
            "chart_path": chart_file,
            "dashboard_path": dashboard_file,
            "lesson_path": lesson_file if os.path.exists(lesson_file) else None
        }

    def generate_markdown_dashboard(self, work_data, time_data=None, tasks=None):
        """Generuje dashboard w formacie Markdown (bez zewnętrznych bibliotek)."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        content = f"# 📊 Dashboard - {date_str}\n\n"
        content += "---\n\n"
        
        # Status ogólny
        if work_data:
            status = work_data.get("overall_status", "N/A")
            score = work_data.get("overall_score", 0)
            status_icon = {"REAL_WORK": "✅", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(status, "⚪")
            
            content += "## 📈 Status pracy\n\n"
            content += f"| Metryka | Wartość |\n"
            content += f"|---------|----------|\n"
            content += f"| Status | {status_icon} {status} |\n"
            content += f"| Wynik | {score} pkt. |\n\n"
        
        # Projekty
        if work_data and "projects" in work_data:
            content += "## 📁 Projekty\n\n"
            content += "| Projekt | Status | Dni stagnacji | Pliki |\n"
            content += "|---------|--------|---------------|-------|\n"
            
            for name, data in work_data["projects"].items():
                icon = {"REAL_WORK": "✅", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(data.get("status", ""), "⚪")
                stagnation = data.get("stagnation_days", 0)
                new_files = data.get("new_files", 0)
                content += f"| {name} | {icon} {data.get('status', 'N/A')} | {stagnation} | {new_files} |\n"
            content += "\n"
        
        # Taski
        if tasks:
            by_priority = {"HIGH": [], "MEDIUM": [], "LOW": []}
            for t in tasks:
                p = t.get("priority", "LOW")
                if p in by_priority:
                    by_priority[p].append(t)
            
            content += "## ✅ Taski\n\n"
            
            for priority, icon in [("HIGH", "🔴"), ("MEDIUM", "🟡"), ("LOW", "🟢")]:
                if by_priority[priority]:
                    content += f"### {icon} {priority}\n\n"
                    for t in by_priority[priority]:
                        content += f"- [{t.get('project', 'N/A')}] {t.get('task', 'Brak')}\n"
                    content += "\n"
        
        # Time tracking
        if time_data:
            content += "## ⏱️ Czas pracy\n\n"
            content += "| Projekt | Czas (godz.) |\n"
            content += "|---------|----------------|\n"
            
            total = 0
            for project, seconds in time_data.items():
                hours = round(seconds / 3600, 2)
                total += hours
                content += f"| {project} | {hours} |\n"
            
            content += f"| **RAZEM** | **{total}** |\n\n"
        
        # Trend
        content += "---\n"
        content += f"*Dashboard wygenerowany: {datetime.now().strftime('%H:%M')}*\n"
        
        return content
    
    def save_dashboard(self, dashboard_content, date_str=None):
        """Zapisuje dashboard do pliku."""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        dashboard_path = os.path.join(self.daily_path, f"{date_str}_dashboard.md")
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        return dashboard_path

if __name__ == "__main__":
    reporter = Reporter()
    
    # Test danych
    mock_projects = [{"name": "towarzysz", "new_files": []}, {"name": "scraper_1", "new_files": ["src/new.py"]}]
    mock_issues = [{"project": "towarzysz", "issue": "Brak src/", "priority": "HIGH"}]
    mock_tasks = [{"project": "towarzysz", "task": "Utwórz src/", "priority": "HIGH"}]
    mock_stagnation = []
    
    result = reporter.generate_report(mock_projects, mock_issues, mock_tasks, mock_stagnation)
    
    print(f"Raport zapisany:")
    print(f" - Lokalnie: {result['local_path']}")
    print(f" - Obsidian: {result['obsidian_path']}")