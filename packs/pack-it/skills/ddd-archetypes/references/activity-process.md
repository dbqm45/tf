# Archetyp Activity / Process — mapper (procedury, czynności, zlecenia pracy)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **pracy** (przegląd, naprawa, wdrożenie, obsługa zgłoszenia) na model, który rozdziela procedurę
(jak praca powinna przebiegać) od wykonania (co faktycznie zrobiono, kto, kiedy, z jakim wynikiem). Efekt: da się
odpowiedzieć „czy zrobiono zgodnie z procedurą?”, rozliczyć czas pracy i odtworzyć przebieg, zamiast trzymać wszystko
w jednym polu `status`. Protokół wspólny: `SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy trzeba odróżnić, JAK praca powinna przebiegać (procedura, wzorzec) od tego, co FAKTYCZNIE
zrobiono, kto, kiedy i z jakim wynikiem?* Tak → pasuje. Jeśli liczy się tylko, kiedy praca ma się odbyć → Planning.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „procedura / checklista / instrukcja”, „zgodnie z procedurą” | ✅ specyfikacja czynności |
| „zlecenie pracy”, „kto wykonał, kiedy, z jakim wynikiem” | ✅ wykonanie |
| „czas pracy na zleceniu”, „wielu wykonawców, role” | ✅ przypisania i rejestracja czasu |
| „zawieszone / przerwane / porzucone zlecenie” | ✅ stany wykonania |
| „harmonogram, równoległe poziomy, ścieżka krytyczna” | ❌ → Planning (`planning.md`) |
| „kolejka oczekujących na zwolnione miejsce” | ❌ → Waitlist |
| „kto ma wykonać, by koszt był minimalny” | ❌ → General assignment |
| „na czym pracujemy, w jakim stanie jest urządzenie” | ❌ → `resource-service.md` |
| „silnik workflow / Camunda / kolejka zadań” | ❌ technika, nie model domeny |
| „proces zatwierdzania z wieloma ścieżkami” | ⚠️ graniczny |

**Przypadki graniczne:**
- *Proces zatwierdzania* — jeśli tylko zmienia stan dokumentu, wystarczy maszyna stanów; jeśli ma procedurę, wykonawców
  i czas, to Activity.
- *Harmonogram vs wykonanie* — plan mówi, **kiedy ma** być zrobione; wykonanie, **co zrobiono**. Plan i wykonanie to dwa
  byty (patrz niżej plan i protokół); terminy z planu nie nadpisują faktów.
- *Reguły decyzyjne wewnątrz kroku* — decyzje to osobna notacja i osobny moduł, nie część czynności.

## Model (istota)
Rozumowanie modelowe fabryki; źródła w `## Źródła` potwierdzają tylko wskazane tam fakty.

- **Specyfikacja czynności (procedura) vs faktyczna czynność** — procedura ma kroki, strukturę (czynność złożona z kroków)
  i **wersję**; wykonanie wskazuje wersję, wg której przebiegało. To nasz wniosek z konwencji typ/egzemplarz; literatura
  wzorców (Hay) ma rozdziały o procedurach i czynnościach, ale treści rozdziałów nie przypisujemy `[założenie]`.
- **Łańcuch pracy** (nazwy pojęć za modelami danych Silverstona): zapotrzebowanie na pracę (work requirement) → zlecenie lub
  wykonanie pracy (work effort) → przypisanie stron z rolami (Work Effort Party Assignment) → rejestracja czasu
  (Work Effort Time Tracking). Zapotrzebowanie mówi **czego potrzeba**, wykonanie **co zrobiono**; jedno zapotrzebowanie
  może dać wiele wykonań i odwrotnie.
- **Akcja proponowana vs wykonana** — Fowler (rozdz. 8) rozdziela „Proposed and Implemented Action”, a także „Completed
  and Abandoned Actions” oraz „Suspension”. W naszym modelu: stany `zaproponowana → rozpoczęta → zawieszona ⇄ rozpoczęta →
  zakończona | porzucona`, każde przejście jako zdarzenie z czasem i osobą.
- **Plan i protokół** — rozdz. 8 Fowlera zawiera także „Plan” i „Protocol”. Rozumiemy je tak: plan to zamierzona sekwencja
  działań, protokół to wzorzec postępowania, wg którego plan powstaje. Harmonogramowanie to Planning.
- **Odpowiedzialność między stronami** — kto za co odpowiada wobec kogo (rozdz. 2 Fowlera nosi tytuł „Accountability”).
  Rola wykonawcy w czynności to relacja ze stroną (Party), a nie atrybut tekstowy; uprawnienia pozostają poza archetypem.
- **Rejestracja czasu** — czas pracy to osobne wpisy (kto, od–do, zlecenie), nie pole `godziny`. Sumy i koszty liczy
  Accounting / Pricing.
- **Wynik kroku** — wynik jest danymi wykonania (ocena, pomiar, uwaga), z typem zdefiniowanym w specyfikacji kroku.

