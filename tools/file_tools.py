"""
tools/file_tools.py - File Tools
Operacje na plikach - read, write, edit
"""

import os
import shutil
from datetime import datetime


class FileTools:
    """Narzędzia do operacji na plikach."""
    
    def read(self, path, encoding='utf-8'):
        """
        Czyta plik.
        
        Args:
            path: Ścieżka do pliku
            encoding: Kodowanie (domyślnie utf-8)
            
        Returns:
            dict: {"success": bool, "content": str, "lines": int}
        """
        result = {
            "success": False,
            "content": None,
            "lines": 0,
            "error": None
        }
        
        if not os.path.exists(path):
            result["error"] = f"Plik nie istnieje: {path}"
            return result
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            result["success"] = True
            result["content"] = content
            result["lines"] = len(content.splitlines())
            result["size"] = os.path.getsize(path)
            
        except UnicodeDecodeError:
            result["error"] = "Błąd kodowania - spróbuj inne kodowanie"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def write(self, path, content, encoding='utf-8', backup=True):
        """
        Zapisuje plik.
        
        Args:
            path: Ścieżka do pliku
            content: Treść do zapisania
            encoding: Kodowanie
            backup: Czy tworzyć backup
            
        Returns:
            dict: {"success": bool, "backup": str}
        """
        result = {
            "success": False,
            "backup": None,
            "error": None
        }
        
        if backup and os.path.exists(path):
            backup_path = f"{path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(path, backup_path)
            result["backup"] = backup_path
        
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            result["success"] = True
            result["bytes_written"] = len(content.encode(encoding))
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def edit(self, path, old_string, new_string, backup=True):
        """
        Edytuje plik - zamienia old_string na new_string.
        
        Args:
            path: Ścieżka do pliku
            old_string: Tekst do zamiany
            new_string: Nowy tekst
            backup: Czy tworzyć backup
            
        Returns:
            dict: {"success": bool, "replacements": int}
        """
        result = {
            "success": False,
            "replacements": 0,
            "error": None
        }
        
        read_result = self.read(path)
        if not read_result["success"]:
            result["error"] = read_result.get("error", "Nie można odczytać pliku")
            return result
        
        content = read_result["content"]
        
        if old_string not in content:
            result["error"] = "Szukany tekst nie znaleziony"
            return result
        
        backup_result = self.write(f"{path}.edit.backup", content) if backup else None
        
        new_content = content.replace(old_string, new_string)
        
        write_result = self.write(path, new_content, backup=False)
        if write_result["success"]:
            result["success"] = True
            result["replacements"] = content.count(old_string)
        
        return result
    
    def exists(self, path):
        """Sprawdza czy plik istnieje."""
        return os.path.exists(path)
    
    def list_dir(self, path):
        """Listuje zawartość katalogu."""
        if not os.path.exists(path):
            return {"success": False, "error": "Katalog nie istnieje"}
        
        try:
            items = os.listdir(path)
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}
