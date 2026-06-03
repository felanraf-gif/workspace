"""
brain/observer.py - Observer
Obserwuje zmiany w środowisku
"""

import os
import hashlib
from datetime import datetime


class Observer:
    """
    Observer - obserwuje zmiany w środowisku.
    
    Służy do:
    - Wykrywania zmian w plikach
    - Monitorowania stanu systemu
    - Śledzenia zmian w projektach
    """
    
    def __init__(self, watch_paths=None):
        self.watch_paths = watch_paths or ["."]
        self.file_states = {}
        self.last_observation = None
    
    def observe(self):
        """
        Przeprowadza obserwację.
        
        Returns:
            dict: Raport z obserwacji
        """
        observation = {
            "timestamp": datetime.now().isoformat(),
            "observer_role": "Observer",
            "changes": [],
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "system_state": self._get_system_state()
        }
        
        all_changes = []
        for watch_path in self.watch_paths:
            if os.path.exists(watch_path):
                changes = self._watch_directory(watch_path)
                all_changes.extend(changes)
        
        observation["changes"] = all_changes
        observation["new_files"] = [c for c in all_changes if c.get("type") == "new"]
        observation["modified_files"] = [c for c in all_changes if c.get("type") == "modified"]
        observation["deleted_files"] = [c for c in all_changes if c.get("type") == "deleted"]
        
        self.last_observation = observation
        
        return observation
    
    def _watch_directory(self, directory):
        """Obserwuje katalog."""
        changes = []
        current_files = {}
        
        skip_dirs = {'__pycache__', '.git', 'venv', 'node_modules', '.venv', 'tor_env'}
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for f in files:
                if f.startswith('.'):
                    continue
                
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, directory)
                
                try:
                    stat = os.stat(file_path)
                    file_hash = self._get_file_hash(file_path)
                    
                    current_files[rel_path] = {
                        "mtime": stat.st_mtime,
                        "hash": file_hash,
                        "size": stat.st_size
                    }
                    
                    if rel_path not in self.file_states:
                        changes.append({
                            "type": "new",
                            "path": rel_path,
                            "full_path": file_path
                        })
                    elif self.file_states[rel_path]["hash"] != file_hash:
                        changes.append({
                            "type": "modified",
                            "path": rel_path,
                            "full_path": file_path,
                            "old_hash": self.file_states[rel_path]["hash"],
                            "new_hash": file_hash
                        })
                
                except:
                    pass
        
        deleted = set(self.file_states.keys()) - set(current_files.keys())
        for d in deleted:
            changes.append({
                "type": "deleted",
                "path": d
            })
        
        self.file_states = current_files
        
        return changes
    
    def _get_file_hash(self, file_path):
        """Oblicza hash pliku."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:16]
        except:
            return None
    
    def _get_system_state(self):
        """Zwraca stan systemu."""
        return {
            "watching_paths": self.watch_paths,
            "tracked_files": len(self.file_states),
            "observation_count": self.last_observation.get("timestamp") if self.last_observation else None
        }
    
    def get_changes_summary(self):
        """Zwraca podsumowanie zmian z ostatniej obserwacji."""
        if not self.last_observation:
            return "Brak obserwacji"
        
        new = len(self.last_observation.get("new_files", []))
        modified = len(self.last_observation.get("modified_files", []))
        deleted = len(self.last_observation.get("deleted_files", []))
        
        return f"Zmian: {new} nowych, {modified} zmodyfikowanych, {deleted} usuniętych"
