# Towarzysz V9 — stan zweryfikowanej kopii, 25.09.2026

## Zakres i pochodzenie
Źródło: archiwum użytkownika oraz poprawki audytu z tej rozmowy. Archiwum nie zawiera historii lokalnego Git, .env ani kompletu danych runtime. To nie jest pełna kopia komputera. Planowana gałąź audytu ma zawierać snapshot źródeł oparty na zdalnym master; nie odtworzy brakujących lokalnych commitów. Publikacja wymaga weryfikacji zdalnej gałęzi; jej wynik podaje raport dostawy poza snapshotem.

## Naprawy
- P1 Git: pomijanie submodułów i jawny format log zapobiegają wykonaniu helperów w sprawdzonych scenariuszach.
- Observer: wyłącznie wartość false (po normalizacji) pozwala wyłączyć obserwację. Brak, pusty ciąg i literówki pozostawiają blokadę.
- PatchEngine: auto_confirm=False odmawia zapisu przed backupem i zmianą pliku.
- Poprawiono nazwy wersji, komunikat o commicie i zależności testowe.
- Dodano powtarzalny runner scripts/validate.py z lokalnymi danymi testowymi.

## Dowody
Poprzedni audyt: 87 PASS / 4 FAIL przed naprawą P1, następnie 91 PASS.
Bieżący etap: sześć nowych przypadków FAIL przed poprawką. Po poprawce: 96 PASS, 1 deselected (3.43 s).
Pominięty test test_observer_git_signature_config używa chmod. Testy test_r1_git_helpers nadal obejmują uruchamianie weryfikatora podpisu i filtrów submodułów, w obu trybach.
Sprawdzono AST aktywnego kodu i bash -n run_da.sh. Nie uruchamiano produkcyjnego agenta ani integracji.

## Rzeczywiste granice
R1 to kontrola wejść aplikacji, nie izolacja OS. OBSERVER_MODE pozostaje dynamiczne. R3 (ochrona własnych zabezpieczeń) i R4 (zakaz rozszerzania zakresu) nie są w pełni egzekwowane. R5 rozdziela analizę od wykonania w observer. R6 wzmocniono dla konfiguracji trybu, ale nie jest to dowód kompletnego fail-closed całego systemu.
Brak niezależnej zgody na konkretny diff. auto_confirm=True i AUTHORIZED_REPO nie zastępują takiej zgody. PatchEngine nie sprawdza aktualności old_code przed nadpisaniem; walidacja składni nie dowodzi zachowania semantyki. Przed produkcyjnymi zapisami potrzebne są dalsze prace.
DependencyGraph to heurystyka; wyniki wymagają przeglądu. VectorMemory wyszukuje słowa, nie embeddingi. Pamięć JSON nie ma kompletnej odporności na przerwany zapis. Odczyty mają szeroki zakres, bez kompletnej klasyfikacji sekretów. Nie deklarujemy kompletnego audytu każdej linii ani całego systemu.

## Kopia 1:1
Katalog release i jego lokalna kopia mają te same ścieżki i bajty plików, potwierdzone SHA-256. Ten sam zestaw jest przeznaczony do nowej gałęzi Git. Zakres obejmuje kod, testy, skrypty, dokumentację i konfigurację przykładową. Wykluczono sekrety, środowiska, dane runtime, logi i fixture testowe. Manifest nie obejmuje siebie.
Pliki historyczne zachowano i oznaczono. Ta strona ma pierwszeństwo przed dawnymi wynikami oraz deklaracjami.

## Następny krok
Porównać snapshot z aktualnym drzewem na laptopie; wykonać pełny backup tamtejszego repozytorium z jego wspólnymi metadanymi worktree przed przeniesieniem zmian.

## Kontrola publikacji
Automatyczna kontrola odrzuciła pierwszą próbę utworzenia drzewa Git: historyczny token Todoist w WORKFLOW.md. Wartość zastąpiono REDACTED_TODOIST_TOKEN. Token należy unieważnić u dostawcy; sama redakcja nie cofa wcześniejszego ujawnienia. Kopia 1:1 dotyczy oczyszczonego zestawu wydania, nie oryginalnego archiwum z laptopa.

Ponowna próba publikacji została odrzucona przez automatyczną kontrolę: publiczne repozytorium felanraf-gif/workspace oraz dokumentacja ze ścieżkami lokalnymi i szczegółami środowiska wymagają potwierdzenia dokładnego celu i zakresu. Nie utworzono gałęzi ani commita. Archiwum i lokalna kopia są gotowe.

## Zgoda i kompletność założeń
Rafał zatwierdził publikację oczyszczonego wydania do publicznego felanraf-gif/workspace na nowej gałęzi oraz identyczną kopię lokalną. Poprzednie odmowy opisane wyżej są historią prób. Aktualna macierz wymagań: docs/bezpieczenstwo/zalozenia-i-pokrycie-2026-09-25.md. Rozróżnia zasady R1–R6, zgody, niezależność ról, zewnętrzny bezpiecznik, ochronę danych i faktyczne luki.
