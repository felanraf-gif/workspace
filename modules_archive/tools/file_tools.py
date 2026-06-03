import os
import json
import hashlib

class FileTools:
    """Narzędzia do operacji na plikach."""
    
    @staticmethod
    def get_file_hash(filepath):
        """Generuje hash MD5 pliku."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    @staticmethod
    def list_files(directory, recursive=True, exclude_dirs=None):
        """Lista plików w katalogu."""
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'tor_env'}
        
        files = []
        dirs = []
        
        if not os.path.exists(directory):
            return {"files": [], "dirs": []}
        
        if recursive:
            for root, dirnames, filenames in os.walk(directory):
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
                
                for filename in filenames:
                    if not filename.startswith('.'):
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.relpath(filepath, directory)
                        files.append({
                            "name": filename,
                            "path": rel_path,
                            "full_path": filepath,
                            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
                        })
                
                for dirname in dirnames:
                    dirpath = os.path.join(root, dirname)
                    rel_path = os.path.relpath(dirpath, directory)
                    dirs.append({
                        "name": dirname,
                        "path": rel_path,
                        "full_path": dirpath
                    })
        else:
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path) and item not in exclude_dirs:
                    dirs.append({
                        "name": item,
                        "path": item,
                        "full_path": full_path
                    })
                elif os.path.isfile(full_path) and not item.startswith('.'):
                    files.append({
                        "name": item,
                        "path": item,
                        "full_path": full_path,
                        "size": os.path.getsize(full_path)
                    })
        
        return {"files": files, "dirs": dirs}
    
    @staticmethod
    def detect_changes(current_state, previous_state):
        """Wykrywa zmiany między stanami."""
        changes = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": []
        }
        
        for path, file_data in current_state.items():
            if path not in previous_state:
                changes["new_files"].append(path)
            elif previous_state[path] != file_data:
                changes["modified_files"].append(path)
        
        for path in previous_state.keys():
            if path not in current_state:
                changes["deleted_files"].append(path)
        
        return changes
    
    @staticmethod
    def get_directory_size(path):
        """Oblicza rozmiar katalogu."""
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total += os.path.getsize(fp)
                    except:
                        pass
        except:
            pass
        return total
    
    @staticmethod
    def get_file_info(filepath):
        """Zwraca informacje o pliku."""
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        return {
            "name": os.path.basename(filepath),
            "path": filepath,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "hash": FileTools.get_file_hash(filepath)
        }
    
    @staticmethod
    def save_state_to_file(state, filepath):
        """Zapisuje stan do pliku JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    @staticmethod
    def load_state_from_file(filepath):
        """Wczytuje stan z pliku JSON."""
        if not os.path.exists(filepath):
            return {}
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    @staticmethod
    def build_file_state(directory, recursive=True):
        """Buduje słownik stanu plików {path: hash}."""
        state = {}
        data = FileTools.list_files(directory, recursive)
        
        for f in data["files"]:
            hash_val = FileTools.get_file_hash(f["full_path"])
            if hash_val:
                state[f["path"]] = {
                    "hash": hash_val,
                    "size": f["size"],
                    "type": "file"
                }
        
        for d in data["dirs"]:
            state[d["path"]] = {
                "hash": None,
                "size": 0,
                "type": "dir"
            }
        
        return state

if __name__ == "__main__":
    from core.config import PROJECTS_PATH
    
    ft = FileTools()
    
    print("=== FileTools Test ===")
    
    data = ft.list_files(PROJECTS_PATH)
    print(f"Files: {len(data['files'])}")
    print(f"Dirs: {len(data['dirs'])}")
    
    state = ft.build_file_state(PROJECTS_PATH)
    print(f"State entries: {len(state)}")
    
    size = ft.get_directory_size(PROJECTS_PATH)
    print(f"Total size: {size} bytes ({size/1024:.1f} KB)")
