# Towarzysz V8

Inteligentny agent-asystent deweloperski, który analizuje własny kod, planuje zadania i zarządza produktywnością.

## Architektura

**Typ:** AI Agent (Python)  
**Przepływ główny:** `ANALYZE → PLAN → ALERTS → SAVE → SYNC → INTERACT`

## Struktura projektu

```
towarzysz/
├── core/
│   ├── loop.py          # Główna pętla systemu
│   ├── config.py        # Konfiguracja (z .env)
│   └── constants.py     # Stałe systemowe
├── brain/
│   ├── analyzer.py       # Analiza projektów (V8 - z refaktoryzacją)
│   ├── planner.py       # Planowanie zadań
│   ├── assistant.py     # Interakcja z użytkownikiem i LLM
│   └── alerts.py        # Alerty produktywności
├── integrations/
│   ├── obsidian.py      # Integracja z Obsidian Vault (V8 - z refaktoryzacją)
│   ├── todoist.py       # Integracja z Todoist API
│   ├── standup.py       # Generowanie Daily Standup (V8 - z refaktoryzacją)
│   └── llm.py          # Integracja LLM (Groq/OpenAI)
├── memory/
│   └── memory.py        # Centralna pamięć systemu (Singleton)
├── tests/               # Testy (18 testów, wszystkie przechodzą)
│   ├── test_brain.py
│   ├── test_integrations.py
│   └── test_memory.py
├── cli/
│   └── commands.py       # CLI Commands
├── modules_archive/      # Archiwum starego kodu (V4-V7)
└── main.py              # Punkt wejścia
```

## Funkcje

### Analiza projektów
- Skanowanie plików Python/JavaScript
- AST parsing dla głębokiej analizy
- Wykrywanie problemów:
  - 🔐 Secrets (API keys, tokens) - **maskowane w output**
  - 📋 TODO/FIXME/BUG comments
  - ⚠️ Długie funkcje (>50 linii)
- Generowanie propozycji architektury
- Tworzenie roadmapy zadań

### Planowanie
- Automatyczne generowanie tasków z analizy
- Priorytetyzacja (HIGH/MEDIUM/LOW)
- Wybór fokus taska
- Wysyłanie do Todoist z etykietami
- **Szczegółowe opisy** - plik, typ problemu, bez eksponowania secrets

### Produktywność
- Alerty stagnacji projektów
- Smart check-in (co 30 min)
- Rekomendacje oparte na LLM
- Analiza trendów pracy

## Konfiguracja

### Zmienne środowiskowe (.env)

Utwórz plik `.env` w głównym katalogu:

```bash
cp .env.example .env
# Edytuj .env i dodaj swoje klucze API
```

### Zmienne wymagane:

```env
# API Tokens
TODOIST_API_TOKEN=your_todoist_token
GROQ_API_KEY=your_groq_key

# Opcjonalne
OBSIDIAN_PATH=/path/to/vault
LLM_PROVIDER=groq
```

### Stałe (core/constants.py)

```python
CHECKIN_INTERVAL_MINUTES = 30    # Interwał check-in
SCAN_INTERVAL_SECONDS = 300     # Skanowanie co 5 minut
MAX_DAILY_TASKS = 5             # Maksymalna liczba tasków/dzień
STAGNATION_THRESHOLD_DAYS = 3   # Próg stagnacji
```

## Uruchomienie

```bash
# Używając środowiska tor_env
./run_da.sh

# Lub bezpośrednio
tor_env/bin/python main.py
```

## Testowanie

```bash
# Uruchom wszystkie testy
tor_env/bin/python -m pytest tests/ -v

# Wynik: 18 testów, wszystkie przechodzą
```

## Integracje

### Obsidian Vault

| Typ | Lokalizacja |
|-----|-------------|
| Daily notes | `Daily/YYYY-MM-DD.md` |
| Projects | `Projects/{project}_intelligence.md` |
| Documentation | `Projects/towarzysz_dokumentacja.md` |
| Standup | `Daily/{date}_standup.md` |

### Todoist

- Tworzenie tasków z priorytetami (4=HIGH, 3=MEDIUM, 2=LOW)
- Etykiety: `development`, `assistant`
- Label `FOCUS` dla aktualnego focus taska
- **Taski zawierają szczegóły** - plik, typ, bez secrets

## Bezpieczeństwo

- ✅ Secrets maskowane w output (tylko typ pliku, nie wartość)
- ✅ Tokeny w osobnym pliku `.env` (nie w git)
- ✅ `.gitignore` zawiera `.env`, logi, cache

## Refaktoryzacja (V8)

### Zrefaktoryzowane funkcje:

| Funkcja | Linie | Podejście |
|---------|-------|-----------|
| `analyze_agent_code()` | 55→40 | Ekstrakcja `_scan_agent_files()` |
| `generate()` (standup) | 60→20 | 4 helpery `_build_*_section()` |
| `save_project_intelligence()` | 68→60 | 4 helpery `_build_*_section()` |

### Pozostawione bez zmian:
- `main_loop()` (185 linii) - zbyt ryzykowne przy refaktoryzacji
- `save_agent_documentation()` (255 linii) - statyczna funkcja generująca

## Historia wersji

- **V8** - Refaktoryzacja, bezpieczeństwo secrets, szczegółowe taski
- **V7** - Smart check-in, Project Intelligence
- **V4-V6** - Archiwum w `modules_archive/`

## Licencja

Własny projekt deweloperski
