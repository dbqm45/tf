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

## Metryki (wzory)
- **MTTR podatności** = średnia (lub mediana, odporniejsza na odstające) czasu od wykrycia do zamknięcia, osobno per ważność.
- **Po terminie** = otwarte po SLA / otwarte ogółem.
- **Pokrycie** = repozytoria z każdą warstwą / repozytoria aktywne (osobno SAST, SCA, sekrety).
- **Precyzja** = prawdziwe / zbadane w próbce; mierz per reguła.
- **Ucieczki** = podatności znalezione po wdrożeniu (pentest, zgłoszenie, incydent), z przypisaniem, która warstwa
  powinna je była złapać.
