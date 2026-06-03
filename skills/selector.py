"""
skills/selector.py - Skill Selector
Wybiera najlepszą umiejętność dla zadania
"""

from datetime import datetime


class SkillSelector:
    """
    SkillSelector - wybiera najlepszą umiejętność dla danego zadania.
    
    Kryteria wyboru:
    1. Dopasowanie typu zadania
    2. Historyczny wskaźnik sukcesu
    3. Częstotliwość użycia
    """
    
    def __init__(self, skill_library=None):
        if skill_library:
            self.library = skill_library
        else:
            from .library import SkillLibrary
            self.library = SkillLibrary()
    
    def select(self, task):
        """
        Wybiera najlepszą umiejętność dla zadania.
        
        Args:
            task: Dict z {"type", "description", "context"}
            
        Returns:
            dict: Wybrana umiejętność lub None
        """
        task_type = task.get("type", "")
        description = task.get("description", "")
        
        candidates = self._find_candidates(task_type, description)
        
        if not candidates:
            return None
        
        scored = []
        for skill in candidates:
            score = self._calculate_score(skill, task)
            scored.append((score, skill))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if scored:
            selected = scored[0][1]
            self.library.record_usage(selected.get("id"), None)
            return selected
        
        return None
    
    def _find_candidates(self, task_type, description):
        """Znajduje pasujące umiejętności."""
        all_skills = self.library.get_all_skills()
        
        if not task_type and not description:
            return all_skills
        
        candidates = []
        description_lower = description.lower()
        
        for skill in all_skills:
            skill_types = skill.get("task_types", [])
            
            type_match = task_type in skill_types
            
            keyword_match = any(
                keyword in description_lower
                for keyword in skill.get("keywords", [])
            )
            
            if type_match or keyword_match:
                candidates.append(skill)
        
        if not candidates:
            candidates = all_skills
        
        return candidates
    
    def _calculate_score(self, skill, task):
        """Oblicza wynik dopasowania."""
        score = 0
        
        success_rate = skill.get("success_rate", 0.5)
        score += success_rate * 50
        
        times_used = skill.get("times_used", 0)
        if times_used > 5:
            score += 20
        elif times_used > 0:
            score += 10
        
        task_type = task.get("type", "")
        if task_type in skill.get("task_types", []):
            score += 30
        
        return score
    
    def suggest_alternatives(self, task, n=3):
        """Sugeruje alternatywne umiejętności."""
        candidates = self._find_candidates(
            task.get("type", ""),
            task.get("description", "")
        )
        
        scored = []
        for skill in candidates:
            score = self._calculate_score(skill, task)
            scored.append((score, skill))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [s for _, s in scored[:n]]
