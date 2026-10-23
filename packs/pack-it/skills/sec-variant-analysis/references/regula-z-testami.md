# Reguła z testami — szablon (Semgrep)

Reguła bez testów psuje się po cichu: przestaje łapać błąd albo zaczyna łapać wszystko. Test to plik z kodem
podatnym i poprawnym, oznaczonym komentarzami.

## Reguła (tryb taint, Python)
```yaml
rules:
  - id: sql-sort-from-request
    languages: [python]
    severity: ERROR
    message: Pole sortowania z żądania trafia do SQL — użyj listy dozwolonych pól (sort_clause)
    mode: taint
    pattern-sources:
      - pattern: request.GET.get(...)
      - pattern: request.args.get(...)
    pattern-sanitizers:
      - pattern: sort_clause(...)
    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: $CUR.execute($Q, ...)
              - pattern: $MODEL.objects.raw($Q, ...)
          - focus-metavariable: $Q
```

## Test (plik o tej samej nazwie co reguła, np. `sql-sort-from-request.py`)
```python
def bad(request, cur):
    sort = request.GET.get("sort")
    # ruleid: sql-sort-from-request
    cur.execute("SELECT * FROM reports ORDER BY " + sort)

def good(request, cur):
    sort = sort_clause(request.GET.get("sort"), "asc")
    # ok: sql-sort-from-request
    cur.execute("SELECT * FROM reports ORDER BY " + sort)
```
Uruchomienie: `semgrep --test <katalog z regułami i testami>`. Test z prawdziwego przypadku (miejsce sprzed
naprawy) to najlepszy przykład podatny.

## W CI
- Reguły w repozytorium (np. `.semgrep/`), testy reguł w CI razem z resztą testów.
- Skan diffu w PR blokuje nowe trafienia tej reguły; całe repozytorium nocą (sec-appsec-devsecops, kroki 4 i 6).
- Wyjątek tylko z powodem i datą wygaśnięcia, nie komentarzem wyłączającym bez śladu.
- CodeQL: to samo w postaci zapytania przepływu danych z testem (katalog testów z kodem i oczekiwanym wynikiem).
