"""
integrations/obsidian.py - Integracja z Obsidian
"""

import os
from datetime import datetime
from core.constants import STATUS_ICONS, PRIORITY_ICONS


class Obsidian:
    """Zapisuje notatki do Obsidian Vault."""
    
    def __init__(self, vault_path=None):
        self.vault_path = vault_path or "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant"
        self.daily_dir = os.path.join(self.vault_path, "Daily")
        self.projects_dir = os.path.join(self.vault_path, "Projects")
        self.interactions_dir = os.path.join(self.vault_path, "Interactions")
        
        os.makedirs(self.daily_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.interactions_dir, exist_ok=True)

    def save_daily_note(self, focus_task, message, work_status, projects, tasks, summary=None, agent_intel=None):
        """Zapisuje notatkę dzienną z szczegółowymi informacjami."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.daily_dir, f"{today}.md")
        
        focus_section = self._format_focus(focus_task, message)
        status_icon = STATUS_ICONS.get(work_status, "⚪")
        
        content = f"""# 📅 {today}

## Status
{status_icon} **{work_status}**

{focus_section}

"""
        
        if summary:
            content += f"## Analiza kodu\n{summary}\n\n"
        
        content += self._build_problems_section(agent_intel, tasks)
        
        content += "## Zadania na dziś\n"
        for t in tasks[:5]:
            icon = PRIORITY_ICONS.get(t.get('priority', 'LOW'), '⚪')
            content += f"- {icon} [{t.get('project', '')}] {t.get('task', '')}\n"
            if t.get('reason'):
                content += f"  → {t['reason']}\n"
            
            content += self._build_task_details(t)
        
        content += f"\n## Sugestie\n{message}\n"
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"[OBSIDIAN] Błąd zapisu: {e}")
        
        return filename
    
    def _build_problems_section(self, agent_intel, tasks):
        """Buduje sekcję z szczegółami problemów."""
        if not agent_intel:
            return ""
        
        issues = agent_intel.get("issues", [])
        if not issues:
            return ""
        
        content = "## 🔍 Szczegóły problemów\n\n"
        
        secrets = []
        todos = []
        long_functions = []
        
        for issue in issues:
            if issue.get("type") == "security" and issue.get("secrets"):
                secrets.extend(issue.get("secrets", []))
            elif issue.get("type") == "technical_debt" and issue.get("todos"):
                todos.extend(issue.get("todos", []))
            elif issue.get("type") == "code_quality" and issue.get("functions"):
                long_functions.extend(issue.get("functions", []))
        
        if secrets:
            content += "### 🔐 Bezpieczeństwo\n\n"
            content += "| Plik | Typ |\n"
            content += "|------|-----|\n"
            for s in secrets[:5]:
                content += f"| `{s.get('file', '?')}` | {s.get('type', '?')} |\n"
            content += "\n"
        
        if todos:
            content += "### 📋 TODO/FIXME do zrobienia\n\n"
            for i, t in enumerate(todos[:10], 1):
                content += f"{i}. `[{t.get('file', '?')}]` {t.get('type', 'TODO')}: {t.get('content', '?')}\n"
            content += "\n"
        
        if long_functions:
            content += "### ⚠️ Długie funkcje (refaktoryzacja)\n\n"
            for f in long_functions[:5]:
                content += f"- `{f.get('function', '?')}()` - **{f.get('lines', '?')} linii** w `{f.get('file', '?')}`\n"
            content += "\n"
        
        return content
    
    def _build_task_details(self, task):
        """Buduje szczegóły dla pojedynczego tasku."""
        issue_details = task.get('issue_details', {})
        task_type = task.get('type', '')
        content = ""
        
        if task_type == 'security' and issue_details.get('secrets'):
            content += "  **Szczegóły:**\n"
            for s in issue_details['secrets'][:3]:
                content += f"  - `{s.get('file')}` ({s.get('type')})\n"
        
        elif task_type == 'technical_debt' and issue_details.get('todos'):
            content += "  **Komentarze w kodzie:**\n"
            for td in issue_details['todos'][:3]:
                content += f"  - `[{td.get('file')}]` {td.get('content')}\n"
        
        elif task_type == 'code_quality' and issue_details.get('functions'):
            content += "  **Do refaktoryzacji:**\n"
            for fn in issue_details['functions'][:3]:
                content += f"  - `{fn.get('function')}()` - {fn.get('lines')}ln\n"
        
        return content

    def save_focus_task(self, focus_task):
        """Zapisuje aktualny focus task."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.daily_dir, f"{today}_focus.md")
        
        if not focus_task:
            content = "# Focus\n\nBrak aktywnego focus taska.\n"
        else:
            content = f"""# Focus

**Projekt:** {focus_task.get('project', 'N/A')}
**Task:** {focus_task.get('task', 'N/A')}
**Priorytet:** {focus_task.get('priority', 'LOW')}
**Time:** {datetime.now().strftime('%H:%M')}

"""
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except:
            pass

    def log_interaction(self, action, task, message):
        """Zapisuje interakcję."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.interactions_dir, f"{today}_interactions.md")
        
        content = f"\n## {datetime.now().strftime('%H:%M:%S')}\n\n"
        content += f"**Akcja:** {action.upper()}\n"
        if task:
            content += f"**Task:** [{task.get('project', '')}] {task.get('task', '')}\n"
        content += f"**Wiadomość:** {message}\n"
        
        try:
            with open(filename, 'a') as f:
                f.write(content)
        except:
            pass

    def create_project_note(self, project_name, data):
        """Tworzy notatkę projektu."""
        filename = os.path.join(self.projects_dir, f"{project_name}.md")
        
        content = f"# {project_name}\n\n"
        content += f"**Utworzono:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        if data.get("status"):
            content += f"**Status:** {data['status']}\n"
        if data.get("last_update"):
            content += f"**Ostatnia aktualizacja:** {data['last_update']}\n"
        if data.get("issues"):
            content += f"\n## Problemy\n"
            for issue in data['issues']:
                content += f"- {issue}\n"
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except:
            pass

    def _format_focus(self, focus_task, message):
        if not focus_task:
            return "## 🎯 Focus\n\n*Brak focus taska*\n"
        
        project = focus_task.get("project", "N/A")
        task = focus_task.get("task", "N/A")
        priority = focus_task.get("priority", "LOW")
        icon = PRIORITY_ICONS.get(priority, "⚪")
        
        return f"""## 🎯 Focus

