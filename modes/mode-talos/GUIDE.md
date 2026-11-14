# mode-talos — warstwa zgodności (przestarzałe)

Pętla „zadanie → PR” jest od wersji 9.34 częścią rdzenia fabryki: polecenie `/tf`, agent `tf`, skrypty
w `.claude/skills/tf/scripts/`. Przewodnik: `.tf/factory/PETLA.md`.

Ten tryb zostaje tylko po to, żeby istniejące instalacje działały bez zmian:

| Stara nazwa | Co robi teraz |
|---|---|
| `/talos-story-run <zadanie>` | to samo co `/tf <zadanie>` |
| `claude --agent talos` | to samo co `claude --agent tf` |
| `.claude/skills/talos-story-run/scripts/*.py` | przekierowanie do skryptu o tej samej nazwie w `.claude/skills/tf/scripts/` |

Nowe instalacje tego trybu nie dostają. Co zrobić u siebie: w poleceniach, własnych skryptach i w CI zamień stare
nazwy na nowe, a potem `tf remove mode-talos`. Tryb zniknie w następnym wydaniu z numerem głównym.
