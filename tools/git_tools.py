"""
tools/git_tools.py - Git Tools
Operacje na git
"""

import subprocess
import os


class GitTools:
    """Narzędzia do operacji git."""
    
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or "."
    
    def _run(self, command, cwd=None):
        """Uruchamia polecenie git."""
        try:
            proc = subprocess.run(
                f"git {command}",
                shell=True,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": proc.returncode == 0,
                "output": proc.stdout,
                "error": proc.stderr if proc.returncode != 0 else None,
                "returncode": proc.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def status(self, short=False, cwd=None):
        """
        Zwraca status git.
        
        Args:
            short: Krótki format
            cwd: Katalog repozytorium
            
        Returns:
            dict: {"success": bool, "output": str}
        """
        cmd = "status -s" if short else "status"
        return self._run(cmd, cwd)
    
    def add(self, files=".", cwd=None):
        """
        Dodaje pliki do staging.
        
        Args:
            files: Pliki do dodania ( "." = wszystkie)
            cwd: Katalog repozytorium
            
        Returns:
            dict: {"success": bool, "output": str}
        """
        return self._run(f"add {files}", cwd)
    
    def commit(self, message, cwd=None):
        """
        Commituje zmiany.
        
        Args:
            message: Wiadomość commita
            cwd: Katalog repozytorium
            
        Returns:
            dict: {"success": bool, "output": str}
        """
        escaped_msg = message.replace('"', '\\"')
        return self._run(f'commit -m "{escaped_msg}"', cwd)
    
    def log(self, n=10, oneline=False, cwd=None):
        """
        Zwraca historię commitów.
        
        Args:
            n: Liczba commitów
            oneline: Format jednolinijkowy
            cwd: Katalog repozytorium
            
        Returns:
            dict: {"success": bool, "output": str}
        """
        cmd = f"log -{n}"
        if oneline:
            cmd += " --oneline"
        return self._run(cmd, cwd)
    
    def branch(self, cwd=None):
        """Zwraca listę branchy."""
        return self._run("branch -a", cwd)
    
    def current_branch(self, cwd=None):
        """Zwraca nazwę aktualnego brancha."""
        result = self._run("branch --show-current", cwd)
        if result["success"]:
            result["output"] = result["output"].strip()
        return result
    
    def diff(self, cached=False, cwd=None):
        """Zwraca różnice."""
        cmd = "diff"
        if cached:
            cmd += " --cached"
        return self._run(cmd, cwd)
    
    def is_repo(self, cwd=None):
        """Sprawdza czy to repozytorium git."""
        result = self._run("rev-parse --git-dir", cwd)
        return result["success"]
