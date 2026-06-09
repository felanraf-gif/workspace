"""
brain/analyzer.py - Inteligentna analiza projektów v8
Rozszerzona analiza kodu: AST, TODO/FIXME, secrets, metryki złożoności
"""

import os
import re
import ast
import json
import hashlib
import requests
from datetime import datetime, timedelta
from core.config import PROJECTS_PATH, MEMORY_PATH, TODOIST_API_TOKEN, INTEGRATE_TODOIST, STAGNATION_DAYS
from brain.code_graph import DependencyGraph


class Analyzer:
    """Inteligentna analiza projektów - czyta zawartość plików, nie tylko nazwy."""
    
    REAL_WORK = "REAL_WORK"
    LOW_PROGRESS = "LOW_PROGRESS"
    STAGNATION = "STAGNATION"
    
    PROJECT_TYPES = {
        "agent": {
            "keywords": ["brain", "analyzer", "planner", "assistant", "memory", "integrations"],
            "indicators": ["class Analyzer", "class Planner", "class Assistant", "class Memory"],
            "architecture": "AI Agent"
        },
        "cli": {
            "keywords": ["click", "typer", "argparse", "docopt"],
            "indicators": ["@click.command", "@cli.command", "def cli(", "argparse.ArgumentParser"],
            "architecture": "CLI Tool"
        },
        "web_api": {
            "keywords": ["fastapi", "flask", "django", "bottle", "starlette"],
            "indicators": ["@app.route", "@router", "@api", "app = FastAPI()", "app = Flask("],
            "architecture": "REST API"
        },
        "scraper": {
            "keywords": ["beautifulsoup", "scrapy", "selenium", "playwright"],
            "indicators": ["BeautifulSoup", "scrapy", "webdriver", "soup.find("],
            "architecture": "Web Scraper"
        },
        "ai_ml": {
            "keywords": ["torch", "tensorflow", "sklearn", "transformers", "openai", "langchain"],
            "indicators": ["import torch", "from transformers", "sklearn", "OpenAI(", "model("],
            "architecture": "AI/ML"
        },
        "bot": {
            "keywords": ["telegram", "discord", "slackclient", "telebot", "aiogram"],
            "indicators": ["Bot(", "client.run", "dispatcher", "bot.polling"],
            "architecture": "Bot"
        },
        "automation": {
            "keywords": ["schedule", "apscheduler", "cron", "celery"],
            "indicators": ["schedule.every", "celery", "BackgroundScheduler"],
            "architecture": "Automation"
        }
    }
    
    def __init__(self):
        self.projects_path = PROJECTS_PATH
        self.decisions_path = os.path.join(MEMORY_PATH, "decisions")
        self.state_file = os.path.join(MEMORY_PATH, "analyzer_state.json")
        self.work_history_file = os.path.join(self.decisions_path, "work_history.json")
        self.sync_api_url = "https://api.todoist.com/sync/v9"
        self.headers = {
            "Authorization": f"Bearer {TODOIST_API_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def analyze_agent_code(self):
        """Analizuje własny kod agenta (brain/, core/, integrations/)."""
        project = self._scan_agent_files()
        
        if not project or not project.get("files"):
            return None
        
        structure = self.analyze_project_structure(project)
        project["structure"] = structure
        
        issues = self._analyze_project_deep(project)
        project["issues"] = issues
        
        architecture = self.generate_architecture_proposal(project)
        project["architecture"] = architecture
        
        roadmap = self.create_roadmap(project, architecture)
        project["roadmap"] = roadmap
        
        summary = self._generate_summary(project, structure, architecture, roadmap, issues)
        
        return {
            "project": project["name"],
            "structure": structure,
            "architecture": architecture,
            "roadmap": roadmap,
            "issues": issues,
            "summary": summary
        }
    
    def _scan_agent_files(self):
        """Skanuje pliki własne agenta."""
        import sys
        agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        project = {
            "name": "towarzysz_agent",
            "path": agent_dir,
            "files": [],
            "new_files": [],
            "changed_files": []
        }
        
        skip_dirs = {'__pycache__', '.git', 'venv', '.venv', 'env', 'tor_env', 'modules_archive', 'modules', 'workspace', 'system', 'reports', 'node_modules', '.tox'}
        
        skip_files = {'.env', '.env.local', '.env.secret', '.env.production'}
        
        for root, dirs, files in os.walk(agent_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            for f in files:
                if f.endswith('.py') and not f.startswith('.') and f not in skip_files:
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, agent_dir)
                    project["files"].append({
                        "name": f,
                        "path": rel_path,
                        "full_path": file_path,
                        "hash": "analyzed",
                        "type": "file"
                    })
        
        return project

    def scan_projects(self):
        """Skanuje projekty i wykrywa nowe/zmienione pliki."""
        projects = []
        previous_state = self._load_state()
        current_state = {}

        if not os.path.exists(self.projects_path):
            return projects, []

        for project_name in os.listdir(self.projects_path):
            project_dir = os.path.join(self.projects_path, project_name)
            if os.path.isdir(project_dir):
                project_info = {
                    "name": project_name,
                    "path": project_dir,
                    "files": [],
                    "new_files": [],
                    "changed_files": []
                }
                
                for root, dirs, files in os.walk(project_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        if file.startswith('.') or file in {'.env', '.env.local', '.env.secret'}:
                            continue
                        
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_dir)
                        file_hash = self._get_hash(file_path)
                        
                        project_info["files"].append({
                            "name": file,
                            "path": rel_path,
                            "full_path": file_path,
                            "hash": file_hash,
                            "type": "file"
                        })
                        
                        prev_hash = previous_state.get(project_name, {}).get(rel_path)
                        if prev_hash:
                            if prev_hash != file_hash:
                                project_info["changed_files"].append(rel_path)
                        else:
                            project_info["new_files"].append(rel_path)
                        
                        if project_name not in current_state:
                            current_state[project_name] = {}
                        current_state[project_name][rel_path] = file_hash

                projects.append(project_info)

        self._save_state(current_state)
        return projects, previous_state

    def detect_issues(self, projects):
        """Inteligentne wykrywanie problemów - ANALIZUJE ZAWARTOŚĆ PLIKÓW."""
        issues = []
        
        for project in projects:
            project_issues = self._analyze_project_deep(project)
            issues.extend(project_issues)
        
        return issues
    
    def _analyze_project_deep(self, project):
        """Głęboka analiza projektu - czyta pliki i wykrywa problemy."""
        issues = []
        project_name = project["name"]
        files = project.get("files", [])
        
        if not files:
            issues.append({
                "project": project_name,
                "issue": "Projekt jest pusty - brak plików",
                "priority": "HIGH",
                "type": "structure",
                "impact": "Nie można zbudować produktu bez kodu"
            })
            return issues
        
        all_imports = []
        all_todos = []
        all_secrets = []
        all_long_functions = []
        python_files = []
        
        for f in files:
            if f["name"].endswith(".py"):
                file_issues = self._analyze_python_file(f, project_name)
                issues.extend(file_issues.get("issues", []))
                all_imports.extend(file_issues.get("imports", []))
                all_todos.extend(file_issues.get("todos", []))
                all_secrets.extend(file_issues.get("secrets", []))
                all_long_functions.extend(file_issues.get("long_functions", []))
                python_files.append(f["path"])
            elif f["name"].endswith((".js", ".ts", ".jsx", ".tsx")):
                file_issues = self._analyze_js_file(f, project_name)
                issues.extend(file_issues.get("issues", []))
                all_todos.extend(file_issues.get("todos", []))
                all_secrets.extend(file_issues.get("secrets", []))
        
        project_type = self._detect_project_type(all_imports)
        if project_type:
            issues.append({
                "project": project_name,
                "issue": f"Wykryto typ projektu: {project_type['architecture']}",
                "priority": "INFO",
                "type": "metadata",
                "details": project_type
            })
        
        if all_todos:
            unique_todos = {t["content"]: t for t in all_todos}.values()
            issues.append({
                "project": project_name,
                "issue": f"Znaleziono {len(unique_todos)} TODO/FIXME/BUG do zrobienia",
                "priority": "MEDIUM",
                "type": "technical_debt",
                "todos": list(unique_todos)[:10]
            })
        
        if all_secrets:
            issues.append({
                "project": project_name,
                "issue": f"⚠️ POTENCJALNE BEZPIECZEŃSTWO: {len(all_secrets)} possible hardcoded secrets",
                "priority": "HIGH",
                "type": "security",
                "secrets": all_secrets[:5]
            })
        
        if all_long_functions:
            issues.append({
                "project": project_name,
                "issue": f"Znaleziono {len(all_long_functions)} długich funkcji wymagających refaktoryzacji",
                "priority": "LOW",
                "type": "code_quality",
                "functions": all_long_functions[:5]
            })
        
        if python_files and not self._has_entry_point(python_files):
            issues.append({
                "project": project_name,
                "issue": "Brak punktu wejścia (main.py, app.py, cli.py)",
                "priority": "MEDIUM",
                "type": "structure"
            })

        if python_files:
            dg = DependencyGraph()
            dg_result = dg.build(project)

            for dead in dg_result["dead_code"]:
                issues.append({
                    "project": project_name,
                    "issue": f"Martwy kod: {dead['file']} — {dead['reason']}",
                    "priority": "MEDIUM",
                    "type": "dependency",
                    "file": dead["file"]
                })

            for cycle in dg_result["cycles"]:
                path = " → ".join(cycle)
                issues.append({
                    "project": project_name,
                    "issue": f"Cykliczna zależność: {path}",
                    "priority": "HIGH",
                    "type": "dependency",
                    "cycle": cycle
                })

            for hi in dg_result["high_impact"][:3]:
                issues.append({
                    "project": project_name,
                    "issue": f"Wysoki wpływ: {hi['file']} — używany w {hi['dependant_count']} plikach",
                    "priority": "INFO",
                    "type": "dependency",
                    "file": hi["file"],
                    "dependant_count": hi["dependant_count"]
                })

        return issues
    
    def _analyze_python_file(self, file_info, project_name):
        """Analizuje pojedynczy plik Python - AST parsing."""
        result = {
            "issues": [],
            "imports": [],
            "todos": [],
            "secrets": [],
            "long_functions": []
        }
        
        try:
            with open(file_info["full_path"], 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return result
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result["issues"].append({
                "project": project_name,
                "issue": f"BŁĄD SKŁADNI: {file_info['path']} - plik nie kompiluje się!",
                "priority": "HIGH",
                "type": "syntax_error"
            })
            return result
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result["imports"].append(node.module)
        
        result["imports"].extend(self._find_string_imports(content))
        
        todos = re.findall(r'#\s*(TODO|FIXME|BUG|HACK|XXX|NOTE):?\s*(.*)', content, re.IGNORECASE)
        for marker, desc in todos:
            result["todos"].append({
                "file": file_info["path"],
                "type": marker.upper(),
                "content": desc.strip() if desc.strip() else "Brak opisu"
            })
        
        secret_patterns = [
            (r'["\']api[_-]?key["\']\s*[:=]\s*["\'][^"\']+["\']', "API Key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Secret"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Token"),
            (r'bearer\s+[a-zA-Z0-9]{32,}', "Bearer Token"),
            (r'github\.com/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@', "Git credentials"),
        ]
        
        for pattern, secret_type in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                result["secrets"].append({
                    "file": file_info["path"],
                    "type": secret_type,
                    "preview": f"<{secret_type}>"
                })
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 1
                if func_lines > 50:
                    result["long_functions"].append({
                        "file": file_info["path"],
                        "function": node.name,
                        "lines": func_lines
                    })
        
        return result
    
    def _find_string_imports(self, content):
        """Znajduje importy w stringach (np. dynamic imports)."""
        imports = []
        patterns = [
            r'__import__\([\'"]([^\'"]+)[\'"]\)',
            r'from\s+([a-zA-Z0-9_\.]+)\s+import',
            r'import\s+([a-zA-Z0-9_\.]+)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        return imports
    
    def _analyze_js_file(self, file_info, project_name):
        """Analizuje plik JavaScript/TypeScript."""
        result = {
            "issues": [],
            "todos": [],
            "secrets": []
        }
        
        try:
            with open(file_info["full_path"], 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return result
        
        todos = re.findall(r'//\s*(TODO|FIXME|BUG|HACK):?\s*(.*)', content, re.IGNORECASE)
        for marker, desc in todos:
            result["todos"].append({
                "file": file_info["path"],
                "type": marker.upper(),
                "content": desc.strip() if desc.strip() else "Brak opisu"
            })
        
        secret_patterns = [
            (r'apiKey\s*[=:]\s*["\'][^"\']+["\']', "API Key"),
            (r'password\s*[=:]\s*["\'][^"\']+["\']', "Password"),
            (r'process\.env\.[A-Z_]+', "Env variable"),
        ]
        
        for pattern, secret_type in secret_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                result["secrets"].append({
                    "file": file_info["path"],
                    "type": secret_type,
                    "preview": f"<{secret_type}>"
                })
        
        return result
    
    def _detect_project_type(self, imports):
        """Wykrywa typ projektu na podstawie importów."""
        imports_lower = [i.lower() for i in imports]
        
        for ptype, config in self.PROJECT_TYPES.items():
            for keyword in config["keywords"]:
                for imp in imports_lower:
                    if keyword in imp:
                        return {
                            "type": ptype,
                            "architecture": config["architecture"],
                            "matched_keyword": keyword
                        }
        
        return None
    
    def _has_entry_point(self, python_files):
        """Sprawdza czy projekt ma punkt wejścia."""
        entry_points = ["main.py", "app.py", "cli.py", "__main__.py", "run.py", "bot.py", "server.py"]
        for pf in python_files:
            if pf in entry_points:
                return True
            for ep in entry_points:
                if pf.endswith(f"src/{ep}") or pf.endswith(f"/src/{ep}"):
                    return True
        return False

    def evaluate_work(self, projects):
        """Ocenia pracę we wszystkich projektach."""
        completed_tasks = self._get_todoist_completed()
        overall_score = 0
        results = {}

        for project in projects:
            name = project["name"]
            score = self._calculate_project_score(project, completed_tasks, name)
            stagnation_days = self._get_stagnation_days(name)
            
            if stagnation_days >= STAGNATION_DAYS:
                score = max(0, score - 3)
            
            status = self._get_status(score)
            overall_score += score
            
            results[name] = {
                "score": score,
                "status": status,
                "stagnation_days": stagnation_days,
                "new_files": len(project.get("new_files", [])),
                "changed_files": len(project.get("changed_files", []))
            }

        return {
            "projects": results,
            "overall_score": overall_score,
            "overall_status": self._get_status(overall_score),
            "completed_tasks": completed_tasks
        }

    def _get_hash(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_state(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f)

    def _get_todoist_completed(self, since_days=7):
        if not INTEGRATE_TODOIST:
            return []
        
        try:
            since = (datetime.now() - timedelta(days=since_days)).isoformat()
            response = requests.post(
                f"{self.sync_api_url}/completed/get_all",
                headers=self.headers,
                data=f"since={since}&limit=100",
                timeout=30
            )
            
            if response.status_code == 200:
                items = response.json().get("items", [])
                completed = []
                for item in items:
                    content = item.get("content", "")
                    if "[" in content and "]" in content:
                        start = content.find("[") + 1
                        end = content.find("]")
                        project_name = content[start:end]
                        task_desc = content[end+1:].strip()
                    else:
                        project_name = "unknown"
                        task_desc = content
                    
                    completed.append({
                        "project": project_name,
                        "task": task_desc,
                        "completed_date": item.get("completed_date")
                    })
                return completed
        except requests.exceptions.Timeout:
            print(f"[ANALYZER] Timeout połączenia z Todoist")
        except requests.exceptions.ConnectionError:
            print(f"[ANALYZER] Błąd połączenia z Todoist")
        except Exception as e:
            print(f"[ANALYZER] Błąd pobierania tasków: {e}")
        return []

    def _calculate_project_score(self, project, completed_tasks, project_name):
        score = 0
        
        new_files = len(project.get("new_files", []))
        if new_files > 0:
            score += 3
        
        total_size = sum(
            os.path.getsize(f["full_path"]) 
            for f in project.get("files", []) 
            if f.get("type") == "file"
        )
        if total_size > 500:
            score += 2
        
        project_tasks = [t for t in completed_tasks if t["project"] == project_name]
        if project_tasks:
            score += min(len(project_tasks), 2) * 3
        
        if not new_files and len(project.get("changed_files", [])) > 0 and total_size < 5000:
            score -= 1
        
        return max(0, score)

    def _get_stagnation_days(self, project_name):
        history = self._load_work_history()
        last_real_work = None
        
        for entry in reversed(history):
            if entry.get("project") == project_name and entry.get("score", 0) >= 3:
                last_real_work = datetime.fromisoformat(entry["timestamp"])
                break
        
        if not last_real_work:
            return STAGNATION_DAYS + 1
        
        return (datetime.now() - last_real_work).days

    def _get_status(self, score):
        if score >= 5:
            return self.REAL_WORK
        elif score >= 1:
            return self.LOW_PROGRESS
        return self.STAGNATION

    def _load_work_history(self):
        if os.path.exists(self.work_history_file):
            try:
                with open(self.work_history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def analyze_project_structure(self, project):
        """Analizuje strukturę projektu + wykrywa typ."""
        name = project["name"]
        files = project.get("files", [])
        
        structure = {
            "name": name,
            "directories": [],
            "file_types": {},
            "language": "unknown",
            "has_readme": False,
            "has_gitignore": False,
            "has_config": False,
            "has_tests": False,
            "is_new": len(files) < 3,
            "complexity": "simple" if len(files) < 10 else "medium" if len(files) < 50 else "complex",
            "project_type": None,
            "metrics": {
                "total_files": len(files),
                "total_lines": 0,
                "python_files": 0,
                "doc_files": 0
            }
        }
        
        for f in files:
            path = f.get("path", "")
            
            if "/" in path:
                parts = path.split("/")
                if len(parts) > 1:
                    structure["directories"].append(parts[0])
            
            ext = os.path.splitext(path)[1].lower()
            if ext:
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
            
            if "readme" in path.lower():
                structure["has_readme"] = True
            if ".gitignore" in path.lower():
                structure["has_gitignore"] = True
            if "config" in path.lower() or ".json" in path.lower() or ".yaml" in path.lower() or ".yml" in path.lower():
                structure["has_config"] = True
            if "test" in path.lower() or "_test" in path.lower():
                structure["has_tests"] = True
            
            if ext == ".py":
                structure["metrics"]["python_files"] += 1
                try:
                    with open(f["full_path"], 'r', encoding='utf-8') as file:
                        structure["metrics"]["total_lines"] += len(file.readlines())
                except:
                    pass
            elif ext in [".md", ".txt", ".rst"]:
                structure["metrics"]["doc_files"] += 1
        
        if ".py" in structure["file_types"]:
            structure["language"] = "python"
        elif ".js" in structure["file_types"] or ".ts" in structure["file_types"]:
            structure["language"] = "javascript"
        elif ".java" in structure["file_types"]:
            structure["language"] = "java"
        
        structure["directories"] = list(set(structure["directories"]))
        
        imports = self._get_all_imports(project)
        project_type = self._detect_project_type(imports)
        if project_type:
            structure["project_type"] = project_type
        
        return structure
    
    def _get_all_imports(self, project):
        """Pobiera wszystkie importy z projektu."""
        imports = []
        for f in project.get("files", []):
            if f["name"].endswith(".py"):
                try:
                    with open(f["full_path"], 'r', encoding='utf-8') as file:
                        content = file.read()
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.append(alias.name)
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        imports.append(node.module)
                        except:
                            pass
                except:
                    pass
        return imports

    def generate_architecture_proposal(self, project):
        """Generuje propozycję architektury na podstawie TYPU PROJEKTU."""
        structure = project.get("structure") or self.analyze_project_structure(project)
        name = structure["name"]
        project_type = structure.get("project_type") or {}
        
        if not project_type:
            project_type = self._detect_project_type(self._get_all_imports(project))
            structure["project_type"] = project_type
        
        ptype = project_type.get("type") if project_type else None
        
        if ptype == "agent":
            architecture = self._generate_agent_architecture(name, structure)
        elif ptype == "web_api":
            architecture = self._generate_web_api_architecture(name, structure)
        elif ptype == "cli":
            architecture = self._generate_cli_architecture(name, structure)
        elif ptype == "scraper":
            architecture = self._generate_scraper_architecture(name, structure)
        elif ptype == "ai_ml":
            architecture = self._generate_ai_ml_architecture(name, structure)
        else:
            architecture = self._generate_generic_architecture(name, structure)
        
        architecture["detected_type"] = project_type
        architecture["missing"] = self._find_missing_components(structure, project_type)
        architecture["suggestions"] = self._generate_suggestions(structure, project_type)
        
        return architecture
    
    def _generate_web_api_architecture(self, name, structure):
        """Architektura dla Web API."""
        return {
            "name": name,
            "language": "python",
            "type": "Web API",
            "suggested_structure": [
                f"{name}/",
                f"{name}/api/",
                f"{name}/api/routes/",
                f"{name}/api/models/",
                f"{name}/api/schemas/",
                f"{name}/core/",
                f"{name}/core/config.py",
                f"{name}/core/database.py",
                f"{name}/services/",
                f"{name}/tests/",
                f"{name}/tests/api/",
                f"{name}/requirements.txt",
                f"{name}/.env.example",
                f"{name}/README.md",
                f"{name}/Dockerfile"
            ],
            "main_file": f"{name}/main.py",
            "patterns": ["REST", "Dependency Injection", "Repository Pattern"]
        }
    
    def _generate_agent_architecture(self, name, structure):
        """Architektura dla AI Agenta."""
        return {
            "name": name,
            "language": "python",
            "type": "AI Agent",
            "suggested_structure": [
                f"{name}/",
                f"{name}/core/",
                f"{name}/core/loop.py        # Główna pętla",
                f"{name}/core/config.py      # Konfiguracja",
                f"{name}/core/constants.py   # Stałe systemowe",
                f"{name}/brain/",
                f"{name}/brain/analyzer.py   # Analiza projektów",
                f"{name}/brain/planner.py    # Planowanie zadań",
                f"{name}/brain/assistant.py  # Interakcja z użytkownikiem",
                f"{name}/brain/alerts.py     # Alerty produktywności",
                f"{name}/integrations/",
                f"{name}/integrations/obsidian.py",
                f"{name}/integrations/todoist.py",
                f"{name}/integrations/standup.py",
                f"{name}/memory/",
                f"{name}/cli/",
                f"{name}/tests/",
                f"{name}/requirements.txt",
                f"{name}/README.md"
            ],
            "main_file": f"{name}/core/loop.py",
            "patterns": ["Event Loop", "State Management", "Integration Pattern", "Agent Architecture"]
        }
    
    def _generate_cli_architecture(self, name, structure):
        """Architektura dla CLI Tool."""
        return {
            "name": name,
            "language": "python",
            "type": "CLI Tool",
            "suggested_structure": [
                f"{name}/",
                f"{name}/cli/",
                f"{name}/cli/commands/",
                f"{name}/cli/commands/{name}_cmd.py",
                f"{name}/core/",
                f"{name}/utils/",
                f"{name}/tests/",
                f"{name}/requirements.txt",
                f"{name}/setup.py lub pyproject.toml",
                f"{name}/README.md"
            ],
            "main_file": f"{name}/cli/__main__.py",
            "patterns": ["Click/ Typer", "Subcommands", "Config file"]
        }
    
    def _generate_scraper_architecture(self, name, structure):
        """Architektura dla Web Scraper."""
        return {
            "name": name,
            "language": "python",
            "type": "Web Scraper",
            "suggested_structure": [
                f"{name}/",
                f"{name}/scraper/",
                f"{name}/scraper/parsers/",
                f"{name}/scraper/models/",
                f"{name}/scraper/exporters/",
                f"{name}/data/raw/",
                f"{name}/data/processed/",
                f"{name}/tests/",
                f"{name}/requirements.txt",
                f"{name}/README.md"
            ],
            "main_file": f"{name}/scraper/run.py",
            "patterns": ["Pipeline", "Rate Limiting", "Retry Logic", "Export to DB/CSV"]
        }
    
    def _generate_ai_ml_architecture(self, name, structure):
        """Architektura dla AI/ML."""
        return {
            "name": name,
            "language": "python",
            "type": "AI/ML",
            "suggested_structure": [
                f"{name}/",
                f"{name}/models/",
                f"{name}/data/",
                f"{name}/data/raw/",
                f"{name}/data/processed/",
                f"{name}/training/",
                f"{name}/inference/",
                f"{name}/api/",
                f"{name}/tests/",
                f"{name}/requirements.txt",
                f"{name}/README.md"
            ],
            "main_file": f"{name}/inference/server.py",
            "patterns": ["Model versioning", "Data pipeline", "Batch/Inference API"]
        }
    
    def _generate_generic_architecture(self, name, structure):
        """Generic architecture."""
        return {
            "name": name,
            "language": structure.get("language", "unknown"),
            "type": "Generic",
            "suggested_structure": [
                f"{name}/",
                f"{name}/src/",
                f"{name}/tests/",
                f"{name}/docs/",
                f"{name}/README.md",
                f"{name}/requirements.txt"
            ],
            "main_file": f"{name}/src/main.py",
            "patterns": []
        }
    
    def _find_missing_components(self, structure, project_type):
        """Znajduje brakujące komponenty."""
        missing = []
        
        if not structure["has_readme"]:
            missing.append("README.md - kluczowe dla zrozumienia projektu")
        if not structure["has_gitignore"]:
            missing.append(".gitignore - ochrona przed przypadkowym commitowaniem secrets")
        if not structure["has_tests"]:
            missing.append("tests/ - brak testów = ryzyko regresji")
        
        ptype = project_type.get("type") if project_type else None
        if ptype == "web_api" and "api" not in structure["directories"]:
            missing.append("api/ - brak katalogu dla endpointów")
        elif ptype == "scraper" and "data" not in structure["directories"]:
            missing.append("data/ - brak katalogu na dane")
        elif ptype == "agent" and "brain" not in structure["directories"]:
            missing.append("brain/ - brak katalogu na moduły agenta")
        
        return missing

    def _generate_suggestions(self, structure, project_type):
        """Generuje inteligentne sugestie."""
        suggestions = []
        
        ptype = project_type.get("type") if project_type else None
        
        if ptype == "web_api":
            suggestions.append("Rozważ FastAPI - automatyczna dokumentacja OpenAPI/Swagger")
            suggestions.append("Dodaj Pydantic dla walidacji danych wejściowych")
            suggestions.append("Użyj SQLAlchemy lub Alembic dla migracji bazy danych")
        elif ptype == "cli":
            suggestions.append("Click lub Typer - łatwe w użyciu CLI z auto-generated help")
            suggestions.append("Dodaj colored output (click.style lub rich)")
        elif ptype == "scraper":
            suggestions.append("Dodaj retry logic z exponential backoff")
            suggestions.append("Rozważ asyncio dla równoległego scrapowania")
        elif ptype == "ai_ml":
            suggestions.append("Użyj Hydra lub OmegaConf dla konfiguracji")
            suggestions.append("Dodaj MLflow lub W&B dla śledzenia eksperymentów")
        elif ptype == "agent":
            suggestions.append("Rozważ dodanie LLM integration (OpenAI, Anthropic) dla lepszych rekomendacji")
            suggestions.append("Dodaj learnings z interakcji użytkownika")
            suggestions.append("Implementuj proaktywne sugestie oparte na wzorcach")
        
        if structure["metrics"]["python_files"] > 20:
            suggestions.append("Projekt rośnie - rozważ modularyzację na domeny")
        
        if structure["metrics"]["total_lines"] > 2000:
            suggestions.append("Duży projekt - dodaj type hints i mypy dla bezpieczeństwa")
        
        return suggestions

    def create_roadmap(self, project, architecture=None):
        """Tworzy roadmapę opartą na ANALIZIE, nie szablonach."""
        structure = project.get("structure") or self.analyze_project_structure(project)
        name = structure["name"]
        project_type = structure.get("project_type") or {}
        
        tasks = []
        ptype = project_type.get("type") if project_type else None
        
        if structure["is_new"]:
            tasks.append({
                "task": "Zdefiniuj MVP i pierwszy release",
                "description": "Co musisz mieć żeby projekt był użyteczny?",
                "priority": "HIGH",
                "estimated_minutes": 30,
                "reason": "Bez jasnego celu nie wiesz co robić"
            })
        
        todos_issues = self._get_todos_as_tasks(project)
        for todo in todos_issues[:5]:
            tasks.append(todo)
        
        if project_type and ptype == "web_api":
            if not structure["has_tests"]:
                tasks.append({
                    "task": "Skonfiguruj testy API",
                    "description": "pytest + FastAPI TestClient lub httpx",
                    "priority": "HIGH",
                    "estimated_minutes": 45,
                    "reason": "Testy = pewność że API działa"
                })
        elif not structure["has_tests"]:
            tasks.append({
                "task": "Skonfiguruj podstawowe testy",
                "description": "pytest z pierwszymi testami smoke",
                "priority": "MEDIUM",
                "estimated_minutes": 30,
                "reason": "Testy pozwalają na śmiałe refaktoryzacje"
            })
        
        missing = architecture.get("missing", []) if architecture else []
        for item in missing[:3]:
            tasks.append({
                "task": f"Utwórz {item.split(' - ')[0]}",
                "description": item.split(' - ')[1] if ' - ' in item else "",
                "priority": "MEDIUM",
                "estimated_minutes": 20,
                "reason": "Brakujący element wymieniony w analizie"
            })
        
        security_issues = self._get_security_issues(project)
        if security_issues:
            tasks.append({
                "task": "Napraw potential security issues",
                "description": f"Znaleziono {len(security_issues)} potential secrets/hardcoded credentials",
                "priority": "HIGH",
                "estimated_minutes": 15 * len(security_issues),
                "reason": "Secrets w kodzie = ryzyko wycieku"
            })
        
        focus_task = self._select_smart_focus(tasks, project, project_type)
        
        return {
            "project": name,
            "detected_type": ptype,
            "tasks": tasks,
            "total_estimated_minutes": sum(t.get("estimated_minutes", 0) for t in tasks),
            "focus_task": focus_task
        }
    
    def _get_todos_as_tasks(self, project):
        """Konwertuje TODO/FIXME na taski."""
        tasks = []
        for f in project.get("files", []):
            if f["name"].endswith(".py"):
                try:
                    with open(f["full_path"], 'r', encoding='utf-8') as file:
                        content = file.read()
                    todos = re.findall(r'#\s*(TODO|FIXME|BUG):?\s*(.*)', content, re.IGNORECASE)
                    for marker, desc in todos:
                        if desc.strip():
                            tasks.append({
                                "task": f"{marker.upper()}: {desc.strip()}",
                                "description": f"W pliku {f['path']}",
                                "priority": "MEDIUM" if marker.upper() == "TODO" else "HIGH",
                                "estimated_minutes": 30,
                                "source": "code_comment"
                            })
                except:
                    pass
        return tasks
    
    def _get_security_issues(self, project):
        """Znajduje potencjalne problemy bezpieczeństwa."""
        issues = []
        for f in project.get("files", []):
            if f["name"].endswith(".py"):
                try:
                    with open(f["full_path"], 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    if re.search(r'["\']api[_-]?key["\']\s*[:=]\s*["\'][^"\']+["\']', content, re.I):
                        issues.append({"file": f["path"], "type": "API Key"})
                    if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.I):
                        issues.append({"file": f["path"], "type": "Password"})
                except:
                    pass
        return issues
    
    def _select_smart_focus(self, tasks, project, project_type):
        """Wybiera fokus na podstawie analizy."""
        if not tasks:
            return None
        
        high_priority = [t for t in tasks if t.get("priority") == "HIGH"]
        if high_priority:
            return high_priority[0]
        
        if project_type.get("type") == "web_api":
            api_tasks = [t for t in tasks if "API" in t.get("task", "") or "test" in t.get("task", "").lower()]
            if api_tasks:
                return api_tasks[0]
        
        return tasks[0]

    def is_new_project(self, project):
        """Sprawdza czy projekt jest nowy (bez historii)."""
        history = self._load_work_history()
        project_name = project["name"]
        
        project_entries = [e for e in history if e.get("project") == project_name]
        
        return len(project_entries) == 0 and len(project.get("files", [])) < 5

    def get_project_intelligence(self, project):
        """Główna funkcja - zwraca pełną analizę projektu."""
        structure = self.analyze_project_structure(project)
        architecture = self.generate_architecture_proposal(project)
        roadmap = self.create_roadmap(project, architecture)
        is_new = self.is_new_project(project)
        
        issues = self._analyze_project_deep(project)

        dependency_graph = None
        if any(f["name"].endswith(".py") for f in project.get("files", [])):
            dg = DependencyGraph()
            dependency_graph = dg.summary(project)

        return {
            "project": project["name"],
            "is_new": is_new,
            "structure": structure,
            "architecture": architecture,
            "roadmap": roadmap,
            "focus_task": roadmap.get("focus_task"),
            "issues": issues,
            "dependency_graph": dependency_graph,
            "summary": self._generate_summary(project, structure, architecture, roadmap, issues)
        }
    
    def _generate_summary(self, project, structure, architecture, roadmap, issues):
        """Generuje podsumowanie w języku naturalnym."""
        name = project["name"]
        detected_type = architecture.get("detected_type") if architecture else None
        ptype = detected_type.get("architecture", "Nieznany typ") if detected_type else "Nieznany typ"
        
        summary = f"""## 📊 Podsumowanie: {name}

**Typ projektu:** {ptype}
**Język:** {structure.get('language', 'unknown')}
**Pliki:** {structure['metrics']['total_files']}
**Linie kodu:** {structure['metrics']['total_lines']}
**Złożoność:** {structure.get('complexity', 'unknown')}

"""
        
        if issues:
            high_priority = [i for i in issues if i.get("priority") == "HIGH"]
            medium_priority = [i for i in issues if i.get("priority") == "MEDIUM"]
            
            if high_priority:
                summary += "### 🚨 Priorytet HIGH:\n"
                for issue in high_priority[:3]:
                    summary += f"- {issue['issue']}\n"
                summary += "\n"
            
            if medium_priority:
                summary += "### ⚠️ Priorytet MEDIUM:\n"
                for issue in medium_priority[:3]:
                    summary += f"- {issue['issue']}\n"
                summary += "\n"
        
        if architecture and architecture.get("suggestions"):
            summary += "### 💡 Sugestie:\n"
            for suggestion in architecture["suggestions"][:3]:
                summary += f"- {suggestion}\n"
        
        if roadmap and roadmap.get("focus_task"):
            focus = roadmap["focus_task"]
            summary += f"\n### 🎯 Focus na dziś:\n"
            summary += f"**{focus.get('task', '')}** - {focus.get('description', '')}\n"
            if focus.get("reason"):
                summary += f"_Dlaczego: {focus['reason']}_\n"
        
        return summary
