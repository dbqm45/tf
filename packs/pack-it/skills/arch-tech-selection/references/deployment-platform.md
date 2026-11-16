# Platforma wdrożeniowa dla MVP

Wybór hostingu to część decyzji o stacku (`stack-decision.md`, sekcja platformy). Fakty o platformach (funkcje,
statusy, limity, ceny) zmieniają się w tygodniach — zawsze ze źródła pierwotnego z datą sprawdzenia
(core-source-research), nigdy z pamięci.

## 1. Filtry twarde (odrzucają bez punktacji)
- runtime stacku nieobsługiwany (wersja języka, adapter frameworka);
- wymagane trwałe połączenia (WebSocket), procesy w tle lub długie zadania → odpadają platformy wyłącznie serverless;
- wymogi zgodności (region danych, np. UE) nie do spełnienia.

## 2. Pięć kryteriów (Pass / Partial / Fail)
| Kryterium | Waga | Pytanie |
|---|---|---|
| CLI do pełnej obsługi | wysoka | wdrożenie, wycofanie i logi bez panelu WWW? |
| usługa zarządzana zamiast surowych maszyn | wysoka | kto łata system, skaluje, robi kopie? |
| deterministyczne, skryptowalne wdrożenie | wysoka | jedno polecenie z kodem wyjścia, które agent i CI mogą sprawdzić? |
| dokumentacja czytelna dla agenta | średnia | markdown, `llms.txt`, aktualne przykłady dla wersji projektu? |
| serwer MCP lub inna integracja z agentem | niska | rozstrzyga remisy |
Przy każdej funkcji status: GA / beta / preview / ograniczona regionalnie + data sprawdzenia. Funkcja w becie nie
jest argumentem za wyborem do produkcji.

## 3. Wywiad (tak / nie / nie wiem)
Trwałe połączenia? Koszt czy wygoda? Platforma znana zespołowi? Zasięg globalny? Baza i storage od jednego
dostawcy? Odpowiedzi zmieniają wagi kryteriów, nie wykluczają (wyjątek: trwałe połączenia → filtr twardy).

## 4. Kandydaci i historia operacyjna
Trzech kandydatów, na liderze test odporności decyzji (arch-architect-practice). Potem „historia operacyjna” —
jedna konkretna odpowiedź na oś:
| Oś | Konkretna odpowiedź |
|---|---|
| podgląd per PR (i jego ochrona przed publicznym dostępem) | |
| sekrety: gdzie, kto czyta, jak rotować | |
| wycofanie: polecenie, czas, zastrzeżenia dla migracji bazy | |
| co wymaga człowieka (konta, domeny, płatności, sekrety produkcyjne) | |
| logi dla agenta tylko do odczytu (CLI lub MCP) | |

## 5. Pierwsze kroki i sygnał zmiany decyzji
- „Pierwsze kroki” (polecenia CLI, adapter frameworka) sprawdzasz wobec **wersji z projektu** — adaptery i CLI
  platform zmieniają się między wersjami głównymi; ogólny poradnik bywa nieaktualny.
- Pierwsze wdrożenie planujesz wg ops-release-engineering („Pierwsze wdrożenie”).
- Zapisz sygnał zmiany decyzji: co ją unieważni po wyjściu z MVP (zadania cykliczne, długie zadania, dedykowana
  baza, ruch globalny, koszt przy N użytkowników).

## Przykład
SvelteKit + PostgreSQL, zespół 2 osoby, MVP w UE. Filtr: potrzebne WebSockety do powiadomień → platforma tylko
serverless odpada. Kandydaci A (PaaS z kontenerami, CLI pełne, Pass×4), B (serverless + zewnętrzny serwis
WebSocket, Partial), C (VM z panelem, Fail na usłudze zarządzanej). Test odporności na A: pre-mortem ujawnia brak
kopii bazy w planie podstawowym → zapisane jako znane ograniczenie + zadanie „kopia nocna do storage”. Historia
operacyjna A: podgląd per PR z hasłem, sekrety w magazynie platformy (czyta tylko runtime), wycofanie poleceniem
do poprzedniego wydania (~1 min, migracje expand–contract), człowiek zakłada konto i domenę, logi agent czyta przez
CLI tylko do odczytu.
