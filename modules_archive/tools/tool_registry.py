import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


class ToolRegistry:
    def __init__(self, tools_path=None, memory_path="memory"):
        self.tools_path = tools_path or "workspace/tools"
        self.memory_path = memory_path
        self.registry_file = os.path.join(memory_path, "decisions", "tool_registry.json")
        self._ensure_registry()

    def _ensure_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        if not os.path.exists(self.registry_file):
            self._save_registry({})

    def _load_registry(self):
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_registry(self, registry):
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

    def scan_tools(self):
        registry = self._load_registry()
        
        if not os.path.exists(self.tools_path):
            return registry

        for root, dirs, files in os.walk(self.tools_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.tools_path)
                
                if file.endswith(('.py', '.sh', '.js', '.ts')):
                    tool_id = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '').replace('.sh', '')
                    
                    if tool_id not in registry:
                        registry[tool_id] = {
                            "path": file_path,
                            "type": self._detect_type(file),
                            "description": self._generate_description(file_path),
                            "last_used": None,
                            "use_count": 0,
                            "added": datetime.now().isoformat()
                        }
                    else:
                        registry[tool_id]["description"] = self._generate_description(file_path)

        self._save_registry(registry)
        return registry

    def _detect_type(self, filename):
        if filename.endswith('.py'):
            return "python"
        elif filename.endswith('.sh'):
            return "shell"
        elif filename.endswith('.js'):
            return "javascript"
        elif filename.endswith('.ts'):
            return "typescript"
        return "unknown"

    def _generate_description(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read(500)
                if '# Description:' in content:
                    start = content.find('# Description:') + 14
                    end = content.find('\n', start)
                    return content[start:end].strip()
                elif '"""' in content:
                    start = content.find('"""') + 3
                    end = content.find('"""', start)
                    if end > start:
                        return content[start:end].strip()[:100]
        except:
            pass
        return "Brak opisu"

    def get_tools(self, tool_type=None):
        registry = self._load_registry()
        if tool_type:
            return {k: v for k, v in registry.items() if v.get('type') == tool_type}
        return registry

    def get_tool(self, tool_id):
        registry = self._load_registry()
        return registry.get(tool_id)

    def record_usage(self, tool_id):
        registry = self._load_registry()
        if tool_id in registry:
            registry[tool_id]['last_used'] = datetime.now().isoformat()
            registry[tool_id]['use_count'] = registry[tool_id].get('use_count', 0) + 1
            self._save_registry(registry)

    def suggest_tool_for_task(self, task_description):
        registry = self._load_registry()
        task_lower = task_description.lower()
        suggestions = []

        keywords = {
            'test': ['test', 'pytest'],
            'build': ['build', 'compile'],
            'deploy': ['deploy', 'push'],
            'analyze': ['analyze', 'parse'],
            'backup': ['backup', 'save'],
            'lint': ['lint', 'format', 'check']
        }

        for keyword, tool_ids in keywords.items():
            if keyword in task_lower:
                for tool_id in tool_ids:
                    if tool_id in registry:
                        suggestions.append(registry[tool_id])

        return suggestions[:5]

    def get_most_used(self, limit=5):
        registry = self._load_registry()
        sorted_tools = sorted(registry.items(), key=lambda x: x[1].get('use_count', 0), reverse=True)
        return [tool for _, tool in sorted_tools[:limit]]

    def format_tool_list(self):
        registry = self._load_registry()
        if not registry:
            return "Brak zarejestrowanych narzędzi."

        lines = ["## Dostępne narzędzia\n"]
        for tool_id, tool in sorted(registry.items()):
            lines.append(f"- **{tool_id}** ({tool.get('type', '?')})")
            lines.append(f"  - {tool.get('description', 'Brak opisu')}")
            if tool.get('use_count', 0) > 0:
                lines.append(f"  - Używany {tool.get('use_count')} razy")
            lines.append("")

        return "\n".join(lines)

    def execute_tool_suggestion(self, tool_id, args=None):
        tool = self.get_tool(tool_id)
        if not tool:
            return {"success": False, "error": "Narzędzie nie znalezione"}

        if not os.path.exists(tool['path']):
            return {"success": False, "error": "Plik nie istnieje"}

        return {
            "success": True,
            "tool": tool_id,
            "path": tool['path'],
            "command": f"# Uruchom ręcznie:\n# {tool['type']} {tool['path']}",
            "note": "Executor Lite - tylko sugestia. Uruchom ręcznie jeśli chcesz."
        }
