---
name: dom-ev-knowledge-base
description: Użyj, gdy pytasz fabrykę o wiedzę EV i chcesz odpowiedzi z cytatem — rejestr zaufanych źródeł EV, rejestr standardów i terminów, persony do wdrożenia.
metadata:
  przeglad: 2027-04-22
  katalog: "Użyj, gdy odpowiedź o branży EV ma wynikać z bazy wiedzy fabryki, a nie z pamięci modelu — rejestr zaufanych źródeł EV (specyfikacje OCPP, OCPI, ISO 15118, akty prawne UE/PL/USA, urzędy) z obszarami, rangą i licencją; rejestr standardów i przepisów z terminami (standards_check.py); persony do wdrożenia odpowiedzi; przykład z cytatem ze specyfikacji. Procedura, forma odpowiedzi i polecenia kb.py: core-knowledge. Nie do procedury badania faktów w sieci (core-source-research) ani do doboru person i zespołu (core-problem-routing)."
  slowa: "zapytaj fabrykę, baza wiedzy, RAG, knowledge base, kb.py, wyszukaj w fabryce, odpowiedź z cytatem, cytat ze specyfikacji, nie z pamięci, źródło odpowiedzi, plik:linia, rejestr źródeł, zaufane źródła, wiarygodne źródła EV, dodać dokument do fabryki, dodać PDF, pobrać specyfikację, ingest, cache źródeł, licencja specyfikacji, czy mogę wrzucić do repozytorium, notatki zespołu, docs/knowledge, aktualność źródeł, stare źródło, propozycja rozwiązania, wsparcie wdrożenia, rejestr standardów, terminy przepisów i standardów, które przepisy wchodzą w życie, nieaktualne wpisy o standardach, przegląd kwartalny fabryki, standards_check"
---

# Baza wiedzy EV

Procedurę „zapytaj fabrykę”, formę odpowiedzi, polecenia `kb.py`, cache i zasady sieci opisuje skill rdzenia
**core-knowledge** (`.claude/skills/core-knowledge/SKILL.md`). Skrypt:
`python3 .claude/skills/core-knowledge/scripts/kb.py <polecenie>`. Stara ścieżka
`.claude/skills/dom-ev-knowledge-base/scripts/kb.py` przekazuje wywołanie do rdzenia i zostaje dla zgodności.
Ten skill dokłada to, co dotyczy branży EV: rejestr źródeł, rejestr standardów, persony i przykład.

## Pytanie o EV — co doprecyzować
Strona rynku (CPO, eMSP, producent, flota), rynek (PL, UE, USA), wersja protokołu (OCPP 1.6 lub 2.0.1, OCPI 2.2.1
lub 2.3). Zapytania do `kb.py search` zadawaj także z identyfikatorami pól i komunikatów, np.
`kb.py search "step_size postój PARKING_TIME"`.

## Rejestr źródeł EV (`references/zrodla.json`)
Obszary rejestru: `ocpp`, `ocpi`, `oicp`, `payments`, `iso15118`, `hardware`, `metering`, `energy`, `security`,
`implementation`, `testing`, `regulations-eu`, `regulations-pl`, `regulations-us`. Format i zasady rejestru:
core-knowledge. Specyfikacje OCA, normy IEC, ISO i SAE oraz dokumenty partnerów mają ograniczenia redystrybucji,
więc pełne teksty zostają w cache (poza gitem). Normy płatne mają w rejestrze tylko kartę normy. Test
`tests/test_kb_ev.py` waliduje rejestr.

## Rejestr standardów i przepisów (`references/rejestr-standardow.json`)
Wersje, statusy i daty (stosowanie, transpozycja, terminy przejściowe) standardów i aktów EV z datą sprawdzenia
i źródłem (`kb:<id>` z linią w `doc.txt`). Skille odsyłają do rejestru zamiast powtarzać daty, a przegląd zaczyna się od:
```bash
python3 .claude/skills/dom-ev-knowledge-base/scripts/standards_check.py --horizon 180   # nadchodzące daty, wpisy po terminie
python3 .claude/skills/dom-ev-knowledge-base/scripts/standards_check.py --strict        # kod 1: wpis do odświeżenia albo data minęła
```
- **stale** — wpis sprawdzony dawniej niż `przeglad_miesiecy`: odśwież go (research, `kb.py ingest`) i zmień `sprawdzono`.
- **recent** — data minęła od ostatniego sprawdzenia (np. przepis zaczął obowiązywać): przejrzyj skille z pola `skille`.
- **unverified** — daty nieznane (normy płatne, brak tekstu w bazie): nie cytuj ich jako faktu.

## Persona do wdrożenia
| Obszar | Persona |
|---|---|
| CSMS, brama OCPP, sesje | Oskar |
| OCPI, huby, taryfy, CDR | Roman |
| firmware, ISO 15118, licznik | Teodor |
| smart charging, energia, V2G | Elżbieta |
| przepisy PL/UE/USA, certyfikacja | Regina |
| testy interoperacyjności, symulatory | Kamil |
| produkt, aplikacja kierowcy, płatności | Patrycja |
| operacje sieci, diagnoza | Nadia |
| dane, KPI, raporty | Dawid |
Nie wiesz, kogo wybrać → Iwona (core-problem-routing).

## Przykład
**Pytanie:** „Jak OCPI liczy `step_size`, gdy po ładowaniu auto stoi jeszcze 7 minut?”
1. `kb.py search "step_size PARKING_TIME TIME postój"` → trafienia w `dom-ev-tariffs-pricing`
   (`.claude/skills/dom-ev-tariffs-pricing/references/step-size-i-zaokraglanie.md`) i w cache `ocpi-2.2.1-d2` (moduł CDRs, sekcja step_size).
2. Czytasz oba fragmenty. Specyfikacja (pobrana 2026-10-20) mówi, że `step_size` stosuje się raz dla czasu ładowania
   i postoju łącznie, ale nie przy przejściu z ładowania na postój. W przykładzie z krokiem 5 min: ładowanie 21 min
   liczy się dokładnie, postój 7 min → 10 min.
3. Odpowiedź z cytatem `…/doc.txt:L<od>-<do>` i URL-em pliku `mod_cdrs.asciidoc`; propozycja testu kalkulatora
   (`dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py`) na tym przykładzie; persona Roman.

## Pułapki EV
- Domeny urzędów i EUR-Lex bywają zablokowane w sesji w chmurze: człowiek dopuszcza domenę (Allowed domains) albo
  pobiera akt sam i podaje go przez `kb.py ingest <id> --file <plik>`.
- Treść norm płatnych (IEC, ISO, SAE) w notatce tylko własnymi słowami, nigdy kopia.
- Daty przepisów cytujesz z rejestru standardów i jego źródła, nie z pamięci; wpis `unverified` to luka.

## Źródła
Rejestr źródeł: adresy oznaczone `checked` sprawdzone 2026-10-20 (GitHub); pozostałe adresy `[do weryfikacji]`
przy pierwszym pobraniu. Mechanizm bazy wiedzy przeniesiony do rdzenia (core-knowledge) 2026-10-22.
