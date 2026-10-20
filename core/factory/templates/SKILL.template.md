---
name: {{name}}
description: {{short}}
metadata:
  katalog: "{{description}}"
---

# {{name}}

<!--
Zasady dobrego skilla:
- description (wyżej) to REGUŁA WYBORU: „Użyj, gdy/przy <sytuacja> — <kluczowe pojęcia>.” (≤ 170 znaków, bez „: ”, bo psuje YAML) — tylko to
  Claude widzi na starcie (pole metadata Claude Code ignoruje), a lista
  wszystkich opisów mieści się w ~1% okna kontekstu. Pełny opis z granicami („Nie do …”) → metadata.katalog
  (czyta go dyspozytor z .claude/catalog.md). Skill uruchamiany tylko ręcznie: disable-model-invocation: true.
- Ewaluacje: tests/skill_evals/<nazwa>.json — 2 pytania, przy których skill ma się uruchomić (z kontrolą wiedzy
  specyficznej), 1 pytanie sąsiedniego skilla (format w tests/skill_evals/README.md).
- Nie używaj pola paths: skill z paths jest dla modelu nieznany („Unknown skill”), dopóki w sesji nie pojawi się
  pasujący plik — także przy jawnym wywołaniu i w personach (pomiar 2026-10-02). Uruchamianie zapewnia hook skill_hint.
- Ten plik: maks. ~150–300 linii (Anthropic: < 500), mieści się „na ekranie telefonu” w części zasad; szczegóły,
  przypadki brzegowe i długie przykłady → references/ (jeden poziom od SKILL.md, spis treści przy > 100 liniach).
- Przykłady > reguły: co najmniej jeden konkretny przykład (wejście → wynik) w sekcji „Przykład”, więcej
  w references/przyklady.md.
- Kod tam, gdzie pasuje: sortowanie, parsowanie, liczenie, walidacja → skrypt w scripts/ (deterministyczny, tańszy).
  Napisz, czy skrypt URUCHOMIĆ, czy PRZECZYTAĆ. Skrypt łączący się z siecią deklarujesz linią „Sieć: …”.
- Jeden skill, jedno zadanie: jeśli opis wymienia kilka niezależnych zadań, podziel skill.
- Nie powtarzaj treści innych skilli — odsyłaj do nich po nazwie („stosuj zasady z fe-css”).
- Dobry skill pakuje PROCEDURĘ, którą agent inaczej by improwizował: kroki, kolejność, punkty decyzji, format wyniku.
  Sama wiedza („czym jest X”) bez kroków rzadko zmienia zachowanie agenta.
- Jeśli skill korzysta z narzędzi zewnętrznych: tryb podglądu przed zapisem, diagnostyka („czy narzędzie działa”),
  rezerwa, gdy narzędzie zawiedzie, i ostrzeżenia o ryzyku (konta, limity, poświadczenia).
-->

## Kiedy stosować
- …

## Procedura
1. …

## Zasady
- …

## Przykład
<!-- Wejście (polecenie lub sytuacja) → wynik (fragment kodu, decyzja, artefakt). Konkretne liczby i nazwy. -->

## Checklista przed oddaniem pracy
- [ ] …

## Materiały dodatkowe
- `references/…` — czytaj tylko, gdy potrzebujesz szczegółów o …
