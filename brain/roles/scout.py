"""
brain/roles/scout.py - Scout Role
Zbiera informacje z projektów i środowiska
"""

import os
import hashlib
from datetime import datetime


class Scout:
    """Scout - zbiera informacje, skanuje, wykrywa zmiany."""
    
    def __init__(self, projects_path="workspace/projects", agent_path="."):
        self.projects_path = projects_path
        self.agent_path = agent_path
        self.last_state = {}
    
    def scout(self, focus_on_agent=True):
        """
        Przeprowadza zwiad - zbiera informacje.
        
        Args:
            focus_on_agent: Czy skupić się na kodzie agenta
            
        Returns:
            dict: Raport ze zwiadu
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "scout_role": "Scout",
            "findings": {}
        }
        
        if focus_on_agent:
            report["findings"]["agent"] = self._scout_agent()
            report["findings"]["projects"] = self._scout_projects()
        else:
            report["findings"]["projects"] = self._scout_projects()
        
        report["changes_detected"] = self._detect_changes(report)
        
        return report
    
    def _scout_agent(self):
        """Zwiad własnego kodu agenta."""
        skip_dirs = {'__pycache__', '.git', 'venv', '.venv', 'env', 'tor_env', 
                    'modules_archive', 'modules', 'workspace', 'system', 'reports'}
        
        files = []
        total_lines = 0
        
        for root, dirs, filenames in os.walk(self.agent_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            for f in filenames:
                if f.endswith('.py') and not f.startswith('.'):
                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as fp:
                            content = fp.read()
                            lines = len(content.splitlines())
                            total_lines += lines
                            
                        files.append({
                            "name": f,
                            "path": os.path.relpath(file_path, self.agent_path),
                            "lines": lines,
                            "hash": hashlib.md5(content.encode()).hexdigest()[:8],
                            "modified": os.path.getmtime(file_path)
                        })
                    except:
                        pass
        
        return {
            "files_count": len(files),
            "total_lines": total_lines,
            "files": files
        }
    
    def _scout_projects(self):
        """Zwiad projektów użytkownika."""
        if not os.path.exists(self.projects_path):
            return {"projects": []}
        
        projects = []
        for name in os.listdir(self.projects_path):
            project_path = os.path.join(self.projects_path, name)
            if os.path.isdir(project_path):
                projects.append({
                    "name": name,
                    "path": project_path,
                    "exists": True
                })
        
        return {"projects": projects}
    
    def _detect_changes(self, report):
        """Wykrywa zmiany od ostatniego zwiadu."""
        changes = []
        
        agent_data = report.get("findings", {}).get("agent", {})
        current_files = {f["path"]: f for f in agent_data.get("files", [])}
        
        if self.last_state:
            last_files = self.last_state.get("agent_files", {})
            
            for path, current in current_files.items():
                if path not in last_files:
                    changes.append({"type": "new_file", "path": path})
                elif current.get("hash") != last_files.get(path, {}).get("hash"):
                    changes.append({"type": "modified_file", "path": path})
        
        self.last_state = {
            "timestamp": report.get("timestamp"),
            "agent_files": current_files
        }
        
        return changes
    
    def get_file_content(self, file_path):
        """Pobiera zawartość pliku."""
        full_path = os.path.join(self.agent_path, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
        return None
