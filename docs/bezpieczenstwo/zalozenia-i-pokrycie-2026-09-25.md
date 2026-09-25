# Założenia bezpieczeństwa — pokrycie i luki

Stan: 25.09.2026. Dokument uzupełnia politykę v0.1 i STATUS_AKTUALNY.md.
Wszystkie poniższe założenia są wymaganiami. Sam zapis wymagania nie dowodzi jego egzekwowania.

| Założenie | Stan implementacji i ograniczenia |
| --- | --- |
| R1: zapis tylko w autoryzowanym repozytorium | Kontrolowane wejścia sprawdzają zakres startowy, tożsamość katalogu, symlinki, hardlinki, zagnieżdżone repozytoria i .git. Testy A/B oraz backupów i rollbacku. Nie jest to sandbox OS. |
| R2: brak samodzielnego zwiększania uprawnień | Shell/Python i nieznane narzędzia są blokowane w kontrolowanych wejściach. Brak izolacji przed dowolnym kodem w procesie; nie uruchamiać agenta jako root. Sudo, chmod i chown wymagają osobnej zgody człowieka. |
| R3: brak samonaprawy zabezpieczeń | Wymaganie NIE jest w pełni wdrożone: pliki zabezpieczeń w autoryzowanym repo nie mają niezależnej ochrony. |
| R4: brak autonomicznego rozszerzania celu | Granica repo jest zamrożona, ale brak niezależnej kontroli zgodności konkretnego patcha z zaakceptowanym zadaniem. |
| R5: analiza oddzielona od wykonania | Observer blokuje kontrolowane skutki, przechowuje stan w RAM. Poza Observer nadal brak pełnej zgody powiązanej z konkretnym diffem. |
| R6: niepewność oznacza STOP | Brak/błędna autoryzacja i nieznane narzędzia są blokowane; tylko wartość false wyłącza Observer. Nie dowiedziono kompletności wszystkich ścieżek. |
| Człowiek akceptuje konkretną zmianę | auto_confirm=False blokuje batch; domyślne True NIE stanowi dowodu zgody. Potrzebne zatwierdzenie treści, celu i zakresu zmiany. |
| Niezależny autor, wykonawca i weryfikator | Role aplikacji nie zapewniają niezależnych granic zaufania. Weryfikacja patcha działa w tym samym procesie. Wymaganie docelowe. |
| Zewnętrzny, niemodyfikowalny bezpiecznik | NIEWDROŻONY. Potrzebna warstwa poza uprawnieniami agenta, zdolna odmówić wykonania i zatrzymać proces. Observer nie zastępuje tej warstwy. |
| Git i publikacja wymagają zgody | Agent blokuje modyfikujący Git. Publikacja tego wydania jest osobną operacją człowieka, zatwierdzoną przez Rafała do publicznego felanraf-gif/workspace na nowej gałęzi. Nie udziela agentowi stałego prawa do commit/push/merge/rebase/wdrożeń. |
| Sekrety i dane prywatne | Nie publikować .env, kluczy, tokenów ani danych runtime. Odczyt nie uprawnia do wysłania danych do LLM lub integracji. Historyczny token zredagowano; wymaga unieważnienia. Brak kompletnej technicznej ochrony przed wyciekiem danych. |
| Ochrona danych i odwracalność | Preflight batcha, backupy i rollback są testowane. Brak transakcji odpornej na przerwanie procesu, kontroli aktualności old_code i pełnej atomowości pamięci JSON. Usuwanie danych wymaga osobnej zgody. |
| Nowa zdolność nie daje nowych praw | Każde nowe narzędzie i integracja wymagają osobnej oceny i testów; zasada nie zależy od zdolności modelu. |
| Minimalny zakres, niezależna kopia | Nie używać worktree do izolowanej pracy na laptopie. Zachować oryginał; kopia wydania nie obejmuje brakujących metadanych Git ani stanu komputera. |

## Dowody i decyzja operacyjna

Zestaw walidacyjny: 96 PASS, 1 deselected. Pominięto historyczny test korzystający z chmod; regresje helperów Git uruchomiono. Wynik dotyczy testowanych scenariuszy, nie całego systemu ani produkcyjnego cyklu.

Kontrola ścieżek nie chroni przed wrogim procesem przenoszącym otwarte katalogi, zmianą montowań ani przejęciem interpretera. Launcher może zapisywać logi i PID poza adapterem Observer. Wywołania LLM poza Observer mogą przesyłać dane do skonfigurowanego dostawcy.

Rekomendowany tryb pozostaje obserwacyjny. Przed autonomicznymi zapisami priorytetem jest niezależna zgoda na konkretny diff i ochrona własnych zabezpieczeń. Ten etap nie rozszerza autonomii ani nie wdraża tych brakujących mechanizmów.
