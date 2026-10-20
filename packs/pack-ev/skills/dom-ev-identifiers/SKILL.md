---
name: dom-ev-identifiers
description: Użyj przy identyfikatorach w branży EV — EVSE ID, EMAID, OCPI country_code i party_id, uid vs evse_id, ID tokenów RFID, walidacja i normalizacja.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba rozpoznać, zwalidować lub znormalizować identyfikator EV: EVSE ID, EMAID (Contract ID), para country_code + party_id, różnica uid i evse_id, UID karty RFID kontra kontrakt, kto nadaje ID, cyfra kontrolna EMAID. Nie do słownika pojęć i skrótów (dom-ev-glossary), nie do ról rynku (dom-ev-market-roles), nie do PKI i certyfikatów kontraktowych Plug & Charge (dom-ev-charging, references/iso-15118.md)."
  slowa: "EVSE ID, evse_id, EMAID, Contract ID, eMA ID, cyfra kontrolna, check digit, country_code, party_id, uid, token RFID, UID karty, walidacja ID, import CSV, separator gwiazdka, normalizacja, CiString, eMI3, ID operatora, ID kontraktu, Luhn, mod 10, algorytm cyfry kontrolnej, wyliczyć cyfrę kontrolną"
---

# Identyfikatory w branży EV

Skill mówi, **jaki identyfikator jest czym**, jak wygląda jego składnia i czego nie wolno z niego wnioskować.
Składnię sprawdza skrypt (nie zgaduj ręcznie). Poziom pewności: bez oznaczenia = źródło pierwotne;
**[do weryfikacji]** = źródło wtórne albo luka.

## Sieć: brak — skrypt działa lokalnie
`ev_id_check.py` nie łączy się z siecią i nie czyta plików poza podanymi argumentami.

## Procedura
1. Ustal, **czego identyfikatorem** jest wartość: punkt ładowania, kontrakt kierowcy, strona (CPO/eMSP), obiekt OCPI
   czy nośnik (karta). Tabela niżej.
2. Gdy dostajesz konkretne wartości (kolumna z importu, log, zgłoszenie), **uruchom skrypt**:
   `python3 .claude/skills/dom-ev-identifiers/scripts/ev_id_check.py <ID> [<ID> ...] [--type auto|evse|emaid] [--json]`
   Kod wyjścia: 0 wszystkie poprawne, 1 co najmniej jeden niepoprawny, 2 błąd wywołania.
3. Czytaj wynik: typ, `valid`, postać znormalizowana, części, błędy i ostrzeżenia. Zapisuj w bazie **postać
   znormalizowaną** (wielkie litery; `*` dla EVSE, `-` dla EMAID) i oryginał osobno, jeśli trzeba go zachować.
4. Skrypt sprawdza **tylko składnię**. Nie potwierdza istnienia operatora w rejestrze ani cyfry kontrolnej —
   powiedz to wprost w odpowiedzi.
5. Pytanie o liczenie cyfry kontrolnej EMAID: patrz „Cyfra kontrolna” niżej; algorytmu nie podajemy.

## Mapa identyfikatorów
| Identyfikator | Czego dotyczy | Kto nadaje | Postać |
|---|---|---|---|
| EVSE ID | punkt ładowania (EVSE) | operator (CPO) | kraj + ID operatora + `E` + ID punktu [do weryfikacji] |
| `evse_id` w OCPI | to samo, pole opcjonalne | operator | CiString(48), format wg eMI3 |
| `uid` w OCPI | obiekt w modelu OCPI, odrębny od `evse_id` | strona zapisująca obiekt [do weryfikacji] | patrz references |
| `country_code` + `party_id` | strona OCPI (CPO lub eMSP) | wg ISO 15118 (`party_id`) | CiString(2) + CiString(3) |
| EMAID / Contract ID | kontrakt kierowcy, Plug & Charge | eMSP | kraj + dostawca + instancja + cyfra kontrolna [do weryfikacji] |
| token OCPI | uprawnienie autoryzacji (karta, aplikacja, PnC) | eMSP | moduł Tokens |
| UID karty RFID | fizyczny nośnik | producent / wydawca karty | numer z odczytu |

Reguły składni EVSE i EMAID oraz ich pewność: `references/formaty.md`.