{icon} **[{project}]** {task}

## ⚠️ Komunikat

{message}
"""

    def save_project_intelligence(self, intelligence):
        """Zapisuje pełną analizę projektu (Project Intelligence)."""
        project_name = intelligence.get("project", "unknown")
        architecture = intelligence.get("architecture", {})
        roadmap = intelligence.get("roadmap", {})
        structure = intelligence.get("structure", {})
        
        filename = os.path.join(self.projects_dir, f"{project_name}_intelligence.md")
        
        content = self._build_intel_header(project_name)
        content += self._build_structure_section(structure)
        content += self._build_architecture_section(architecture)
        content += self._build_roadmap_section(roadmap)
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except:
            pass
        
        return filename
    
    def _build_intel_header(self, project_name):
        """Buduje nagłówek Project Intelligence."""
        return f"""# 🏗 {project_name} - Project Intelligence

**Wygenerowano:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    
    def _build_structure_section(self, structure):
        """Buduje sekcję struktury projektu."""
        return f"""## Struktura projektu

| Właściwość | Wartość |
|------------|---------|
| Język | {structure.get('language', 'nieznany')} |
| Plików | {len(structure.get('file_types', {}))} |
| Złożoność | {structure.get('complexity', 'nieznana')} |
| Katalogi | {', '.join(structure.get('directories', [])[:5]) or 'brak'} |

"""
    
    def _build_architecture_section(self, architecture):
        """Buduje sekcję architektury."""
        content = "## Architektura\n\n"
        
        if architecture.get("suggested_structure"):
            content += "### Sugerowana struktura\n\n"
            for item in architecture.get("suggested_structure", []):
                content += f"```\n{item}\n```\n"
        
        content += "\n### Główne pliki\n\n"
        content += f"- **Main:** `{architecture.get('main_file', 'brak')}`\n"
        if architecture.get("config_file"):
            content += f"- **Config:** `{architecture.get('config_file')}`\n"
        
        if architecture.get("missing"):
            content += "\n### Brakujące elementy\n\n"
            for item in architecture["missing"]:
                content += f"- ❌ {item}\n"
        
        if architecture.get("suggestions"):
            content += "\n### Sugestie\n\n"
            for s in architecture["suggestions"]:
                content += f"- 💡 {s}\n"
        
        return content
    
    def _build_roadmap_section(self, roadmap):
        """Buduje sekcję roadmapy."""
        content = "\n## Roadmap\n\n"
        
        for i, task in enumerate(roadmap.get("tasks", []), 1):
            icon = PRIORITY_ICONS.get(task.get("priority", "LOW"), "⚪")
            content += f"### {i}. {icon} {task.get('task', 'brak')}\n\n"
            content += f"- **Opis:** {task.get('description', '')}\n"
            content += f"- **Priorytet:** {task.get('priority', 'LOW')}\n"
            content += f"- **Estymacja:** {task.get('estimated_minutes', 0)} min\n\n"
        
        content += f"\n**Łączny czas:** {roadmap.get('total_estimated_minutes', 0)} min\n"
        
        focus = roadmap.get("focus_task")
        if focus:
            content += f"\n## 🎯 Focus na dziś\n\n"
            content += f"**{focus.get('task', '')}** - {focus.get('description', '')}\n"
        
        return content

    def intelligence_exists(self, project_name):
        """Sprawdza czy plik Project Intelligence już istnieje."""
        filepath = os.path.join(self.projects_dir, f"{project_name}_intelligence.md")
        return os.path.exists(filepath)
    
    def update_project_changes(self, project_name, changes):
        """Aktualizuje Project Intelligence o nowe zmiany."""
        filepath = os.path.join(self.projects_dir, f"{project_name}_intelligence.md")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            changes_section = f"""

---

## 🔄 Ostatnie zmiany ({datetime.now().strftime('%Y-%m-%d %H:%M')})

"""
            if changes.get('new_files'):
                changes_section += "### Nowe pliki:\n"
                for f in changes['new_files'][:5]:
                    changes_section += f"- 📄 `{f}`\n"
                changes_section += "\n"
            
            if changes.get('changed_files'):
                changes_section += "### Zmienione pliki:\n"
                for f in changes['changed_files'][:5]:
                    changes_section += f"- ✏️ `{f}`\n"
                changes_section += "\n"
            
            if changes.get('message'):
                changes_section += f"**Info:** {changes['message']}\n"
            
            content += changes_section
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            return filepath
        except:
            return None

    def save_agent_documentation(self):
        """Zapisuje dokumentację wszystkich modułów agenta."""
        filename = os.path.join(self.projects_dir, "towarzysz_dokumentacja.md")
        
        content = f"""# Dokumentacja Towarzysz V8

**Wygenerowano:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Architektura

**Typ:** AI Agent (Python)
**Przepływ główny:** ANALYZE → PLAN → ALERTS → SAVE → SYNC → INTERACT

---

## Moduł: core/loop.py

**Opis:** Główna pętla systemu - koordynuje wszystkie moduły

### Funkcje:

- `safe_print(*args, **kwargs)` - Bezpieczne printowanie z obsługą BrokenPipeError
- `_log_to_file(msg)` - Zapisuje do pliku daemon.log jako fallback
- `main_loop()` - Główna pętla z 6 fazami

---

## Moduł: brain/analyzer.py

**Opis:** Inteligentna analiza projektów - AST parsing, wykrywanie problemów, generowanie roadmap

### Funkcje publiczne:

- `analyze_agent_code()` - Analizuje własny kod agenta
- `scan_projects()` - Skanuje projekty i wykrywa zmiany
- `detect_issues(projects)` - Wykrywa problemy w kodzie
- `evaluate_work(projects)` - Ocenia pracę projektów
- `analyze_project_structure(project)` - Analizuje strukturę projektu
- `generate_architecture_proposal(project)` - Generuje propozycję architektury
- `create_roadmap(project, architecture)` - Tworzy roadmapę
- `is_new_project(project)` - Sprawdza czy projekt jest nowy
- `get_project_intelligence(project)` - Zwraca pełną analizę projektu

### Funkcje prywatne (szczegóły implementacji):

- `_analyze_project_deep(project)` - Głęboka analiza plików
- `_analyze_python_file(file_info, project_name)` - Parsowanie AST Python
- `_analyze_js_file(file_info, project_name)` - Analiza JS/TS
- `_detect_project_type(imports)` - Wykrywanie typu projektu
- `_find_string_imports(content)` - Importy dynamiczne
- `_has_entry_point(python_files)` - Sprawdzanie punktu wejścia
- `_calculate_project_score(project, completed_tasks, project_name)` - Obliczanie score
- `_get_stagnation_days(project_name)` - Dni stagnacji
- `_get_status(score)` - Status: REAL_WORK/LOW_PROGRESS/STAGNATION
- `_get_todoist_completed(since_days)` - Pobieranie tasków z Todoist
- `_generate_agent_architecture()` - Architektura AI Agenta
- `_generate_web_api_architecture()` - Architektura Web API
- `_generate_cli_architecture()` - Architektura CLI
- `_generate_scraper_architecture()` - Architektura Web Scraper
- `_generate_ai_ml_architecture()` - Architektura AI/ML
- `_find_missing_components()` - Brakujące komponenty
- `_generate_suggestions()` - Inteligentne sugestie
- `_get_todos_as_tasks()` - Konwersja TODO/FIXME na taski
- `_get_security_issues()` - Wykrywanie problemów bezpieczeństwa
- `_select_smart_focus()` - Wybór fokus taska
- `_generate_summary()` - Generowanie podsumowania

---

## Moduł: brain/planner.py

**Opis:** Planowanie zadań i zarządzanie fokusem

### Funkcje publiczne:

- `create_tomorrow_plan(projects, issues)` - Generuje plan zadań
- `create_tomorrow_plan_from_intelligence(intel)` - Plan z Project Intelligence
- `select_focus_task(tasks)` - Wybiera najważniejszy task
- `generate_message(status, work_data, tasks)` - Komunikaty systemowe
- `send_to_todoist(tasks, due_date)` - Wysyła zadania do Todoist
- `close_task(task_content)` - Zamyka task w Todoist
- `mark_focus(task_content)` - Oznacza jako FOCUS
- `save_focus_log(focus_task, message, status)` - Zapisuje log focusa
- `get_today_focus()` - Pobiera focus z dzisiaj
- `get_task_content(task)` - Treść tasku dla Todoist

### Funkcje prywatne:

- `_issue_to_task(issue)` - Konwersja issue na task
- `_build_detailed_task_content(task)` - Szczegółowa treść tasku
- `_load_focus_log()` - Ładowanie logu focusa

---

## Moduł: brain/assistant.py

**Opis:** Interakcja z użytkownikiem, nauka wzorców, LLM rekomendacje

### Funkcje publiczne:

- `record_task_completion(task, project, duration)` - Zapisuje ukończenie
- `record_task_skipped(task, project)` - Zapisuje pominięcie
- `get_recommendations()` - Rekomendacje na podstawie wzorców
- `get_productivity_score(days)` - Wynik produktywności 0-100
- `suggest_daily_limit()` - Sugeruje limit tasków na dzień
- `get_proactive_suggestions(project_state)` - Proaktywne sugestie
- `detect_context_switches()` - Wykrywanie zmian kontekstu
- `suggest_project_focus()` - Sugestia skupienia na projekcie
- `should_checkin(last_check, interval_minutes)` - Czy czas na check-in
- `prompt_checkin(focus_task, work_data, cycles)` - Smart check-in
- `process_status(status, focus_task)` - Przetwarza odpowiedź
- `generate_suggestions(focus_task, work_status)` - Generuje sugestie
- `handle_breakdown(task)` - Rozbiera task na mniejsze kroki

### Funkcje prywatne:

- `_get_llm_recommendation()` - Rekomendacja z LLM
- `_generate_smaller_step(task)` - Mniejszy krok dla zablokowanego
- `_update_patterns()` - Aktualizacja wzorców
- `_log_interaction(result)` - Logowanie interakcji
- `_load_learning()` / `_save_learning()` - Zarządzanie danymi uczenia
- `_load_patterns()` / `_save_patterns()` - Zarządzanie wzorcami

---

## Moduł: brain/alerts.py

**Opis:** Sprawdzanie i raportowanie alertów produktywności

### Funkcje publiczne:

- `check(work_data, focus_task, state)` - Sprawdza warunki alertów
- `format_alerts(alerts)` - Formatuje alerty do konsoli

### Funkcje prywatne:

- `_check_stagnation(work_data)` - Sprawdza stagnację
- `_check_overdue(focus_task, state)` - Sprawdza overdue
- `_check_no_focus(focus_task)` - Sprawdza brak focusa
- `_check_good_progress(work_data)` - Sprawdza dobry postęp

---

## Moduł: integrations/obsidian.py

**Opis:** Zapisywanie notatek do Obsidian Vault

### Funkcje publiczne:

- `save_daily_note(focus_task, message, work_status, projects, tasks, summary, agent_intel)` - Notatka dzienna
- `save_focus_task(focus_task)` - Zapisuje focus task
- `log_interaction(action, task, message)` - Loguje interakcję
- `create_project_note(project_name, data)` - Tworzy notatkę projektu
- `save_project_intelligence(intelligence)` - Zapisuje Project Intelligence
- `intelligence_exists(project_name)` - Sprawdza czy istnieje
- `update_project_changes(project_name, changes)` - Aktualizuje o zmiany
- `save_agent_documentation()` - Zapisuje tę dokumentację

### Funkcje prywatne:

- `_build_problems_section()` - Buduje sekcję problemów
- `_build_task_details()` - Buduje szczegóły tasku
- `_format_focus()` - Formatuje sekcję Focus

---

## Moduł: integrations/todoist.py

**Opis:** Komunikacja z Todoist API

### Funkcje publiczne:

- `get_active_tasks(project_id)` - Pobiera aktywne taski
- `get_completed_tasks(since_days)` - Pobiera ukończone taski
- `create_task(content, project_id, priority, labels, due_date)` - Tworzy task
- `close_task(task_id)` - Zamyka task
- `update_task(task_id, updates)` - Aktualizuje task
- `add_label(task_id, label)` - Dodaje etykietę
- `get_project_id(project_name)` - Pobiera ID projektu
- `sync_with_state(tasks)` - Synchronizuje taski
- `get_stats()` - Zwraca statystyki

### Funkcje prywatne:

- `_safe_request(method, url, **kwargs)` - Bezpieczny request
- `_get_project_id(project_name)` - Pobiera/tworzy projekt
- `_get_task(task_id)` - Pobiera pojedynczy task

---

## Moduł: integrations/standup.py

**Opis:** Generowanie porannego standup o 6:00

### Funkcje publiczne:

- `should_run()` - Sprawdza czy to godzina 6:00
- `was_run_today()` - Sprawdza czy standup był dziś
- `generate(focus_task, projects, work_data, planner)` - Generuje raport

---

## Moduł: memory/memory.py

**Opis:** Singleton - centralna pamięć systemu

### Funkcje publiczne:

- `get_state()` - Pobiera stan systemu
- `save_state(updates)` - Aktualizuje stan
- `add_history_entry(status, score, tasks, projects)` - Dodaje wpis historii
- `get_history(days)` - Pobiera historię pracy
- `get_work_trends()` - Analizuje trendy
- `archive_old_files()` - Archiwizuje stare plany
- `clear_old_cache()` - Czyści cache
- `get_daily_time(date_str)` - Czas pracy dla dnia
- `save_daily_time(project, duration)` - Zapisuje czas pracy
- `log_time_event(event_type, task)` - Loguje zdarzenie czasowe
- `get_cycles_without_progress()` - Cykle bez postępu
- `increment_cycles_without_progress()` - Zwiększa licznik
- `reset_cycles_without_progress()` - Resetuje licznik
- `get_last_completed_task()` - Ostatni ukończony task
- `set_last_completed_task(task)` - Ustawia ostatni ukończony
- `can_check_todoist_again(minutes)` - Rate limiting Todoist
- `can_send_more_tasks(max_daily)` - Limit dzienny tasków

---

## Podsumowanie

| Moduł | Funkcje publiczne | Funkcje prywatne |
|-------|------------------|------------------|
| core/loop.py | 3 | 1 |
| brain/analyzer.py | 9 | 19 |
| brain/planner.py | 10 | 3 |
| brain/assistant.py | 14 | 6 |
| brain/alerts.py | 2 | 4 |
| integrations/obsidian.py | 8 | 3 |
| integrations/todoist.py | 9 | 3 |
| integrations/standup.py | 3 | 0 |
| memory/memory.py | 18 | 1 |

**RAZEM:** 9 modułów | ~76 funkcji publicznych | ~40 funkcji prywatnych

---
*Wygenerowano automatycznie przez Towarzysz V8*
"""
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"[OBSIDIAN] Błąd zapisu dokumentacji: {e}")
            return None
    
    def save_project_note(self, project_name, progress, recommendations):
        """Zapisuje notatkę per-projekt do Obsidian."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.projects_dir, f"{project_name}.md")
        
        status = progress.get("status", "unknown")
        status_icon = STATUS_ICONS.get(status, "⚪")
        
        git = progress.get("git_metrics", {})
        code = progress.get("code_metrics", {})
        activity = progress.get("activity_metrics", {})
        
        content = f"""# {project_name}

