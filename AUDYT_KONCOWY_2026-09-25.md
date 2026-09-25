> Dokument historyczny. Aktualny stan i granice walidacji: `STATUS_AKTUALNY.md` w katalogu głównym.

# Towarzysz V9 — raport końcowy audytu

Data: 25.09.2026  
Zakres: przesłana kopia `towarzysz-v9-agent-clean`, aktywny kod, testy,
konfiguracja i dokumentacja. Bez `.git`, `.env`, produkcyjnego uruchomienia,
commita i push.

## Wynik

Projekt po poprawkach przechodzi pełny dostępny zestaw testów:

- `91 passed in 3.47s`;
- parsowanie AST: 54 aktywne pliki Python — PASS;
- `bash -n run_da.sh` — PASS;
- `pip check` — brak uszkodzonych zależności;
- start bez zmiennych środowiskowych: `observer_mode=True`,
  `authorized_repo=None`.

## Krytyczne ustalenie P1

Stan wejściowy miał 4 niezaliczone testy bezpieczeństwa Git. Odczytowe
operacje mogły uruchomić kod skonfigurowany w obserwowanym repozytorium:

1. filtr `clean` znajdujący się w konfiguracji submodułu przy `status`/`diff`;
2. program weryfikacji podpisu wymuszony przez `format.pretty=%G?` przy `log`.

Skutek: sama analiza obcego repozytorium nie była całkowicie bezskutkowa.

### Naprawa

- `status` i `diff` jawnie ignorują wszystkie submoduły;
- wyłączono rekursję i podsumowania submodułów również przez konfigurację Git;
- `log` zawsze otrzymuje zaufany format (`medium` albo `oneline`) oraz
  `--no-show-signature`;
- te same ograniczenia zastosowano w `ProjectTracker`.

Istniejące testy reprodukujące oba ataki przechodzą po poprawce.

## Pozostałe wprowadzone zmiany

- Observer Mode jest teraz domyślnie włączony (fail-closed).
- `.env.example` rozpoczyna pracę od `OBSERVER_MODE=true`.
- Test jawnie włącza tryb wykonawczy tylko w scenariuszu Buildera.
- Usunięto fałszywy komunikat o automatycznym commicie; PatchEngine nie
  wykonuje stagingu ani commita.
- Ujednolicono oznaczenia wersji V9 w konfiguracji, punkcie startowym i skrypcie.
- README opisuje R1, aktualne ograniczenia Git, 91 testów i leksykalny charakter
  `VectorMemory`.
- `AGENTS.md` zastąpiono aktualną instrukcją V9.
- Dodano `requirements-dev.txt` z zależnością testową pytest.

## Stan zabezpieczeń

### Potwierdzone

- R1 ogranicza kontrolowane zapisy do jednego `AUTHORIZED_REPO` przejętego
  przed załadowaniem `.env`.
- Observer Mode blokuje Buildera, patche, komendy wykonawcze, zewnętrzne zapisy
  i połączenia LLM objęte aktywnymi adapterami.
- PatchEngine wykonuje preflight całego batcha, kontroluje składnię Pythona,
  weryfikuje zapis i wycofuje batch po błędzie.
- Modyfikujące polecenia Git i zapis do `.git` są blokowane.
- Odczyty Git są utwardzone wobec hooków, external diff, filtrów, submodułów,
  fsmonitor i programów weryfikacji podpisów w objętych testami ścieżkach.

### Nadal otwarte

1. R3: polityka działa w tym samym procesie co agent i nie jest niezależnym
   sandboxem systemowym.
2. R4: brak kompletnego, jednorazowego mechanizmu zgody człowieka wiążącego
   konkretny plan z konkretnym wykonaniem.
3. Kod nadal zawiera szerokie `except:` i historyczne moduły; ich hurtowa
   przebudowa nie była potrzebna do usunięcia aktualnej luki P1.
4. `VectorMemory` nie korzysta z embeddingów; wykonuje dopasowanie słów.
5. Nie wykonano produkcyjnego cyklu na rzeczywistych repozytoriach ani zapisu
   do Obsidian/Todoist. Byłoby to rozszerzenie zakresu i wymaga osobnej zgody.

## Zmienione pliki

- `.env.example`
- `AGENTS.md`
- `README.md`
- `brain/project_tracker.py`
- `core/config.py`
- `core/loop.py`
- `core/observer_policy.py`
- `main.py`
- `requirements-dev.txt` (nowy)
- `run_da.sh`
- `tests/test_observer_execution.py`
- `tests/test_role_patch.py`

## Rekomendowany następny krok

Zaprojektować R4 jako jawny, jednorazowy token zgody powiązany z hashem planu,
autoryzowanym repozytorium i krótkim czasem ważności. Dopiero potem uruchamiać
Buildera poza Observer Mode. Nie łączyć tego etapu z implementacją R3.
