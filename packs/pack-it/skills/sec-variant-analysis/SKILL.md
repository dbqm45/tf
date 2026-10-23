---
name: sec-variant-analysis
description: Użyj po znalezieniu podatności, by znaleźć jej warianty w kodzie — przyczyna, wzorzec źródło→ujście, grep/Semgrep/CodeQL, triaż trafień, reguła w CI.
metadata:
  przeglad: 2027-10-23
  katalog: "Użyj, gdy znaleziono jedną podatność (pentest, zgłoszenie, incydent, przegląd) i trzeba sprawdzić, czy ten sam błąd nie występuje gdzie indziej — w tym repozytorium albo w wielu repozytoriach firmy: przyczyna i klasa (CWE), uogólnienie do wzorca źródło → ujście na kilku poziomach, wyszukiwanie od najtańszego (grep, Semgrep, CodeQL, w tym wiele repozytoriów naraz), triaż każdego trafienia z osiągalnością i ekspozycją, naprawa u źródła wspólnym bezpiecznym API, reguła z testami w CI blokująca nowe wystąpienia, raport z liczbami. Nie do programu skanerów i terminów napraw (sec-appsec-devsecops), modelu zagrożeń (arch-threat-modeling), obsługi incydentu (ops-security-operations) ani analizy podejrzanego pliku (sec-malware-analysis)."
  slowa: "analiza wariantów, variant analysis, gdzie jeszcze jest ten błąd, ten sam błąd w innych miejscach, podobne podatności, znaleźliśmy podatność, pentester znalazł, po incydencie sprawdzić resztę kodu, wszystkie repozytoria, reguła semgrep na ten błąd, zapytanie codeql, źródło i ujście, taint, przepływ danych, sql injection w innych miejscach, deserializacja w innych usługach"
---

# Analiza wariantów podatności

Cel: jedna znaleziona podatność zamienia się w znalezione **wszystkie** jej wystąpienia i w regułę, która nie
wpuści następnych. Naprawa tylko zgłoszonego miejsca zostawia zwykle rodzeństwo błędu w kodzie. Tylko w kodzie,
który jest Twój albo do którego masz zgodę (core-agent-security).

## Procedura
1. **Zrozum znaleziony błąd**: skąd przychodzi niezaufana dana (źródło), gdzie robi szkodę (ujście), której
   kontroli brakuje (walidacja, parametryzacja, uprawnienie), jaki jest warunek wykorzystania. Nazwij klasę CWE
   (np. CWE-89 wstrzyknięcie SQL, CWE-502 deserializacja niezaufanych danych).
2. **Uogólnij do wzorca** na trzech poziomach, od wąskiego do szerokiego:
   - **ten sam kod** — to samo wywołanie, skopiowane fragmenty, ta sama funkcja pomocnicza;
   - **to samo ujście** — każde miejsce, gdzie dane z wejścia docierają do tego ujścia inną drogą;
   - **ta sama klasa** — inne ujścia tej samej kategorii (np. każde sklejanie SQL, każde `ORDER BY` z wejścia,
     każda deserializacja formatu z typami).
3. **Szukaj od najtańszego**: grep/ripgrep po nazwach ujść i funkcji → Semgrep (wzorzec składniowy, tryb taint
   ze źródłami, ujściami i sanitizerami) → CodeQL (przepływ danych między funkcjami i plikami). Zapisz każde
   zapytanie i liczbę trafień — zbyt wiele trafień to sygnał do zawężenia, zero przy szerokim wzorcu — do
   sprawdzenia, czy wzorzec w ogóle działa (uruchom go na znanym, naprawionym miejscu w historii gita).
4. **Zakres**: inne repozytoria (wspólne biblioteki, skopiowany kod, szablony projektów), stare gałęzie wydań
   wspierane przez firmę. Wiele repozytoriów: ten sam skrypt i reguły po wszystkich klonach albo analiza wielu
   repozytoriów naraz w CodeQL. Lista repozytoriów i wersji — od człowieka.
5. **Triaż każdego trafienia**: czy dane są osiągalne z niezaufanego wejścia, czy po drodze jest kontrola, jaka
   jest ekspozycja usługi (internet, sieć wewnętrzna, tylko administrator). Wynik: prawdziwe / fałszywe /
   niepewne, z `plik:linia` i uzasadnieniem. Niepewne sprawdza człowiek albo test.
6. **Naprawa u źródła**: jedno bezpieczne API lub funkcja pomocnicza (np. lista dozwolonych pól sortowania,
   bezpieczny deserializator) zamiast łatki w każdym miejscu; kolejność napraw i terminy według
   sec-appsec-devsecops (`.claude/skills/sec-appsec-devsecops/references/triaz-i-sla.md`).
7. **Zapobieganie**: reguła (Semgrep albo CodeQL) z testami — przykład podatny i poprawny — w CI na diffie PR,
   blokująca nowe wystąpienia; szablon w `references/regula-z-testami.md`. Wniosek w `docs/project/lessons.md`.
8. **Raport**: klasa i wzorzec, zapytania, liczby (trafienia / prawdziwe / fałszywe / niepewne), lista z
   `plik:linia`, naprawy i reguły, czego nie sprawdzono.

## Przykład
Pentest: wstrzyknięcie SQL w `/reports` — parametr `sort` trafiał do `ORDER BY` sklejanego ze stringa (CWE-89).
Wzorzec: dane z żądania → nazwa kolumny lub kierunek w SQL (tu parametryzacja nie działa, potrzebna lista
dozwolonych wartości). Szukanie: `rg -n "ORDER BY|order_by\(|\.extra\(|\.raw\("` → 41 trafień; reguła Semgrep
w trybie taint (źródło: parametry żądania, ujście: `cursor.execute`, `raw`, `extra`) → 12; triaż → 3 prawdziwe
(`/reports`, `/invoices/export`, `/admin/users`), 8 fałszywych (stałe), 1 niepewne (dane z kolejki). Naprawa:
funkcja `sort_clause(field, direction)` z listą dozwolonych pól, użyta w 4 miejscach. Reguła z testami w CI
blokuje nowe przypadki; te same reguły uruchomione w 2 innych repozytoriach — 1 trafienie, prawdziwe.

## Źródła
- MITRE CWE, cwe.mitre.org — klasy słabości (dostęp 2026-10-23).
- Semgrep, dokumentacja: tryb taint i testowanie reguł (`semgrep --test`), semgrep.dev/docs (dostęp 2026-10-23).
- GitHub, dokumentacja CodeQL: zapytania przepływu danych i analiza wariantów w wielu repozytoriach,
  docs.github.com/code-security/codeql-for-vs-code (dostęp 2026-10-23).
- Inspiracja tematem: Trail of Bits, skill `variant-analysis` (licencja CC BY-SA 4.0 — treści nie przejęto).
Opisane własnymi słowami.
