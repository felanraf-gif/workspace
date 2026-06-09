"""
tools/bash_tools.py - Bash Tools
Uruchamianie poleceń bash i python
"""

import subprocess
import sys
from datetime import datetime


class BashTools:
    """Narzędzia do uruchamiania poleceń."""
    
    def __init__(self, cwd=None, timeout=30):
        self.cwd = cwd
        self.timeout = timeout
    
    def run(self, command, cwd=None, timeout=None, shell=True):
        """
        Uruchamia polecenie bash.
        
        Args:
            command: Polecenie do wykonania
            cwd: Katalog roboczy
            timeout: Timeout w sekundach
            shell: Czy użyć shella
            
        Returns:
            dict: {"success": bool, "stdout": str, "stderr": str, "returncode": int}
        """
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "command": command,
            "error": None
        }
        
        work_dir = cwd or self.cwd or "."
        exec_timeout = timeout or self.timeout
        
        try:
            proc = subprocess.run(
                command,
                shell=shell,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=exec_timeout
            )
            
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
            
        except subprocess.TimeoutExpired:
            result["error"] = f"Timeout po {exec_timeout}s"
        except FileNotFoundError:
            result["error"] = "Polecenie nie znalezione"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_python(self, script, args=None, python_path=None):
        """
        Uruchamia skrypt Python.
        
        Args:
            script: Ścieżka do skryptu lub kod
            args: Lista argumentów
            python_path: Ścieżka do Pythona
            
        Returns:
            dict: Wynik wykonania
        """
        python = python_path or sys.executable
        cmd_args = [python]
        
        if os.path.isfile(script):
            cmd_args.append(script)
        else:
            cmd_args.extend(["-c", script])
        
        if args:
            cmd_args.extend(args)
        
        return self.run(" ".join(cmd_args), shell=False)
    
    def check_output(self, command, cwd=None):
        """Uruchamia i zwraca tylko stdout."""
        result = self.run(command, cwd=cwd)
        return result.get("stdout", "").strip()
    
    def is_available(self, command):
        """Sprawdza czy polecenie jest dostępne."""
        result = self.run(f"which {command}", shell=True)
        return result.get("success", False)


import os
