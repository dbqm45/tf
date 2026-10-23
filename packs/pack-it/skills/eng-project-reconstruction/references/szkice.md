# Szkice CLAUDE.md i REVIEW.md ze standardów

Oba pliki to propozycje do zatwierdzenia przez człowieka (`CLAUDE.draft.md`, `REVIEW.draft.md` w katalogu raportu).
Bierzesz tylko standardy z udziałem ≥ 70% i dowodem; resztę zostawiasz w raporcie jako „mieszane”.

## CLAUDE.draft.md (poniżej strony)
Tylko to, czego agent nie wywnioskuje z kodu, README i konfiguracji (core-agent-instructions):
- polecenia budowania i testów z plików budowania (`plik:linia`);
- 3–7 konwencji, które narzędzia nie wymuszają (np. wyjątki domenowe zamiast kodów błędów);
- pułapki: moduły legacy z innym stylem, miejsca bez testów, rzeczy niewidoczne w grafie.

## REVIEW.draft.md
Reguły przeglądu PR (core-git-workflow, odniesienie do `REVIEW.md`):
- **Ważne** (blokuje): naruszenie standardu z udziałem ≥ 90% albo reguły biznesowej z testem;
- **Drobne** (najwyżej 5 na przegląd): pozostałe standardy;
- **Wyłączenia:** kod wygenerowany i wykluczenia z `repo_inventory`, katalogi legacy wskazane jako wyjątki.
Każda reguła z odnośnikiem do `standards/<obszar>.md`.