## Status
- **Status:** {status_icon} {status.upper()}
- **Typ:** {progress.get("type", "unknown")}
- **Ostatnia aktualizacja:** {today}

## Metryki Git
- Commity (7d): {git.get("commits_last_7d", 0)}
- Commity (30d): {git.get("commits_last_30d", 0)}
- Ostatni commit: {git.get("last_commit_date", "brak")}
- Branch'e: {len(git.get("branches", []))}
- Nie commits: {"Tak" if git.get("has_uncommitted") else "Nie"}

## Metryki kodu
- Plików: {code.get("files_count", 0)}
- Linii kodu: {code.get("total_lines", 0)}

## Aktywność
- Dni od edycji: {activity.get("days_since_edit", "?")}
- Commity/dzień (7d): {activity.get("edit_frequency_7d", 0)}

## Rekomendacje

"""
        
        if recommendations:
            for rec in recommendations[:5]:
                priority = rec.get("priority", "LOW")
                icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
                content += f"{icon} **{rec.get('title', '?')}**\n"
                content += f"   {rec.get('description', '')}\n"
                content += f"   → {rec.get('action', '')}\n\n"
        else:
            content += "Brak rekomendacji.\n"
        
        content += f"""
---
*Wygenerowano: {today}*
"""
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"[OBSIDIAN] Błąd zapisu notatki projektu {project_name}: {e}")
            return None
    
    def save_multi_project_dashboard(self, projects_summary):
        """Zapisuje dashboard wielu projektów."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.projects_dir, "dashboard.md")
        
        content = f"""# 🌐 Multi-Project Dashboard

**Wygenerowano:** {today}

## Podsumowanie projektów

| Projekt | Status | Typ | Rekomendacje |
|--------|--------|-----|--------------|
"""
        
        for proj in projects_summary.get("projects", []):
            status = proj.get("status", "unknown")
            status_icon = STATUS_ICONS.get(status, "⚪")
            recs_count = proj.get("recommendations_count", 0)
            content += f"| {proj.get('name')} | {status_icon} {status} | {proj.get('type')} | {recs_count} |\n"
        
        content += f"""
## Statystyki

- **Wszystkie:** {projects_summary.get('total', 0)}
- **Aktywne:** {projects_summary.get('active', 0)}
- **Stagnant:** {projects_summary.get('stagnant', 0)}
- **Porzucone:** {projects_summary.get('abandoned', 0)}
- **Wymagają uwagi:** {projects_summary.get('needs_attention', 0)}

---
*Wygenerowano automatycznie przez Towarzysz V9*
"""
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"[OBSIDIAN] Błąd zapisu dashboardu: {e}")
            return None
