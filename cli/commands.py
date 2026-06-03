"""
cli/commands.py - CLI Commands dla Towarzysza
"""

import os
import sys
from datetime import datetime

sys_path = os.path.dirname(os.path.dirname(__file__))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from brain.analyzer import Analyzer
from brain.planner import Planner
from integrations.obsidian import Obsidian


class CLI:
    """Obsługa komend CLI."""
    
    COMMANDS = {
        '/intel': 'cmd_intel',
        '/focus': 'cmd_focus',
        '/status': 'cmd_status',
        '/plan': 'cmd_plan',
        '/help': 'cmd_help',
        '/now': 'cmd_now'
    }
    
    def __init__(self, config=None):
        self.config = config or {}
        self.analyzer = Analyzer()
        self.planner = Planner()
        self.obsidian = Obsidian()
    
    def parse(self, user_input):
        """Parsuje input użytkownika."""
        if not user_input:
            return None
        
        user_input = user_input.strip()
        
        if user_input.startswith('/'):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None
            
            if cmd in self.COMMANDS:
                return getattr(self, self.COMMANDS[cmd])(args)
            else:
                return {"error": f"Nieznana komenda: {cmd}. Użyj /help"}
        
        return self.handle_status_input(user_input)
    
    def cmd_intel(self, args):
        """Generuje Project Intelligence dla projektu."""
        if not args:
            return {"error": "Użycie: /intel <projekt>"}
        
        project_name = args.strip()
        projects, _ = self.analyzer.scan_projects()
        
        target = None
        for p in projects:
            if p["name"].lower() == project_name.lower():
                target = p
                break
        
        if not target:
            return {"error": f"Projekt '{project_name}' nie znaleziony"}
        
        intel = self.analyzer.get_project_intelligence(target)
        filename = self.obsidian.save_project_intelligence(intel)
        
        return {
            "success": True,
            "message": f"Project Intelligence wygenerowane: {filename}",
            "project": target["name"]
        }
    
    def cmd_focus(self, args):
        """Pokazuje aktualny focus."""
        focus = self.planner.get_today_focus()
        
        if not focus:
            return {"message": "Brak focus taska na dziś."}
        
        return {
            "focus": focus.get("focus_task"),
            "message": focus.get("message"),
            "status": focus.get("status")
        }
    
    def cmd_status(self, args):
        """Pokazuje status systemu."""
        projects, _ = self.analyzer.scan_projects()
        work_data = self.analyzer.evaluate_work(projects)
        
        status_icon = {"REAL_WORK": "🟢", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}
        
        output = {
            "overall_status": work_data.get("overall_status"),
            "overall_score": work_data.get("overall_score"),
            "projects": []
        }
        
        for name, data in work_data.get("projects", {}).items():
            icon = status_icon.get(data.get("status"), "⚪")
            output["projects"].append({
                "name": name,
                "status": data.get("status"),
                "score": data.get("score"),
                "icon": icon
            })
        
        return output
    
    def cmd_plan(self, args):
        """Pokazuje plan na dziś."""
        projects, _ = self.analyzer.scan_projects()
        issues = self.analyzer.detect_issues(projects)
        tasks = self.planner.create_tomorrow_plan(projects, issues)
        
        if not tasks:
            return {"message": "Brak tasków na dziś."}
        
        return {"tasks": tasks, "count": len(tasks)}
    
    def cmd_now(self, args):
        """Pokazuje co teraz."""
        projects, _ = self.analyzer.scan_projects()
        issues = self.analyzer.detect_issues(projects)
        work_data = self.analyzer.evaluate_work(projects)
        tasks = self.planner.create_tomorrow_plan(projects, issues)
        focus = self.planner.select_focus_task(tasks)
        
        return {
            "time": datetime.now().strftime("%H:%M"),
            "status": work_data.get("overall_status"),
            "focus": focus,
            "projects_count": len(projects),
            "tasks_count": len(tasks)
        }
    
    def cmd_help(self, args):
        """Pokazuje help."""
        return {
            "commands": {
                "/intel <projekt>": "Generuj Project Intelligence",
                "/focus": "Pokaż aktualny focus",
                "/status": "Status systemu i projektów",
                "/plan": "Plan na dziś",
                "/now": "Co teraz?",
                "/help": "Ta pomoc"
            }
        }
    
    def handle_status_input(self, user_input):
        """Obsługuje odpowiedzi bez komend (done, working, etc.)."""
        status_map = {
            'done': 'done',
            'working': 'working', 
            'blocked': 'blocked',
            'skip': 'skip'
        }
        
        if user_input.lower() in status_map:
            return {"status_update": status_map[user_input.lower()]}
        
        return {"note": f"Użyj /help dla listy komend"}
    
    def format_output(self, result):
        """Formatuje wynik do wyświetlenia."""
        if not result:
            return ""
        
        if result.get("error"):
            return f"❌ {result['error']}"
        
        if result.get("success"):
            return f"✅ {result['message']}"
        
        if result.get("message"):
            return result["message"]
        
        lines = []
        
        if result.get("overall_status"):
            icon = {"REAL_WORK": "🟢", "LOW_PROGRESS": "🟡", "STAGNATION": "🔴"}.get(result["overall_status"], "⚪")
            lines.append(f"Status: {icon} {result['overall_status']} (score: {result.get('overall_score', 0)})")
        
        if result.get("projects"):
            lines.append("\nProjekty:")
            for p in result["projects"]:
                lines.append(f"  {p['icon']} {p['name']}: {p['status']} ({p['score']} pkt)")
        
        if result.get("focus"):
            focus = result["focus"]
            lines.append(f"\n🎯 Focus: [{focus.get('project', '')}] {focus.get('task', '')}")
        
        if result.get("tasks"):
            lines.append(f"\n📋 Plan ({result['count']} tasków):")
            for i, t in enumerate(result["tasks"][:5], 1):
                icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(t.get("priority", "LOW"), "⚪")
                lines.append(f"  {i}. {icon} [{t.get('project', '')}] {t.get('task', '')}")
        
        if result.get("time"):
            lines.append(f"\n⏰ {result['time']}")
        
        if result.get("commands"):
            lines.append("\n📖 Dostępne komendy:")
            for cmd, desc in result["commands"].items():
                lines.append(f"  {cmd:<20} - {desc}")
        
        return "\n".join(lines)
