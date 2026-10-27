---
name: sec-appsec-devsecops
description: Użyj przy programie bezpieczeństwa aplikacji w pipeline — ASVS, SAMM, SAST, DAST, SCA, triaż i SLA podatności, SLSA, podpisy, metryki.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy budujesz lub oceniasz program bezpieczeństwa aplikacji w cyklu dostarczania (AppSec, DevSecOps) — wymagania wg OWASP ASVS 5.0 i dojrzałość wg OWASP SAMM i DSOMM, mapowanie na NIST SSDF (SP 800-218), shift left i bezpieczne ustawienia domyślne, przegląd kodu pod kątem bezpieczeństwa (niebezpieczne API i domyślne konfiguracje per język), warstwy skanerów w CI/CD (sekrety, SAST, SCA i SBOM, DAST, IAST, IaC i kontenery) i miejsce każdej, strojenie fałszywych alarmów, triaż i terminy napraw wg CVSS v4, EPSS i CISA KEV, polityka blokowania buildu, integralność łańcucha (SLSA, provenance, Sigstore/cosign), security champions, metryki (MTTR, pokrycie). Nie do mechaniki pipeline'u (ops-ci-cd), lockfile i karencji zależności (ops-supply-chain-security), modelu zagrożeń (arch-threat-modeling), kodu auth (be-auth-security), łatek i incydentów w operacjach (ops-security-operations) ani sekretów (ops-secrets-identities) ani szukania wariantów znalezionej podatności (sec-variant-analysis)."
  slowa: "SSDF, NIST SP 800-218, DSOMM, DevSecOps Maturity Model, shift left, secure by default, bezpieczne ustawienia domyślne, zgodność z SSDF, devsecops, appsec, bezpieczeństwo aplikacji, ASVS, SAMM, SAST, DAST, IAST, SCA, semgrep, codeql, zap, trivy, grype, syft, dependency-track, SBOM cyclonedx spdx, skaner w CI, fałszywe alarmy, false positives, blokować build, SLA podatności, CVSS, EPSS, KEV, MTTR podatności, SLSA, cosign, sigstore, provenance, security champions, podpisywanie obrazów, podpis obrazu kontenera, nikt go nie podmienił, zbudowano w naszym CI, integralność artefaktu, przegląd kodu security, pentest, wymagania bezpieczeństwa, niebezpieczne funkcje, niebezpieczne API, domyślne ustawienia, domyślne hasła, tryb debug na produkcji, wyłączona weryfikacja certyfikatu, pickle, yaml.load, BinaryFormatter, InsecureSkipVerify, przegląd bezpieczeństwa przed wydaniem"
---

# AppSec w pipeline (DevSecOps)

Cel: znaleźć podatność tam, gdzie jest najtańsza do naprawy (shift left), zacząć od bezpiecznych ustawień
domyślnych i nie zalać zespołu szumem. Program składa się z czterech
rzeczy: **wymagania** (co ma być bezpieczne), **kontrole w pipeline** (co sprawdza maszyna), **przegląd ludzki**
(co wymaga rozumu) i **pomiar** (czy działa). Granice: mechanika jobów i uprawnienia runnera to `ops-ci-cd`,
lockfile i karencja to `ops-supply-chain-security`, STRIDE to `arch-threat-modeling`, łatanie na produkcji
to `ops-security-operations`.

## Procedura
1. **Stan wyjściowy.** Co już skanuje (repo, CI, chmura), kto reaguje na wyniki, ile jest otwartych znalezisk i jak
   stare. Bez tego nie ma punktu odniesienia dla metryk.
2. **Wymagania.** Wybierz poziom ASVS dla aplikacji (L1 każda, L2 domyślnie dla danych wrażliwych, L3 krytyczne)
   i zapisz wybrane rozdziały jako kryteria akceptacji. Dojrzałość całego programu (nie jednej aplikacji) ocenia SAMM,
   dojrzałość pipeline'u DSOMM; wymóg zgodności z NIST SSDF to tabela praktyka → kontrola → dowód z pipeline'u.
   Szczegóły i wersje: `references/standardy-i-metryki.md`.
3. **Warstwy kontroli** (tabela niżej): dla każdej wskaż etap, narzędzie, tryb (blokuje / ostrzega) i właściciela.
   Zaczynaj od tych o najlepszym stosunku sygnału do szumu: sekrety, SCA, SAST z małym zestawem reguł.
4. **Strojenie przed blokowaniem.** Nowe narzędzie działa 2–4 tygodnie w trybie ostrzegania; mierz odsetek
   znalezisk uznanych za prawdziwe, wyłącz reguły o niskiej precyzji, dodaj reguły własne dla wzorców firmy.
   Wyjątki (suppress) mają powód, właściciela i datę wygaśnięcia, nie wpis „ignore” w kodzie bez śladu.
5. **Triaż i terminy.** Reguły priorytetu i przykładowa tabela SLA: `references/triaz-i-sla.md`. Skrót: ważność bazowa
   (CVSS), do tego znane wykorzystanie (CISA KEV), prawdopodobieństwo (EPSS), osiągalność w kodzie i ekspozycja usługi.
6. **Polityka blokowania.** Blokuj tylko to, co ma wysoką precyzję i jasną naprawę: ujawniony sekret, znana
   wykorzystywana podatność w osiągalnej zależności, krytyczne ustalenie SAST nowe w diffie. Resztę zgłaszaj jako
   zadanie z terminem. Skanuj **diff** w PR (nowy dług), a całość nocą (stary dług). Wyłączenie bramki to decyzja
   człowieka z wpisem w rejestrze wyjątków.
7. **Integralność artefaktu.** Każdy wydany artefakt ma SBOM, provenance i podpis; wdrożenie weryfikuje podpis
   i tożsamość budującego (sekcja niżej).
