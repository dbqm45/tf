---
name: talos-story-run
description: Użyj tylko, gdy człowiek wpisał /talos-story-run — przestarzała nazwa polecenia /tf (pętla zadanie → PR).
metadata:
  przeglad: "2027-04-21"
  katalog: "Przestarzała nazwa polecenia `/tf` — użyj tylko wtedy, gdy człowiek wpisał `/talos-story-run`. Pętla „zadanie → PR” jest w rdzeniu (skill tf). Nie do nowych instalacji ani jako osobny sposób pracy."
argument-hint: "[plik story | treść | TSK-n [--change CHG-n]] [--auto] [--budget USD]"
disable-model-invocation: true
---

# /talos-story-run → /tf

Ta nazwa jest przestarzała. Pętla „zadanie → PR” jest częścią rdzenia fabryki pod poleceniem `/tf`.

1. Przeczytaj narzędziem Read `.claude/skills/tf/SKILL.md`.
2. Prowadź przebieg dokładnie według niego, z argumentami tego polecenia: `$ARGUMENTS`.
3. Skrypty wołaj z `.claude/skills/tf/scripts/` (stara ścieżka `.claude/skills/talos-story-run/scripts/` tylko
   przekierowuje do nich).
4. Na końcu powiedz człowiekowi jednym zdaniem: następnym razem `/tf`; warstwę zgodności usuwa `tf remove mode-talos`.

## Przykład
**Wejście:** `/talos-story-run "Jako operator chcę limit dobowy 45 zł." --auto`

**Wynik:** ten sam przebieg co `/tf "Jako operator chcę limit dobowy 45 zł." --auto`, a w podsumowaniu zdanie
o nowej nazwie.

## Checklista
- [ ] przeczytany `.claude/skills/tf/SKILL.md`, przebieg według niego
- [ ] argumenty przekazane bez zmian
- [ ] człowiek wie o nowej nazwie `/tf`