## Przykład
Wejście: import partnera z kolumny `evse_id`: `DE*ABC*E12345*1`, `de-abc-e12345-1`, `PLXYZE777`, `NL*AB*E1`.
Postępowanie: uruchom skrypt na czterech wartościach z `--json`. Oczekiwany obraz [składnia wg references/formaty.md]:
pierwsze trzy to ten sam typ w różnych zapisach (mieszane separatory lub ich brak da ostrzeżenie, normalizacja do
wielkich liter i `*`); `NL*AB*E1` ma operatora o 2 znakach — błąd składni. Wniosek: wczytaj postać znormalizowaną,
odrzuć błędne wiersze z listą, i zaznacz, że istnienia operatora skrypt nie sprawdza.

## Cyfra kontrolna EMAID
- ISO 15118 opisuje własny algorytm; jego treść **nie jest publicznie dostępna** w sprawdzonych źródłach. Nie podawaj
  wzoru z pamięci i nie przedstawiaj Luhna ani mod 10 jako tego algorytmu.
- Sprawdzenie: walidator referencyjny OCHP (ochp.eu/id-validator, GPL v3) [do weryfikacji] albo egzemplarz normy.
- W praktyce cyfra bywa opcjonalna: Hubject normalizuje ID bez separatorów i bez niej; Plugsurfing waliduje, gdy
  jest [do weryfikacji]. Skrypt tylko ostrzega „cyfra kontrolna niesprawdzana”.
- Decyzja, czy ją wymagać, należy do właściciela produktu (eMSP), nie do kodu.

## Pułapki
- Traktowanie UID karty RFID jak kontraktu lub EMAID: to trzy różne identyfikatory (nośnik, token, kontrakt);
  łączy je eMSP.
- Użycie `evse_id` zamiast `uid` jako klucza obiektu OCPI albo wnioskowanie jednego z drugiego; `evse_id` jest opcjonalny.
- Porównywanie ID tekstem bez normalizacji: `de*abc*e1` i `DE-ABC-E1` to ten sam ID; wielkość liter i separator
  nie niosą znaczenia [do weryfikacji, CiString nie rozróżnia wielkości liter].
- Mieszanie separatorów w jednym ID; EVSE ma `*`, EMAID `-` (lub `*`).
- Przekroczenie 48 znaków (CiString(48)) po doklejeniu własnych sufiksów.
- Odczytywanie z `party_id` lub kodu operatora adresu, kraju działania czy właściciela stacji.
- Traktowanie „poprawnej składni” jako dowodu, że operator lub kontrakt istnieje.

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| dokładna składnia EVSE ID i EMAID, długości, separatory, pewność, ostrzeżenia skryptu | `references/formaty.md` |
| `country_code`, `party_id`, `uid` vs `evse_id`, tokeny, UID karty, kto nadaje ID | `references/identyfikatory-ocpi-i-tokeny.md` |

Granice: słownik pojęć — `dom-ev-glossary`; role CPO/eMSP/hub — `dom-ev-market-roles`; PKI i certyfikaty Plug & Charge —
`dom-ev-charging` (`.claude/skills/dom-ev-charging/references/iso-15118.md`).

## Checklista
- [ ] Wiadomo, czego identyfikatorem jest wartość (punkt, kontrakt, strona, obiekt, karta)
- [ ] Składnię sprawdził skrypt, nie ręczne zgadywanie; kod wyjścia i ostrzeżenia odczytane
- [ ] Zapisano postać znormalizowaną; oryginał osobno, jeśli potrzebny
- [ ] Jasno powiedziano: cyfra kontrolna i istnienie operatora nie były sprawdzane
- [ ] Algorytmu cyfry kontrolnej EMAID nie podano; wskazano walidator referencyjny lub normę
- [ ] Fakty wtórne oznaczone [do weryfikacji]

## Źródła
Tabela faktów researchera z 2026-10-20: OCPI 2.2.1 mod_locations (github.com/ocpi/ocpi, pierwotne); OSM wiki
Key:ref:EU:EVSE, support.ionity.eu, IDACS (rvo.nl), support.hubject.com, github.com/ShellRechargeSolutionsEU/mobilityid,
Benelux IDRR, ochp.eu (wtórne). Import dom-ev-charging (`.claude/skills/dom-ev-charging/references/`: ocpi.md, iso-15118.md), 2024–2025.
Luki: eMI3 Part 2 i ISO 15118-2 Annex H niepobrane; urzędy nadające kody operatorów — brak w źródłach.
