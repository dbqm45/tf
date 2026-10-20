# Zgłoszenie „ładuje wolno” — drzewo przyczyn

Cel: ustalić, **kto ogranicza moc** — pojazd, ładowarka, profil czy lokacja. Nie zgłaszaj awarii, zanim nie sprawdzisz
punktów 1–4. Dowód z ramek i logów: dom-ev-diagnostics (`ocpp_log_analyze.py`).

## Pytania do kierowcy
1. AC czy DC (złącze Type 2 bez prądu stałego czy CCS)? Jaka moc na wyświetlaczu auta?
2. SoC na starcie i teraz? Czy przekracza ok. 80 %?
3. Temperatura otoczenia; czy auto jechało długo na autostradzie (gorące ogniwa) lub stało na zimnie?
4. Czy auto ma 1-fazową ładowarkę pokładową? Czy w ustawieniach auta jest ograniczenie prądu?
5. Czy obok ładuje się drugie auto na tej samej szafie mocy?

## Drzewo
| Krok | Sprawdź w CSMS | Wynik → przyczyna |
|---|---|---|
| 1. Oferta | `Current.Offered`/`Power.Offered` w `MeterValues`; composite schedule dla EVSE | oferta niska → profil, DLM, podział mocy (dom-ev-smart-charging, dom-ev-energy-management) |
| 2. Pobór vs oferta | `Power.Active.Import` względem oferty | pobór ≪ oferta → limituje auto (kroki 3–5) |
| 3. SoC (DC) | `SoC` w czasie | powyżej ok. 80 % → naturalny spadek krzywej, nie usterka |
| 4. Temperatura | pory roku, `Temperature` jeśli stacja raportuje; kierowca | zimno/gorąco → BMS tnie moc; podpowiedź preconditioningu |
| 5. AC: OBC i fazy | prąd na fazach (`Current.Import` z fazą) | jedna faza aktywna albo niska moc OBC → limit auta |
| 6. Napięcie (DC) | zakres napięcia ładowarki vs auto | auto 800 V na stacji 400 V → niższa moc (SKILL.md) |
| 7. Stacja | alarmy termiczne, status modułów, błędy | derating termiczny lub awaria modułu → serwis (dom-ev-charger-hardware) |
| 8. Kabel/złącze | `ConnectorLockFailure`, ostrzeżenia temperatury | tylko jeśli powyższe wykluczone |

## Format odpowiedzi dla supportu
- Przyczyna z dowodem (jedna linia danych: SoC, moc, oferta, temperatura).
- Co zrobić: ładować do 80 %, rozgrzać baterię, wybrać stację z wyższym zakresem napięcia, przejść na drugie EVSE.
- Kiedy eskalować do serwisu: oferta wysoka, auto nie ma ograniczeń (SoC niski, ciepła bateria), a pobór niski na
  kilku autach tej samej stacji.

## SoH
Gdy na tym samym aucie moc w podobnych warunkach spada sezon po sezonie, może to być spadek SoH. CSMS tego nie
zmierzy; to temat dla kierowcy i serwisu auta. Nie obiecuj diagnozy baterii.
