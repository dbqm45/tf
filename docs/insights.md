# Insights

## Konsultanci: jak zespoły z różnych nakładek pytają się nawzajem

### Ograniczenie, z którego to wynika

W Claude Code agenci nie rozmawiają ze sobą swobodnie:

- **Podagent nie może wywołać kolejnego podagenta.** Według dokumentacji Claude Code podagenci nie uruchamiają
  własnych podagentów. Wykonawca uruchomiony przez personę (np. `jan-backend`) nie zleci więc pracy innemu agentowi;
  robi to tylko sesja główna.
- **Sesje są od siebie odizolowane.** Persona uruchomiona jako `claude --agent jan` nie widzi rozmowy persony
  `claude --agent oskar`, nawet w tym samym repozytorium. Nie ma kanału, którym jedna sesja zada pytanie drugiej
  i dostanie odpowiedź.
- **Podagent nie widzi rozmowy, która go wywołała.** Dostaje tylko brief i zwraca jeden raport.

„Swobodna rozmowa” persony IT z personą EV nie jest więc możliwa. Możliwe jest coś węższego: **sesja główna
(persona) wywołuje wyspecjalizowanego podagenta z wiedzą innej dziedziny i dostaje od niego odpowiedź.**

### Mechanizm

1. **Konsultanci nakładki.** Każda nakładka deklaruje w `pack.yaml` (sekcja `consultants`) agentów do konsultacji:
   nazwę, opis, skille i tier. `factory/build.py` generuje z nich agentów:
   - tylko do odczytu (`Read`, `Grep`, `Glob`, `Skill`) — konsultant odpowiada, nie zmienia plików;
   - z wczytanymi skillami swojej dziedziny;
   - z kontraktem odpowiedzi: krótka odpowiedź, źródło (skill, plik, standard), czego nie wie, co wymaga decyzji
     człowieka.
2. **Generowany katalog „kogo zapytać”.** Do promptu każdej persony `build.py` wkleja tabelę konsultantów
   z **innych** zainstalowanych nakładek i dopisuje ich do listy agentów, których persona może wywołać
   (`Agent(...)` w nagłówku pliku agenta). Persona `jan` (pack-it) przy zainstalowanym pack-ev widzi np.
   `ev-consult-protocols`; bez pack-ev tego wiersza nie ma i nic się nie psuje.
3. **Wspólne skille.** Skille wszystkich zainstalowanych nakładek leżą w jednym `.claude/skills/`, więc persona może
   też sama wczytać skill innej dziedziny. Konsultant jest lepszy przy szerszym pytaniu: czyta wiele skilli i plików
   we własnym kontekście, a do persony wraca tylko odpowiedź (kontekst persony nie puchnie).
4. **Plik pytań do innej persony.** Gdy pytanie wymaga pracy innej persony w jej własnej sesji albo decyzji
   człowieka, persona zapisuje je w `docs/project/questions.md` (kto pyta, do kogo, pytanie, kontekst, termin).
   Druga persona odpowiada w tym pliku w swojej sesji. To kanał asynchroniczny, nie rozmowa na żywo.

### Kto może konsultować

| Kto | Może wywołać konsultanta? | Dlaczego |
|---|---|---|
| persona uruchomiona jako sesja (`claude --agent jan`) | tak | ma narzędzie `Agent` |
| wykonawca persony (`jan-backend`) | nie | podagent nie wywołuje podagentów; potrzebę konsultacji zgłasza w raporcie, a persona ją wykonuje |
| konsultant | nie | jest podagentem; jeśli pytanie wykracza poza jego dziedzinę, pisze to w odpowiedzi |

Typowy przebieg: `jan-backend` w raporcie pisze „potrzebna decyzja: jak liczyć kWh przy korekcie CDR”. Jan wywołuje
`ev-consult-business`, dostaje odpowiedź ze źródłem i przekazuje ją w kolejnym briefie wykonawcy.

### Koszty i granice

- Każde wywołanie konsultanta to nowy kontekst: wczytuje skille od zera. Persona pyta, gdy odpowiedź jest warta
  więcej niż samodzielne wczytanie jednego skilla.
- Opisy wszystkich agentów (także konsultantów) trafiają do kontekstu sesji. Każda nakładka dokłada więc kilka
  wierszy; dlatego konsultantów jest kilku na nakładkę (po obszarach), a nie po jednym na skill.
- Konsultant nie zastępuje persony innej dziedziny w dłuższej pracy (projekt, implementacja). Do tego służy osobna
  sesja tej persony i plik pytań.

### Inne narzędzia niż Claude Code

Warstwa targetów (`core/targets/`) pozwoli kiedyś generować pliki dla innych narzędzi (np. Codex, Gemini CLI).
Tam, gdzie narzędzie nie ma podagentów, konsultacje przechodzą w tryb zastępczy: persona wczytuje skille innej
nakładki sama (pkt 3) albo korzysta z pliku pytań (pkt 4).
