# Szablony raportów gotowości

## Szkielet nowego projektu — `docs/project/06-delivery/bootstrap-verification.md`

```markdown
# Weryfikacja szkieletu — <data>
**TL;DR:** <status: ok / failed / ok-z-uwagami> · generator `<polecenie>` (<wersja>, świeżość: <świeży / starzejący się / nieaktualny>)

| Krok | Wynik |
|---|---|
| Decyzja o stacku | `docs/project/04-architecture/stack-decision.md` (accepted, <data>) |
| Polecenie generatora | `<pełne polecenie>` — kod wyjścia <n> |
| Przeniesione pliki | <liczba>; lista w załączniku |
| Konflikty | `CLAUDE.md.scaffold`, `package.json.scaffold` — różnice: <krótko> |
| `.gitignore` | scalony: +<n> linii |
| Audyt zależności | `<komenda>` — bezpośrednie: <k/w/ś/n>, przechodnie: <k/w/ś/n> |
| Testy szkieletu | `<komenda>` — <wynik> |
| Build | `<komenda>` — <wynik> |

## Następne kroki (decyzje człowieka)
- [ ] scalić lub odrzucić pliki `.scaffold`
- [ ] `git init` / pierwszy commit
- [ ] podatności bezpośrednie: <działanie>; przechodnie: <czekamy na opiekuna / overrides po przeglądzie>
```

Status `failed`: zamiast tabeli przeniesień — polecenie, kod wyjścia, ostatnie 20 linii wyjścia, ścieżka
`.bootstrap-scaffold/` zostawiona do inspekcji. Żadnych ręcznie dopisanych plików.

## Audyt istniejącego repo — `docs/project/07-review/<data>-gotowosc-repo.md`

```markdown
# Gotowość repo do pracy agentów — <data>, commit <sha>
**TL;DR:** projekt <zdrowe / wymaga-uwagi / krytyczne>, stack <gotowe / gotowe-z-kompensacją / duże-tarcie>; poprawka nr 1: <…>

## Fakty (readiness_check.py, detect_stack.py, polecenia uruchomione za zgodą)
| Obszar | Ustalenie | Dowód |
|---|---|---|
| lockfile | … | `package-lock.json` |
| audyt | bezpośrednie 0, przechodnie 2 wysokie | `npm audit --json` (<data>) |
| testy | runner: BRAK | `package.json` bez skryptu `test` |
| CI | lint ✓ test ✗ build ✓ typy ✗ bezpieczeństwo ✗ | `.github/workflows/ci.yml` |
| konfiguracja | `.gitignore` ✓, strict —, linter ✓, formater ✗ | … |

## Cztery bramki stacku
| Komponent | Typy | Konwencje | Popularność w rodzinie | Dokumentacja | Dowód |
|---|---|---|---|---|---|
| API (Express 5) | ✗ | ✗ | ✓ | ✓ | brak TS, trasy w 3 różnych miejscach |

### Kompensacje — reguły do CLAUDE.md (gotowe do wklejenia)
- Trasy tylko w `src/routes/<zasób>.js`, każda eksportuje `router`; rejestracja w `src/app.js`.
- Błędy: `next(err)`, jeden handler w `src/middleware/errors.js`; nie wysyłaj odpowiedzi z `catch`.

## Poprawki (kolejność wpływu na agenta)
| # | Co | Dlaczego dla agenta | Polecenie | Wysiłek |
|---|---|---|---|---|
| 1 | runner testów + test dymny | agent nie ma jak sprawdzić zmian | `<polecenie z dokumentacji runnera>` | średnio |

## Czego nie sprawdzono
<np. audyt Javy pominięto — brak wbudowanego narzędzia; testy nie były uruchamiane, tylko listowane>
```

Zasada wspólna: każda liczba i ocena ma dowód (plik lub polecenie z datą); brak dowodu = „nie sprawdzono”.
