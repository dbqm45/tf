# `/tf-task`: dwa tematy odłożone z serii 2026-11-21/22

Data: 2026-11-22. Oba tematy padły przy pracy nad rodziną poleceń `/tf*` (PR #375: podział `/tf` i `/tf-task`,
PR #377: propozycja trybu). Decyzja właściciela: **odłożone**; ta notatka zapisuje je, żeby nie zostały tylko w opisach
PR-ów. Nic z tego nie jest zrobione.

## 1. Kilka zadań równolegle, każde w osobnym worktree

### Stan dziś

- `/tf-task EBO-1 EBO-2 EBO-3` prowadzi zadania **kolejno** (PR #375): `intake.py resolve` zwraca `Input: batch`,
  każde zadanie ma własną gałąź i własny PR, STOP zatrzymuje tylko swoje zadanie, na końcu jest jedno podsumowanie.
  Decyzja właściciela z 2026-11-21: najpierw kolejno, równoległość później.
- Praca bez nadzoru w osobnym worktree już istnieje: `tf work --once --budget <USD>` (`core/factory/work.py`) bierze
  **jedno** zadanie w trybie Auto (waga light lub normal), tworzy worktree `.tf/worktrees/<KEY>`, blokadę
  `.tf/locks/<KEY>.json` i uruchamia `claude -p "/tf-task <KEY> --auto --budget <USD>"` z limitem kosztu. Nie scala
  i nie wdraża; wynik to gałąź `story/<key>` z PR albo blok STOP.

### Pomysł

Kilka zadań naraz, każde w swoim worktree, z jednym widokiem postępu — złożone z istniejących elementów (`tf work`,
blokady, dashboard), bez nowego mechanizmu.

### Do ustalenia, gdy wrócimy

- **Kiedy wolno równolegle:** tylko tryb Auto (nikt nie odpowiada na pytania kilku zadań naraz) i tylko zadania bez
  wspólnych plików. Pliki znane są dopiero po planie — wcześniej trzeba je szacować (np. z wyszukania pojęć w kodzie)
  albo planować wszystkie zadania przed startem implementacji.
- **Konflikty:** dwa zadania zmieniające te same pliki → kolejno, nie równolegle; konflikt przy scaleniu drugiego PR
  rozwiązuje człowiek albo kolejny przebieg.
- **Koszt i limity:** łączny budżet (`--budget` na całość i na zadanie), limit liczby równoległych sesji; koszt rośnie
  liniowo z liczbą zadań, równoległość skraca tylko czas.
- **Widok:** dashboard `/tf-task` pokazuje już wiele przebiegów; do sprawdzenia, czy wystarczy, czy potrzebny jest
  widok „partii” (kto czeka na człowieka, które zadanie zablokowane).
- **Pytania do człowieka:** w trybie Auto pytanie kończy zadanie blokiem STOP; trzeba ustalić, jak STOP-y z kilku
  zadań trafiają do człowieka (lista „Waiting for you” już istnieje).

## 2. Złożoność liczona z kodu i kalibracja progów trybu

### Stan dziś

- `tf task mode <KEY> --propose [--apply]` (PR #377, `core/factory/task_weight.py`, `propose_mode`) proponuje tryb
  z **treści** zgłoszenia i **wagi**: jedno krótkie zdanie bez kryteriów → `plan`; brak kryteriów, otwarte pytanie,
  placeholder, zadanie wydajnościowe, waga `full` → `normal`; mała zmiana mechaniczna albo waga `light` bez braków →
  `auto`. Fabryka sama tylko obniża autonomię; podniesienie proponuje, decyduje człowiek.
- Progi są stałe i ustalone z głowy: `FEW_WORDS = 60` znaków, słowa w wyrażeniach regularnych (`SMALL`, `OPEN`,
  `PERFORMANCE`), liczba plików i cięć z planu w regule wagi.

### Pomysł A: złożoność z kodu

Ocena oparta nie tylko na treści, ale na kodzie, którego zmiana dotyczy:
- ile modułów i plików zależy od zmienianych plików (zasięg zmiany);
- pokrycie testami zmienianych miejsc (zmiana bez testów → mniej autonomii);
- złożoność cyklomatyczna i rozmiar zmienianych funkcji;
- odwracalność (migracja danych, publiczne API — częściowo już w wadze przez `risk_triage.py`).

Rozróżnienie z rozmowy 2026-11-21, które warto zachować: **rozmiar ≠ trudność**. Zmiana nazwy funkcji użytej
w 40 miejscach jest duża, ale mechaniczna i sprawdzalna kompilacją i testami (`auto` z tanim wykonawcą); poprawka
warunku w module płatności to 1 plik, ale subtelna i trudna do odwrócenia (`normal` z potwierdzeniem).

**Ograniczenie:** miary z kodu zależą od języka i narzędzi projektu, a fabryka ma być niezależna od technologii.
Możliwa droga: miary dostarczane przez dodatek (`.tf/addons/`) albo moduł `tf analyze`, a rdzeń korzysta z nich,
gdy są, i działa bez nich jak dziś. Notacja O nie mierzy trudności zadania (mierzy koszt algorytmu i jest cechą
rozwiązania) — przydaje się tylko jako sygnał, gdy zgłoszenie mówi o wydajności.

### Pomysł B: kalibracja progów na historii przebiegów

Porównywać prognozę (`proposal` i `reasons` z `mode_log` w `task.json`) z przebiegiem: liczba rund naprawy, bloki
STOP i ich kody, koszt (`core/factory/cost_stats.py`, `.tf/runs/`), a potem korygować progi. Bez tego progi pozostają
zgadywaniem.

Do ustalenia: gdzie zbierać pary prognoza–wynik (zapis przy `run_report.py finish`?), od ilu przebiegów zmiana progu
ma sens, kto zatwierdza zmianę progu (człowiek, jak każdą zmianę fabryki), czy kalibracja jest per projekt czy globalna.
Wiąże się z wnioskiem 1 z `docs/plans/2026-11-22-harness2-wnioski.md` (weryfikacja różnicowa przy zmianach fabryki).