**Dobór notacji** (kiedy co):

| Notacja | Kiedy | Uwaga |
|---|---|---|
| BPMN 2.0.2 (OMG, styczeń 2014) | proces o znanym z góry przebiegu | ISO/IEC 19510:2013 odpowiada wg OMG wersji 2.0.1 |
| CMMN 1.1 (OMG, grudzień 2016) | sprawa, przebieg zależy od decyzji ludzi | nie wymuszaj sekwencji |
| DMN 1.5 (OMG, formal/24-01-01, 2024) | decyzje i reguły (tablice decyzyjne) | DMN 1.6 była w beta (wrzesień 2024); stan na 2026 `[niezweryfikowane]` |

- **Wzorce przepływu sterowania** (van der Aalst i in. 2003) służą jako **lista kontrolna przypadków**: równoległość,
  synchronizacja, wybór, anulowanie. Dla każdego kroku zapytaj, czy któryś z nich występuje i jak wpływa na stany.
- **Silnik workflow to technika**: model domeny opisuje czynności i stany; silnik jest wyborem wdrożeniowym.

## Pytania
**A — decyzje standardowe:**
- Czy istnieje **procedura** (kroki, wersja)? Kto ją zmienia i czy wykonania pamiętają wersję?
- Skąd bierze się praca: zapotrzebowanie, zgłoszenie, harmonogram? Jedno zlecenie – jedno wykonanie, czy wiele?
- Jakie **stany** ma wykonanie (zawieszone, porzucone, wznowione)? Kto i z jakim uzasadnieniem je zmienia?
- Jakie **role** wykonawców i czy jeden krok ma wielu wykonawców?
- Czy rejestrujemy **czas pracy** i na jakim poziomie (zlecenie, krok)?
- Jak przebieg: znany z góry (BPMN), zależny od decyzji ludzi (CMMN), czy sterowany regułami (DMN)?

**B — luki** (przykłady):
- czynności równoległe i synchronizacja · anulowanie kroku w toku · powtarzanie kroku · zmiana procedury w trakcie
  wykonania · wynik negatywny kroku (co dalej) · czynność złożona zakończona częściowo · poprawki po zakończeniu (reopen) ·
  załączniki/dowody · audyt zmian · terminy i eskalacje (parametr, nie logika archetypu).

## Kroki mapowania
1. **Rozdziel** procedurę (specyfikację) od wykonania; ustal wersjonowanie.
2. **Struktura procedury** — kroki, kolejność, typy wyników; czynność złożona z kroków.
3. **Źródło pracy** — zapotrzebowanie → zlecenie; relacje 1–N.
4. **Stany wykonania** — proponowana, rozpoczęta, zawieszona, zakończona, porzucona; zdarzenia przejść.
5. **Strony i role** — przypisania z rolą i okresem (styk z Party); kto odpowiada.
6. **Czas pracy** — wpisy czasu; odesłanie sum do Accounting.
7. **Przypadki przepływu** — przejdź listę: równoległość, synchronizacja, wybór, anulowanie.
8. **Granice** — Planning (terminy), General assignment (kto), resource-service (na czym), silnik (technika).

## Decyzje do kontroli (R/A/X)
Wersjonowanie procedury · liczba wykonań na zlecenie · lista stanów i przejść · zawieszenie/porzucenie · role wykonawców ·
poziom rejestracji czasu · wynik negatywny kroku · zmiana procedury w trakcie · notacja (BPMN/CMMN/DMN) · ponowne otwarcie.

## Format wyniku
```markdown
# Model Activity / Process: <obszar>
## Procedury             — | Procedura | Wersja | Kroki (kolejność) | Typ wyniku kroku |
## Wykonania             — | Zlecenie | Procedura (wersja) | Źródło (zapotrzebowanie) | Stany |
## Stany i przejścia     — | Stan | Zdarzenie | Następny stan | Kto / uzasadnienie |
## Przypisania i czas    — | Wykonanie | Strona | Rola | Okres | Wpis czasu |
## Przypadki przepływu   — | Przypadek (równoległość / synchronizacja / wybór / anulowanie) | Gdzie | Reguła |
## Mapowanie pojęć       — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Integracje            — | Zdarzenie | Z / do archetypu | Reakcja |
## Decyzje (R/A/X)       — | Decyzja | Źródło |
## Uwagi                 — założenia (X), notacja, parametry polityk zmiennych, [niezweryfikowane]
```

## Wzorce i pułapki
- Jedno pole `status` i jedno pole `wykonawca` zamiast zdarzeń i przypisań: tracisz historię, zawieszenia i role.
- Procedura edytowana „w miejscu” – stare wykonania tracą punkt odniesienia. Wersjonuj lub kopiuj kroki do wykonania.
- Mieszanie planu z wykonaniem: przesunięty termin nie zmienia faktu, że krok zrobiono wcześniej lub później.
- Zakładanie, że każdy proces jest sekwencją; sprawy z decyzjami ludzi (CMMN) wymagają stanów, nie sztywnej kolejności.
- Silnik workflow jako model domeny: stany silnika nie są pojęciami biznesu; nazwy kroków powinny być z języka eksperta.
- Reguły („jeśli wynik < próg, to powtórz”) wpisane na stałe w czynność – to polityka zmienna, przekaż jako parametr.
- Autoryzacja „kto może zatwierdzić krok” – poza archetypem; archetyp zapisuje, kto to zrobił.

