"""
brain/roles/critic.py - Critic Role
Ocenia wyniki i sugeruje poprawki
"""

from datetime import datetime


class Critic:
    """Critic - ocenia wyniki i sugeruje ulepszenia."""
    
    def __init__(self):
        self.critique_history = []
    
    def critique(self, build_result, context=None):
        """
        Krytykuje wyniki Buildiera.
        
        Args:
            build_result: Wyniki od Buildiera
            context: Dodatkowy kontekst (opcjonalny)
            
        Returns:
            dict: Ocena i sugestie
        """
        critique = {
            "timestamp": datetime.now().isoformat(),
            "critic_role": "Critic",
            "verdict": "",
            "score": 0,
            "observations": [],
            "suggestions": [],
            "approved": False
        }
        
        summary = build_result.get("summary", {})
        total = summary.get("total", 0)
        success = summary.get("success", 0)
        failed = summary.get("failed", 0)
        
        if total == 0:
            critique["verdict"] = "NO_TASKS"
            critique["score"] = 0
            critique["observations"].append("Brak zadań do wykonania")
        else:
            success_rate = success / total if total > 0 else 0
            critique["score"] = int(success_rate * 100)
            
            if success_rate == 1.0:
                critique["verdict"] = "EXCELLENT"
                critique["approved"] = True
                critique["observations"].append(f"Wszystkie zadania wykonane ({success}/{total})")
            elif success_rate >= 0.8:
                critique["verdict"] = "GOOD"
                critique["approved"] = True
                critique["observations"].append(f"Dobry wynik ({success}/{total})")
            elif success_rate >= 0.5:
                critique["verdict"] = "NEEDS_IMPROVEMENT"
                critique["approved"] = False
                critique["observations"].append(f"Część zadań nie powiodła się ({failed}/{total})")
            else:
                critique["verdict"] = "POOR"
                critique["approved"] = False
                critique["observations"].append(f"Dużo niepowodzeń ({failed}/{total})")
        
        executions = build_result.get("executions", [])
        for exec_result in executions:
            if not exec_result.get("success"):
                error = exec_result.get("error", "Unknown error")
                task = exec_result.get("task", {})
                critique["suggestions"].append({
                    "task": task.get("action"),
                    "target": task.get("target"),
                    "issue": error
                })
        
        critique["recommendations"] = self._generate_recommendations(critique)
        
        self.critique_history.append(critique)
        
        return critique
    
    def _generate_recommendations(self, critique):
        """Generuje rekomendacje na podstawie oceny."""
        recommendations = []
        
        if critique["verdict"] in ["POOR", "NEEDS_IMPROVEMENT"]:
            recommendations.append("Rozważ mniejsze kroki w planowaniu")
            recommendations.append("Sprawdź logi błędów")
            
        if critique.get("suggestions"):
            recommendations.append("Przeanalizuj nieudane zadania")
            
        if critique["score"] >= 80:
            recommendations.append("Kontynuuj w podobny sposób")
            
        return recommendations
    
    def get_critique_history(self, limit=10):
        """Zwraca historię krytyki."""
        return self.critique_history[-limit:]
