import json
import os
from datetime import datetime
from core.config import MEMORY_PATH, ENABLE_TRENDS

class EfficiencyAnalyzer:
    def __init__(self):
        self.memory_path = MEMORY_PATH
        self.analytics_path = os.path.join(MEMORY_PATH, "analytics")

    def evaluate_task_efficiency(self, tasks):
        """Ocenia efektywność zadań na podstawie priorytetu i typu."""
        evaluated_tasks = []
        for t in tasks:
            # Domyślna ocena na podstawie priorytetu
            score = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}.get(t["priority"], 0.5)
            
            # Modyfikatory na podstawie typu
            if t.get("type") == "fix":
                score *= 1.1  # Naprawy są cenniejsze
            elif t.get("type") == "new_file":
                score *= 0.9  # Nowe pliki są mniej pilne
            
            # Ograniczenie do zakresu 0-1
            score = max(0.0, min(1.0, score))
            
            t["value_score"] = score
            evaluated_tasks.append(t)
        
        # Zbierz metryki dla trendów (jeśli włączone)
        if ENABLE_TRENDS:
            self._collect_trend_metrics(evaluated_tasks)
        
        self._log(evaluated_tasks, "efficiency")
        return evaluated_tasks

    def _collect_trend_metrics(self, tasks):
        """Zbiera metryki projektów do analizy trendów."""
        project_metrics = {}
        
        for task in tasks:
            project = task["project"]
            if project not in project_metrics:
                project_metrics[project] = {
                    "task_count": 0,
                    "total_value": 0,
                    "priority_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                }
            
            metrics = project_metrics[project]
            metrics["task_count"] += 1
            metrics["total_value"] += task.get("value_score", 0.5)
            metrics["priority_distribution"][task["priority"]] += 1
        
        # Zapisz metryki
        metrics_path = os.path.join(MEMORY_PATH, "trends", "project_metrics.json")
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        
        # Wczytaj istniejące metryki
        existing_metrics = {}
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    existing_metrics = json.load(f)
            except:
                pass
        
        # Połącz z nowymi metrykami
        timestamp = datetime.now().isoformat()
        for project, data in project_metrics.items():
            if project not in existing_metrics:
                existing_metrics[project] = []
            existing_metrics[project].append({
                "timestamp": timestamp,
                "avg_value": data["total_value"] / data["task_count"] if data["task_count"] > 0 else 0,
                "task_count": data["task_count"],
                "priority_distribution": data["priority_distribution"]
            })
            
            # Ogranicz do ostatnich 50 wpisów
            if len(existing_metrics[project]) > 50:
                existing_metrics[project] = existing_metrics[project][-50:]
        
        with open(metrics_path, 'w') as f:
            json.dump(existing_metrics, f, indent=2)

    def recommend_next_tasks(self, memory_lessons, current_tasks):
        """Generuje rekomendacje na podstawie historii i efektywności."""
        recommendations = []
        
        # Analiza zadań o niskiej efektywności
        low_efficiency_tasks = [t for t in current_tasks if t.get("value_score", 0) < 0.5]
        
        for t in low_efficiency_tasks:
            recommendations.append({
                "project": t["project"],
                "task": f"Przeanalizuj i popraw: {t['task']}",
                "priority": "MEDIUM",
                "type": "optimization",
                "value_score": 0.7
            })
        
        # Analiza lessons.txt pod kątem powtarzających się problemów
        if os.path.exists(memory_lessons):
            try:
                with open(memory_lessons, 'r') as f:
                    content = f.read()
                    # Prosta heurystyka: jeśli występuje "STAGNATION", dodaj zadanie przeglądu
                    if "STAGNATION" in content:
                        recommendations.append({
                            "project": "all",
                            "task": "Przegląd stagnacji projektów",
                            "priority": "HIGH",
                            "type": "review",
                            "value_score": 0.8
                        })
            except:
                pass
        
        self._log(recommendations, "recommendations")
        return recommendations

    def _log(self, data, name):
        """Zapisuje dane analityczne."""
        os.makedirs(self.analytics_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.analytics_path, f"{name}_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    analyzer = EfficiencyAnalyzer()
    
    # Test
    test_tasks = [
        {"project": "test", "task": "Fix bug", "priority": "HIGH", "type": "fix"},
        {"project": "test", "task": "New feature", "priority": "MEDIUM", "type": "development"}
    ]
    
    evaluated = analyzer.evaluate_task_efficiency(test_tasks)
    print("Ocena zadań:")
    for t in evaluated:
        print(f" - {t['task']}: {t['value_score']}")
    
    recommendations = analyzer.recommend_next_tasks("memory/lessons.txt", evaluated)
    print(f"\nRekomendacje: {len(recommendations)}")