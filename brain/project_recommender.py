"""
brain/project_recommender.py - Rekomendacje dla projektów
Generuje automatyczne rekomendacje na podstawie postępów
"""

from datetime import datetime


class ProjectRecommender:
    """Generuje rekomendacje dla projektów."""
    
    def __init__(self):
        self.recommendations = []
    
    def generate_recommendations(self, projects_progress):
        """Generuje rekomendacje dla wszystkich projektów."""
        self.recommendations = []
        
        for progress in projects_progress:
            recs = self._analyze_project(progress)
            if recs:
                self.recommendations.extend(recs)
        
        self._sort_by_priority()
        return self.recommendations
    
    def _analyze_project(self, progress):
        """Analizuje pojedynczy projekt i generuje rekomendacje."""
        recommendations = []
        name = progress.get("name")
        status = progress.get("status")
        git = progress.get("git_metrics", {})
        activity = progress.get("activity_metrics", {})
        code = progress.get("code_metrics", {})
        
        commits_7d = git.get("commits_last_7d", 0)
        days_since_edit = activity.get("days_since_edit")
        has_uncommitted = git.get("has_uncommitted", False)
        files_count = code.get("files_count", 0)
        total_lines = code.get("total_lines", 0)
        
        if status == "abandoned":
            recommendations.append({
                "project": name,
                "type": "warning",
                "priority": "HIGH",
                "title": f"⚠️ Projekt '{name}' może być porzucony",
                "description": f"Nie było edycji przez {days_since_edit} dni",
                "action": "Rozważ archiwizację lub wznowienie projektu"
            })
        
        elif status == "stagnant":
            recommendations.append({
                "project": name,
                "type": "warning",
                "priority": "MEDIUM",
                "title": f"📉 Projekt '{name}' nie jest aktywny",
                "description": f"Ostatnia edycja {days_since_edit} dni temu",
                "action": "Zaplanuj sesję pracy lub zarchiwizuj projekt"
            })
        
        if commits_7d == 0 and days_since_edit and days_since_edit < 7:
            recommendations.append({
                "project": name,
                "type": "info",
                "priority": "LOW",
                "title": f"📝 Brak commitów w '{name}'",
                "description": "Nie było commitów w ostatnim tygodniu",
                "action": "Zrób commit jeśli są nie commits"
            })
        
        if has_uncommitted:
            recommendations.append({
                "project": name,
                "type": "action",
                "priority": "HIGH",
                "title": f"🔄 Nie commits w '{name}'",
                "description": "Są nie commits zmiany w projekcie",
                "action": "Wykonaj git add i git commit"
            })
        
        if git.get("branches") and len(git.get("branches", [])) > 5:
            recommendations.append({
                "project": name,
                "type": "cleanup",
                "priority": "LOW",
                "title": f"🌿 Wiele branchy w '{name}'",
                "description": f"{len(git['branches'])} branchy - możliwy bałagan",
                "action": "Rozważ usunięcie starych branchy"
            })
        
        if files_count > 100 and commits_7d == 0:
            recommendations.append({
                "project": name,
                "type": "strategy",
                "priority": "MEDIUM",
                "title": f"📦 Duży projekt '{name}' bez aktywności",
                "description": f"{files_count} plików, {total_lines} linii kodu",
                "action": "Może potrzebuje refaktoryzacji lub podziału"
            })
        
        if commits_7d > 10:
            recommendations.append({
                "project": name,
                "type": "success",
                "priority": "INFO",
                "title": f"🚀 '{name}' bardzo aktywny",
                "description": f"{commits_7d} commitów w ostatnim tygodniu",
                "action": "Świetnie! Kontynuuj"
            })
        
        return recommendations
    
    def _sort_by_priority(self):
        """Sortuje rekomendacje według priorytetu."""
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
        self.recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "LOW"), 3))
    
    def get_summary(self):
        """Zwraca podsumowanie rekomendacji."""
        summary = {
            "total": len(self.recommendations),
            "by_priority": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
            "by_type": {},
            "urgent": [],
            "projects_affected": set()
        }
        
        for rec in self.recommendations:
            priority = rec.get("priority", "LOW")
            rec_type = rec.get("type", "unknown")
            
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
            summary["by_type"][rec_type] = summary["by_type"].get(rec_type, 0) + 1
            summary["projects_affected"].add(rec.get("project"))
            
            if priority == "HIGH":
                summary["urgent"].append(rec)
        
        summary["projects_affected"] = list(summary["projects_affected"])
        return summary
    
    def get_markdown_report(self):
        """Generuje raport w formacie Markdown."""
        if not self.recommendations:
            return "## 📊 Rekomendacje projektów\n\nBrak rekomendacji - wszystkie projekty w porządku!"
        
        md = "## 📊 Rekomendacje projektów\n\n"
        
        summary = self.get_summary()
        md += f"**Podsumowanie:** {summary['total']} rekomendacji\n"
        md += f"- 🔴 HIGH: {summary['by_priority'].get('HIGH', 0)}\n"
        md += f"- 🟡 MEDIUM: {summary['by_priority'].get('MEDIUM', 0)}\n"
        md += f"- 🟢 LOW: {summary['by_priority'].get('LOW', 0)}\n\n"
        
        if summary.get("urgent"):
            md += "### 🚨 Pilne\n\n"
            for rec in summary["urgent"]:
                md += f"- **{rec['title']}**\n"
                md += f"  - {rec['description']}\n"
                md += f"  - 💡 {rec['action']}\n\n"
        
        by_project = {}
        for rec in self.recommendations:
            proj = rec.get("project")
            if proj not in by_project:
                by_project[proj] = []
            by_project[proj].append(rec)
        
        md += "### 📁 Według projektu\n\n"
        for proj, recs in by_project.items():
            md += f"#### {proj}\n"
            for rec in recs:
                emoji = "🔴" if rec.get("priority") == "HIGH" else "🟡" if rec.get("priority") == "MEDIUM" else "🟢"
                md += f"{emoji} **{rec['title']}**\n"
                md += f"   {rec['description']}\n"
                md += f"   → {rec['action']}\n\n"
        
        return md
    
    def get_todoist_tasks(self):
        """Zwraca listę tasków do wysłania do Todoist."""
        tasks = []
        
        for rec in self.recommendations:
            if rec.get("priority") in ["HIGH", "MEDIUM"]:
                tasks.append({
                    "project": rec.get("project"),
                    "task": f"📋 {rec.get('action', 'Sprawdź projekt')}",
                    "priority": "HIGH" if rec.get("priority") == "HIGH" else "MEDIUM",
                    "type": "project_recommendation",
                    "reason": rec.get("description", ""),
                    "source": "auto_recommendation"
                })
        
        return tasks[:10]
