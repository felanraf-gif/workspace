> Dokument historyczny. Aktualny stan i granice walidacji: `STATUS_AKTUALNY.md` w katalogu głównym.

# Towarzysz V9 — zgodność polityki v0.1 z Observer Mode

Data: 18.09.2026. Zakres: dokumentacja i weryfikacja istniejących mechanizmów; bez implementacji, commita i push.

## Punkt odniesienia

- Repozytorium: /home/felanraf/Projekty/towarzysz-v9-agent-clean
- Gałąź: agent-fix-unused-import-2026-09-09
- HEAD: e0f70c986c4f7e963d1cdb7889f1668b60394ec5 — zgodny z work/observer-validation/branch-head.txt.
- V9_CHECKPOINT.md opisuje starszy HEAD 46b666de i 32 testy z 09.09.2026. Pozostawiono go bez zmian; aktualnym punktem odniesienia tej sesji jest raport Observer Mode i zastane drzewo robocze.
- Drzewo zawierało już liczne niezatwierdzone zmiany Observer Mode oraz wcześniejsze zmiany pamięci i checkpointu. Nie są rezultatem tej sesji.
- Politykę skopiowano w całości, bez redakcji treści, z dokumentu w rozmowie „Reguły bezpieczeństwa V9”, conversationId 6aacf089-9aec-83ed-9c27-cdf31ff803d6, wiadomość 7d0aa910-7806-4df5-8327-404e7ff747f6. Usunięto wyłącznie opakowanie bloku pisarskiego i tekst rozmowy poza dokumentem. Plik: [polityka-bezpieczenstwa-i-zgod-v0.1.md](polityka-bezpieczenstwa-i-zgod-v0.1.md).
- Liczby 33/72 testy, 11 projektów, 20 rekomendacji i 17 027 wpisów w polityce dotyczą wcześniejszej walidacji, nie testów tej sesji.

## Znaczenie ocen

„Egzekwowana” oznacza potwierdzenie reguły w objętych przeglądem aktywnych ścieżkach przy OBSERVER_MODE=true, a nie gwarancję dla dowolnego kodu lub trybu wykonawczego. „Częściowo egzekwowana” oznacza istniejącą blokadę części skutków przy braku pełnego mechanizmu wymaganej reguły. „Tylko udokumentowana” oznacza brak kontroli konkretnego warunku w przejrzanej ścieżce; nie dowodzi nieistnienia jakiegokolwiek zabezpieczenia w całym systemie.

Observer Mode to polityka aplikacyjna. Klasa brain/observer.py:Observer monitoruje pliki; nie jest warstwą egzekwującą te zakazy.

## Każda twarda reguła

