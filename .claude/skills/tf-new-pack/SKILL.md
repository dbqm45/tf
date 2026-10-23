---
name: tf-new-pack
description: Użyj, gdy w repo fabryki tf trzeba dodać nową nakładkę albo tryb — zakres, prefiks, zależności, scenariusze, generator new-pack, treść, bramki, PR.
metadata:
  katalog: "Użyj w repozytorium fabryki tf, gdy autor chce dodać nową nakładkę (packs/pack-*) albo tryb (modes/mode-*) — dopytanie o zakres i granice wobec istniejących skilli, wybór prefiksu i zależności, scenariusze ewaluacji przed treścią, generator `tools/workspace.py new-pack`, wypełnienie szkieletu, bramki, sprawdzenie w workspace, PR. Nie do dopisania skilla do istniejącej nakładki (core-skill-authoring), instalowania nakładek w projekcie (tf add) ani zmian w rdzeniu."
  slowa: "nowa nakładka, nowy pack, new pack, nowy tryb, nowy mode, dodać nakładkę do fabryki, pakiet wiedzy dziedzinowej, nakładka z wiedzą o, tryb pracy włączany na żądanie, workspace.py new-pack"
---

# Nowa nakładka lub tryb w fabryce

Tylko w repozytorium fabryki tf (ten skill nie trafia do projektów). Przewodnik z polami i wersjonowaniem:
`docs/new-pack.md`; zasady skilli: `core/skills/core-skill-authoring/SKILL.md`.

## Procedura
1. **Dopytaj** (core-plan-interview, jedno pytanie na raz, z rekomendacją), zanim cokolwiek powstanie:
   - jakie pytania ma obsłużyć nakładka — 3–5 przykładów słowami użytkownika;
   - czy to wiedza dziedzinowa (**nakładka**) czy sposób pracy włączany na żądanie (**tryb**, `--kind mode`);
   - granice: które z tych pytań obsługują już istniejące skille — sprawdź katalog w workspace
     (`python3 tools/workspace.py assemble --packs all`, potem `.work/all/.claude/catalog.md`); pokrywające się
     zostają w starych skillach, nowa nakładka odsyła do nich;
   - prefiks (krótki, wolny — generator odmówi zajętego) i pierwsze skille; zależności: `requires.packs`
     (bez nich nakładka nie działa) albo `optional_packs` (odwołania pomijane, gdy nakładki nie ma);
   - role lub persony: kto będzie używał skilli.
2. **Scenariusze przed treścią** — dla pierwszego skilla pokaż człowiekowi 2× trigger (pytania z luki, z grupami
   `checks.all`), 1× no-trigger z sąsiadem; po akceptacji idą do pliku scenariuszy.
3. **Generator**: `python3 tools/workspace.py new-pack <nazwa> [--kind mode] --prefix <p-> --title "…"
   --description "…" --skill <p-nazwa> [--role <rola>]`. Tworzy szkielet, dopisuje macierz CI, uruchamia
   `check` i `refs`. Szkielet nie przechodzi bramki — to oczekiwane.
4. **Wypełnij**: `pack.yaml` (komentarz, opis po angielsku, pytanie wymiaru, zależności), scenariusze z kroku 2,
   treść skilla według `core/skills/core-skill-authoring/SKILL.md` (procedura, przykład, źródła z datą), rola
   lub persona; dla trybu `GUIDE.md`. Obcych treści nie kopiujesz — licencja i audyt
   (`core/factory/skill_audit.py`).
5. **Bramki w workspace** `.work/<id>`: `python3 factory/skill_gate.py <skill>` i `--hints`, potem
   `python3 tools/workspace.py sync-gate --out .work/<id>`; podpowiedzi także na `--packs all` (nowe skille nie
   mogą podkradać pytań innym).
6. **Sprawdzenie**: `python3 tools/workspace.py check --packs <id>`, `python3 tools/workspace.py check --packs all`,
   `python3 tools/workspace.py refs`; potem PR `feat(<id>): …` (Conventional Commits) i merge po zielonym CI.

## Przykład
Prośba: „nakładka o prawie zamówień publicznych”. Pytania: przykłady (specyfikacja warunków, terminy odwołań,
kryteria oceny ofert), nakładka, nie tryb; granice — prawo UE dla produktu cyfrowego zostaje w istniejącym
skillu pack-it, nowa nakładka odsyła do niego przez `optional_packs: [pack-it]`; prefiks `pzp-`; pierwszy skill
`pzp-terminy`, rola `procurement-analyst`. Scenariusze zaakceptowane → `python3 tools/workspace.py new-pack zamowienia
--prefix pzp- --title "Public procurement" --description "Polish public procurement law…" --skill pzp-terminy
--role procurement-analyst` → treść → bramki → `check --packs pack-zamowienia` i `all` → PR
`feat(pack-zamowienia): public procurement pack`.

## Źródła
- `docs/new-pack.md`, `core/factory/PUBLIC_API.md` (format nakładki), `core/skills/core-skill-authoring/SKILL.md`.
