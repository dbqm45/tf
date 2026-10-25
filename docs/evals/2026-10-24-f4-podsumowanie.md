# F4: podsumowanie — rekonstrukcja projektu z kodu wobec maistera — 2026-10-24

Decyzja człowieka (2026-10-24): **obecny poziom kosztu jest zaakceptowany**, bo jakość jest wyraźnie lepsza od maistera.
Do dalszego obniżania kosztu można wrócić w przyszłości (sekcja „Powrót do kosztu”).

## Wynik końcowy
| | Nasz skill (`eng-project-reconstruction`) | maister 2.2.6 |
|---|---|---|
| Pokrycie złotego standardu (z 60, ślepa ocena) | **58–58,5** | 45–48 |
| Stack / Moduły (z 12) | 12 / 12 | 12 / 10,5–12 |
| Reguły biznesowe (z 15) | **14,5–15** | 5–5,5 |
| Standardy (z 15) | 13,5–14 | 13,5–14 |
| Inne (z 6) | 5,5–6 | 4–4,5 |
| Poprawność twierdzeń w próbie | 90–100% | 83–90% |
| Dowody `plik:linia` | przy każdym twierdzeniu, sprawdzane skryptem | pojedyncze |
| Koszt (3 repozytoria) | 4,54–5,18 USD (**76–86%** maistera) | 6,01 USD |

## Droga do wyniku
| Etap | Raport | Co zmieniono | Pokrycie | Koszt |
|---|---|---|---|---|
| v1 | `2026-10-24-f4-benchmark-maister.md` | punkt wyjścia | 51 | 4,07 USD |
| v2 | `2026-10-24-f4-benchmark-v2.md` | tabela stacku i lista modułów wymuszane przez `recon_check --final` | 51,5 | 4,34 USD |
| v3 | `2026-10-24-f4-benchmark-v3.md` | karty modułów w Markdownie, kontrola CI, idiomy testów i kodu w `standards_scan` | 58,5 | 5,38 USD |
| v4–v6 | `2026-10-24-f4-koszt.md` | `recon_scan.py`, karty zawsze na Haiku, bez odpytywania w pętli, `rules.md` i sekcja Moduły ze skryptu, samokontrola kart | 58 (v4) | 4,54–5,18 USD |

Najważniejsze lekcje:
- **Skrypty zamiast modelu tam, gdzie się da.** Skan, karty w Markdownie, reguły, sekcja Moduły i kontrola dowodów
  nic nie kosztują, a podnoszą jakość i powtarzalność.
- **Kontrola końcowa łapie błędy, których model nie widzi**, np. „brak CI” przy istniejącym `.github/workflows/`
  albo dowody ze ścieżką względną.
- **O koszcie decyduje liczba tur głównego modelu**, bo każda tura czyta cały kontekst. Mniej tur dało więcej niż
  krótsze pliki.
- **Rozrzut między przebiegami jest duży** (±0,6 USD na repozytorium, ocena maistera ±1,5 pkt). Pojedyncze rundy
  pokazują kierunek, nie dokładny efekt.

## Powrót do kosztu (na przyszłość)
Cel z planu F4 (≤ 50% kosztu maistera, czyli ≤ 3,00 USD za trzy repozytoria) nie jest osiągnięty. Główny model
(Sonnet) kosztuje 1,0–1,5 USD na repozytorium. Większość jego wyjścia to rozumowanie, a nie treść plików. Opcje do
sprawdzenia, każda z ponowną ślepą oceną jakości:
1. **Synteza na Haiku** (domeny, wymagania, szkice), Sonnet tylko dla standardów i raportu: największa oszczędność,
   ale ryzyko w standardach, gdzie przewaga nad maisterem jest najmniejsza.
2. **Szkice `CLAUDE.draft.md` i `REVIEW.draft.md` tylko na żądanie:** mniejsza oszczędność, bez wpływu na pokrycie.
3. **Tańsza samokontrola kart:** w v6 kosztowała 1,37 USD na Haiku. Można sprawdzać tylko karty, które nie przeszły
   `recon_check`.
4. **Pomiar na kilku przebiegach na repozytorium**, żeby oddzielić efekt zmiany od rozrzutu.

Narzędzia pomiaru: `docs/evals/2026-10-24-f4b/narzedzia/`.
- `run.sh` i `refresh.sh` uruchamiają przebieg; wymagają zmiennych `F4B_DIR` i `TF_WS`.
- `score.py` i `evidence.py` liczą pokrycie i dowody.
- `prompt-oceniajacego.md` zawiera prompt ślepej oceny.
- Złote standardy są w `docs/evals/2026-10-24-f4b/gold/`.

Repozytoria (commity w raporcie v1) i maistera trzeba sklonować na nowo.

## Otwarte po F4
- Test odświeżenia ze zmianą w logice: wykonany, `2026-10-24-f4-odswiezenie-logika.md` (6/6 zmian opisanych, 2 pozostałości starego opisu; maister 5,5/6, 0 pozostałości, taniej).
- Pozostałości po odświeżaniu: poprawione w PR #71 (`recon_cards.py --prev`); w powtórce testu 0 prawdziwych
  pozostałości (`2026-10-24-f4-odswiezenie-logika.md`, sekcja „Powtórka”).
- Sygnały układu pakietów i czasów życia DI w `standards_scan`: dodane (2026-10-25). Ich wpływu na pokrycie
  standardów nie mierzono ponownie.
- Koszt odświeżania: niższy niż w maisterze od wersji z `recon_refresh.py` (0,56 wobec 0,66 USD za dwa repozytoria,
  6/6 zmian, 0 pozostałości; `2026-10-24-f4-odswiezenie-logika.md`, sekcja „Powtórka 2”).