| Reguła | Ocena | Dowód w aktualnym kodzie i testach | Luka / granica |
|---|---|---|---|
| R1. Granica projektu | **częściowo egzekwowana** | core/observer_policy.py:31–49 blokuje mutacje i narzędzia wykonawcze w observer. tools/file_tools.py:54 oraz :99 osłaniają write/edit; test_file_writes_and_backups_blocked i test_direct_patch_entrypoints_do_not_access_files_or_git potwierdzają odmowę. brain/patch_engine.py:668 kontroluje realpath i commonpath względem _project_root. | Blokada wszystkich zapisów chroni także inne projekty, ale nie modeluje zgody na konkretny projekt. _project_root pochodzi z przekazanego projektu (brain/patch_engine.py:39–47), nie z niezależnej autoryzacji. FileTools i BashTools poza observer nie mają tej samej granicy projektu. |
| R2. Zakaz samodzielnego zwiększania uprawnień | **częściowo egzekwowana** | tools/bash_tools.py:18 blokuje run; także run_python/check_output/is_available mają dekoratory. core/observer_storage.py:83–92 odrzuca nieznane operacje OS, w tym chmod/chown. test_shell_python_helpers_do_not_spawn potwierdza brak procesu; test_observer_blocks_llm_requests_and_unknown_os_mutation sprawdza blokadę chmod i unlink adaptera. | Nie ma tu kontroli efektywnego UID ani niezależnej ochrony przed uruchomieniem całego procesu jako root. Adapter nie zastępuje globalnego os. Brak osobnej autoryzacji eskalacji poza observer; test chown/root nie był wykonywany. |
| R3. Zakaz modyfikacji własnych zabezpieczeń | **częściowo egzekwowana** | Blokady FileTools, Builder i PatchEngine nie dopuszczają zmian plików także wtedy, gdy celem byłby kod zabezpieczeń. test_direct_patch_entrypoints_do_not_access_files_or_git i test_builder_and_direct_helpers_block_execution sprawdzają odmowę na wejściach. | core/observer_policy.py:10–11 odczytuje zmienną środowiskową przy każdym sprawdzeniu, z domyślnym false. core/observer_storage.py:85 udostępnia environ. Brak niezmiennej konfiguracji i osobnej ochrony plików polityki. test_policy_default_off_and_dynamic potwierdza dynamiczność. To podatna na zmianę konfiguracja w tym samym procesie, nie niezależny strażnik; nie demonstrowano obejścia na rzeczywistych plikach. |
| R4. Zakaz autonomicznego rozszerzania zakresu | **tylko udokumentowana** | core/loop.py:252–280 wybiera dwa projekty z kolejności priorytetów i wywołuje ich cykle; brain/roles/manager.py:74–125 tworzy plan, a :127–142 zwraca go jako rekomendacje. W tych ścieżkach brak argumentu/warunku reprezentującego autoryzowany cel sesji. test_role_manager_proposes_without_calling_builder bada blokadę wykonania, nie zgodność planu z celem sesji. | Observer zapobiega realizacji wykrytych zadań, ale nie rozpoznaje scope creepu i nie wymusza oddzielnej zgody na nowy cel. Sama analiza wielu projektów nie musi naruszać polityki; brakuje kontroli przejścia od znaleziska do autoryzowanego zadania. |
| R5. Rozdzielenie analizy od wykonania | **egzekwowana** | brain/roles/manager.py:127–142 zwraca OBSERVED, rekomendacje, executed=False i NOT_EXECUTED dla Critica. core/loop.py:379 wyklucza fallback patchowania w observer. core/observer_storage.py:31–54 kieruje zapisy stanu do RAM. test_role_manager_proposes_without_calling_builder, test_real_state_read_but_updates_stay_in_memory i test_one_complete_loop_with_disk_writes_denied potwierdzają analizę, priorytety, brak wykonania i brak zapisu testowego stanu na dysk. | Ocena dotyczy aktywnego observer i sprawdzonych wejść. Nie oznacza rozdzielenia procesów/systemowych uprawnień ani kompletnego mechanizmu zgód w trybie wykonawczym. |
| R6. Fail closed | **częściowo egzekwowana** | core/observer_policy.py:44–69 dopuszcza znane nazwy narzędzi i ścisłe postacie poleceń Git; :73–94 odmawia przy błędzie klasyfikacji filtrów. tools/git_tools.py:18–42 zatrzymuje niedozwoloną komendę przed uruchomieniem. core/observer_storage.py:83–92 odrzuca nieznane operacje OS. test_unknown_registered_tool_fails_closed_and_reads_work oraz parametryzowany test_git_allowlist_rejects_execution_and_writes potwierdzają odmowy. | Nieobecne/błędne OBSERVER_MODE oznacza false, nie STOP. tool_allowed(name, args) nie analizuje args: znany odczyt nie sprawdza chronionego zasobu, sekretu ani zgody. Brak pełnej klasyfikacji zakresu, zgód i trwałych skutków; blocked zatrzymuje operację, nie cały cykl. |

Nazwy testów w tabeli odnoszą się do tests/test_observer_execution.py i tests/test_observer_mode.py.

## Zgody i niezależność — istotne ograniczenia polityki

Sekcja 4 polityki to katalog wymagań, nie kompletny zaimplementowany przepływ zgód. W observer zakazane zapisy są odrzucane bez procedury udzielania wyjątku. Odczyt FileTools.read (tools/file_tools.py:15–43) nie rozróżnia sekretów od zwykłych plików. Nie odczytywano sekretów dla potrzeb audytu.

Sekcja 5 opisuje architekturę docelową. Aktualna polityka, executor i konfiguracja działają w tym samym procesie; testy nie potwierdzają niezależnej, odpornej na samomodyfikację warstwy bezpieczeństwa. Po wyłączeniu observer PatchEngine może automatycznie commitować (brain/patch_engine.py:449, :523, :599). Nie uruchamiano tej ścieżki.

Te luki odnotowano bez prób naprawy i bez ingerencji w inne projekty.

## Weryfikacja w tej sesji

