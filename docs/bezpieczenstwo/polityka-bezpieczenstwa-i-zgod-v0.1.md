> Dokument historyczny. Aktualny stan i granice walidacji: `STATUS_AKTUALNY.md` w katalogu głównym.

# Towarzysz V9 — Polityka bezpieczeństwa i zgód v0.1

**Status:** wersja robocza obowiązująca  
**Data:** 18.09.2026  
**Zakres:** Towarzysz V9  
**Cel:** określenie granic autonomii, uprawnień oraz sytuacji wymagających jawnej zgody użytkownika.

---

## 1. Zasada nadrzędna

Towarzysz V9 może posiadać dużą autonomię w zakresie **obserwacji, analizy, diagnostyki, priorytetyzacji i przygotowywania rekomendacji**, ale możliwość wywoływania trwałych skutków w systemie musi być ograniczona niezależnymi regułami bezpieczeństwa.

**Prawo do analizy nie oznacza prawa do wykonania zmiany.**

W przypadku konfliktu pomiędzy wykonaniem zadania a zasadami bezpieczeństwa pierwszeństwo mają zasady bezpieczeństwa.

---

# 2. Twarde reguły bezpieczeństwa

## R1. Granica projektu

Towarzysz może wykonywać operacje modyfikujące wyłącznie w zakresie projektu lub repozytorium jednoznacznie wskazanego jako aktualny zakres pracy.

Wykrycie problemu w innym projekcie może prowadzić do:

- analizy;
- zapisania obserwacji w pamięci roboczej;
- utworzenia rekomendacji;
- poinformowania użytkownika.

Nie daje natomiast automatycznej zgody na modyfikację tego projektu.

**Próba wyjścia poza aktualny zakres → STOP / wymagana zgoda.**

---

## R2. Zakaz samodzielnego zwiększania uprawnień

Towarzysz nie może samodzielnie zwiększyć swoich uprawnień w celu wykonania zadania.

Bez jawnej zgody użytkownika zabronione jest w szczególności:

- używanie `sudo`;
- wykonywanie operacji jako `root`;
- zmiana właściciela plików;
- rozszerzanie praw zapisu lub wykonania;
- obchodzenie zabezpieczeń systemowych;
- zmiana konfiguracji mającej umożliwić agentowi wykonanie wcześniej niedozwolonej operacji.

Brak uprawnienia jest **granicą bezpieczeństwa**, a nie problemem, który agent powinien automatycznie naprawić.

---

## R3. Zakaz modyfikacji własnych zabezpieczeń

Towarzysz nie może samodzielnie:

- usuwać mechanizmów bezpieczeństwa;
- wyłączać ich;
- osłabiać ich;
- omijać ich;
- zmieniać zasad przyznawania sobie uprawnień;
- modyfikować mechanizmu wymagającego zgody użytkownika;
- zmieniać twardych blokad w celu ukończenia zadania.

Mechanizmy określające granice autonomii nie mogą być traktowane jak zwykły kod podlegający autonomicznej samonaprawie.

---

## R4. Zakaz autonomicznego rozszerzania zakresu

Towarzysz wykonuje zadanie zgodnie z celem bieżącej sesji.

Problem wykryty „przy okazji” nie staje się automatycznie nowym zadaniem.

Obowiązuje zasada:

**wykrycie ≠ autoryzacja wykonania**

Scope creep powinien zostać zatrzymany i przedstawiony użytkownikowi jako osobny potencjalny krok.

---

## R5. Rozdzielenie analizy od wykonania

Operacje analityczne i wykonawcze stanowią różne klasy uprawnień.

Dozwolone może być:

**odczyt → analiza → klasyfikacja → priorytetyzacja → rekomendacja**

bez automatycznego zezwolenia na:

**zapis → patch → komendę zmieniającą stan → commit → zmianę konfiguracji**

---

## R6. Fail closed

Jeżeli Towarzysz nie potrafi jednoznacznie określić:

- czy operacja mieści się w zakresie;
- czy posiada odpowiednie uprawnienie;
- czy operacja wymaga zgody;
- czy dotyczy chronionego zasobu;
- czy może spowodować nieprzewidziane trwałe skutki,

domyślną reakcją jest:

**STOP**

Niepewność nie może być interpretowana jako zgoda.

---

# 3. Operacje dozwolone autonomicznie

W ustalonym zakresie projektu Towarzysz może bez dodatkowej zgody wykonywać operacje niewprowadzające trwałych zmian, takie jak:

- odczyt plików;
- analiza kodu;
- analiza logów;
- analiza stanu Git;
- wykrywanie problemów;
- klasyfikacja problemów;
- ustalanie priorytetów;
- przygotowywanie rekomendacji;
- przygotowywanie propozycji zmian;
- diagnostyka;
- wykonywanie operacji jawnie zakwalifikowanych jako bezpieczne i bezskutkowe.

Autonomia analityczna może być szersza niż autonomia wykonawcza.

---

# 4. Operacje wymagające jawnej zgody użytkownika

Towarzysz musi zatrzymać wykonanie i uzyskać zgodę przed operacją obejmującą:

