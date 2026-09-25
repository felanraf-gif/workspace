# Towarzysz V9 — instrukcje pracy w repozytorium

## Cel

Towarzysz jest lokalnym agentem obserwującym, analizującym i raportującym stan
projektów. Rozwój ma zachować kontrolę człowieka, ograniczenie uprawnień,
testowalność i możliwość bezpiecznego zatrzymania.

## Aktywna architektura

- `main.py` uruchamia `core/loop.py`.
- `brain/roles/` realizuje przepływ Scout → Architect → Builder → Critic.
- `brain/patch_engine.py` przygotowuje i stosuje kontrolowane patche.
- `core/observer_policy.py` egzekwuje Observer Mode i granicę R1.
- `core/observer_storage.py` utrzymuje stan w RAM, gdy zapis jest niedozwolony.
- `tools/` udostępnia kontrolowane operacje na plikach i odczyty Git.
- `memory/` przechowuje stan globalny i projektowy.

`modules_archive/` jest kodem historycznym i nie należy do aktywnej ścieżki.

## Zasady bezpieczeństwa

1. Domyślnie używaj `OBSERVER_MODE=true`.
2. Analiza nie oznacza zgody na zapis ani wykonanie.
3. Zapis może dotyczyć tylko repozytorium wskazanego przez `AUTHORIZED_REPO`
   w środowisku startowym procesu.
4. Nie uruchamiaj sudo, nie zmieniaj uprawnień ani właścicieli.
5. Nie wykonuj autonomicznych commitów, push, merge, rebase ani zmian `.git`.
6. Nie modyfikuj zabezpieczeń w ramach automatycznej samonaprawy.
7. Przy niejednoznacznym zakresie działaj fail-closed.

Szczegółowa polityka znajduje się w `docs/bezpieczenstwo/`.

## Walidacja

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
.venv/bin/python -B scripts/validate.py
```

Przed uznaniem zmiany za gotową sprawdź składnię zmodyfikowanych plików, wynik
testów bezpieczeństwa i zgodność dokumentacji ze stanem kodu.

## Stan hardeningu

- R1: granica autoryzowanego repozytorium — zaimplementowana i testowana.
- Observer Mode — zaimplementowany i testowany.
- Bezpieczne odczyty Git — hooki, filtry, zewnętrzne diffy, submoduły i
  weryfikatory podpisów są ograniczane.
- R3/R4 oraz niezależna warstwa bezpieczeństwa — nadal niewdrożone.

Aktualna macierz wymagań i ograniczeń: `docs/bezpieczenstwo/zalozenia-i-pokrycie-2026-09-25.md`. Publikacja przez operatora wymaga osobnej zgody; zakaz autonomicznego Git dotyczy agenta.
