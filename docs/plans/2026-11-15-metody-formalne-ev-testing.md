# Metody formalne dla EV: `pack-ev` i repo `ev-testing` — notatka do powrotu (2026-11-15)

Stan: propozycja, bez zmian w kodzie. Decyzja człowieka 2026-11-15: w `ev-testing` nic teraz nie robić, zapisać plan
(pozycje K10 i K10-pilot w `docs/todo.md`, sekcja „Luki z przeglądu agend szkoleń”). Repo `dbqm45/ev-testing`
przeczytane w commicie `e0b1a9a` (klon tylko do odczytu); fragmenty kodu i scenariuszy poniżej z tego commitu.

## Czy metody formalne przydadzą się w `ev-testing`?
Tak, i to bardziej niż w typowej aplikacji. `evtest` testuje dokładnie to, w czym metody formalne są najmocniejsze:
maszyny stanów, zgubione wiadomości, ponowienia i reconnect.

**Najmocniejsze dopasowanie: kontrprzykład z TLC jako scenariusz `evtest`.**
- `evtest` ma własne osie czasu w YAML (`at:` i `action:` w `internal/scenario/library/`) oraz wstrzykiwanie awarii:
  disconnect, gubienie odpowiedzi w mock CPMS, odrzucanie duplikatów połączeń.
- Ślad z TLC ma tę samą postać: krok po kroku, co się stało i w jakiej kolejności.
- Można więc przetłumaczyć kontrprzykład na scenariusz `evtest` i uruchomić go na prawdziwym CPMS. TLC znajduje
  rzadki przeplot, `evtest` sprawdza, czy prawdziwy backend się na nim wywraca. Tego nie robi ani sam model, ani sam
  losowy chaos.

**Konkretne miejsca w kodzie, które warto zamodelować:**

| Miejsce | Narzędzie | Właściwość do sprawdzenia |
|---|---|---|
| Kolejka offline transakcji (`txCall` w `internal/charger/charger.go`) | TLA+ | Start, Stop i MeterValues dostarczone w kolejności; Stop nigdy nie ginie; co dzieje się z wiadomością wysłaną tuż przed zerwaniem połączenia (ponowna wysyłka i duplikat po stronie CPMS) |
| Reconnect po cichej utracie sieci i HTTP 409 przy ponownym połączeniu (FAIL z demo w README) | TLA+ z żywotnością | „ładowarka w końcu wraca online”, gdy CPMS trzyma stare, półotwarte połączenie |
| Firmware w trakcie sesji (scenariusz FW-004, `fw_update_during_charging.yaml`) | TLA+ | instalacja nigdy nie przerywa aktywnej transakcji, także przy Reset albo restarcie w trakcie |
| Profile ładowania i composite schedule (`dom-ev-smart-charging`) | Z3 | złożony harmonogram z `stackLevel` nigdy nie przekracza limitu A/W dla żadnej kombinacji profili |

**Hipoteza do sprawdzenia, nie znalezisko:** w `txCall` wiadomość jest kolejkowana ponownie po `ErrConnLost`, ale nie
po `ErrTimeout`. Model w TLA+ szybko pokazałby, czy po timeoucie można zgubić StopTransaction, czy obsługuje to kod
wywołujący. Całej ścieżki wywołań nie czytano [niezweryfikowane].

**W fabryce `tf`** powiązanie jest naturalne: `pack-ev` ma `dom-ev-simulation-testing`, `dom-ev-session-lifecycle`
i `dom-ev-smart-charging`, a `qa-formal-methods` jest w `pack-it`. Do `dom-ev-simulation-testing` można dodać krótką
sekcję „model przed symulacją” z odnośnikiem do `qa-formal-methods` (sprawdzić, czy `pack-ev` deklaruje `pack-it`
w `requires` albo `optional_packs` — inaczej `workspace.py refs` odrzuci odwołanie).

## Proponowana kolejność
1. **K10 (repo tf):** odnośnik i sekcja „model przed symulacją” w `dom-ev-simulation-testing`; scenariusz ewaluacji
   (np. reconnect z 409 albo kolejka offline), który bez zmiany nie przechodzi; bramka; ewaluacja za zgodą.
   Opcjonalnie w `qa-formal-methods/references/` krótki opis tłumaczenia śladu TLC na oś czasu scenariusza
   (akcja modelu → akcja `evtest`: zgubiona odpowiedź → błąd mock CPMS, utrata sieci → `disconnect`).
2. **K10-pilot (repo ev-testing, za zgodą i z dostępem do zapisu):** model TLA+ kolejki offline z `txCall`
   (stany połączenia, wysyłka, odpowiedź, timeout, zerwanie, flush po BootNotification); właściwości: kolejność,
   Stop nigdy nie ginie, duplikat po zerwaniu widoczny jako dozwolony; sprawdzenie hipotezy o `ErrTimeout`.
   Każdy kontrprzykład → scenariusz YAML w `internal/scenario/library/` i test w Go (czerwony przed poprawką).
   Model w repo obok kodu (np. `internal/charger/formal/`), z commitem, który opisuje.
3. Kolejne modele z tabeli (reconnect z 409, firmware w trakcie sesji, composite schedule w Z3) — po wyniku pilotu.
