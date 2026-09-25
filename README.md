# Towarzysz V9

Towarzysz analizuje projekty i przygotowuje rekomendacje. Domyślnie działa w Observer Mode. Moduły integracji istnieją, lecz ich trwałe skutki są blokowane przez bieżącą politykę.

Aktualny wynik: **96 PASS, 1 pominięty**. Szczegóły: [STATUS_AKTUALNY.md](STATUS_AKTUALNY.md).

Instalacja zależności testowych: `python3 -m pip install -r requirements-dev.txt` w wybranym środowisku wirtualnym.

## Architektura

```
OBSERVE → ROLES (SCOUT → ARCHITECT → BUILDER → CRITIC) → ANALYZE → PLAN → ALERTS → SAVE → SYNC → INTERACT → REFLECT
```

| Faza | Komponent | Opis |
|------|-----------|------|
| OBSERVE | `brain/observer.py` | Wykrywa zmiany w plikach (hash-based) |
| ROLES | `brain/roles/manager.py` | Cykl agentów: Scout (skan), Architect (plan), Builder (wykonanie), Critic (ewaluacja) |
| ANALYZE | `brain/analyzer.py` | Analiza AST Python, regex JS, wykrywanie problemów |
| PLAN | `brain/planner.py` | Generowanie zadań, priorytetyzacja, wybór fokusu |
| ALERTS | `brain/alerts.py` | Alerty stagnacji i przeterminowania |
| SAVE | `integrations/obsidian.py` | Zapis do Obsidian Vault |
| SYNC | `integrations/todoist.py` | Synchronizacja z Todoist |
| INTERACT | `brain/assistant.py` | Smart check-in, rekomendacje LLM |
| REFLECT | `brain/reflection/` | Samokrytyka, nauka na błędach |

## Struktura

```
towarzysz/
├── core/                    # Główna pętla i konfiguracja
│   ├── loop.py              # Daemon loop
│   ├── config.py            # Konfiguracja z .env
│   └── constants.py         # Stałe systemowe
├── brain/                   # Inteligencja
│   ├── analyzer.py          # Analiza projektów (AST, regex)
│   ├── planner.py           # Planowanie zadań
│   ├── assistant.py         # Interakcja + LLM
│   ├── alerts.py            # Alerty produktywności
│   ├── observer.py          # Detekcja zmian w plikach
│   ├── executor.py          # Wykonawca zadań
│   ├── project_discovery.py # Auto-odkrywanie projektów
│   ├── project_tracker.py   # Śledzenie postępu projektów
│   ├── project_manager.py   # Zarządzanie wieloma projektami
│   ├── project_recommender.py # Rekomendacje projektów
│   ├── roles/               # Agenci ról (Scout, Architect, Builder, Critic)
│   ├── planning/            # Dekompozycja celów, harmonogramowanie
│   └── reflection/          # Samokrytyka, nauka
├── integrations/
│   ├── obsidian.py          # Obsidian Vault
│   ├── todoist.py           # Todoist API
│   ├── standup.py           # Daily Standup
│   └── llm.py               # LLM (Groq / OpenAI / Anthropic)
├── memory/
│   ├── memory.py            # Pamięć centralna (singleton)
│   ├── project_memory.py    # Pamięć per-projekt
│   ├── short.py             # Pamięć krótkoterminowa (TTL)
│   ├── long.py              # Pamięć długoterminowa (JSON)
│   └── vector.py            # Pamięć wektorowa (JSON fallback)
├── tools/                   # System narzędzi
│   ├── executor.py          # Silnik wykonywania
│   ├── registry.py          # Rejestr narzędzi
│   ├── file_tools.py        # Operacje na plikach
│   ├── bash_tools.py        # Polecenia bash/python
│   ├── search_tools.py      # Wyszukiwanie (grep/find)
│   └── git_tools.py         # Operacje git
├── skills/                  # Biblioteka strategii
│   ├── library.py           # Magazyn skilli
│   └── selector.py          # Selekcja skilli
├── cli/commands.py          # Komendy interaktywne
├── reports/reporter.py      # Raporty dzienne
├── tests/                   # Testy regresyjne
├── main.py                  # Punkt wejścia
├── requirements.txt         # Zależności uruchomieniowe
└── requirements-dev.txt     # Zależności testowe
```

