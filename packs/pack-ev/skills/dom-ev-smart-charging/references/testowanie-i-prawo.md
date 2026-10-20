# Testowanie profili i wymogi prawne

## 1. Drugi przykład: sufit 11 kW w watach kontra TxDefault 16 A
Dane (`<profil>.json`): `ChargePointMaxProfile` (`Absolute`, `W`, 11000 W, 3 fazy); `TxDefaultProfile`
(`Relative`, `stackLevel` 1, `A`, okresy 0 s: 16 A, 3600 s: 6 A); transakcja rusza o 10:00.
```bash
python3 .claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py <profil>.json \
  --start 2026-10-20T10:00:00Z --duration 7200 --tx-start 2026-10-20T10:00:00Z
```
Wynik (uruchomiony 2026-10-20): `+0 s: 15,942 A` (źródło `ChargePointMaxProfile`), `+3600 s: 6 A` (`TxDefaultProfile`),
kod 0. Przeliczenie 11000 / (230 × 3) = 15,94 A jest niższe od 16 A, więc wygrywa sufit; po godzinie `TxDefault`
spada poniżej sufitu. Na ramce wysyłaj 15,9 A (krok 0,1). Z `--unit W` te same okresy to 11000 W i 4140 W.

Wariant błędny: dodaj `TxProfile` `Relative` z `startSchedule` i pierwszym `startPeriod` = 10. Skrypt zwraca kod 1:
„pierwszy `startPeriod` musi być 0” i „`Relative` nie może mieć `startSchedule`”, pomija profil, a wynik pozostaje
taki jak wyżej. Stacja odpowiedziałaby `Rejected` (`ChargingProfileFirstStartScheduleIsNotZero`,
`ChargingProfileExtraneousStartSchedule`).

## 2. Przypadki testowe po zmianie firmware lub CSMS
| Przypadek | Oczekiwanie |
|---|---|
| brak profili | odpowiedź z jednym okresem; wartość = limit domyślny stacji, zapisz ją |
| `TxDefault` 16 A + sufit 10 A | 10 A (sufit tylko obniża) |
| `Tx` 20 A + `TxDefault` 16 A, brak sufitu | 20 A (`Tx` zastępuje `TxDefault`, nie jest ograniczony nim) |
| dwa `TxDefault`, `stackLevel` 0 i 1 | obowiązuje 1; po jego `validTo` wraca 0 |
| `Recurring Daily` wpięty przed `startSchedule` | okres z poprzedniej doby |
| profil w `W` na stacji 1- i 3-fazowej | różne ampery |
| utrata łączności w trakcie sesji z `TxProfile` | limit nadal obowiązuje; po powrocie CSMS odczytuje stan |
| restart stacji | `GetCompositeSchedule` po `BootNotification` zgadza się z oczekiwanym |
| limit 5 A | brak ładowania lub odrzucenie; sprawdź zachowanie modelu |

Symulator stacji i reguły testu bramy: **dom-ev-simulation-testing**. Uwaga: wynik skryptu to wzorzec libocpp, a
nie gwarancja zgodności konkretnej ładowarki; spór między skryptem a stacją rozstrzyga `GetCompositeSchedule` ze
stacji plus ramki w logu (**dom-ev-diagnostics**).

## 3. Przepisy UE (stan tekstów pobranych 2026-10-20)
| Akt | Brzmienie (parafraza) | Miejsce |
|---|---|---|
| AFIR, rozporządzenie (UE) 2023/1804 | „smart recharging” to ładowanie, w którym natężenie prądu dostarczanego do baterii jest regulowane w czasie rzeczywistym na podstawie informacji z komunikacji elektronicznej | Art. 2 pkt 65 (`.claude/knowledge/eu-afir/doc.txt` L462) |
| AFIR | operatorzy mają zapewnić, że publiczne punkty zbudowane po 13.04.2024 lub odnowione po 14.10.2024 są zdolne do smart recharging | Art. 5 ust. 8 (L1047-1052) |
| AFIR | do 14.10.2024 wszystkie publiczne punkty mają być cyfrowo połączone (warunek wstępny dla zdalnych profili) | Art. 5 ust. 7 |
| RED III, dyrektywa (UE) 2023/2413 | „smart recharging” — natężenie regulowane dynamicznie na podstawie informacji z komunikacji elektronicznej | art. 2 pkt 14m dyrektywy 2018/2001 (`.claude/knowledge/eu-red-iii/doc.txt` L1658) |
| RED III | państwa zapewniają, że nowe i wymieniane normalne punkty niepubliczne obsługują smart recharging, interfejs z licznikiem inteligentnym (gdzie wdrożony) i, gdzie stosowne, ładowanie dwukierunkowe | Art. 20a ust. 4 (L2973-2977) |
| RED III | transpozycja do 21.05.2025 | Art. 5 (L4619-4621) |

Co z tego wynika dla oprogramowania **[wniosek, nie cytat]**: ładowarka i CSMS muszą umieć zmienić natężenie w czasie
rzeczywistym na podstawie komunikatu; profile OCPP i `ExternalConstraints` są typową realizacją, ale przepisy nie
wskazują protokołu. Obowiązek RED III dotyczy państw, więc zakres i termin dla punktów niepublicznych zależą
od ustawy krajowej. Odesłanie z Art. 20a ust. 4 RED III do „Art. 15 ust. 3 i 4” AFIR nie pasuje do tekstu AFIR
(Art. 15 ust. 3 to ocena elastyczności pojazdów przez państwa); nie wyprowadzaj z niego obowiązków **[do weryfikacji]**.
Pełna mapa obowiązków i terminów: **dom-ev-regulations-eu**; prawo polskie: **dom-ev-regulations-pl**.
