# Notatki zespołu, wiki i świeżość wiedzy

Spis treści: 1. Trzy strefy zapisu · 2. Nagłówek notatki · 3. Pojęcie przypięte do ścieżek · 4. Plik instrukcji czy
pipeline w kodzie · 5. Świeżość generowanej wiedzy

## 1. Trzy strefy zapisu
| Strefa | Gdzie w fabryce | Kto zmienia |
|---|---|---|
| Źródła | `.claude/knowledge/<id>/` (`kb.py ingest`), rejestry `zrodla.json` | nikt nie edytuje; tylko ponowne pobranie |
| Strony utrzymywane przez agenta (streszczenia, mapy, indeksy) | `docs/knowledge/**`, z polem `sources` | agent; **aktualizacja** istniejącej strony, nie przepisywanie od nowa |
| Notatki i decyzje zespołu | `docs/knowledge/**`, `docs/project/decisions.md` | tylko za zgodą człowieka |

Każde wczytanie nowych źródeł zaczynasz od planu: które strony powstaną, a które się zmienią. Człowiek widzi go
przed zapisem.

## 2. Nagłówek notatki
Notatka w `docs/knowledge/` ma krótki frontmatter, żeby inne agenty czytały ją bez zgadywania:
```yaml
type: decision        # decision | concept | partner | metric | runbook
owner: zespół-płatności
status: stable        # draft | stable | deprecated
sources: [docs/project/decisions.md#D-14, https://… (2026-10-20)]
code_refs:            # sekcja 3
  - {path: src/payments/api/, level: constraint}
verified: 2026-10-30  # wpisuje TYLKO człowiek; agent ustawia generated: <data>
stale_after: 2027-04-30
```
- **Pole `verified` wpisuje tylko człowiek.** Agent zapisuje `generated` z datą. Strona „zweryfikowana przez
  agenta” nie jest zweryfikowana.
- Opis pojęcia piszesz **słowami, którymi ludzie szukają** (i synonimami: „deploy”, „wdrożenie”, „release”).
  Wyszukiwanie słowami (BM25, `kb.py search`) nie zna synonimów.
- Decyzja zapisuje wybrany wariant, warianty odrzucone z powodem i czy kod ją realizuje. Tego agent nie odczyta
  z repo.
- Najczęstsze pułapki projektu idą na początek indeksu (`docs/knowledge/index.md`, jeśli go macie) albo do
  `docs/project/lessons.md`.
- Ten układ jest zbliżony do pól proponowanych w formacie OKF (`type`, `status`, `stale_after`, `verified`,
  `index.md`). Zgodności z samym formatem nie sprawdzono [niezweryfikowane]. Przed deklaracją zgodności porównaj
  ze specyfikacją z datą.

## 3. Pojęcie przypięte do ścieżek
Ustalenie zespołu działa dopiero wtedy, gdy agent je zobaczy **przed** edycją pliku, a nie na przeglądzie PR.
- Notatka wskazuje ścieżki, których dotyczy (`code_refs`), z poziomem:
  - `constraint` — niezmiennik do zachowania (np. zamrożone API); agent może zmieniać plik, ale nie łamie
    ustalenia;
  - `hold` — stop: przed zmianą pliku agent pyta człowieka.
- Przed pierwszą edycją pliku w zadaniu agent szuka notatek, które obejmują jego ścieżkę: `kb.py search "<ścieżka>"`
  albo `grep -rl "<katalog>" docs/knowledge`. Trafienie cytuje w planie kroku.
- To samo pole po stronie bramki (reguła „PR rusza obszar przyjętej decyzji”) jest kontrolą po zmianie. Jedno nie
  zastępuje drugiego.

## 4. Plik instrukcji czy pipeline w kodzie
- **Plik instrukcji z etapami** (np. sekcja w `AGENTS.md` albo `CLAUDE.md`) wystarcza dla małej bazy (rzędu kilkuset
  dokumentów) i na początku, gdy szukacie kształtu wiki.
- **Pipeline w kodzie**, gdy korpus jest duży, wynik ma być powtarzalny albo wiki zasila dalszą automatykę:
  - identyfikator strony jako skrót treści lub stabilny klucz (zmiana nazwy pliku nic nie psuje);
  - kontrakty typów między etapami;
  - **lint struktury Markdown przed zapisem:** jeden H1, poprawny frontmatter, żywe linki. Dwa H1 albo zepsuty
    nagłówek po cichu psują kolejne etapy;
  - wyszukiwanie słowami (BM25) zamiast wektorów dla małej wiki (pack-it: ai-rag dla większych korpusów).
- Definicje, które muszą być dokładne i mieć właściciela (metryki, schematy, reguły), czytasz deterministycznie
  z kuratorowanych plików. Wyszukiwanie zostawiasz dla archiwów i treści masowych.

## 5. Świeżość generowanej wiedzy
Generowany indeks, graf kodu albo mapa dryfuje po cichu: hook raportuje „sukces”, a mapa jest sprzed tygodni
(pominięte uruchomienie przy obciążeniu, lista rozszerzeń rozjechana ze źródłem, serwer z cache sprzed regeneracji).
- Każdy generowany artefakt wiedzy ma **znacznik czasu i commit źródła**, z którego powstał.
- Kontrola w CI (albo przy starcie sesji) porównuje ten commit z `git log -1` na ścieżkach źródłowych i alarmuje po
  progu (np. więcej niż N commitów albo 24 h różnicy). Sam kod wyjścia hooka nie wystarcza.
- Dla pobranych źródeł: `kb.py status --max-age <dni>`. Dla notatek: `stale_after` i przegląd właściciela.
- Dotyczy też map z pack-it: eng-codebase-mapping i każdego cache, który czyta agent.

Źródła: R. Brasil Monteiro, „Building a Complete Personal Harness: LLM Wiki…” (2026-05-03); U. Estari,
„Production-Grade OKF + Graphify Setup” (2026-08-13); C. Core, „The Dev with Two Brains” (2026-10-07; narzędzie
`okf-agent-memory` niesprawdzone, przed użyciem `skill_audit` i zgoda człowieka); artykuł o wiki z LLM „kod czy
plik instrukcji” (2026). Liczby i zachowanie narzędzi wg autorów [niezweryfikowane].
