# RLS w PostgreSQL dla puli najemców — szczegóły i pułapki

Fakty sprawdzone przez agenta `researcher` 2026-10-18. Strony źródłowe nie zostały otwarte z sesji w chmurze
(proxy 403), więc werdykty opierają się na streszczeniach wyszukiwarki z oficjalnych domen — oznaczenie [wtórne].
Przed decyzją produkcyjną sprawdź w dokumentacji swojej wersji PostgreSQL.

## Fakty
| Fakt | Źródło | Status |
|---|---|---|
| Właściciel tabeli domyślnie omija polityki RLS, chyba że tabela ma `FORCE ROW LEVEL SECURITY`; superużytkownik i rola z `BYPASSRLS` omijają je zawsze. | postgresql.org/docs/current/ddl-rowsecurity.html (potwierdzone przez kopie dokumentacji wersji 12 i 15) | [wtórne] |
| Włączony RLS bez żadnej polityki = domyślna odmowa: brak widocznych i modyfikowalnych wierszy. | j.w. | [wtórne] |
| `SET LOCAL` działa do końca bieżącej transakcji (commit lub rollback); `set_config(nazwa, wartość, true)` — tak samo. | postgresql.org/docs/current/sql-set.html; …/functions-admin.html | [wtórne] |
| PgBouncer w trybie `transaction`: `SET`/`RESET` oznaczone jako niewspierane („Never”) — kolejna transakcja może trafić na inne połączenie; wyjątek to parametry śledzone (np. `TimeZone`, `application_name`). | pgbouncer.org/features.html; pgbouncer.org/config.html | [wtórne] |
| Modele silo, pool, bridge; „noisy neighbor” — obciążenie jednego najemcy pogarsza działanie innych. | docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html | [wtórne] |
| Najnowsza wydana wersja główna: PostgreSQL 18 (premiera 25.09.2025); PG 19 w RC1 od 15.10.2026; wsparcie PG 14 kończy się 12.11.2026. | postgresql.org/support/versioning/ | [wtórne] |

## Wzorzec (szkic)
```sql
ALTER TABLE invoice ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice FORCE ROW LEVEL SECURITY;   -- także gdy aplikacja jest właścicielem (lepiej: nie jest)
CREATE POLICY tenant_isolation ON invoice
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```
W transakcji aplikacji: `SELECT set_config('app.tenant_id', $1, true);` przed pierwszym zapytaniem.
`current_setting(…, true)` zwraca NULL przy braku ustawienia, więc porównanie nie przepuszcza żadnego wiersza.

## Pułapki
- Rola aplikacji jest właścicielem tabel (migracje tą samą rolą) → RLS nie działa bez `FORCE`. Osobna rola migracji.
- `SET` (bez `LOCAL`) w puli połączeń → najemca „przecieka” do następnej transakcji innego klienta.
- Widoki: domyślnie wykonują się z uprawnieniami właściciela widoku; od PostgreSQL 15 opcja `security_invoker`
  [wtórne, 2026-10-20: man page CREATE VIEW z pakietu postgresql15, blog Supabase — dokumentacja postgresql.org
  niedostępna z sesji].
- Funkcje `SECURITY DEFINER` omijają RLS, jeśli ich właściciel go omija — przegląd każdej takiej funkcji.
- Indeksy złożone z `tenant_id` na początku; bez nich polityka zamienia zapytania w skan (be-database).

## Test katalogu (szkic)
```sql
SELECT c.relname
FROM pg_class c JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id'
WHERE c.relkind = 'r' AND NOT c.relrowsecurity;   -- ma tenant_id, a RLS wyłączony → test czerwony
```
