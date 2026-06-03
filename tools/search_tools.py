"""
tools/search_tools.py - Search Tools
Wyszukiwanie w plikach
"""

import os
import re
from datetime import datetime


class SearchTools:
    """Narzędzia do wyszukiwania w plikach."""
    
    def __init__(self, case_sensitive=False):
        self.case_sensitive = case_sensitive
    
    def grep(self, pattern, path=".", file_pattern="*", recursive=True, context=0):
        """
        Wyszukuje wzorzec w plikach.
        
        Args:
            pattern: Wzorzec do wyszukania (regex lub string)
            path: Katalog do przeszukania
            file_pattern: Filtr plików (np. "*.py")
            recursive: Czy rekursywnie
            context: Liczba linii kontekstu
            
        Returns:
            dict: {"success": bool, "matches": [{"file", "line", "content", "line_num"}, ...]}
        """
        result = {
            "success": False,
            "matches": [],
            "files_searched": 0,
            "error": None
        }
        
        if not os.path.exists(path):
            result["error"] = f"Ścieżka nie istnieje: {path}"
            return result
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            result["error"] = f"Błędny regex: {e}"
            return result
        
        def search_file(file_path):
            matches = []
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if compiled_pattern.search(line):
                            matches.append({
                                "file": file_path,
                                "line": line_num,
                                "content": line.strip(),
                                "match": compiled_pattern.findall(line)
                            })
            except:
                pass
            return matches
        
        def walk_dir(dir_path):
            all_matches = []
            files_searched = 0
            
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
                
                for f in files:
                    if file_pattern != "*" and not f.endswith(file_pattern.replace("*", "")):
                        continue
                    
                    file_path = os.path.join(root, f)
                    files_searched += 1
                    all_matches.extend(search_file(file_path))
                
                if not recursive:
                    break
            
            return all_matches, files_searched
        
        matches, files_searched = walk_dir(path)
        result["matches"] = matches
        result["files_searched"] = files_searched
        result["success"] = True
        
        return result
    
    def find(self, name, path=".", file_type="f"):
        """
        Znajduje pliki/katalogi po nazwie.
        
        Args:
            name: Nazwa do wyszukania
            path: Katalog początkowy
            file_type: "f" = pliki, "d" = katalogi, "fd" = oba
            
        Returns:
            dict: {"success": bool, "found": [paths]}
        """
        result = {
            "success": False,
            "found": [],
            "error": None
        }
        
        if not os.path.exists(path):
            result["error"] = f"Ścieżka nie istnieje: {path}"
            return result
        
        type_filter = {
            "f": lambda p: os.path.isfile(p),
            "d": lambda p: os.path.isdir(p),
            "fd": lambda p: True
        }
        
        matches = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
            
            items = files + dirs if file_type == "fd" else (files if file_type == "f" else dirs)
            
            for item in items:
                if name.lower() in item.lower():
                    full_path = os.path.join(root, item)
                    if type_filter.get(file_type, lambda p: True)(full_path):
                        matches.append(full_path)
        
        result["found"] = matches
        result["success"] = True
        
        return result