## Funkcje

### Multi-Agent (V9)
- **Scout** — skanuje pliki i środowisko
- **Architect** — planuje rozwiązania architektoniczne
- **Builder** — wykonuje zaplanowane zadania narzędziami
- **Critic** — ewaluuje wyniki i sugeruje poprawki
- **RoleManager** — orkiestruje cykl życia agentów

### Analiza kodu
- Parsowanie AST dla Pythona
- Wykrywanie: secrets, TODO/FIXME, długie funkcje, błędy składni
- Generowanie propozycji architektury i roadmap

### Pamięć trójpoziomowa (V9)
- **ShortMemory** — in-memory z TTL (cache kontekstu)
- **LongMemory** — trwała w plikach JSON
- **VectorMemory** — proste wyszukiwanie leksykalne w trwałym magazynie JSON

### System narzędzi (V9)
- File: odczyt/zapis/edycja plików
- Bash: interfejs istnieje, wykonanie jest blokowane
- Search: grep i find po projekcie
- Git: kontrolowane odczyty; add/commit są blokowane

### Produktywność
- Alerty stagnacji (CRITICAL / WARNING / INFO)
- Smart check-in co 30 min
- Rekomendacje LLM (Groq/OpenAI/Anthropic)
- Daily Standup o 6:00
- Project Intelligence dla nowych projektów

## Konfiguracja

```bash
cp .env.example .env
# Edytuj .env — dodaj klucze API
```

Zmienne opcjonalnych integracji (niewymagane w Observer Mode):
```env
TODOIST_API_TOKEN=your_todoist_token
GROQ_API_KEY=your_groq_key
```

## Uruchomienie

```bash
./run_da.sh                     # Jako daemon w tle
.venv/bin/python -B main.py     # Bezpośrednio
```

## CLI

| Komenda | Opis |
|---------|------|
| `/intel <projekt>` | Generuj Project Intelligence |
| `/focus` | Pokaż aktualny fokus |
| `/status` | Status systemu |
| `/plan` | Plan na dziś |
| `/now` | Co teraz? |
| `/help` | Lista komend |

## Testowanie

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B scripts/validate.py
```

## Integracje

| System | Zakres |
|--------|--------|
| **Obsidian** | Daily notes, Project Intelligence, Standup, dokumentacja |
| **Todoist** | Taski z priorytetami, etykietą FOCUS, deduplikacja |
| **LLM** | Groq (domyślnie), OpenAI, Anthropic |

## Bezpieczeństwo

- Domyślny start działa w `OBSERVER_MODE=true` i blokuje trwałe skutki.
- `AUTHORIZED_REPO` jest przejmowane wyłącznie ze środowiska procesu przed
  załadowaniem `.env`; brak poprawnej wartości oznacza brak zapisów.
- Kontrolowane zapisy są ograniczone do autoryzowanego repozytorium; blokowane
  są m.in. wyjścia przez `..`, symlinki, hardlinki, zagnieżdżone repozytoria i `.git`.
- Odczyty Git wyłączają hooki, filtry, zewnętrzne diffy, rekursję submodułów i
  formaty uruchamiające weryfikatory podpisów.
- PatchEngine nie wykonuje stagingu ani commitów.
- Jest to polityka aplikacyjna, nie sandbox systemu operacyjnego. R3/R4 i pełny
  przepływ jednorazowej zgody pozostają dalszym etapem hardeningu.

## Wersje

- **V9** — Multi-agent, pamięć 3-poziomowa, narzędzia, refleksja, skills
- **V8** — Refaktoryzacja, bezpieczeństwo, szczegółowe taski
- **V7** — Smart check-in, Project Intelligence
- **V4-V6** — Archiwum w `modules_archive/`

## Ograniczenia

Tylko jawne `OBSERVER_MODE=false` wyłącza obserwację; inne wartości pozostawiają blokadę. `auto_confirm=False` odmawia zastosowania patchy, lecz nie stanowi pełnego mechanizmu zgód. Ignorowanie submodułów ogranicza kompletność metryk Git. `run_da.sh` zapisuje log i PID niezależnie od polityki aplikacji. Do analizy bez tego launchera użyj `OBSERVER_MODE=true .venv/bin/python -B main.py --once`.
