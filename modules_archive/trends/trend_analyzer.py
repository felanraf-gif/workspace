import json
import os
from datetime import datetime, timedelta
from core.config import MEMORY_PATH

class TrendAnalyzer:
    def __init__(self):
        self.memory_path = MEMORY_PATH
        self.trends_path = os.path.join(MEMORY_PATH, "trends")

    def evaluate_project_trends(self, memory_analytics):
        """Ocenia trendy projektów na podstawie danych historycznych."""
        trends = {}
        
        # Wczytaj dane historyczne z analytics
        analytics_files = [f for f in os.listdir(memory_analytics) if f.startswith("efficiency_")]
        if not analytics_files:
            return trends
        
        # Sortuj pliki po dacie
        analytics_files.sort()
        
        # Analizuj ostatnie 10 plików
        for file in analytics_files[-10:]:
            file_path = os.path.join(memory_analytics, file)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                    for task in data:
                        project = task["project"]
                        if project not in trends:
                            trends[project] = {
                                "history": [],
                                "current_trend": 0,
                                "volatility": 0
                            }
                        
                        # Zapisz wartość taska
                        value = task.get("value_score", 0.5)
                        trends[project]["history"].append({
                            "date": file.split("_")[1].replace(".json", ""),
                            "value": value
                        })
            except:
                continue
        
        # Oblicz trendy dla każdego projektu
        for project, data in trends.items():
            history = data["history"]
            if len(history) >= 2:
                # Prosty trend: średnia różnica między ostatnimi wartościami
                recent_values = [h["value"] for h in history[-5:]]
                if len(recent_values) >= 2:
                    avg_diff = (recent_values[-1] - recent_values[0]) / len(recent_values)
                    data["current_trend"] = avg_diff
                    
                    # Zmienność (odchylenie standardowe)
                    mean_val = sum(recent_values) / len(recent_values)
                    variance = sum((x - mean_val) ** 2 for x in recent_values) / len(recent_values)
                    data["volatility"] = variance ** 0.5
        
        self._log(trends, "project_trends")
        return trends

    def recommend_new_projects(self, memory_lessons, trends):
        """Sugeruje nowe projekty na podstawie trendów i lekcji."""
        recommendations = []
        
        # Analiza trendów spadkowych (może wymagać interwencji)
        for project, data in trends.items():
            if data["current_trend"] < -0.1:  # Spadek wartości
                recommendations.append({
                    "project": project,
                    "task": f"Analiza spadku wartości projektu (trend: {data['current_trend']:.2f})",
                    "priority": "MEDIUM",
                    "type": "trend_review",
                    "trend_score": 0.5
                })
        
        # Analiza lessons.txt pod kątem sugestii nowych projektów
        if os.path.exists(memory_lessons):
            try:
                with open(memory_lessons, 'r') as f:
                    content = f.read()
                    if "new project" in content.lower():
                        recommendations.append({
                            "project": "all",
                            "task": "Rozważ utworzenie nowego projektu (sugestia z lekcji)",
                            "priority": "LOW",
                            "type": "new_project_suggestion",
                            "trend_score": 0.3
                        })
            except:
                pass
        
        self._log(recommendations, "project_recommendations")
        return recommendations

    def _log(self, data, name):
        """Zapisuje dane trendów."""
        os.makedirs(self.trends_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.trends_path, f"{name}_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    analyzer = TrendAnalyzer()
    
    # Test
    test_analytics = os.path.join(MEMORY_PATH, "analytics")
    trends = analyzer.evaluate_project_trends(test_analytics)
    print("Trendy projektów:")
    for project, data in trends.items():
        print(f" - {project}: trend={data['current_trend']:.2f}, volatility={data['volatility']:.2f}")
    
    recommendations = analyzer.recommend_new_projects("memory/lessons.txt", trends)
    print(f"\nRekomendacje: {len(recommendations)}")
    for rec in recommendations:
        print(f" - {rec['task']}")