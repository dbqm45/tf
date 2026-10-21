# Talos — historyjka → PR na żądanie

Talos (`mode-talos`) to tryb fabryki, który bierze jedną historyjkę użytkownika i prowadzi ją do jednego PR: plan, testy, kod,
weryfikacja, commity i raport kosztu. Działa tylko wtedy, gdy go uruchomisz — model nigdy nie włącza go sam.
Instaluje się domyślnie; bez niego: `tf remove mode-talos`, z powrotem: `tf add mode-talos`.

## Do czego
- **Pasuje:** historyjka z kryteriami akceptacji, które da się sprawdzić testem; zmiana mieści się w kilku
  kawałkach (do 5) i w jednym PR; repozytorium ma testy i polecenia weryfikacji (CLAUDE.md).
- **Nie pasuje:** praca koncepcyjna (co budować, architektura od zera), decyzje produktowe w trakcie, dostęp do
  produkcji, historyjka bez kryteriów akceptacji. Wtedy pracujesz z personą, a Talos wróci, gdy historyjka będzie
  gotowa.

## Jak uruchomić
Dwa sposoby, ten sam przebieg (skill `talos-story-run`):

| Sposób | Polecenie | Kiedy |
|---|---|---|
| agent Talos | `claude --agent talos`, potem treść historyjki albo ścieżka do pliku | sesja tylko na automat |
| w dowolnej personie | `/talos-story-run <plik story albo treść> [--auto] [--budget USD]` | jednorazowo, w bieżącej sesji |

Opcje (w wiadomości do Talosa albo przy poleceniu):
- `--auto` — plan nie czeka na Twoją akceptację; bez tej opcji Talos pokazuje plan i czeka;
- `--budget <USD>` — twardy limit: po kawałku, który go przekroczy, Talos się zatrzymuje. Domyślnie budżetu nie ma,
  ale Talos zawsze wybiera najtańszy wystarczający model i najmniej pracy.

Przykład:
```
claude --agent talos
> Jako operator chcę zaimportować plik CDR (CSV) i zobaczyć sesje z błędem. --auto
```

## Co robi
1. **Start:** wymaga czystego drzewa roboczego, zakłada katalog przebiegu i gałąź `story/<slug>`.
2. **Przyjęcie historyjki:** sprawdza, kto, co i po co oraz kryteria akceptacji. Gdy ich brakuje, zadaje do 3 pytań
   (z `--auto` — zatrzymuje się z tymi pytaniami).
3. **Plan:** do 5 kawałków pionowych — każdy niesie wartość, sam przechodzi testy i jest osobnym commitem.
   Historyjka na więcej kawałków → propozycja podziału i STOP.
4. **Kawałek po kawałku:** test, który nie przechodzi → najmniejszy kod → weryfikacja (testy, lint, typy) → przegląd
   zakresu przez `scope-reviewer` w świeżym kontekście → commit. Najwyżej 2 próby naprawy, potem STOP z opisem
   blokady.
5. **KISS:** przypadki brzegowe, pomysły i ryzyka spoza kryteriów nie trafiają do kodu, tylko do `parked.md`
   i do sekcji „Odłożone do decyzji” w opisie PR.
6. **Fazy warunkowe:** dokumentacja tylko przy zmianie publicznego API, przegląd bezpieczeństwa tylko przy auth,
   sekretach, IaC lub CI, architekt tylko przy decyzji trudnej do odwrócenia.
7. **Koniec:** jeden PR (Talos go nie scala) i raport.

## Co dostajesz
Katalog `.claude/runs/<data>-<slug>/` (ignorowany przez git):

| Plik | Treść |
|---|---|
| `story.md` | historyjka |
| `plan.md` | kawałki z polami do odhaczenia — stan, od którego wznawiasz przerwany przebieg |
| `parked.md` | sprawy odłożone do Twojej decyzji |
| `report.md` | raport przebiegu |

Raport (`python3 .claude/skills/talos-story-run/scripts/run_report.py finish <katalog>`): czas, tokeny (wejście, wyjście, odczyt i zapis cache),
koszt w USD, modele i agenci, kawałki zrobione / plan, liczba odłożonych spraw. Liczy go skrypt z transkryptów
sesji, nie model, więc nie zużywa tokenów. Koszt to szacunek z cennika API — przy subskrypcji równowartość, nie
faktura. W trakcie przebiegu jedna linia stanu:
`python3 .claude/skills/talos-story-run/scripts/run_report.py status <katalog>`.

## Gdy Talos się zatrzyma
Blok STOP mówi, co blokuje (z dowodem), co jest już zrobione (commity), czego potrzeba od Ciebie i od którego
kawałka wznowić. Po decyzji poproś Talosa o wznowienie i podaj katalog przebiegu: pierwszy nieodhaczony kawałek
w `plan.md` to miejsce, od którego kontynuuje. Raport kosztu powstaje także po STOP.

Szczegóły przebiegu: `.claude/skills/talos-story-run/SKILL.md` (w źródłach fabryki:
`modes/mode-talos/skills/talos-story-run/SKILL.md`); mechanizm: `docs/insights.md` w repozytorium fabryki, sekcje
„Tryby” i „Talos”.
