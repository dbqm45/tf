# Kontrakt OCPI, regresja na logach, narzędzia

## Testy kontraktowe OCPI
OCPI to protokół między stronami (CPO ↔ eMSP/hub), nie ze sprzętem (`.claude/skills/dom-ev-charging/references/ocpi.md`).
Testuj go bez prawdziwego partnera:
| Test | Jak |
|---|---|
| Zgodność ze specyfikacją | porównaj odpowiedzi swojego API z opisem modułu w repozytorium `github.com/ocpi/ocpi` dla używanej wersji (2.2.1 lub 2.3) |
| Kontrakt z partnerem | uzgodnij przykładowe żądania i odpowiedzi, uruchom je jako testy po obu stronach; zmiana pola łamie test |
| Atrapa partnera | prosty serwer HTTP zwracający uzgodnione odpowiedzi; sprawdza, jak reagujesz na błędy, puste listy i pola opcjonalne |
| Sandbox partnera | jeśli hub lub partner go udostępnia — dostępność i zakres **[do weryfikacji]** |
| Zdarzenia z OCPP do OCPI | sesja z symulatora → oczekiwany Session i CDR po stronie OCPI |

Sprawdzaj: wersje i endpointy z wymiany credentials, pola wymagane i opcjonalne, formaty identyfikatorów
(dom-ev-identifiers), niezmienność CDR i korekty przez kredyt (dom-ev-charging). Nie kopiuj tekstu specyfikacji do testów — odwołaj się do wersji.

## Regresja na nagranych logach
1. Brama zapisuje ramki w formacie JSON Lines `{ts, cp, dir, frame}` (dom-ev-diagnostics, `.claude/skills/dom-ev-diagnostics/references/log-i-skrypt.md`).
2. **Anonimizuj** przed użyciem poza produkcją: `idTag`, identyfikatory kierowców i kont, tokeny, ewentualnie ID
   stacji. Zastąp stałym mapowaniem (ten sam token → ten sam pseudonim), żeby powiązania w logu zostały.
   Anonimizacja jest wymogiem RODO przy kopiowaniu logu do testów.
3. **Odtwórz** tylko ramki `cp>csms` na symulatorze lub własnym kliencie, zachowując kolejność i odstępy czasu
   (możesz je skrócić). Ramki `csms>cp` to oczekiwane odpowiedzi do porównania.
4. **Porównaj**: stan domeny, odpowiedzi CSMS i ustalenia analizatora z wersją sprzed zmiany.
5. Błąd z produkcji zamień na stały test: zanonimizowany fragment logu + oczekiwany wynik.

Ograniczenia: odtworzenie nie odtworzy stanu zewnętrznego (np. stanu bazy w chwili nagrania) ani zegara; ustaw
oba w teście.

## Narzędzia open source (przykłady, nie rekomendacja)
- EVerest — projekt stosu oprogramowania ładowarki, bywa używany do symulacji stacji **[do weryfikacji]** stan projektu i zakres.
- SteVe — otwarty CSMS dla OCPP, używany jako system odniesienia lub cel testów **[do weryfikacji]** stan projektu i obsługiwane wersje.
- Źródła tych nazw w katalogu fabryki nie ma; sprawdź aktualny stan, licencję i wersje OCPP w repozytoriach projektów przed użyciem.
Wybór narzędzia zależy od wersji OCPP, potrzebnych scenariuszy awarii i skali; własny symulator (`charge_sim.py`) pokrywa 1.6J bez TLS.
