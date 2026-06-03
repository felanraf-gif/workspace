"""
brain/planning/decomposer.py - Goal Decomposer
Dzieli duże cele na mniejsze zadania
"""

from datetime import datetime


class GoalDecomposer:
    """
    GoalDecomposer - rozkłada duże cele na mniejsze zadania.
    
    Przykład:
    Cel: "Napraw wszystkie błędy w projekcie"
    ↓
    Zadania:
    1. Znajdź wszystkie TODO/FIXME
    2. Priorytetyzuj błędy
    3. Napraw błędy HIGH
    4. Napraw błędy MEDIUM
    """
    
    def __init__(self):
        self.decomposition_history = []
    
    def decompose(self, goal, context=None):
        """
        Rozkłada cel na zadania.
        
        Args:
            goal: Cel główny (dict lub string)
            context: Kontekst (opcjonalny)
            
        Returns:
            dict: Rozkład celu na zadania
        """
        if isinstance(goal, str):
            goal = {"description": goal}
        
        goal_text = goal.get("description", "")
        
        decomposition = {
            "timestamp": datetime.now().isoformat(),
            "original_goal": goal_text,
            "goal_id": self._generate_id(),
            "tasks": [],
            "subtasks": [],
            "estimated_duration": 0
        }
        
        if self._is_complex_goal(goal_text):
            tasks = self._decompose_complex(goal_text, context)
        else:
            tasks = self._decompose_simple(goal_text)
        
        decomposition["tasks"] = tasks
        decomposition["estimated_duration"] = sum(t.get("estimated_minutes", 30) for t in tasks)
        
        self.decomposition_history.append(decomposition)
        
        return decomposition
    
    def _is_complex_goal(self, goal_text):
        """Sprawdza czy cel jest złożony."""
        complex_keywords = [
            "wszystkie", "napraw", "przebuduj", "zrefaktoryzuj",
            "全部", "napraw wszystkie", "rewrite", "implement"
        ]
        
        goal_lower = goal_text.lower()
        return any(keyword in goal_lower for keyword in complex_keywords)
    
    def _decompose_complex(self, goal_text, context):
        """Rozkłada złożony cel."""
        tasks = []
        
        goal_lower = goal_text.lower()
        
        if "napraw" in goal_lower:
            tasks.append({
                "id": self._generate_id(),
                "action": "analyze",
                "description": "Znajdź problemy",
                "estimated_minutes": 15,
                "priority": "HIGH"
            })
            tasks.append({
                "id": self._generate_id(),
                "action": "fix",
                "description": "Napraw zidentyfikowane problemy",
                "estimated_minutes": 60,
                "priority": "HIGH"
            })
        
        elif "refaktoryzuj" in goal_lower or "zrefaktoryzuj" in goal_lower:
            tasks.append({
                "id": self._generate_id(),
                "action": "identify",
                "description": "Zidentyfikuj kod do refaktoryzacji",
                "estimated_minutes": 20,
                "priority": "MEDIUM"
            })
            tasks.append({
                "id": self._generate_id(),
                "action": "refactor",
                "description": "Przeprowadź refaktoryzację",
                "estimated_minutes": 60,
                "priority": "MEDIUM"
            })
        
        else:
            tasks = self._decompose_simple(goal_text)
        
        return tasks
    
    def _decompose_simple(self, goal_text):
        """Rozkłada prosty cel."""
        return [{
            "id": self._generate_id(),
            "action": "execute",
            "description": goal_text,
            "estimated_minutes": 30,
            "priority": "MEDIUM"
        }]
    
    def _generate_id(self):
        import hashlib
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
