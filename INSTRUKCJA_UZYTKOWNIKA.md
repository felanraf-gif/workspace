# Development Assistant V4 - Instrukcja Użytkownika

## Uruchomienie systemu

### 1. Skrypt startowy
```bash
cd /home/felanraf/workspace
./run_da.sh
```

### 2. Sprawdzenie statusu
```bash
ps aux | grep "python3 main.py"
```

### 3. Zatrzymanie agenta
```bash
pkill -f "python3 main.py"
```

## Jak działa system

### Rano (08:00)
1. Otwórz **Obsidian** → DevelopmentAssistant → Dashboard.md
2. Zobacz najważniejsze zadania na dziś
3. Otwórz **Todoist** i rozpocznij pracę

### W ciągu dnia
- Agent monitoruje projekty co minutę
- Wykrywa nowe pliki i problemy
- Wysyła zadania krytyczne (HIGH) do Todoist
- Monitoruje czas pracy automatycznie

### Wieczorem (22:00)
1. Agent generuje raport dzienny
2. Otwórz **Obsidian** → Daily → YYYY-MM-DD.md
3. Przeczytaj podsumowanie dnia
4. Sprawdź plan na jutro w Todoist

## Gdzie znaleźć pliki

### Obsidian Vault
Ścieżka: `/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant/`

Struktura:
```
DevelopmentAssistant/
├── Daily/              # Raporty dzienne
├── Projects/           # Strony projektów
├── lessons/            # Lekcje i refleksje
└── Dashboard.md        # Dashboard ogólny
```

### Logi systemowe
- Globalne: `/home/felanraf/workspace/system/global_log.txt`
- Time tracking: `/home/felanraf/workspace/memory/decisions/time_*.json`

## Funkcje systemu

### ✅ Monitorowanie projektów
- Skanowanie co 60 sekund
- Wykrywanie nowych plików
- Identifikacja problemów strukturalnych

### ✅ Generowanie zadań
- Zadania HIGH (krytyczne) - wysyłane natychmiast
- Zadania MEDIUM (rozwój) - wysyłane w regularnych cyklach
- Limit 5 zadań dziennie

### ✅ Time tracking
- Automatyczne śledzenie czasu pracy
- Logi w `memory/decisions/time_*.json`

### ✅ Raporty dzienne
- Generowane o 22:00 w vault Obsidian
- Format czytelny w 10 sekund
- Zawierają: zadania, wykonane, problemy, analizę, wnioski

## Rozwiązywanie problemów

### Agent nie działa
```bash
# Sprawdź, czy działa
ps aux | grep "python3 main.py"

# Jeśli nie działa, uruchom ponownie
./run_da.sh
```

### Zadania nie są wysyłane do Todoist
- Sprawdź połączenie internetowe
- Sprawdź token API w `core/config.py`
- Sprawdź logi: `tail -f system/global_log.txt`

### Pliki nie pojawiają się w Obsidian
- Sprawdź ścieżkę vaultu w `core/config.py`
- Odśwież vault w programie Obsidian

## Przykłady

### Widok Dashboard w Obsidian
```
# 📊 Dashboard - Development Assistant

## 🔥 Najważniejsze zadania
- [ ] towarzysz: Utwórz katalog src/
- [ ] scraper_1: Utwórz lub napraw plik config.json

## 📅 Dziennie raporty
- [2026-03-18](Daily/2026-03-18.md)
```

### Widok raportu dziennego
```
# 📅 2026-03-18

## 🔥 Najważniejsze zadania
- [ ] towarzysz: Utwórz katalog src/

## 📋 Pozostałe zadania
- 🟡 scraper_1: Przeglądaj i aktualizuj kod

## ✅ Wykonane
- towarzysz: Zainicjalizowano projekt

## ⚠️ Problemy
- Brak problemów

## 📊 Analiza
- Czas całkowity: 2.5 godz.
```

---

*Development Assistant V4 - Twój osobisty asystent rozwojowy*