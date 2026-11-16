# Triaż i SLA podatności

## Sygnały
- **CVSS v4.0** (FIRST, listopad 2023): ważność techniczna; nie jest zgodny wstecznie z v3.1, więc nie porównuj
  wyników z różnych wersji. Nazwy grup metryk (Base, Threat, Environmental, Supplemental) [niezweryfikowane
  w tej sesji, z pamięci]. CVSS-B (sama baza) przecenia ryzyko; dodaj wiedzę o zagrożeniu i środowisku.
- **EPSS** (FIRST): prawdopodobieństwo wykorzystania w ciągu 30 dni, odświeżane codziennie. Estymata statystyczna,
  nie dowód.
- **CISA KEV**: katalog podatności potwierdzonych jako wykorzystywane; to najsilniejszy sygnał do pilności.
- **Osiągalność**: czy podatny kod jest wywoływany, czy usługa jest wystawiona, czy działa kontrola kompensująca (VEX/
  „not affected” z uzasadnieniem).

## Reguła priorytetu
1. W KEV lub z działającym exploitem i usługa dostępna z internetu → P0.
2. Wysoki EPSS (np. > 0,1 [przykład progu]) albo CVSS ≥ 9 i osiągalne → P1.
3. CVSS 7–8,9 osiągalne lub krytyczne nieosiągalne → P2.
4. Reszta → P3 w cyklu, nieosiągalne mogą być zamknięte z VEX.

## Tabela SLA [przykład, ustal z właścicielem ryzyka]
| Priorytet | Termin naprawy lub kontroli kompensującej |
|---|---|
| P0 | 48 godzin (ograniczenie), pełna naprawa 7 dni |
| P1 | 14 dni |
| P2 | 30–60 dni |
| P3 | 90 dni lub cykl wydawniczy |
Przekroczenie terminu = eskalacja do właściciela produktu; wyjątek wymaga zgody człowieka, uzasadnienia, kontroli
kompensującej i daty wygaśnięcia. Wykonanie łatki w produkcji: `ops-security-operations`.

## Znalezisko w zgłoszeniu (pola)
ID, źródło (narzędzie, reguła), komponent i wersja, ważność bazowa, KEV (tak/nie), EPSS, osiągalność z dowodem,
właściciel, termin, status (nowe / potwierdzone / fałszywe / wyjątek / naprawione), data zamknięcia.
Fałszywe alarmy oznacz w narzędziu z powodem, by nie wracały.