## Kontrola jakości
- [ ] procedura rozdzielona od wykonania; wersja zapisana w wykonaniu
- [ ] stany wykonania obejmują zawieszenie i porzucenie, z przejściami jako zdarzeniami
- [ ] przypisania stron mają rolę i okres; czas pracy jest osobnymi wpisami
- [ ] przejrzano przypadki przepływu (równoległość, synchronizacja, wybór, anulowanie)
- [ ] granice z Planning, General assignment i `resource-service.md` opisane
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** `[przykład]` „Przegląd techniczny pojazdu wg procedury z checklistą (hamulce, światła, emisja spalin).
Diagnosta wykonuje przegląd; każdy punkt dostaje wynik pozytywny lub negatywny; rejestrujemy czas pracy diagnosty.”

```markdown
## Procedury — | przegląd osobowy | v3 | hamulce → światła → spaliny (kolejność dowolna) | pozytywny/negatywny + uwaga |
## Wykonania — | przegląd pojazdu X | przegląd osobowy v3 | zgłoszenie klienta | proponowana → rozpoczęta → zakończona |
## Przypisania i czas — | przegląd X | diagnosta A | wykonawca | 10:00–10:40 | wpis czasu 40 min |
## Przypadki przepływu — wybór: wynik negatywny hamulców → przegląd zakończony z werdyktem negatywnym (X → zapytaj,
   czy kontynuować pozostałe punkty) · anulowanie: klient odjeżdża w trakcie → porzucona z uzasadnieniem
## Niezmapowane — cena przeglądu (→ Pricing) · stanowisko kontrolne (→ resource-service / Availability) ·
   termin wizyty (→ Availability / Planning)
## Decyzje — wersja procedury zapisana w wykonaniu (R) · czas na poziomie zlecenia (X, małe) ·
   skutek wyniku negatywnego (X → zapytaj)
```

## Źródła
Odczyt 2026-10-17.
- D. Hay, „Data Model Patterns: Conventions of Thought”, Dorset House 1996 — **książka; spis potwierdzony w katalogu bibliotecznym**; potwierdzony jest rozdział „Procedures and Activities”. ISBN w źródłach sprzeczne, nie podajemy. Rozróżnienia „specyfikacja vs faktyczna czynność” w treści rozdziału nie potwierdzono `[założenie]` z konwencji typ/egzemplarz. W „Enterprise Model Patterns” (Technics Publications, ISBN 978-1-935504-05-4, rok 2011 potwierdzony częściowo) rozdz. 7 „Activities” dotyczy definiowania czynności i ich podziału.
- L. Silverston, „The Data Model Resource Book”, Vol. 1 Revised Edition, Wiley 2001, ISBN 978-0-471-38023-8 — **książka; spis potwierdzony w O'Reilly (wtórnie)**; potwierdzone częściowo pojęcia: work requirement, work effort, Work Effort Party Assignment, Work Effort Time Tracking.
- M. Fowler, „Analysis Patterns: Reusable Object Models”, Addison-Wesley 1997 (autor podaje 1996), ISBN 0-201-89542-0 — **książka; spis potwierdzony u wydawcy (InformIT)**; tytuły: rozdz. 8 „Planning” (Proposed and Implemented Action, Completed and Abandoned Actions, Suspension, Plan, Protocol), rozdz. 2 „Accountability”. Treść wzorców opisana własnymi słowami i interpretacją fabryki.
- OMG, BPMN 2.0.2 (formal, styczeń 2014); ISO/IEC 19510:2013 odpowiada wg OMG wersji 2.0.1 — **norma/specyfikacja, pierwotne**; wersja i zastosowanie; samej specyfikacji nie czytano, pojęcia to wiedza ogólna.
- OMG, CMMN 1.1 (grudzień 2016) — **pierwotne**; wersja.
- OMG, DMN 1.5 (formal/24-01-01, 2024) — **pierwotne, potwierdzone częściowo**; wersja 1.6 w beta od września 2024, jej stan w 2026 niepotwierdzony.
- W. M. P. van der Aalst, A. H. M. ter Hofstede, B. Kiepuszewski, A. P. Barros, „Workflow Patterns”, Distributed and Parallel Databases 14(1), 5–51, 2003 — **pierwotne (artykuł)**; wzorce sterowania jako lista kontrolna. Rozszerzenie listy w 2006 i perspektywy danych/zasobów potwierdzone częściowo.

Opisane własnymi słowami; treść książek i norm nie była cytowana.
