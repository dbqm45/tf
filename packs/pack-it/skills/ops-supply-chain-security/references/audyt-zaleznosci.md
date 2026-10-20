# Audyt zależności — polecenia i czytanie wyników

Audyt uruchamiasz w CI i przy starcie pracy w repo (eng-repo-readiness). Audyt **raportuje**, nie naprawia:
`npm audit fix` i odpowiedniki tylko za zgodą człowieka, z przeglądem diffu lockfile.

| Rodzina | Polecenie (wynik maszynowy) | Uwagi |
|---|---|---|
| JS/TS (npm) | `npm audit --json` | kod wyjścia ≠ 0 przy znaleziskach to informacja, nie awaria kroku; próg: `--audit-level=high` |
| JS/TS (pnpm) | `pnpm audit --json` | |
| Python | `pip-audit --format json` (sprawdzone na 2.10.1) | bez natywnej wagi → domyślnie średnia, chyba że opis mówi inaczej; dla projektu z lockfile: `pip-audit --locked` |
| Rust | `cargo audit --json` | wymaga `cargo install cargo-audit` |
| Go | `govulncheck -json ./...` | zgłasza tylko podatności osiągalne z kodu — mniej szumu |
| Ruby | `bundle audit check --update` | wynik tekstowy |
| PHP | `composer audit --format json` | od Composera 2.4 — sprawdź wersję |
| .NET | `dotnet list package --vulnerable --include-transitive` | w nowszym SDK także `dotnet package list --vulnerable` |
| Java, Dart | brak wbudowanego — narzędzie zewnętrzne (np. OWASP Dependency-Check, OSV-Scanner) | bez narzędzia zapisz „pominięto”, **nigdy „0 znalezisk”** |

## Czytanie wyników
- **Waga z CVSS:** ≥ 9,0 krytyczna · 7,0–8,9 wysoka · 4,0–6,9 średnia · < 4,0 niska. Krytyczne i wysokie pokazujesz
  od razu, resztę w raporcie.
- **Bezpośrednie osobno od przechodnich:** bezpośrednie naprawiasz od razu (aktualizacja, zamiana); przechodnie
  czekają na poprawkę opiekuna albo nadpisanie wersji (`overrides` / `resolutions`) po przeglądzie. Mieszanie ich
  na starcie projektu daje zmęczenie alertami.
- Priorytet: osiągalność i znane wykorzystanie (SKILL.md, §5 — katalog KEV), nie sama waga.
- Wynik zapisujesz z datą i wersją narzędzia; brak narzędzia lub błąd sieci = „nie sprawdzono”, nie „czysto”.
