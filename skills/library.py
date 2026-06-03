"""
skills/library.py - Skill Library
Biblioteka umiejętności agenta
"""

import os
import json
from datetime import datetime


class SkillLibrary:
    """
    SkillLibrary - przechowuje i zarządza umiejętnościami agenta.
    
    Umiejętność = sprawdzona sekwencja kroków
    """
    
    def __init__(self, skills_path="skills"):
        self.skills_path = skills_path
        self.skills_file = os.path.join(skills_path, "skills.json")
        self.examples_dir = os.path.join(skills_path, "examples")
        
        os.makedirs(skills_path, exist_ok=True)
        os.makedirs(self.examples_dir, exist_ok=True)
        
        self._ensure_file()
        self._load_seed_skills()
    
    def _ensure_file(self):
        """Upewnia się, że plik istnieje."""
        if not os.path.exists(self.skills_file):
            with open(self.skills_file, 'w') as f:
                json.dump({"skills": [], "usage_count": {}}, f, indent=2)
    
    def _load_seed_skills(self):
        """Ładuje seed skills jeśli biblioteka jest pusta."""
        skills = self._load_skills()
        if not skills:
            self._add_seed_skills()
    
    def _add_seed_skills(self):
        """Dodaje przykładowe umiejętności."""
        seed_skills = [
            {
                "id": "refactor_long_function",
                "name": "Refaktoryzacja długiej funkcji",
                "task_types": ["code_quality", "refactor"],
                "steps": [
                    "Znajdź granice funkcji",
                    "Zidentyfikuj osobne odpowiedzialności",
                    "Wyekstrahuj subfunkcje",
                    "Zaktualizuj wywołania"
                ],
                "success_rate": 0.85,
                "times_used": 0
            },
            {
                "id": "fix_security_secret",
                "name": "Naprawienie exposed secrets",
                "task_types": ["security", "fix"],
                "steps": [
                    "Znajdź plik z secret",
                    "Zidentyfikuj typ secret",
                    "Przenieś do .env",
                    "Zaktualizuj kod"
                ],
                "success_rate": 0.95,
                "times_used": 0
            },
            {
                "id": "write_tests",
                "name": "Pisanie testów",
                "task_types": ["testing", "development"],
                "steps": [
                    "Zidentyfikuj funkcję do przetestowania",
                    "Napisz testy jednostkowe",
                    "Uruchom testy",
                    "Napraw błędy testów"
                ],
                "success_rate": 0.80,
                "times_used": 0
            }
        ]
        
        for skill in seed_skills:
            self.add_skill(skill)
    
    def add_skill(self, skill):
        """Dodaje nową umiejętność."""
        data = self._load_skills_data()
        
        skill_entry = {
            **skill,
            "created": datetime.now().isoformat(),
            "last_used": None
        }
        
        existing = self._find_skill(skill.get("id"))
        if existing:
            existing.update(skill_entry)
        else:
            data["skills"].append(skill_entry)
        
        self._save_skills_data(data)
        return skill_entry
    
    def get_skill(self, skill_id):
        """Pobiera umiejętność po ID."""
        data = self._load_skills_data()
        return self._find_skill(skill_id, data.get("skills", []))
    
    def find_skill_for_task(self, task_type):
        """Znajduje najlepszą umiejętność dla typu zadania."""
        data = self._load_skills_data()
        skills = data.get("skills", [])
        
        matching = [s for s in skills if task_type in s.get("task_types", [])]
        
        if not matching:
            return None
        
        matching.sort(key=lambda s: (
            s.get("success_rate", 0),
            s.get("times_used", 0)
        ), reverse=True)
        
        return matching[0]
    
    def record_usage(self, skill_id, success):
        """Rejestruje użycie umiejętności."""
        data = self._load_skills_data()
        skill = self._find_skill(skill_id, data.get("skills", []))
        
        if skill:
            skill["times_used"] = skill.get("times_used", 0) + 1
            skill["last_used"] = datetime.now().isoformat()
            
            if success:
                skill["success_rate"] = (
                    skill.get("success_rate", 0) * 0.9 + 0.1
                )
            else:
                skill["success_rate"] = (
                    skill.get("success_rate", 0) * 0.95
                )
        
        self._save_skills_data(data)
    
    def get_all_skills(self):
        """Zwraca wszystkie umiejętności."""
        return self._load_skills_data().get("skills", [])
    
    def _load_skills(self):
        return self._load_skills_data().get("skills", [])
    
    def _load_skills_data(self):
        try:
            with open(self.skills_file, 'r') as f:
                return json.load(f)
        except:
            return {"skills": [], "usage_count": {}}
    
    def _save_skills_data(self, data):
        with open(self.skills_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _find_skill(self, skill_id, skills=None):
        skills = skills or self._load_skills()
        return next((s for s in skills if s.get("id") == skill_id), None)
