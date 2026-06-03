"""
tools/registry.py - Tool Registry
Rejestr wszystkich dostępnych narzędzi
"""

from datetime import datetime


class ToolRegistry:
    """Rejestr narzędzi - zarządza wszystkimi dostępnymi narzędziami."""
    
    def __init__(self):
        self.tools = {}
        self.usage_log = []
    
    def register(self, name, tool):
        """
        Rejestruje narzędzie.
        
        Args:
            name: Nazwa narzędzia
            tool: Instancja narzędzia
        """
        self.tools[name] = tool
        print(f"[TOOL_REGISTRY] Zarejestrowano: {name}")
    
    def register_all(self):
        """Rejestruje wszystkie wbudowane narzędzia."""
        from .file_tools import FileTools
        from .bash_tools import BashTools
        from .search_tools import SearchTools
        from .git_tools import GitTools
        
        self.register("file_read", FileTools().read)
        self.register("file_write", FileTools().write)
        self.register("file_edit", FileTools().edit)
        self.register("bash_run", BashTools().run)
        self.register("python_run", BashTools().run_python)
        self.register("grep", SearchTools().grep)
        self.register("git_status", GitTools().status)
        self.register("git_commit", GitTools().commit)
        self.register("git_add", GitTools().add)
        
        print(f"[TOOL_REGISTRY] Zarejestrowano {len(self.tools)} narzędzi")
    
    def get(self, name):
        """Pobiera narzędzie po nazwie."""
        return self.tools.get(name)
    
    def list_tools(self):
        """Zwraca listę wszystkich narzędzi."""
        return list(self.tools.keys())
    
    def log_usage(self, tool_name, args, result):
        """Loguje użycie narzędzia."""
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": str(args)[:100],
            "success": result.get("success", False)
        })
        
        if len(self.usage_log) > 1000:
            self.usage_log = self.usage_log[-500:]
    
    def get_usage_stats(self):
        """Zwraca statystyki użycia narzędzi."""
        stats = {}
        for entry in self.usage_log:
            tool = entry["tool"]
            if tool not in stats:
                stats[tool] = {"total": 0, "success": 0}
            stats[tool]["total"] += 1
            if entry["success"]:
                stats[tool]["success"] += 1
        
        return stats
