# Event Storming prowadzony przez agenta — fazy i protokół tury

Agent jest facylitatorem i skrybą, a wiedzę o domenie i decyzje dają ludzie. Czytasz **tylko kartę bieżącej fazy**:
mniej reguł naraz to mniej pomyłek, gdy tablica rośnie. Tablicę prowadzi skrypt (zero tokenów):
`python3 .claude/skills/ddd-event-storming/scripts/es_board.py <polecenie> --id <id-sesji>`.

## Protokół tury (każda Twoja odpowiedź w trakcie sesji)
1. **Zapisz to, co powiedział człowiek**: `add`, `edit`, `move`, `resolve`. Jego słowami, bez upiększania.
2. **Zrób jeden ruch:** jedno pytanie albo jedną małą propozycję. Nie wykładasz teorii i nie rozwiązujesz modelu
   za ludzi. Pytasz tak, żeby wydobyć wiedzę („co musiało się stać wcześniej?”, „kto o tym decyduje?”).
3. **Własną propozycję oznacz `[propozycja]`** i dodaj ją do tablicy dopiero po zgodzie człowieka.
   Fakt biznesowy, którego nikt nie potwierdził, zapisujesz jako hot spot, a nie jako kartkę.
4. **Brak wiedzy domenowej:** zapytaj eksperta domeny, czyli wykonawcę tylko do odczytu (np. analityk domeny
   persony, `specialist` ze skillami dziedzinowymi). Jego odpowiedź to propozycja dla ludzi, nie fakt na tablicy.
5. **Co kilka tur pokaż stan:** `show` (krótko: co doszło, czego brakuje), a nie całą tablicę po każdym zdaniu.

## Faza 1 — kontekst sesji
- **Cel:** jedno pytanie sesji, zakres (co poza), format (Big Picture, Process, Design), aktorzy i systemy.
- **Kartki:** `actor`, `system`, `hotspot`, `opportunity`.
- **Ruchy:** „Na jakie pytanie ma odpowiedzieć ta sesja?”, „Gdzie zaczyna się i kończy ten proces?”.
  Kontekst domeny (słownik, `docs/project/02-domain/`) czytasz raz, na starcie.
- **Wyjście:** pytanie sesji i granice są zapisane (`init --question`), człowiek potwierdza zakres.

## Faza 2 — zdarzenia
- **Cel:** jak najwięcej zdarzeń domenowych na osi czasu.
- **Kartki:** dochodzi `event` (`--pivotal` dla zdarzeń przełomowych).
- **Ruchy:** „Wypiszcie 10–20 rzeczy, które się dzieją, w czasie przeszłym”. Potem porządkowanie osi (`move`),
  synonimy jako sygnał dla słownika i zdarzenia przełomowe. Na koniec opowieść od lewej do prawej i od końca.
- **Typowe błędy:** zdarzenie w trybie rozkazującym („Wyślij paczkę” to komenda), zdarzenie techniczne zamiast
  biznesowego („Rekord zapisany”), wczesna dyskusja o rozwiązaniach.
- **Wyjście:** oś bez oczywistych luk, zdarzenia przełomowe zaznaczone, hot spoty zapisane, a człowiek mówi „dalej”.

## Faza 3 — komendy i polityki
- **Cel:** co wywołuje każde zdarzenie i co dzieje się automatycznie potem.
- **Kartki:** dochodzą `command` (`--causes`, `--actor`), `policy` (`--on`, `--issues`), `readmodel` (`--for`);
  zdarzenie z zewnątrz: `edit E --by S`.
- **Ruchy:** przy każdym zdarzeniu „co je spowodowało?”, „co aktor musiał wiedzieć?”, „co potem dzieje się
  samo?”. Ścieżki błędów i odrzuceń też są zdarzeniami.
- **Kontrola:** `check` → zdarzenie bez wyzwalacza, komenda bez zdarzenia, polityka bez „kiedy/wtedy”.
  Luka to pytanie do ludzi albo hot spot. Nie uzupełniasz jej sam.
- **Wyjście:** `check` bez luk albo luki zamienione w hot spoty; człowiek akceptuje.

## Faza 4 — agregaty
- **Cel:** która część systemu pilnuje reguł przy każdej komendzie (granica spójności).
- **Kartki:** dochodzi `aggregate` (`--handles`). Komenda do systemu zewnętrznego: `edit C --to S`.
- **Ruchy:** „jaka reguła może odrzucić tę komendę?”, „co musi być spójne natychmiast, a co może dojść później
  zdarzeniem?”. Nazwy biorą się z komend i zdarzeń, nie z tabel w bazie.
- **Zasady (ddd-tactical-design):** małe agregaty; inne agregaty wskazuje się tylko przez identyfikator; reakcje
  między agregatami idą przez zdarzenia. `check` ostrzega przy agregacie z więcej niż 7 komendami.
- **Bramka człowieka (obowiązkowa):** w późnych krokach błędy modelu się kumulują, więc agregaty zatwierdza
  człowiek. Wcześniej przegląd w świeżym kontekście: `specialist` z ddd-tactical-design dostaje `board.md`
  i odpowiada, które agregaty są za duże, za małe albo źle nazwane.
- **Wyjście:** `check` bez luk, przegląd omówiony, zgoda człowieka.

## Faza 5 — konteksty i mapa
- **Cel:** konteksty ograniczone, ich typ subdomeny i relacje między nimi.
- **Kartki:** dochodzą `context` (`--contains`, `--kind core|supporting|generic`) i `link` (`--from`, `--to`,
  `--pattern`).
- **Ruchy:** granice szukasz przy zdarzeniach przełomowych, zmianie języka i zmianie właściciela. Przy każdej
  strzałce pytasz, kto jest upstream, czy potrzebna jest warstwa ochronna (ACL) i jaki jest format wiadomości.
  Wzorce opisuje ddd-context-mapping.
- **Typ subdomeny ustala wysiłek:** core to najlepsi ludzie i pełne DDD; supporting to prościej; generic to kupić
  lub zintegrować przez ACL.
- **Typowe błędy:** granice z organigramu zamiast z języka i odpowiedzialności, jeden „uniwersalny” model tego
  samego pojęcia w kilku kontekstach, shared kernel bez potrzeby.
- **Bramka człowieka (obowiązkowa):** mapa kontekstów to decyzja trudna do odwrócenia, więc zapisz ją jako ADR.
  Przegląd w świeżym kontekście robi `architect` albo `specialist` z ddd-strategic-analysis i ddd-context-mapping.
- **Wyjście:** `check` bez luk, mapa zatwierdzona.

## Po sesji
- `show` zapisuje `board.md` obok dziennika. Słownik uzupełniasz w `docs/project/02-domain/glossary.md`,
  a decyzje w dzienniku projektu (core-project-record).
- Otwarte hot spoty to zadania z właścicielem pytania. Sesja to punkt startu, nie ostateczny model: granice
  sprawdza dopiero dostarczanie kodu.
