# Prompt karty modułu — stały początek (pod cache), zmienna końcówka

Stały początek jest identyczny dla wszystkich partii (wspólny prefiks = trafienia w cache promptu); zmienna jest
tylko końcówka z listą plików. Nie wstawiaj daty, numeru partii ani nazwy modułu do części stałej.

```text
Jesteś wykonawcą rekonstrukcji projektu z kodu. Czytasz WYŁĄCZNIE pliki z listy na końcu i zapisujesz JEDEN obiekt
JSON wg schematu karty modułu (pola: module, batch, purpose, entry_points, depends_on, data, rules, terms, deviations,
unknowns). Zasady:
1. Każdy element z polem evidence ma `ścieżka:linia` z tego repozytorium; reguła ma też quote — dosłowny fragment
   tej linii (sprawdza go skrypt; zmyślony cytat = karta odrzucona).
2. purpose i rules piszesz językiem biznesu, nie opisem kodu. Pewność reguły: test (jest test), kod, do potwierdzenia.
3. Czego nie widać w tych plikach (DI, kolejki, HTTP, konfiguracja zewnętrzna) — do unknowns, nie zgadujesz.
4. Ścieżki w evidence podajesz od korzenia repozytorium (z katalogiem partii).
5. Wejścia: metoda i pełna ścieżka albo nazwa zdarzenia, z klasą lub funkcją obsługującą (np. „GET /vets.html →
   VetController.showVetList”). Dane: encja lub tabela z kluczem i relacjami (np. ManyToMany ze Specialty).
6. Reguły z wartościami: długości, wzorce (regex), zakresy, daty, unikalność; mapowanie (błąd → kod HTTP, lista
   błędów, wartości enuma) w całości, z przypadkiem domyślnym i kodem sukcesu. Reguła z testu ma pewność test.
7. Pojęcia: nazwy klas, typów i adnotacji, którymi kod wyraża pojęcie (code_name), np. BaseEntity.isNew().
8. Zapisujesz kartę do pliku modules/<moduł>.json (bez komentarza przed i po JSON), potem sam ją sprawdzasz:
   python3 .claude/skills/eng-codebase-mapping/scripts/recon_cards.py <katalog modules> --repo .
   python3 .claude/skills/eng-codebase-mapping/scripts/recon_check.py <katalog modules>/<moduł>.md --repo .
   Złe dowody i cytaty poprawiasz w karcie (właściwy plik i linia z listy partii), aż kontrola da 0 złych.
   Odpowiadasz jedną linią: ścieżka pliku, liczba reguł, wynik kontroli.
Mapa repozytorium (moduły i zależności z grafu) jest poniżej, przed listą plików — nie czytasz plików spoza listy.
<MAPA REPO — stała dla całego przebiegu>
---
Partia: <nazwa> · pliki:
<lista ścieżek>
```
