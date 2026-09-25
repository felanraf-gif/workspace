> Dokument historyczny. Aktualny stan i granice walidacji: `STATUS_AKTUALNY.md` w katalogu głównym.

# R1 — checkpoint implementacji

Data: 18.09.2026. Repozytorium: `/home/felanraf/Projekty/towarzysz-v9-agent-clean`.
HEAD: `e0f70c986c4f7e963d1cdb7889f1668b60394ec5` — bez commita.

## Wynik i przyjęty wariant

Zaimplementowano R1 w istniejącej polityce `core/observer_policy.py` i adapterze stanu `core/observer_storage.py`. Kontrolowane zapisy i patche mogą zmieniać wyłącznie autoryzowane repozytorium. Dowolny shell/Python, nieznane narzędzia oraz modyfikujące operacje Git są blokowane również przy aktywnej autoryzacji. Nie dodano systemu izolacji ani R2–R6.

## Jak działa autoryzacja

- `AUTHORIZED_REPO` pochodzi wyłącznie ze środowiska uruchomienia procesu. `core/__init__.py` inicjalizuje politykę przed załadowaniem projektowego `.env`. Wymagany jest jeden absolutny, istniejący katalog z markerem `.git`; wartość nie jest listą.
- Kanoniczna ścieżka i tożsamość katalogu (urządzenie/inode) są zapamiętywane w zamrożonym obiekcie. Wszystkie cykle procesu używają tej samej autoryzacji. Zmiana zakresu wymaga nowego, jawnie skonfigurowanego uruchomienia. Nie ma narzędzia ani pola planu zmieniającego autoryzację. Builder i RoleManager raportują `authorized_repo`.
- Brak lub błędna autoryzacja oznacza blokadę wykonawczych zapisów. Odczyty i analiza innych projektów pozostają dostępne. Stan roboczy agenta poza zakresem jest przechowywany w RAM przez dotychczasowy adapter, bez utrwalania na dysku.
- Centralny dekorator działa fail-closed: tylko jawnie oznaczone, kontrolowane implementacje mogą wykonywać zapisy. Executor filtruje nazwy narzędzi i ścieżki; bezpośrednie wywołania FileTools, Buildera i PatchEngine również podlegają kontroli.
- Kontrola używa rozwiązywania ścieżek i `commonpath`, nie tekstowego `startswith`. Odrzuca cele poza granicą, także przez `../`, ścieżki absolutne i symlinki. Dodatkowo odrzuca zagnieżdżone repozytoria, metadane `.git`, pliki specjalne i zapisy do plików z wieloma hardlinkami.
- Otwarcie zapisu przebiega względem deskryptorów katalogów z `O_NOFOLLOW`. Plik jest weryfikowany przed obcięciem zawartości. Backupy korzystają z tej samej kontroli, a nowe backupy powstają wyłącznie przy wyłącznym tworzeniu.
- PatchEngine najpierw sprawdza wszystkie cele batcha i składnię Pythona, następnie zapisuje i weryfikuje wynik. Przy błędzie wycofuje wykonane zapisy w obrębie autoryzacji. Nie uruchamia Git, nie staginguje i nie commituje. Backupy pozostają do ręcznego odtworzenia; rollback również sprawdza zakres.
- Odczyty Git zachowują zabezpieczenia przed helperami, filtrami i opcjonalnymi zapisami indeksu także poza Observer Mode. Integracje zapisujące poza lokalnym zakresem oraz niekontrolowane porządki pamięci pozostają zablokowane. Wywołania LLM służące analizie zachowują dotychczasowe zachowanie poza Observer Mode.

Przykład jawnej konfiguracji startowej (nie uruchamiano realnego cyklu produkcyjnego):

```bash
AUTHORIZED_REPO=/home/felanraf/Projekty/towarzysz-v9-agent-clean OBSERVER_MODE=false .venv/bin/python -B main.py --once
```

Umieszczenie `AUTHORIZED_REPO` tylko w `.env` nie udziela autoryzacji. `OBSERVER_MODE=true` nadal ma pierwszeństwo i blokuje wykonanie.

## Dokładne pliki zmienione względem początku tej implementacji

- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/.env.example`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/brain/patch_engine.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/brain/project_tracker.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/brain/roles/builder.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/brain/roles/manager.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/core/__init__.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/core/observer_policy.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/core/observer_storage.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/integrations/llm.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/integrations/todoist.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_integrations.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_memory.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_observer_execution.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_patch_engine.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_r1_scope.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tests/test_role_patch.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tools/file_tools.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/tools/git_tools.py`
- `/home/felanraf/Projekty/towarzysz-v9-agent-clean/docs/bezpieczenstwo/r1-checkpoint.md` — niniejszy checkpoint.

To 18 plików kodu/konfiguracji/testów oraz jeden dokument. Wcześniejsze niezatwierdzone zmiany nie są przypisywane tej sesji. `work/r1-implementation/session.diff` zawiera różnicę względem zastanego stanu, a nie względem HEAD.

Materiały robocze i testowe znajdują się wyłącznie w `/home/felanraf/Projekty/towarzysz-v9-agent-clean/work/r1-implementation`. Pełny wykaz ich plików i skrótów SHA-256 zapisano w `artifact-manifest.json`. Obejmuje skrypty edycji i uruchomienia testów, snapshot wejściowy, diff, logi oraz lokalne dane testowe `case-*`. Te dane są pomocnicze, nie są częścią implementacji produkcyjnej.

## Testy

Końcowy wynik: **79 passed, 1 deselected in 6.57s**, pytest exit 0.

Zestaw: `test_r1_scope.py`, `test_patch_engine.py`, `test_role_patch.py`, `test_observer_execution.py`, `test_observer_mode.py`, `test_project_tracker.py`, `test_memory.py`, `test_integrations.py`.

Potwierdzono scenariusz rozstrzygający A/B, brak autoryzacji, brak autoryzacji przez dane planu/projektu oraz późniejszą zmianę środowiska, ignorowanie `.env`, blokadę procesów przed ich uruchomieniem, bezpieczeństwo backupów i rollbacku, walidację całego batcha, działanie stanu w RAM i regresję Observer Mode. Testy z podmianą pliku oraz katalogu na symlink między sprawdzeniem a otwarciem nie przekierowały zapisu do B.

Pominięto tylko `test_observer_git_signature_config`, ponieważ przygotowanie tego historycznego testu wywołuje `chmod`. Nie przypisujemy mu aktualnego wyniku PASS. Testy patchowania zaktualizowano do zatwierdzonego kontraktu bez commitów; usunięto ich zależność od hooków wymagających zmiany uprawnień. Zachowano testy poprawnego patchowania, odrzucenia złej składni, rollbacku i błędu w późnym etapie batcha.

Uruchomienie: `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B work/r1-implementation/run_tests.py`. Runner zastępuje `tmp_path` lokalnym `tempfile.mkdtemp`, aby nie używać zmieniającej uprawnienia domyślnej fixture pytest. Nie uruchamiano całego zestawu ani produkcyjnego cyklu na rzeczywistych projektach. Repozytoria A/B są danymi testowymi pod `work/r1-implementation`.

Dodatkowo: `git diff --check` PASS; parsowanie składni wszystkich zmienionych plików Pythona PASS. Nie wykonywano sudo, zmian właścicieli/uprawnień, stagingu, commita ani push. Nie modyfikowano innych istniejących repozytoriów.

## Granice i ograniczenia

To egzekwowanie w kontrolowanych wejściach aplikacji, nie izolacja systemowa dowolnego kodu. Zakładamy zaufany kod uruchomionego agenta, interpreter i Git. Nie wdrożono R3: zamrożony obiekt nie chroni przed dowolnym złośliwym kodem wykonanym wewnątrz procesu ani zmianą kodu zabezpieczeń i jego ponownym uruchomieniem.

Ochrona przed symlinkami została sprawdzona także przy podmianie przed otwarciem. Nie deklarujemy ochrony przed wrogim procesem przenoszącym już otwarte katalogi poza repozytorium, zmianami montowań ani przejęciem procesu. Nie jest to pełny sandbox systemu operacyjnego.

Zmiana zakresu wymaga restartu. Zapis stanu poza zakresem nie przetrwa restartu. Nie ma automatycznego usuwania backupów ani wykonywania komend build/test przez agenta. Historyczny test podpisów Git pozostaje niewykonany. Walidacja `.git` sprawdza marker, nie integralność całego repozytorium Git. Nie zweryfikowano trybów wykonawczych w archiwalnych modułach `modules_archive` — nie należą do aktywnych ścieżek.

## Dokładnie jeden następny krok

Przejrzeć diff tej sesji (`work/r1-implementation/session.diff`) przed decyzją o commicie.
