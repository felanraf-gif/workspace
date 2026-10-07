# Towarzysz V9 — paczka testowa na VM, 07.10.2026

Paczka zawiera aktualne źródła z archiwum użytkownika oraz poprawki wykonane
w chmurze: ograniczenie zapisów kontrolera przez Landlock, kontrolę katalogów,
czytelny diff i parametr katalogu roboczego dla launchera. Nie zawiera historii
Git, sekretów, venv ani danych testowych. Nie jest wydaniem produkcyjnym.

W chmurze: **145 PASS, 2 SKIPPED, 1 DESELECTED**. Dwie pominięte próby
dotyczą prawdziwego Landlock. Izolowany start Observera pozostał zablokowany.
Na VM wymagamy faktycznego zaliczenia tych dwóch prób i sondy bubblewrap.

## 1. Sprawdź i rozpakuj paczkę

Umieść archiwum i plik `.sha256` w jednym katalogu, następnie:

```bash
sha256sum -c towarzysz-v9-vm-tests-20261007.tar.gz.sha256
# Rozpakowuj w nowym katalogu, bez nadpisywania wcześniejszych plików.
tar --no-same-owner -xzf towarzysz-v9-vm-tests-20261007.tar.gz
python3 -B towarzysz-v9-vm-tests-20261007/verify_package.py
```

## 2. Przygotuj osobną kopię testową — polecenia operatora

Wykonaj poniższe polecenia ręcznie, poza agentem. Zmień `CURRENT_REPO` na
rzeczywistą ścieżkę Twojego repozytorium. Zachowaj stary katalog w całości;
nie resetuj go, nie przenoś do niego paczki i nie kasuj lokalnych zmian.
Kopia powstaje ze snapshotu HEAD i nie przenosi niezatwierdzonych plików ani
ignorowanego `.env`; lokalna historia Git pozostaje w kopii. Nie używaj
repozytorium z sekretami w śledzonych plikach. Źródła paczki mają pierwszeństwo
tylko w nowym katalogu testowym.

```bash
CURRENT_REPO="$HOME/Projekty/workspace"  # sprawdź i zmień, jeśli trzeba
PACKAGE="$(pwd)/towarzysz-v9-vm-tests-20261007"
CANDIDATE="$HOME/Projekty/towarzysz-v9-test-20261007"
test -d "$CURRENT_REPO/.git" && test ! -e "$CANDIDATE" || exit 1
git clone --no-hardlinks -- "$CURRENT_REPO" "$CANDIDATE"
cp -R "$PACKAGE/sources/." "$CANDIDATE/"
python3 -m venv "$CANDIDATE/.venv"
"$CANDIDATE/.venv/bin/python" -m pip install -r "$CANDIDATE/requirements-dev.txt"
"$CANDIDATE/.venv/bin/python" -m pip check
```

Potrzebny jest Python 3.10+ (sprawdzone tutaj na 3.12), Linux x86_64/aarch64
z Landlock ABI ≥ 3, zaufany systemowy `/usr/bin/bwrap` i działające przestrzenie
użytkownika. Nie zmieniaj właściciela narzędzia ani polityk jądra, aby pozornie
zaliczyć test. Jeśli `.git` jest plikiem wskazującym worktree, ta procedura
odmawia przygotowania kopii: najpierw wskaż zwykły checkout.

## 3. Wykonaj testy akceptacyjne

```bash
python3 -B "$PACKAGE/test_vm.py" \
  --repo "$CANDIDATE" \
  --python "$CANDIDATE/.venv/bin/python" \
  --workspace-root "$HOME/Projekty" \
  --results "$HOME/towarzysz-v9-results-20261007"
```

Runner nie uruchamia usługi, nie używa zewnętrznych integracji, nie stosuje
zmian w prawdziwych projektach i nie obchodzi izolacji. Najpierw uruchamia pełny
zestaw, potem dwie próby Landlock na fikcyjnym repozytorium (w tym przeniesienie
katalogu po kontroli), następnie sondę odmowy zapisu i jeden izolowany cykl.
Pominięcie choć jednej wymaganej próby Landlock zatrzymuje procedurę.
Historyczny test wymagający chmod pozostaje celowo wyłączony.

Sukces to kod 0 oraz końcowy komunikat PASS; samo uruchomienie procesu lub
kod 0 z pytest, które pomija testy, nie wystarcza. Logi i raport XML znajdziesz
w katalogu `--results`. Ponowna próba wymaga nowego katalogu wyników.
Runner sprawdza niezmienność plików źródłowych, pomijając `.git`, `.venv`,
`work` i cache; nie jest to audyt całej VM. Przed przekazaniem logów sprawdź,
czy nie ujawniają danych lokalnych.

## 4. Powrót i dalsze kroki

Poprzednie repozytorium jest nietknięte, więc powrót polega na korzystaniu
z jego dotychczasowej ścieżki. Niczego nie kopiuj z powrotem z kopii testowej.
Nie zmieniaj usług systemd, nie włączaj Buildera i nie wykonuj push.
Katalog testowy można zachować do diagnozy; nie wymaga usuwania, aby wrócić.

Po zaliczeniu wszystkich prób przejrzyj diff względem starej kopii. Dopiero
w osobnym kroku zdecyduj o przeniesieniu źródeł do właściwego repozytorium.
Sukces tych testów nie zapewnia niezależnej zgody między złośliwymi procesami
działającymi na tym samym UID ani gotowości do pracy autonomicznej.
