# Formaty identyfikatorów — składnia i poziom pewności

Reguły składni, które sprawdza `scripts/ev_id_check.py`. Skrypt waliduje **tylko składnię**: nie sprawdza, czy operator
istnieje w rejestrze, ani cyfry kontrolnej.

Poziomy: bez oznaczenia = źródło pierwotne (przeczytane u wydawcy, 2026-10-20); **[do weryfikacji]** = źródło wtórne
(strona trzecia, wyniki wyszukiwania) albo luka w źródłach.

## EVSE ID (identyfikator punktu ładowania)
| Część | Reguła | Pewność |
|---|---|---|
| kraj | 2 litery, ISO 3166-1 alpha-2 | [do weryfikacji] (OSM wiki, IONITY, IDACS) |
| operator | 3 znaki alfanumeryczne | [do weryfikacji] |
| typ | litera `E` | [do weryfikacji] |
| ID punktu | 1–31 znaków alfanumerycznych lub `*` | [do weryfikacji]; zakres długości zadany skryptowi, norma niesprawdzona |
| separator | `*` między częściami, opcjonalny (czytelność) | [do weryfikacji] |
| pole OCPI `evse_id` | CiString(48), opcjonalne, format wg eMI3 V1.0 Part 2, nadaje operator | pierwotne (OCPI 2.2.1, Locations) |

Przykład: `SK*IOY*E222901` (IONITY) [do weryfikacji]. Ten sam ID bez separatorów: `SKIOYE222901`.
Przykład z importu dom-ev-charging: `PL*ABC*E12345*1` — końcowe `*1` to część ID punktu.
Treść eMI3 Part 2 nie była dostępna — tabela wyżej to opis zachowania, nie cytat normy.

## EMAID / Contract ID (identyfikator kontraktu e-mobilności)
| Część | Reguła | Pewność |
|---|---|---|
| kraj | 2 litery | [do weryfikacji] |
| dostawca (eMSP) | 3 znaki alfanumeryczne | [do weryfikacji] |
| instancja | 9 znaków alfanumerycznych | [do weryfikacji]; długość wg ISO 15118-2 Annex H niesprawdzona |
| cyfra kontrolna | 1 znak, opcjonalna w praktyce | [do weryfikacji] |
| separator | `-` lub `*`, opcjonalny; jeden rodzaj w obrębie ID | [do weryfikacji] |

Przykład: `NL-TNM-000122045-U` (dostawca `TNM`, instancja `000122045`, cyfra kontrolna `U`) [do weryfikacji].

## Cyfra kontrolna EMAID — czego nie wiemy
- ISO 15118 opisuje własny algorytm (wg wtórnych źródeł: równania nad Z2 i Z3, macierze P1, P2) [do weryfikacji].
  **Treść nie jest publicznie dostępna** w sprawdzonych źródłach; skill i skrypt **nie podają algorytmu**.
- To nie jest zwykły Luhn ani mod 10 — nie zgaduj i nie implementuj „podobnego” wzoru.
- Walidator referencyjny OCHP (licencja GPL v3): ochp.eu/id-validator [do weryfikacji].
- W praktyce: IDACS — decyzja eMSP; Plugsurfing waliduje cyfrę, gdy jest; Hubject normalizuje ID bez separatorów
  i bez cyfry kontrolnej [do weryfikacji].

## Ostrzeżenia skryptu (znaczenie)
| Ostrzeżenie | Co zrobić |
|---|---|
| cyfra kontrolna niesprawdzana | zwykła informacja; weryfikację zrób walidatorem referencyjnym |
| długość > 48 znaków | nie zmieści się w polu OCPI CiString(48) |
| mieszane separatory | zapisz ID w jednej postaci kanonicznej |
| niejednoznaczny typ | podaj `--type evse` albo `--type emaid` |

## Luki
Długości pól EMAID wg normy, dozwolone znaki CiString, treść eMI3 Part 2 i ISO 15118-2 Annex H (płatne / niepobrane).
Urzędy nadające kody operatorów w poszczególnych krajach: brak w źródłach [do weryfikacji].
