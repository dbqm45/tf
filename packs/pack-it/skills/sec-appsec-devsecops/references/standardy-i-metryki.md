# Standardy i metryki AppSec

## ASVS
- Wersja 5.0.0 wydana 30.05.2025 (źródło wtórne: zapowiedź OWASP Global AppSec EU 2025 i tabela referencyjna; 17.10.2026).
  Pierwsze duże wydanie od ok. pięciu lat; numeracja wymagań i rozdziałów różni się od 4.0.3, więc mapowanie
  starych odwołań (np. V2 → nowy rozdział) wymaga tabeli z dokumentu OWASP [niezweryfikowane: dokładny podział rozdziałów].
- Trzy poziomy: L1 (podstawa dla każdej aplikacji), L2 (większość aplikacji z danymi wrażliwymi), L3 (krytyczne).
  Wymaganie ma identyfikator; w backlogu cytuj identyfikator, w teście podaj, który punkt dowodzi.
- Użycie: nie „zgodność z całym ASVS”, tylko wybór rozdziałów istotnych dla aplikacji i testy akceptacyjne z nich.

## SAMM
OWASP SAMM (Software Assurance Maturity Model) ocenia program organizacji w funkcjach biznesowych (m.in. zarządzanie,
projektowanie, implementacja, weryfikacja, operacje) w skali dojrzałości 1–3 [niezweryfikowane: aktualna wersja,
zakładam 2.x]. Stosuj co rok: ocena, 2–3 cele na kwartał, ponowna ocena.

## NIST SSDF (SP 800-218)
- **Wersja:** SSDF 1.1 (SP 800-218, final, 03.02.2022) to obowiązująca podstawa. SSDF 1.2 (SP 800-218 Rev. 1) to
  projekt do konsultacji z 17.12.2025 — nie powołuj się na niego jak na wersję końcową. Profil dla modeli AI:
  SP 800-218A (final, 26.07.2024).
- **Cztery grupy praktyk:** PO (przygotuj organizację: role, wymagania, narzędzia, kryteria), PS (chroń oprogramowanie:
  repozytorium, integralność wydań, archiwum), PW (wytwarzaj dobrze zabezpieczone: projekt i model zagrożeń, przegląd
  i testy, bezpieczne ustawienia domyślne, zależności), RV (reaguj na podatności: przyjmowanie zgłoszeń, analiza
  przyczyn, naprawa).
- **Użycie bez papierologii:** SSDF mówi „co”, nie „jak”. Zrób tabelę praktyka → kontrola, którą już masz (skaner,
  bramka w PR, SBOM, podpis, proces zgłoszeń) → dowód z systemu (log CI, raport, wpis w rejestrze) → luka. Dowodem
  jest artefakt generowany przez pipeline, nie dokument pisany pod audyt. Klient pytający o zgodność dostaje tę
  tabelę z odnośnikami do dowodów.
- Mapowanie na ten skill: PW ↔ warstwy kontroli i przegląd kodu; PS ↔ łańcuch dostaw artefaktu (SLSA, podpisy);
  RV ↔ triaż i SLA (`triaz-i-sla.md`); PO ↔ wymagania (ASVS) i ludzie (security champions).

## OWASP DSOMM
OWASP DevSecOps Maturity Model ocenia dojrzałość praktyk bezpieczeństwa **w pipeline'ie** (budowa, wdrożenie,
testy, kultura, informacje), poziomami od podstawowego do zaawansowanego, z konkretnymi działaniami na każdym
poziomie [niezweryfikowane: aktualna wersja — projekt nie publikuje numerowanych wydań w znalezionych źródłach].
SAMM odpowiada na pytanie „jak dojrzały jest program bezpieczeństwa organizacji”, DSOMM — „co jeszcze
zautomatyzować w pipeline'ie zespołu”. Używaj DSOMM do wyboru następnych 2–3 kroków, nie do oceny zespołu.

## Shift left i bezpieczne ustawienia domyślne
- **Shift left** = kontrola w najwcześniejszym miejscu, gdzie da się ją wykonać tanio i z dobrym sygnałem: wymaganie
  i model zagrożeń przed kodem, skaner w IDE i w PR, a nie tylko pentest przed wydaniem. Nie oznacza przerzucenia
  całej odpowiedzialności na programistów bez narzędzi i wsparcia.
- **Bezpieczne ustawienia domyślne** (secure by default): nowy serwis, szablon lub moduł startuje z włączonym
  uwierzytelnianiem, TLS, minimalnymi uprawnieniami i wyłączonym trybem debug; wyłączenie zabezpieczenia wymaga
  jawnej decyzji. Szablony i złote ścieżki: ops-platform-engineering.

## Metryki (wzory)
- **MTTR podatności** = średnia (lub mediana, odporniejsza na odstające) czasu od wykrycia do zamknięcia, osobno per ważność.
- **Po terminie** = otwarte po SLA / otwarte ogółem.
- **Pokrycie** = repozytoria z każdą warstwą / repozytoria aktywne (osobno SAST, SCA, sekrety).
- **Precyzja** = prawdziwe / zbadane w próbce; mierz per reguła.
- **Ucieczki** = podatności znalezione po wdrożeniu (pentest, zgłoszenie, incydent), z przypisaniem, która warstwa
  powinna je była złapać.
