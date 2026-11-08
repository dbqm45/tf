# Protokół: porównanie przepływów na tych samych zgłoszeniach

Cel: zmierzyć, kiedy pełny przepływ (`mode-pdi`), krótki (`talos`) i sam tryb planu dają lepszy wynik przy jakim
koszcie. Wniosek z porównania z dev-kitem (2026-11-08): pełny przepływ kosztował tam 7–12× więcej (źródło: raport z testów dev-kitu przekazany przez człowieka) niż tryb planu przy
porównywalnej jakości, a o wyniku decydował kontekst w zgłoszeniu; własnych danych fabryka jeszcze nie ma.

## Dobór zgłoszeń
- 6–10 zgłoszeń z prawdziwego repozytorium, w trzech grupach: fakty w całości w zgłoszeniu; potrzeba krótkiego
  rozpoznania; zależność od kontekstu spoza zgłoszenia (bezpieczeństwo, integracja, konfiguracja środowiska).
- To samo zgłoszenie i ten sam punkt startu (`base`) dla każdego przepływu; ten sam model sesji.
- Kolejność przebiegów losowa na zgłoszenie (przebieg późniejszy nie widzi wcześniejszych PR).

## Przebiegi
Każdy przepływ na osobnej gałęzi; koszt i czas z raportu przebiegu (`run_report.py`, `cost_report.py`) albo z
`total_cost_usd`. Wpisy do `flows.json` (format w nagłówku `tools/flow_compare.py`).

## Ocena ślepa
1. `python3 tools/flow_compare.py prepare flows.json --out <katalog>` — diffy A/B/C i szablon `ocena.json`.
2. Oceniający (człowiek albo agent bez dostępu do klucza i do repo przebiegów) wypełnia ocenę wg kryteriów z szablonu:
   poprawność wobec kryteriów zgłoszenia, testy sprawdzają zachowanie, zgodność z konwencjami repo, rozmiar
   i czytelność, gotowe do merge bez dalszych poprawek.
3. `python3 tools/flow_compare.py report flows.json --key <katalog>/key.json --verdicts oceny.json --out <raport>.md`.

## Raport w docs/evals/
Tabela na zgłoszenie i podsumowanie wygranych; linia „Pliki:” ze źródłami danych; `claims_check.py` bez błędów.
Wniosek formułujemy na grupę zgłoszeń (fakty w zgłoszeniu / rozpoznanie / kontekst spoza), nie jedną liczbą.

## Koszt
Przebiegi są płatne (rzędu 5–100 USD na zgłoszenie i przepływ wg danych dev-kitu) — uruchomienie tylko za zgodą
człowieka z budżetem.
