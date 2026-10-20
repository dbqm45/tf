# Fork, nowa sesja, subagent czy agent teams

Najpierw zasada z SKILL.md §0: domyślnie pracuje główna sesja, delegujesz tylko, gdy przekazanie się opłaca.
Gdy się opłaca, wybierz najtańszą formę, która daje potrzebną izolację:

| Forma | Kiedy | Koszt i ograniczenia |
|---|---|---|
| **Fork** (`subagent_type: fork`; `/subtask` od v2.1.212) | poboczne zadanie, które potrzebuje całej dotychczasowej rozmowy (np. sprawdzenie hipotezy bez zaśmiecania głównego wątku) | dziedziczy cały kontekst, więc każda jego tura czyta tę historię; do sesji wraca tylko wynik |
| **Nowa sesja z worktree** (`claude -w <nazwa>`, `git worktree add`) | osobna zmiana z własną gałęzią i przeglądem, praca równoległa (core-git-workflow) | czysty start: czyta pliki od nowa, ale nie płaci za cudzą historię; środowisko (porty, baza) izolujesz sam |
| **Subagent** (`Agent`, opcjonalnie `isolation: worktree`) | dużo czytania i krótki wynik, świeże spojrzenie, zmiana mechaniczna z testem | zaczyna od zera, dostaje tylko brief; tańszy model przez parametr `model`; cache 5 min |
| **Agent teams** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | wyjątkowo: kilka ról, które muszą rozmawiać ze sobą w trakcie | **eksperymentalne**; 3–5 członków, znacznie więcej tokenów niż subagenci; bez zgody człowieka nie włączasz |

- **Limit zagnieżdżania:** subagent może uruchamiać kolejnych do głębokości `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
  (domyślnie 3; 1 = bez zagnieżdżania). Każdy poziom to osobny start od zera — w briefie zabraniaj dalszego
  delegowania, gdy nie jest potrzebne.
- [niezweryfikowane] czy fork współdzieli cache z sesją główną i czy może działać w worktree — nie zakładaj tego
  przy szacowaniu kosztu.

Źródło: Anthropic, dokumentacja Claude Code (code.claude.com/docs: „Subagents”, „Agent teams”, „Common workflows”
— worktree), dostęp 2026-10-18. Opisane własnymi słowami.
