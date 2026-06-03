# Towarzysz V7 LEAN - Dokumentacja

## Struktura projektu (PROSTA)

```
towarzysz/

core/
    loop.py              (~165 linii) - główna pętla

brain/
    analyzer.py          (~500 linii) - analiza + work detection + Project Intelligence
    planner.py          (~320 linii) - planowanie + fokus + Todoist
    assistant.py        (~300 linii) - interakcja + nauka + Smart Check-in
    alerts.py           (~120 linii) - Productivity Alerts

cli/
    commands.py         (~180 linii) - CLI Commands

memory/
    memory.py           (~260 linii) - pamięć + time tracking

integrations/
    obsidian.py         (~230 linii) - zapis do Obsidian + Project Intelligence
    todoist.py          (~180 linii) - integracja Todoist
    standup.py         (~110 linii) - Daily Standup o 6:00

reports/
    reporter.py         (~90 linii) - raporty

RAZEM: ~2400 linii
```

## Nowe funkcje (V7.1)

### CLI Commands
```
/intel <projekt>   - Generuj Project Intelligence
/focus             - Pokaż aktualny focus
/status            - Status systemu i projektów
/plan              - Plan na dziś
/now               - Co teraz?
/help              - Lista komend
```

### Smart Check-in
- Kontekstowe pytania zależne od statusu
- Obsługuje: `1, 2, 3, 4` lub `done, working, blocked, skip`
- Informuje o stagnacji

### Project Changes Detection
- Wykrywa zmiany w plikach projektów
- Aktualizuje Project Intelligence automatycznie

### Daily Standup
- Generuje raport o 6:00 rano
- Zapisuje do `Daily/{date}_standup.md`

### Productivity Alerts
- Alerty w konsoli przy stagnacji
- Różne poziomy: CRITICAL, WARNING, INFO

## Zasady architektury

1. **Prostota** - każdy moduł ma jedną odpowiedzialność
2. **Konsolidacja** - łączenie podobnych funkcji
3. **Czytelność** - kod łatwy do zrozumienia i debugowania
4. **Stabilność** - mniej punktów awarii

## Konfiguracja

```python
# core/config.py
OBSIDIAN_PATH = "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant"
MEMORY_PATH = "memory"
TODOIST_API_TOKEN = "..."

# Limity
MAX_TASKS_PER_DAY = 5
INTERACTION_INTERVAL = 30  # minuty
```

## Główna pętla (core/loop.py)

```python
while True:
    # 1. ANALYZE
    projects = analyzer.scan_projects()
    issues = analyzer.detect_issues(projects)
    work_data = analyzer.evaluate_work(projects)
    
    # 1.5 PROJECT INTELLIGENCE (dla nowych projektów)
    for project in projects:
        if analyzer.is_new_project(project):
            intel = analyzer.get_project_intelligence(project)
            obsidian.save_project_intelligence(intel)
    
    # 2. PLAN
    tasks = planner.create_tomorrow_plan(projects, issues)
    focus_task = planner.select_focus_task(tasks)
    focus_message = planner.generate_message(...)
    
    # 3. OBSIDIAN
    obsidian.save_daily_note(focus_task, ...)
    
    # 4. TODOIST
    if memory.can_send_more_tasks():
        planner.send_to_todoist(tasks)
    
    # 5. INTERACTION (co 30 min)
    if assistant.should_checkin():
        assistant.prompt_checkin(focus_task)
    
    sleep(300)  # 5 minut
```

## Project Intelligence

### brain/analyzer.py - metody:

- `analyze_project_structure(project)` - analizuje strukturę
- `generate_architecture_proposal(project)` - generuje propozycję architektury
- `create_roadmap(project, architecture)` - tworzy roadmapę
- `is_new_project(project)` - sprawdza czy projekt jest nowy
- `get_project_intelligence(project)` - zwraca pełną analizę

### integrations/obsidian.py - metody:

- `save_project_intelligence(intelligence)` - zapisuje do Obsidian

### Output (Obsidian):

Zapisywany do: `Projects/{project_name}_intelligence.md`

Zawiera:
- Struktura projektu
- Sugerowana architektura
- Brakujące elementy
- Roadmap zadań (HIGH/MEDIUM/LOW)
- Focus task na dziś
- Estymacja czasu

## Brain Modules

### analyzer.py
- `scan_projects()` - skanuje projekty
- `detect_issues()` - wykrywa problemy
- `evaluate_work()` - ocenia postęp (REAL_WORK/LOW_PROGRESS/STAGNATION)

### planner.py
- `create_tomorrow_plan()` - tworzy plan zadań
- `select_focus_task()` - wybiera 1 fokus
- `generate_message()` - komunikaty systemowe
- `send_to_todoist()` - wysyła do Todoist
- `mark_focus()` - oznacza fokus w Todoist

### assistant.py
- `get_recommendations()` - rekomendacje na podst. wzorców
- `get_productivity_score()` - wynik 0-100
- `prompt_checkin()` - pyta o status (done/working/blocked/skip)
- `process_status()` - przetwarza odpowiedź
- `generate_suggestions()` - sugestie akcji
- `record_task_completion()` - zapisuje ukończenie

## Memory

### memory/memory.py
- `get_state()` / `save_state()` - stan systemu
- `add_history_entry()` - historia pracy
- `get_history()` - historia z X dni
- `get_work_trends()` - trendy
- `can_send_more_tasks()` - kontrola limitów
- `can_check_todoist_again()` - rate limiting

## Integrations

### integrations/obsidian.py
- `save_daily_note()` - notatka dzienna
- `save_focus_task()` - zapis fokusu
- `log_interaction()` - log interakcji
- `create_project_note()` - notatka projektu

### integrations/todoist.py
- `get_active_tasks()` - aktywne taski
- `create_task()` - tworzy task
- `close_task()` - zamyka task
- `add_label()` - dodaje etykietę (FOCUS)
- `sync_with_state()` - synchronizacja

## Raporty

### reports/reporter.py
- `generate_daily_report()` - raport dnia
- `generate_dashboard_md()` - dashboard

## Cykl życia

1. **Start** → Inicjalizacja wszystkich komponentów
2. **Analyze** → Skanuj projekty, wykryj zmiany
3. **Plan** → Stwórz plan, wybierz fokus
4. **Save** → Zapisz do Obsidian
5. **Sync** → Synchronizuj z Todoist
6. **Interact** → Check-in z użytkownikiem (co 30 min)
7. **Learn** → Zapisz wzorce
8. **Sleep** → 5 minut przerwy

## Migration Notes

Stara architektura (5000+ linii) została skonsolidowana do LEAN (1600 linii):

| Stare | Nowe |
|-------|------|
| modules/analyzer/ | brain/analyzer.py |
| modules/tracker/ | brain/analyzer.py |
| modules/intelligence/ | brain/analyzer.py |
| modules/planner/ | brain/planner.py |
| modules/guidance/ | brain/planner.py |
| modules/learning/ | brain/assistant.py |
| modules/interaction/ | brain/assistant.py |
| modules/memory/ | memory/memory.py |
| modules/reporter/ | integrations/obsidian.py + reports/reporter.py |
| modules/tools/ | (część w brain/) |

## Uruchomienie

```bash
python core/loop.py
```

## Testowanie

```bash
python -c "from brain.analyzer import Analyzer; a = Analyzer(); print(a.scan_projects())"
python -c "from brain.planner import Planner; p = Planner(); print(p.create_tomorrow_plan([], []))"
```
