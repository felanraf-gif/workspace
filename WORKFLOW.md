# Development Assistant V4 - Workflow Dzienny

## Przegląd

Development Assistant V4 to system monitorujący projekty deweloperskie, analizujący trendy i generujący zadania. Działa w trybie ciągłym (24/7) i automatyzuje codzienną pracę.

## Struktura folderów

```
workspace/
├── projects/           # Projekty deweloperskie
├── memory/             # Dane pamięci
│   ├── analytics/      # Metryki efektywności
│   ├── trends/         # Analiza trendów
│   └── daily_logs/     # Logi dzienne
├── Obsidian/           # Notatki w Obsidian
│   └── DevelopmentAssistant/
│       ├── daily_logs/ # Raporty dzienne
│       └── lessons/    # Lekcje i refleksje
└── core/               # Moduły systemowe
```

## 1. Uruchomienie agenta

### Ręczne uruchomienie
```bash
cd /home/felanraf/workspace
./run_da.sh
```

### Sprawdzenie statusu
```bash
ps aux | grep "python3 main.py"
```

### Zatrzymanie agenta
```bash
pkill -f "python3 main.py"
```

## 2. Poranny przegląd (automatyczny)

Agent działa w tle i co 60 sekund wykonuje:

1. **Skanowanie projektów** (Analyzer)
   - Wykrywa nowe pliki
   - Identifikuje braki strukturalne
   - Aktualizuje stan projektów

2. **Monitorowanie** (Tracker)
   - Śledzi zmiany w plikach
   - Wykrywa stagnację projektów (>2 dni)
   - Zapisuje czas pracy (time tracking)

3. **Analiza trendów** (TrendAnalyzer)
   - Ocenia wartość projektów w czasie
   - Wykrywa trendy rozwojowe

## 3. Bloki czasowe pracy

Agent monitoruje czas pracy nad zadaniami:

- **Rozpoczęcie zadania**: Agent automatycznie rozpoczyna śledzenie czasu
- **Zakończenie zadania**: Czas jest zapisywany w `memory/decisions/time_YYYY-MM-DD.json`

### Przykład workflow:

```
09:00 - Rozpoczęcie pracy nad zadaniem HIGH
        → Agent rozpoczyna time tracking

10:30 - Zakończenie zadania
        → Agent zapisuje czas (1.5 godz.)

11:00 - Przerwa

11:15 - Rozpoczęcie zadania MEDIUM
        → Agent rozpoczyna time tracking
```

## 4. Raport dzienny (22:00)

O godzinie 22:00 agent wykonuje pełny cykl i generuje:

### 4.1. Plan na jutro (Todoist)
- Zadania HIGH/MEDIUM/LOW
- Wysłane do projektu "Development Assistant Tasks"
- Oznaczone datą "jutro"

### 4.2. Lekcja dnia (Obsidian)
Plik: `Obsidian/DevelopmentAssistant/lessons/YYYY-MM-DD_lekcja.md`

Zawiera:
- ⏱️ Czas pracy (godziny per projekt)
- ✅ Wykonane zadania
- ⚠️ Problemy i wyzwania
- 💡 Refleksje i wnioski
- 🤖 Sugestie agenta

### 4.3. Raport dzienny (Obsidian)
Plik: `Obsidian/DevelopmentAssistant/daily_logs/YYYY-MM-DD_report.md`

Zawiera:
- Podsumowanie projektów
- Lista zadań do wykonania
- Wykresy (PNG + HTML)
- Link do lekcji dnia

### 4.4. Dashboard (HTML)
Plik: `Obsidian/DevelopmentAssistant/daily_logs/charts/dashboard_YYYY-MM-DD.html`

Zawiera:
- Wykres rozkładu priorytetów
- Histogram wartości zadań
- Trendy projektów
- Zmienność projektów

## 5. Integracje

### Todoist
- Zadania wysyłane o 22:00 na jutro
- Priorytety: HIGH (1), MEDIUM (2), LOW (3)
- Etykiety: development, assistant

### Obsidian
- Raporty dzienne w formacie Markdown
- Lekcje w folderze `lessons/`
- Dashboardy w formacie HTML

## 6. Pliki konfiguracyjne

### core/config.py
```python
SCAN_INTERVAL = 60  # sekundy
TODOIST_API_TOKEN = "981bf199808938a05f81776999fb58de655fe9cc"
OBSIDIAN_PATH = "Obsidian/DevelopmentAssistant/"
ENABLE_ANALYTICS = True
ENABLE_TRENDS = True
```

### Uruchomienie
```bash
# Skrypt startowy
./run_da.sh

# Lub bezpośrednio
python3 main.py
```

## 7. Rozwiązywanie problemów

### Agent nie generuje raportu o 22:00
- Sprawdź godzinę systemową: `date`
- Sprawdź logi: `tail -f system/global_log.txt`

### Zadania nie są wysyłane do Todoist
- Sprawdź połączenie internetowe
- Sprawdź token API w `core/config.py`
- Sprawdź logi: `grep "Todoist" system/global_log.txt`

### Lekcje nie są zapisywane
- Sprawdź folder: `ls -la Obsidian/DevelopmentAssistant/lessons/`
- Sprawdź uprawnienia do zapisu

## 8. Dziennik pracy (Time Tracking)

Agent automatycznie śledzi czas pracy:

```
memory/decisions/time_2026-03-18.json
{
  "towarzysz": 7200,  # 2 godziny
  "scraper_1": 3600   # 1 godzina
}
```

## 9. Planowanie na jutro

O 22:00 agent generuje zadania na jutro na podstawie:

1. **Problemów wykrytych heute** (HIGH priority)
2. **Nowych plików** (MEDIUM priority)
3. **Trendów projektów** (spadki wymagają interwencji)
4. **Lekcji z poprzednich dni** (unikanie powtarzania błędów)

Zadania są wysyłane do Todoist i oznaczone datą "jutro".

## 10. Porady produktyjne

1. **Uruchom agenta rano** - pozwala monitorować pracę przez cały dzień
2. **Sprawdzaj raport o 22:00** - podsumowanie dnia w Obsidian
3. **Czytaj lekcje** - ucz się na błędach i sukcesach
4. **Sprawdzaj dashboard** - wizualizacja postępu
5. **Zadania w Todoist** - mają zawsze aktualny harmonogram

---

*Development Assistant V4 - Twój osobisty asystent rozwojowy*