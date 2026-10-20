# Gotowe do produkcji — definicja i przegląd gotowości

Przegląd przeprowadza w fazie 7 DevOps/SRE z security-reviewerem i projektantem testów (pack-it: Piotr i Kasia;
pack-ev: Nadia i Kamil). Wynik zapisuje w `docs/project/07-review/<data>-gotowosc.md` (artefakt `review`)
i przedstawia człowiekowi na bramce B4. Każdy punkt ma
jeden z trzech stanów: **spełniony** (z dowodem: link do testu, raportu, pliku, wyniku polecenia), **niespełniony**
albo **ryzyko zaakceptowane** (kto zaakceptował i do kiedy naprawić). Punkty oznaczone *(minimum)* obowiązują także
w ścieżce skróconej.

Dowód to wynik sprawdzenia, nie deklaracja. „Testy przechodzą” bez linku do przebiegu CI jest założeniem, nie dowodem.

W nawiasach przy punktach: obszar wiedzy i przykładowy skill z nakładki (oznaczonej). Gdy tej nakładki nie ma,
odpowiednik znajdziesz w `.claude/catalog.md` albo zapytasz konsultanta innej nakładki.

## 1. Funkcje i jakość
- [ ] *(minimum)* Wszystkie wymagania z priorytetem „musi” zrealizowane. Kryteria akceptacji pokryte testami, z mapą
  wymaganie → test (projekt testów; pack-it: qa-test-design).
- [ ] *(minimum)* Testy jednostkowe, integracyjne i end-to-end krytycznych ścieżek przechodzą w CI na gałęzi wydania.
- [ ] Testy regresji i eksploracyjne sesje dla obszarów ryzyka (pack-it: qa-regression, qa-exploratory-manual);
  znane defekty sklasyfikowane, żaden krytyczny otwarty.
- [ ] Dostępność kluczowych ścieżek sprawdzona (pack-it: fe-web-platform; pack-ux: ux-accessibility) i decyzje UX
  potwierdzone testem użyteczności albo jawnie odłożone (pack-ux: ux-feature-design).

## 2. Bezpieczeństwo
- [ ] *(minimum)* Przegląd bezpieczeństwa (security-reviewer) bez otwartych ustaleń wysokich i krytycznych; model
  zagrożeń aktualny (pack-it: arch-threat-modeling).
- [ ] *(minimum)* Sekrety tylko w menedżerze sekretów lub zmiennych środowiska, nic w repozytorium ani obrazach
  (pack-it: ops-secrets-identities); skan sekretów w CI.
- [ ] Uwierzytelnianie i autoryzacja przetestowane, także dostęp do cudzych zasobów (OWASP API1; pack-it: be-auth-security).
- [ ] Skan zależności i obrazów, SBOM, podpisane artefakty, przypięte wersje (pack-it: ops-supply-chain-security).
- [ ] Nagłówki bezpieczeństwa, TLS, limity żądań i rozmiaru, walidacja wejścia (pack-it: be-api-design;
  be-auth-security, `checklista-bezpieczenstwa-api.md` w pack-it).

## 3. Wydajność i pojemność
- [ ] Cele z wymagań jakości (np. p95, przepustowość) potwierdzone testem obciążeniowym na środowisku zbliżonym do
  produkcji (pack-it: qa-performance-testing), z raportem.
- [ ] Szacunek pojemności na start i na wzrost; limity autoskalowania i pule połączeń dobrane (pack-it: arch-system-design).

## 4. Obserwowalność i dyżury
- [ ] *(minimum)* Logi strukturalne bez danych wrażliwych, metryki RED/USE, kontrole zdrowia (pack-it: ops-observability).
- [ ] *(minimum)* SLO dla krytycznych ścieżek i alerty na budżet błędów; alert prowadzi do runbooka (pack-it: ops-sre-incidents).
- [ ] Ślady rozproszone dla ścieżek przez kilka usług; dashboard wydania (wersja, błędy, opóźnienie).
- [ ] Wiadomo, kto odbiera alerty i jak eskaluje (człowiek, nie agent).

## 5. Wydanie i wycofanie
- [ ] *(minimum)* Wdrożenie powtarzalne z pipeline'u, artefakt zbudowany raz i promowany między środowiskami
  (pack-it: ops-ci-cd, eng-continuous-delivery).
- [ ] *(minimum)* Wycofanie opisane i **przećwiczone** na środowisku testowym, z czasem trwania (pack-it: ops-release-engineering).
- [ ] Strategia stopniowa (canary, blue-green, flagi) z bramkami opartymi na SLO; migracje bazy zgodne wstecz
  (rozszerz → przenieś → zawęź; pack-it: be-database).
- [ ] Infrastruktura jako kod, bez ręcznych zmian; wykrywanie dryfu (pack-it: ops-iac-terraform).

## 6. Dane
- [ ] *(minimum)* Kopie zapasowe automatyczne i **przywracanie przetestowane**, z RPO i RTO zgodnymi z wymaganiami
  (pack-it: ops-sre-incidents).
- [ ] Retencja i usuwanie danych osobowych zgodne z decyzją człowieka (RODO); dane testowe bez danych produkcyjnych.

## 7. Dokumentacja i przekazanie
- [ ] *(minimum)* README z uruchomieniem lokalnym, konfiguracją i zmiennymi środowiska (pack-docs: docs-tech-writing).
- [ ] *(minimum)* Runbook: wdrożenie, wycofanie, typowe awarie, kontakty.
- [ ] Dokument architektury i ADR aktualne względem kodu; dziennik projektu z raportem (`project_record.py report`).
- [ ] Teksty dla użytkowników i dokumentacja po korekcie językowej (pack-editorial-pl: txt-polish-correctness).

## 8. Koszt i zgodność
- [ ] Szacunek kosztu miesięcznego, budżety i alerty kosztowe, tagi zasobów (pack-it: ops-finops).
- [ ] Wymagania prawne i umowne potwierdzone przez człowieka (RODO, regulacje branżowe, AI Act, licencje zależności).
  Agent zbiera fakty i listę pytań, decyzję podejmuje człowiek (pack-it: ops-security-operations, `zgodnosc.md`).

## Werdykt
Na końcu artefaktu: **gotowe / gotowe z zaakceptowanymi ryzykami / niegotowe**, lista punktów niespełnionych
z właścicielem i terminem oraz rekomendacja strategii wydania. Decyzję „wydajemy” podejmuje człowiek na B4.

## Źródła
- Google SRE Book i SRE Workbook — Production Readiness Review, launch checklist
- Listy z pack-it: checklista wydajności backendu i frontendu, checklista bezpieczeństwa API, ops-release-engineering
Opisane własnymi słowami.