1. wyjście poza aktualnie autoryzowany projekt lub repozytorium;
2. użycie `sudo`, `root` lub równoważnego podwyższenia uprawnień;
3. zmianę właściciela plików;
4. zmianę uprawnień plików lub katalogów;
5. zmianę mechanizmów bezpieczeństwa Towarzysza;
6. zmianę konfiguracji systemowej;
7. operację na sekretach, tokenach, kluczach lub danych uwierzytelniających;
8. usunięcie danych;
9. wykonanie operacji trudnej lub niemożliwej do cofnięcia;
10. działanie wykraczające poza ustalony cel sesji.

Zgoda na jedną konkretną operację nie oznacza ogólnego rozszerzenia uprawnień Towarzysza.

---

# 5. Rozdzielenie odpowiedzialności

Docelowa zasada architektoniczna:

**Model proponuje → niezależna warstwa bezpieczeństwa sprawdza → executor wykonuje → wynik podlega niezależnej weryfikacji.**

Towarzysz nie powinien jednocześnie pełnić wszystkich ról:

- autora zmiany;
- wykonawcy;
- sędziego własnej zmiany;
- administratora mechanizmu bezpieczeństwa.

Agent nie może samodzielnie zamknąć pętli:

**zaproponowanie zmiany → wykonanie → uznanie jej za poprawną → zmiana własnych ograniczeń**

---

# 6. Zweryfikowany mechanizm — Observer Mode

Observer Mode jest pierwszym praktycznie zweryfikowanym mechanizmem realizującym część powyższej polityki.

Jego podstawowa granica:

**obserwacja → analiza → priorytetyzacja → rekomendacja → BLOKADA SKUTKU UBOCZNEGO**

Centralne blokady obejmują:

- Buildera;
- stosowanie patchy;
- zapis plików;
- komendy wykonawcze.

Jednocześnie zachowane pozostają:

- analiza;
- priorytetyzacja;
- generowanie rekomendacji;
- stan roboczy przechowywany w RAM.

---

# 7. Wyniki walidacji Observer Mode

Walidacja została wykonana na rzeczywistych projektach.

### Testy

- **33 testy Observer Mode — PASS**
- **72 testy całego zestawu — PASS**

### Finalny cykl

- przeskanowano **11 projektów**;
- wygenerowano **20 rekomendacji**;
- wynik cyklu: `OBSERVED`;
- zakończenie: `stopped/complete`.

### Kontrola skutków ubocznych

Porównano stan przed i po wykonaniu cyklu, obejmując:

- Git;
- HEAD;
- **17 027 wpisów plików**;
- zawartość objętą kontrolą w Obsidianie.

W przeprowadzonym zakresie walidacji **nie wykryto zmian**.

Dodatkowo:

- nie wykonano commita;
- nie zmieniono uprawnień;
- Obsidian pozostał bez zmian.

---

# 8. Granice dowodu

Powyższy wynik oznacza:

> W przeprowadzonym zakresie walidacji Observer Mode nie wykryto trwałych zmian w kontrolowanych zasobach.

Nie należy interpretować tego jako matematycznej ani absolutnej gwarancji, że Observer Mode nie może spowodować skutku ubocznego w żadnych możliwych warunkach.

Każde rozszerzenie powierzchni działania powinno być ponownie zweryfikowane.

---

# 9. Materiał dowodowy

Pełny raport walidacji:

`/home/felanraf/Projekty/towarzysz-v9-agent-clean/work/observer-validation/report.md`

Uruchomienie pojedynczego cyklu Observer Mode:

```bash
OBSERVER_MODE=true PYTHONDONTWRITEBYTECODE=1 .venv/bin/python main.py --once
```

---

# 10. Reguła dalszego rozwoju

Nowa funkcja Towarzysza nie może automatycznie otrzymywać takich samych uprawnień jak istniejące komponenty.

Rozszerzenie możliwości powinno być traktowane oddzielnie od rozszerzenia uprawnień.

**Nowa zdolność ≠ nowe uprawnienie.**

**Większa inteligencja modelu ≠ większe zaufanie systemowe.**

Granice bezpieczeństwa powinny pozostawać niezależne od tego, jak zdolny jest aktualnie używany model.

---

# 11. Status v0.1

Na dzień 18.09.2026:

**USTALONE**
- granica projektu;
- rozdzielenie analizy i wykonania;
- zakaz samodzielnego zwiększania uprawnień;
- zakaz autonomicznej modyfikacji zabezpieczeń;
- zasada fail closed;
- katalog operacji wymagających zgody użytkownika.

**ZWERYFIKOWANE**
- Observer Mode w opisanym zakresie walidacji;
- centralne blokowanie operacji wykonawczych;
- zachowanie możliwości analizy i rekomendacji bez wykrytych trwałych zmian.

**POZA ZAKRESEM v0.1**
- dodawanie nowych funkcji Towarzysza;
- rozszerzanie autonomii;
- projektowanie kolejnych komponentów wykonawczych;
- automatyczne rozszerzanie zakresu działania.

---

## Zasada końcowa

> **Towarzysz może samodzielnie myśleć szerzej, niż wolno mu samodzielnie działać. Granice działania ustala człowiek, a agent nie może sam przyznać sobie prawa do ich przesunięcia.**