- Przegląd pełnej polityki, AGENTS.md, V9_CHECKPOINT.md, istniejącego raportu, verification.json i branch-head.txt oraz kodu wskazanego powyżej.
- Uruchomiono istniejące tests/test_observer_execution.py i tests/test_observer_mode.py: **32 passed, 1 deselected in 2.25s**, kod wyjścia 0.
- Pominięto test_observer_git_signature_config: przygotowanie testu wywołuje chmod i tworzy syntetyczny obiekt commita. Zakaz zmiany uprawnień obowiązuje także dla plików testowych. Jego wcześniejszy wynik pozostaje historycznym dowodem, bez ponownego potwierdzenia.
- Python: .venv/bin/python; OBSERVER_MODE=true, PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1. Argumenty pytest: -q -p no:cacheprovider tests/test_observer_execution.py tests/test_observer_mode.py -k "not test_observer_git_signature_config".
- Tymczasowa lokalna fixture tmp_path tworzyła katalogi przez tempfile.mkdtemp wyłącznie w work/policy-v0.1-audit; zastąpiła domyślną fixture pytest, której przygotowanie katalogu mogłoby zmieniać jego uprawnienia. Nie zmieniano plików testów. Dane testowe pozostawiono do inspekcji. Testy tworzyły wyłącznie lokalne repozytoria testowe w tym katalogu; nie modyfikowano innych istniejących repozytoriów.
- Snapshot przed/po testach: **309 plików**, porównanie SHA-256 (celu dla symlinków), trybu, UID/GID i mtime. **W tym zakresie nie wykryto zmian** poza katalogiem materiałów audytu. Snapshot wykonano po zapisaniu polityki, przed utworzeniem niniejszego raportu.
- Wyłączenia tego porównania: .git, .pytest_cache, .venv, __pycache__, node_modules, tor_env, venv oraz work/policy-v0.1-audit. Nie jest to kontrola całego komputera ani nowych zapisów do wyłączonych katalogów.
- git diff --check: PASS (zastane zmiany śledzonych plików); nowe dokumenty sprawdzono osobno.
- Nie uruchamiano całego zestawu ani nowego cyklu na rzeczywistych projektach: nie były potrzebne do tego audytu.
- Materiały: work/policy-v0.1-audit/tests.log, before.json, verification.json oraz katalogi case-* z danymi testowymi.

## Wcześniejsza walidacja — granice dowodu

work/observer-validation/report.md i verification.json raportują 33 testy observer, 72 całego zestawu, 11 projektów, 20 rekomendacji, OBSERVED, stopped/complete oraz 17 027 wpisów plików i brak różnic w objętym kontrolą Obsidianie. W przeprowadzonym wówczas zakresie walidacji **nie wykryto zmian**.

Wyłączono zależności/cache (.mypy_cache, .observer-test-tmp, .pytest_cache, .tox, .venv, __pycache__, env, node_modules, tor_env, venv), obiekty/logi Git i work/observer-validation. Tego pomiaru nie powtórzono. Historyczny wynik nie jest absolutną gwarancją ani dowodem pełnego wdrożenia R1–R6.

## Checkpoint końcowy

Pliki dodane przez sesję:
1. docs/bezpieczenstwo/polityka-bezpieczenstwa-i-zgod-v0.1.md — pełny dokument z rozmowy.
2. docs/bezpieczenstwo/audyt-observer-v0.1.md — niniejszy audyt i checkpoint.
3. work/policy-v0.1-audit/ — log, manifest, wynik porównania i izolowane dane istniejących testów.

Nie zmieniono kodu, testów ani wcześniejszego raportu/checkpointu. Bez sudo, zmian uprawnień/właścicieli, stagingu, commita i push. Zastane zmiany pozostają niezatwierdzone.

Wynik: R5 egzekwowana w opisanym zakresie; R1, R2, R3, R6 częściowo egzekwowane; R4 tylko udokumentowana. 32 testy PASS, 1 świadomie pominięty. Główne luki: brak autoryzowanego zakresu/celu sesji i przepływu zgód, brak niezależnej ochrony własnych zabezpieczeń, domyślne wyłączenie observer i brak klasyfikacji chronionych odczytów.

**Dokładnie jeden proponowany następny krok:** wspólnie zatwierdzić specyfikację kryteriów akceptacji dla R1 — jak jednoznacznie wskazać autoryzowane repozytorium i rozpoznać próbę wyjścia poza nie — przed jakąkolwiek implementacją.

