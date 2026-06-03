import os
import json
import hashlib
from datetime import datetime
from core.config import PROJECTS_PATH, MEMORY_PATH

class Analyzer:
    def __init__(self):
        self.projects_path = PROJECTS_PATH
        self.memory_logs_path = os.path.join(MEMORY_PATH, "daily_logs")
        self.state_file = os.path.join(MEMORY_PATH, "analyzer_state.json")

    def _get_file_hash(self, filepath):
        """Generuje hash pliku dla wykrywania zmian."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None

    def _load_previous_state(self):
        """Wczytuje poprzedni stan plików."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_current_state(self, current_state):
        """Zapisuje aktualny stan plików."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(current_state, f)

    def scan_projects(self):
        """Skanuje projekty i wykrywa nowe/zmienione pliki."""
        projects = []
        previous_state = self._load_previous_state()
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
                
                # Skanowanie rekurencyjne
                for root, dirs, files in os.walk(project_dir):
                    rel_root = os.path.relpath(root, project_dir)
                    
                    # Dodaj katalogi do listy plików
                    for dir_name in dirs:
                        if dir_name.startswith('.'):
                            continue
                            
                        dir_path = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(dir_path, project_dir)
                        
                        # Katalogi nie mają hashu, używamy specjalnej wartości
                        dir_info = {
                            "name": dir_name,
                            "path": rel_path,
                            "full_path": dir_path,
                            "hash": None,
                            "type": "dir"
                        }
                        
                        project_info["files"].append(dir_info)
                    
                    for file in files:
                        if file.startswith('.'):
                            continue
                            
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_dir)
                        
                        file_hash = self._get_file_hash(file_path)
                        file_info = {
                            "name": file,
                            "path": rel_path,
                            "full_path": file_path,
                            "hash": file_hash,
                            "type": "file"
                        }
                        
                        project_info["files"].append(file_info)
                        
                        # Wykrywanie zmian
                        prev_hash = previous_state.get(project_name, {}).get(rel_path)
                        if prev_hash:
                            if prev_hash != file_hash:
                                project_info["changed_files"].append(rel_path)
                        else:
                            project_info["new_files"].append(rel_path)
                        
                        # Aktualizacja stanu
                        if project_name not in current_state:
                            current_state[project_name] = {}
                        current_state[project_name][rel_path] = file_hash

                projects.append(project_info)

        self._save_current_state(current_state)
        return projects, previous_state

    def detect_issues(self, projects):
        """Wykrywa problemy w projektach."""
        issues = []
        
        for project in projects:
            project_name = project["name"]
            files = [f["path"] for f in project["files"]]
            
            # Sprawdź strukturę katalogów
            # files to lista słowników, musimy sprawdzić pole 'path'
            file_paths = [f["path"] for f in project["files"]]
            has_src = any(f.startswith("src/") or f == "src" for f in file_paths)
            has_config = "config.json" in file_paths
            
            if not has_src:
                issues.append({
                    "project": project_name,
                    "issue": "Brak katalogu src/",
                    "priority": "HIGH",
                    "type": "structure"
                })
            
            if not has_config:
                issues.append({
                    "project": project_name,
                    "issue": "Brak pliku config.json",
                    "priority": "HIGH",
                    "type": "structure"
                })
            else:
                # Sprawdź zawartość config.json
                config_path = os.path.join(project["path"], "config.json")
                try:
                    with open(config_path, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            issues.append({
                                "project": project_name,
                                "issue": "Pusty plik config.json",
                                "priority": "HIGH",
                                "type": "structure"
                            })
                except Exception as e:
                    issues.append({
                        "project": project_name,
                        "issue": f"Błąd odczytu config.json: {str(e)}",
                        "priority": "HIGH",
                        "type": "error"
                    })

            # Sprawdź czy projekt jest pusty
            if len(project["files"]) == 0:
                issues.append({
                    "project": project_name,
                    "issue": "Pusty projekt (brak zawartości)",
                    "priority": "HIGH",
                    "type": "structure"
                })

            # Zadania dla nowych plików (MEDIUM)
            for new_file in project["new_files"]:
                issues.append({
                    "project": project_name,
                    "issue": f"Nowy plik: {new_file}",
                    "priority": "MEDIUM",
                    "type": "new_file"
                })

        return issues

    def save_analysis(self, projects, issues):
        """Zapisuje wyniki analizy."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(self.memory_logs_path, f"analysis_{timestamp}.json")
        
        analysis_data = {
            "timestamp": timestamp,
            "projects_count": len(projects),
            "issues_count": len(issues),
            "projects": projects,
            "issues": issues
        }
        
        os.makedirs(self.memory_logs_path, exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        return log_file, analysis_data

if __name__ == "__main__":
    analyzer = Analyzer()
    projects, _ = analyzer.scan_projects()
    issues = analyzer.detect_issues(projects)
    print(f"Znaleziono projektów: {len(projects)}")
    print(f"Znaleziono problemów: {len(issues)}")
    for i in issues:
        print(f" - {i['project']}: {i['issue']}")