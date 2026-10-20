# Przykłady i tryb brownfield

## Tryb brownfield — co zmienia się w fazach
| Faza | Greenfield | Brownfield (wymagania jako delta) |
|---|---|---|
| Problem | ból, osoba, moment, koszt dziś | co istnieje, kto używa, co boli, **co nie może się zepsuć** |
| Dostęp | model logowania i ról | obecny model; czy zmiana go dotyka |
| MVP | pierwszy przepływ i szacunek | najmniejsza zmiana dowodząca poprawy + zasięg rażenia (moduły, dane, integracje) |
| Wymagania | `FR-NNN … Priorytet` | jak wyżej + `Zmiana: nowe / zmienione / zachowane` |
| Reguła biznesowa | jedno zdanie, test pustego CRUD | jedno zdanie o zmianie reguły albo „bez zmiany reguły domenowej” |
| Zapis | brief + wymagania | dodatkowo „Obecny system” i „Zachowane zachowanie” |

W sekcji „Obecny system” wolno nazywać technologie (opisujesz to, co jest). `requirements_lint.py` jej nie sprawdza.

## Przykład brownfield — lista oczekujących w systemie rezerwacji
**Wejście:** „Mamy działający system rezerwacji sal. Chcemy listę oczekujących, gdy sala jest zajęta.”
**Szare strefy fazy 1 (opcje z rekomendacją):**
- kto zapisuje się na listę: a) pracownik, b) też recepcja w czyimś imieniu → rekomendacja: a (mniejszy zasięg);
- co się dzieje po zwolnieniu sali: a) powiadomienie i 30 min na potwierdzenie, b) automatyczna rezerwacja →
  rekomendacja: a (b zmienia regułę przydziału — większe ryzyko);
- nie wiem → do „Otwartych pytań” (→ kierownik biura).
**Wynik (fragment):**
```
- FR-014: Pracownik może zapisać się na listę oczekujących na zajęty termin sali. Priorytet: must. Zmiana: nowe
- FR-003: Pracownik może anulować rezerwację. Priorytet: must. Zmiana: zmienione (anulacja zwalnia termin dla listy)
## Zachowane zachowanie
- rezerwacja bez listy oczekujących działa jak dziś; limity rezerwacji na osobę bez zmian
## Reguła biznesowa
Zwolniony termin dostaje pierwsza osoba z listy, która potwierdzi go w ciągu 30 minut od powiadomienia.
```

## Przykład rundy wyzwania (faza 5)
`FR-002: Uczący się może zaakceptować, poprawić albo odrzucić każdą propozycję.`
Kontrargumenty do wyboru:
1. przy 15 propozycjach akceptacja pojedynczo męczy — rozważ „zaakceptuj wszystkie” z podglądem;
2. poprawianie treści psuje powiązanie z tekstem źródłowym — zapisz, czy fiszka trzyma odnośnik do źródła;
3. odrzucone propozycje mogą wracać przy kolejnym generowaniu — czy pamiętamy odrzucenia?
4. bez kontrargumentu.
Wynik zapisany pod FR jako „Wyzwanie: …”; nowa potrzeba z rozmowy trafia do „Otwartych pytań”, a nie do FR.

## Przykład pustego CRUD
**Wejście:** „Użytkownik dodaje, przegląda, edytuje i usuwa przepisy.”
**Odpowiedź agenta:** „To pusty CRUD — aplikacja niczego sama nie rozstrzyga. Który kształt reguły pasuje?
rekomendacja (co ugotować z tego, co mam w lodówce) · klasyfikacja (dieta, alergeny) · obliczenie (porcje,
kalorie, lista zakupów na tydzień) · walidacja (przepis bez kroków nie zostanie opublikowany) · albo świadomie
zostajemy przy CRUD i zapisuję to jako otwarte pytanie.”

## Przykład wyjścia skryptu
```
$ python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py requirements.md --brief brief.md
Gotowość: 3/4
  · brak: historyjka z kryteriami Given/When/Then dla głównego przepływu
requirements.md:41 — miejsce wykonania: „po stronie serwera” → opisz zachowanie widoczne z zewnątrz albo przenieś do „Do decyzji o stacku”
MVP: szacunek 25 dni > budżet 15 dni — BRAK potwierdzenia kosztu — zaproponuj cięcia
✗ są blokujące problemy
```
