# Agent teams (`mode-team`) — zespół agentów na żądanie

Persona prowadzi zespół 3–5 członków (wykonawców fabryki), którzy piszą do siebie bezpośrednio i biorą zadania ze
wspólnej listy. To funkcja eksperymentalna Claude Code i jest znacznie droższa od zwykłego delegowania do subagentów,
dlatego tryb nie instaluje się domyślnie, a flagę włączasz sam.

## Kiedy
- **Pasuje:** role muszą wymieniać ustalenia i spierać się w trakcie — przegląd z kilku stron, debugowanie
  z konkurencyjnymi hipotezami, zmiana przez kilka warstw z uzgadnianiem kontraktu.
- **Nie pasuje:** zadania po kolei, edycja tych samych plików, praca bez nadzoru (`claude -p` nie tworzy zespołu).
  Wtedy wystarczą subagenci persony.

## Jak
1. `tf add mode-team` — instalacja trybu.
2. `python3 .claude/skills/team-session/scripts/team_switch.py on` — flaga w `.claude/settings.local.json`
   (tylko u Ciebie); działa od następnej sesji.
3. Nowa sesja interaktywna z personą, np. `claude --agent kuba`, potem `/team-session <zadanie>`.
   Persona sprawdza, czy zespół ma sens, i pyta o skład i limit kosztu.
4. Po sesji: `team_switch.py off`. Z włączoną flagą podagent nazwany przez Claude startuje jako członek zespołu
   także wtedy, gdy nikt o zespół nie prosił.

## Na co uważać
- Koszt rośnie z liczbą członków; zmierzysz go `python3 factory/cost_report.py --days 1`.
- Każdy plik powinien mieć jednego właściciela — dwóch członków nadpisuje sobie zmiany.
- Jeden zespół na sesję; `/resume` nie przywraca członków zespołu.
- Pytania o uprawnienia członków pojawiają się w Twojej sesji; częste polecenia dopisz do `allow` przed startem.

Szczegóły przebiegu: `.claude/skills/team-session/SKILL.md`.
