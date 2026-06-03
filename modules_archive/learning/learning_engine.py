import os
import json
from datetime import datetime, timedelta
from collections import defaultdict


class LearningEngine:
    def __init__(self, memory_path="memory"):
        self.memory_path = memory_path
        self.learning_file = os.path.join(memory_path, "analytics", "learning_data.json")
        self.patterns_file = os.path.join(memory_path, "decisions", "user_patterns.json")
        self._ensure_files()

    def _ensure_files(self):
        os.makedirs(os.path.join(self.memory_path, "analytics"), exist_ok=True)
        os.makedirs(os.path.join(self.memory_path, "decisions"), exist_ok=True)
        
        if not os.path.exists(self.learning_file):
            self._save_learning_data({"history": [], "stats": {}})
        if not os.path.exists(self.patterns_file):
            self._save_patterns({})

    def _load_learning_data(self):
        try:
            with open(self.learning_file, 'r') as f:
                return json.load(f)
        except:
            return {"history": [], "stats": {}}

    def _save_learning_data(self, data):
        with open(self.learning_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_patterns(self):
        try:
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_patterns(self, patterns):
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

    def record_task_completion(self, task, project, duration_minutes=0):
        data = self._load_learning_data()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "project": project,
            "duration_minutes": duration_minutes,
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday()
        }
        
        data["history"].append(entry)
        
        if len(data["history"]) > 1000:
            data["history"] = data["history"][-1000:]
        
        self._save_learning_data(data)
        self._update_patterns()

    def record_task_skipped(self, task, project):
        data = self._load_learning_data()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "project": project,
            "action": "skipped",
            "hour": datetime.now().hour
        }
        
        data["history"].append(entry)
        self._save_learning_data(data)

    def record_stagnation(self, project, days):
        data = self._load_learning_data()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "stagnation",
            "project": project,
            "days": days
        }
        
        data["history"].append(entry)
        self._save_learning_data(data)

    def _update_patterns(self):
        data = self._load_learning_data()
        history = data.get("history", [])
        
        if len(history) < 5:
            return

        patterns = {}

        hour_counts = defaultdict(int)
        for entry in history:
            if "hour" in entry:
                hour_counts[entry["hour"]] += 1
        
        if hour_counts:
            best_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns["best_working_hours"] = [h for h, _ in best_hours]

        day_counts = defaultdict(int)
        for entry in history:
            if "day_of_week" in entry:
                day_counts[entry["day_of_week"]] += 1
        
        if day_counts:
            best_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns["best_working_days"] = [d for d, _ in best_days]

        recent = [e for e in history if "duration_minutes" in e][-50:]
        if recent:
            avg_duration = sum(e.get("duration_minutes", 30) for e in recent) / len(recent)
            patterns["avg_task_duration_minutes"] = round(avg_duration)

        project_stats = defaultdict(lambda: {"completed": 0, "skipped": 0, "total": 0})
        for entry in history:
            if "project" in entry:
                project_stats[entry["project"]]["total"] += 1
                if entry.get("action") == "skipped":
                    project_stats[entry["project"]]["skipped"] += 1
                elif "duration_minutes" in entry:
                    project_stats[entry["project"]]["completed"] += 1

        patterns["project_completion_rates"] = {}
        for proj, stats in project_stats.items():
            if stats["total"] > 0:
                rate = stats["completed"] / stats["total"]
                patterns["project_completion_rates"][proj] = round(rate, 2)

        patterns["last_updated"] = datetime.now().isoformat()
        self._save_patterns(patterns)

    def get_recommendations(self):
        patterns = self._load_patterns()
        recommendations = []

        current_hour = datetime.now().hour
        best_hours = patterns.get("best_working_hours", [])
        
        if best_hours:
            if current_hour in best_hours:
                recommendations.append({
                    "type": "good_time",
                    "message": "Teraz jest dobry czas na pracę (zgodnie z Twoimi wzorcami).",
                    "priority": "high"
                })
            else:
                next_good = min([h for h in best_hours if h > current_hour] or best_hours)
                recommendations.append({
                    "type": "optimal_time_later",
                    "message": f"Najlepsze godziny pracy: {best_hours}. Następny szczyt: {next_good}:00",
                    "priority": "medium"
                })

        avg_duration = patterns.get("avg_task_duration_minutes", 0)
        if avg_duration > 0:
            if avg_duration > 120:
                recommendations.append({
                    "type": "task_size",
                    "message": f"Średni czas zadania: {int(avg_duration)} min. Rozważ mniejsze taski.",
                    "priority": "medium"
                })
            elif avg_duration < 30:
                recommendations.append({
                    "type": "task_size",
                    "message": f"Szybko kończysz ({int(avg_duration)} min). Możesz brać więcej.",
                    "priority": "low"
                })

        completion_rates = patterns.get("project_completion_rates", {})
        slow_projects = [(p, r) for p, r in completion_rates.items() if r < 0.5]
        if slow_projects:
            recommendations.append({
                "type": "problematic_projects",
                "message": f"Projekty z niskim completion rate: {[p for p,_ in slow_projects]}",
                "priority": "high"
            })

        return recommendations

    def get_productivity_score(self, days=7):
        data = self._load_learning_data()
        history = data.get("history", [])
        
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in history if datetime.fromisoformat(e["timestamp"]) > cutoff]
        
        if not recent:
            return {"score": 0, "tasks_completed": 0, "message": "Brak danych"}

        completed = len([e for e in recent if "duration_minutes" in e and e.get("duration_minutes", 0) > 0])
        skipped = len([e for e in recent if e.get("action") == "skipped"])
        stagnations = len([e for e in recent if e.get("type") == "stagnation"])

        score = 50
        score += completed * 10
        score -= skipped * 5
        score -= stagnations * 15
        
        score = max(0, min(100, score))

        return {
            "score": score,
            "tasks_completed": completed,
            "tasks_skipped": skipped,
            "stagnations": stagnations,
            "days": days,
            "message": self._score_message(score)
        }

    def _score_message(self, score):
        if score >= 80:
            return "Świetnie! Wysoka produktywność."
        elif score >= 60:
            return "Dobra praca. Tak trzymaj."
        elif score >= 40:
            return "Przeciętnie. Spróbuj się bardziej skupić."
        else:
            return "Niski wynik. Może warto zrobić mniejsze kroki?"

    def suggest_daily_task_limit(self):
        patterns = self._load_patterns()
        
        avg_duration = patterns.get("avg_task_duration_minutes", 60)
        current_hour = datetime.now().hour
        hours_left = max(0, 22 - current_hour)
        
        realistic_tasks = max(1, int(hours_left / (avg_duration / 60)))
        
        return min(realistic_tasks, 5)

    def get_learning_summary(self):
        patterns = self._load_patterns()
        productivity = self.get_productivity_score(7)
        recommendations = self.get_recommendations()
        
        return {
            "patterns": patterns,
            "productivity": productivity,
            "recommendations": recommendations,
            "daily_limit_suggestion": self.suggest_daily_task_limit()
        }

    def format_summary(self):
        summary = self.get_learning_summary()
        
        lines = ["## Uczenie się o Tobie\n"]
        
        prod = summary["productivity"]
        lines.append(f"### Produktywność (7 dni)")
        lines.append(f"- Wynik: **{prod['score']}**/100")
        lines.append(f"- Ukończone: {prod['tasks_completed']}")
        lines.append(f"- Pominięte: {prod['tasks_skipped']}")
        lines.append(f"- Stagnacje: {prod['stagnations']}")
        lines.append(f"- {prod['message']}\n")
        
        patterns = summary["patterns"]
        if patterns.get("best_working_hours"):
            lines.append(f"### Optymalne godziny")
            lines.append(f"- {patterns['best_working_hours']}\n")
        
        if summary["recommendations"]:
            lines.append("### Rekomendacje")
            for rec in summary["recommendations"]:
                lines.append(f"- [{rec['priority'].upper()}] {rec['message']}")
        
        return "\n".join(lines)
