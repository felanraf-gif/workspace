"""
brain/reflection/self_critic.py - Self Critic
Samokrytyka agenta - analiza własnych działań
"""

from datetime import datetime


class SelfCritic:
    """
    Samokrytyka - agent analizuje własne działania.
    
    Po każdym cyklu:
    - Co poszło dobrze?
    - Co można poprawić?
    - Jakie wzorce się pojawiają?
    """
    
    def __init__(self):
        self.self_analysis_history = []
        self.patterns = {
            "repeated_failures": [],
            "repeated_successes": [],
            "inefficient_approaches": []
        }
    
    def analyze(self, cycle_result, role_manager_status):
        """
        Przeprowadza samokrytykę cyklu.
        
        Args:
            cycle_result: Wynik cyklu RoleManagera
            role_manager_status: Status wszystkich ról
            
        Returns:
            dict: Analiza i rekomendacje
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "cycle_id": cycle_result.get("cycle_id"),
            "overall_status": cycle_result.get("overall_status"),
            "self_reflection": {
                "what_went_well": [],
                "what_could_improve": [],
                "patterns_identified": []
            },
            "improvement_suggestions": [],
            "confidence_score": 0
        }
        
        roles = cycle_result.get("roles", {})
        
        if roles.get("scout", {}).get("changes_found", 0) > 0:
            analysis["self_reflection"]["what_went_well"].append(
                f"Scout wykrył {roles['scout']['changes_found']} zmian"
            )
        
        if roles.get("builder", {}).get("success_rate", 0) > 0:
            analysis["self_reflection"]["what_went_well"].append(
                f"Builder wykonał {roles['builder']['success_rate']} zadań"
            )
        
        critic_score = roles.get("critic", {}).get("score", 0)
        if critic_score < 50:
            analysis["self_reflection"]["what_could_improve"].append(
                "Niska skuteczność - rozważ zmianę strategii"
            )
            self.patterns["inefficient_approaches"].append(cycle_result.get("cycle_id"))
        
        if len(self.patterns["repeated_failures"]) >= 3:
            analysis["self_reflection"]["patterns_identified"].append(
                "Powtarzające się błędy - wymaga analizy"
            )
        
        analysis["confidence_score"] = self._calculate_confidence(analysis)
        analysis["improvement_suggestions"] = self._generate_suggestions(analysis)
        
        self.self_analysis_history.append(analysis)
        self._update_patterns(cycle_result)
        
        return analysis
    
    def _calculate_confidence(self, analysis):
        """Oblicza poziom pewności agenta."""
        score = 50
        
        what_went_well = len(analysis["self_reflection"]["what_went_well"])
        score += what_went_well * 10
        
        what_could_improve = len(analysis["self_reflection"]["what_could_improve"])
        score -= what_could_improve * 15
        
        patterns = len(analysis["self_reflection"]["patterns_identified"])
        score -= patterns * 20
        
        return max(0, min(100, score))
    
    def _generate_suggestions(self, analysis):
        """Generuje sugestie poprawy."""
        suggestions = []
        
        if analysis["confidence_score"] < 30:
            suggestions.append("Rozważ mniejsze kroki w planowaniu")
            suggestions.append("Sprawdź czy narzędzia działają poprawnie")
        
        if len(self.patterns["repeated_failures"]) > 0:
            suggestions.append("Zidentyfikuj powtarzające się błędy")
        
        if analysis["overall_status"] == "NEEDS_ATTENTION":
            suggestions.append("Przeanalizuj krytykę od Critic")
        
        return suggestions
    
    def _update_patterns(self, cycle_result):
        """Aktualizuje wzorce."""
        roles = cycle_result.get("roles", {})
        
        builder = roles.get("builder", {})
        if builder.get("failed_count", 0) > builder.get("success_rate", 0):
            self.patterns["repeated_failures"].append(cycle_result.get("cycle_id"))
        elif builder.get("success_rate", 0) == builder.get("success_rate", 0) and builder.get("success_rate", 0) > 0:
            self.patterns["repeated_successes"].append(cycle_result.get("cycle_id"))
        
        if len(self.patterns["repeated_failures"]) > 10:
            self.patterns["repeated_failures"] = self.patterns["repeated_failures"][-5:]
    
    def get_self_analysis(self, limit=10):
        """Zwraca historię samokrytyki."""
        return self.self_analysis_history[-limit:]
    
    def get_patterns(self):
        """Zwraca zidentyfikowane wzorce."""
        return self.patterns
