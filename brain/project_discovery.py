"""
brain/project_discovery.py - Wykrywanie i zarządzanie projektami
Automatycznie wykrywa projekty z różnych lokalizacji
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path


class ProjectDiscovery:
    """Wykrywa projekty z różnych źródeł."""
    
    PROJECT_MARKERS = {
        "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "setup.cfg"],
        "javascript": ["package.json", "yarn.lock", "package-lock.json"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod", "go.sum"],
        "java": ["pom.xml", "build.gradle"],
        "csharp": ["*.csproj", "*.sln"],
        "docker": ["Dockerfile", "docker-compose.yml"],
    }
    
    SKIP_DIRS = {
        '__pycache__', '.git', 'venv', '.venv', 'env', 'tor_env',
        'node_modules', '.tox', '.mypy_cache', '.pytest_cache',
        'dist', 'build', '.egg-info', '.idea', '.vscode',
        'vendor', 'target', 'bin', 'obj'
    }
    
    SKIP_NAMES = {
        '.env', '.env.local', '.env.production', '.DS_Store',
        'Thumbs.db', '*.pyc', '*.pyo'
    }
    
    def __init__(self, scan_paths=None):
        self.scan_paths = scan_paths or [
            "workspace/projects",
            "/home/felanraf/Projekty"
        ]
        self.discovered_projects = []
        self.project_cache_file = "memory/projects_cache.json"
    
    def discover_all(self):
        """Wykrywa wszystkie projekty ze wszystkich ścieżek."""
        self.discovered_projects = []
        
        for scan_path in self.scan_paths:
            if os.path.exists(scan_path):
                projects = self._scan_path(scan_path)
                self.discovered_projects.extend(projects)
            else:
                print(f"[DISCOVERY] Ścieżka nie istnieje: {scan_path}")
        
        self._save_cache()
        return self.discovered_projects
    
    def _scan_path(self, base_path):
        """Skanuje pojedynczą ścieżkę w poszukiwaniu projektów."""
        projects = []
        
        if os.path.isfile(base_path):
            return projects
        
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            
            if os.path.isdir(item_path):
                project = self._analyze_project(item_path, item)
                if project:
                    projects.append(project)
            else:
                continue
        
        return projects
    
    def _analyze_project(self, project_path, project_name):
        """Analizuje pojedynczy projekt."""
        skip_dirs = self.SKIP_DIRS | {'.git'}
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            project_type = self._detect_project_type(files)
            if project_type:
                metadata = self._load_config(project_path)
                
                return {
                    "name": project_name,
                    "path": project_path,
                    "type": project_type,
                    "discovery_method": self._get_discovery_method(project_path),
                    "config": metadata,
                    "files_count": self._count_files(project_path),
                    "lines_of_code": self._count_loc(project_path),
                    "last_modified": self._get_last_modified(project_path),
                    "has_git": os.path.exists(os.path.join(project_path, ".git")),
                    "detected_at": datetime.now().isoformat()
                }
        
        return None
    
    def _detect_project_type(self, files):
        """Wykrywa typ projektu na podstawie plików."""
        files_set = set(files)
        
        for lang, markers in self.PROJECT_MARKERS.items():
            for marker in markers:
                if marker in files_set or marker.replace("*", "") in str(files_set):
                    return lang
        
        for f in files:
            if f.endswith('.py'):
                return "python"
            elif f.endswith('.js') or f.endswith('.ts'):
                return "javascript"
            elif f.endswith('.rs'):
                return "rust"
            elif f.endswith('.go'):
                return "go"
            elif f.endswith('.java'):
                return "java"
        
        return None
    
    def _get_discovery_method(self, project_path):
        """Określa metodę wykrycia projektu."""
        if "/workspace/projects/" in project_path:
            return "workspace"
        elif "/Projekty/" in project_path:
            return "projects_dir"
        elif "/.git" in project_path:
            return "git_scan"
        return "unknown"
    
    def _load_config(self, project_path):
        """Ładuje config projektu jeśli istnieje."""
        config_file = os.path.join(project_path, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _count_files(self, project_path):
        """Liczy pliki w projekcie."""
        count = 0
        skip_dirs = self.SKIP_DIRS | {'.git'}
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            count += len([f for f in files if not f.startswith('.')])
        
        return count
    
    def _count_loc(self, project_path):
        """Liczy linie kodu."""
        total = 0
        skip_dirs = self.SKIP_DIRS | {'.git'}
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            for f in files:
                if f.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.c', '.cpp', '.h')):
                    try:
                        file_path = os.path.join(root, f)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                            total += len(fp.readlines())
                    except:
                        pass
        
        return total
    
    def _get_last_modified(self, project_path):
        """Zwraca datę ostatniej modyfikacji."""
        try:
            mtime = os.path.getmtime(project_path)
            return datetime.fromtimestamp(mtime).isoformat()
        except:
            return None
    
    def _save_cache(self):
        """Zapisuje cache odkrytych projektów."""
        os.makedirs(os.path.dirname(self.project_cache_file), exist_ok=True)
        
        cache = {
            "last_scan": datetime.now().isoformat(),
            "projects": self.discovered_projects
        }
        
        try:
            with open(self.project_cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[DISCOVERY] Błąd zapisu cache: {e}")
    
    def load_cache(self):
        """Ładuje cache projektów."""
        if os.path.exists(self.project_cache_file):
            try:
                with open(self.project_cache_file, 'r') as f:
                    cache = json.load(f)
                    self.discovered_projects = cache.get("projects", [])
                    return cache
            except:
                pass
        return {"last_scan": None, "projects": []}
    
    def get_project(self, name):
        """Pobiera projekt po nazwie."""
        for project in self.discovered_projects:
            if project.get("name") == name:
                return project
        return None
    
    def get_projects_by_type(self, project_type):
        """Pobiera projekty danego typu."""
        return [p for p in self.discovered_projects if p.get("type") == project_type]
    
    def get_status_summary(self):
        """Zwraca podsumowanie statusu wszystkich projektów."""
        return {
            "total": len(self.discovered_projects),
            "by_type": self._count_by_type(),
            "by_method": self._count_by_method(),
            "total_files": sum(p.get("files_count", 0) for p in self.discovered_projects),
            "total_loc": sum(p.get("lines_of_code", 0) for p in self.discovered_projects)
        }
    
    def _count_by_type(self):
        """Liczy projekty według typu."""
        counts = {}
        for p in self.discovered_projects:
            t = p.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    def _count_by_method(self):
        """Liczy projekty według metody wykrycia."""
        counts = {}
        for p in self.discovered_projects:
            m = p.get("discovery_method", "unknown")
            counts[m] = counts.get(m, 0) + 1
        return counts