8. **Ludzie.** Security champion w zespole (ok. 1 na zespół, część etatu, wspierany szkoleniem i kanałem do AppSec),
   przegląd bezpieczeństwa dla zmian w auth, kryptografii, parsowaniu wejścia, uploadach i nowych integracjach.
9. **Pomiar** co miesiąc: MTTR wg ważności, odsetek znalezisk po terminie, pokrycie (repozytoria ze skanerem / wszystkie),
   odsetek fałszywych alarmów, liczba podatności wykrytych po wdrożeniu (ucieczki). Metryki służą do poprawy
   procesu, nie do rankingu zespołów.

## Warstwy kontroli
| Warstwa | Przykłady | Gdzie | Domyślny tryb |
|---|---|---|---|
| Sekrety | gitleaks, trufflehog, push protection | pre-commit + CI + historia | blokuje |
| SAST | Semgrep, CodeQL | PR (diff) + nocą (całość) | blokuje krytyczne nowe, resztą ostrzega |
| SCA + SBOM | Grype, osv-scanner, Syft, CycloneDX/SPDX, Dependency-Track | PR + build + ciągle po wydaniu | blokuje znane wykorzystywane |
| IaC | Checkov, KICS, tfsec/Trivy | PR | ostrzega, blokuje publiczne magazyny i otwarte porty |
| Kontener | Trivy, Grype na obrazie | build + rejestr | blokuje krytyczne z poprawką |
| DAST | OWASP ZAP | staging, nocą, po wdrożeniu | ostrzega (zakres uzgodniony) |
| IAST | agent w testach | testy integracyjne | ostrzega |
Testy ofensywne tylko na własnych środowiskach i za zgodą. Skanery to też kod z zewnątrz: przypinasz je
i izolujesz od sekretów (`ops-ci-cd`, `ops-supply-chain-security`).

## Przegląd kodu pod kątem bezpieczeństwa
Skanery nie widzą logiki. Człowiek (lub agent, wynik zatwierdza człowiek) sprawdza: kontrolę dostępu na każdym
zasobie (IDOR), walidację na granicy, budowanie zapytań i poleceń z wejścia, deserializację, SSRF przy pobieraniu URL,
obsługę błędów bez wycieku, logi bez danych wrażliwych. Lista pytań wg ASVS, nie wg intuicji.
Niebezpieczne API per język (Python, JS/Node, Java, C#, Go) i domyślne konfiguracje (konta, debug, TLS, CORS,
usługi bez uwierzytelnienia, fail-open): `references/niebezpieczne-api.md`. Po znalezieniu podatności — jej
warianty w reszcie kodu i reguła w CI: sec-variant-analysis.

## Łańcuch dostaw artefaktu
- **SLSA** (build track, v1.0): L1 provenance istnieje, L2 provenance podpisuje hostowana platforma buildu, L3 platforma
  jest utwardzona (izolowane, efemeryczne buildy, klucz niedostępny dla kroków). Celuj w L2, w L3 dla wydań krytycznych.
- **Podpis** bez długotrwałego klucza: Sigstore/cosign w trybie keyless (tożsamość OIDC z CI, certyfikat krótkożyjący,
  wpis w dzienniku przejrzystości). Weryfikacja przy wdrożeniu sprawdza **tożsamość i wystawcę**, nie samo istnienie podpisu.
- Provenance mówi, jak zbudowano; SBOM, z czego; podpis, kto. Żadne nie dowodzi braku podatności.

## Przykład
**Sytuacja:** „Mamy Semgrep w CI, 900 znalezisk, nikt ich nie czyta. Co robimy?”
**Wynik** [przykład]: (1) tydzień 1: Semgrep tylko na diffie PR, zestaw reguł ograniczony do kategorii security
z wysoką pewnością, reszta nocą bez blokady; (2) próbka 50 znalezisk → 14 prawdziwych (28%), wyłączone 3 reguły
odpowiadające za 60% fałszywych; (3) blokada tylko dla nowych znalezisk „high” z pewnością „high”; (4) stare dostają
zadania z terminem wg tabeli SLA, 20 najważniejszych na sprint; (5) mierzymy MTTR i odsetek fałszywych co miesiąc.

## Checklista
- [ ] poziom ASVS wybrany i zapisany jako kryteria, dojrzałość programu oceniona (SAMM)
- [ ] każda warstwa ma etap, tryb, właściciela; nowe narzędzia najpierw w trybie ostrzegania
- [ ] priorytet z CVSS + KEV + EPSS + osiągalność; terminy per ważność; wyjątki z datą wygaśnięcia
- [ ] blokada tylko dla ustaleń o wysokiej precyzji; skan diffu w PR
- [ ] SBOM, provenance i podpis; weryfikacja przy wdrożeniu
- [ ] security champions i metryki (MTTR, pokrycie, fałszywe alarmy)

## Źródła
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) — wersja 5.0.0, 30.05.2025 (wyszukiwanie 17.10.2026)
- [OWASP SAMM](https://owaspsamm.org/), [SLSA v1.0](https://slsa.dev/spec/v1.0/levels), [Sigstore](https://docs.sigstore.dev/signing/overview/) (17.10.2026)
- NIST SP 800-218 SSDF 1.1 (final, 02.2022; 1.2 — projekt 12.2025); [OWASP DSOMM](https://dsomm.owasp.org/)
  (wersja [niezweryfikowane]); statusy wg wyszukiwania 2026-10-27
- FIRST: CVSS v4.0 (listopad 2023), EPSS; [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
Opisane własnymi słowami. Szczegóły i znaczniki niezweryfikowanych faktów: pliki w `references/`.
