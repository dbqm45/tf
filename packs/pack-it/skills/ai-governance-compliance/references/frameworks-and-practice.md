# Ramy dobrowolne i praktyka zarządzania AI

## NIST AI RMF 1.0 i profil AI 600-1
- **AI RMF 1.0** (NIST AI 100-1, styczeń 2023), dobrowolny. Cztery funkcje:
  - **Govern** — polityki, role, kultura, odpowiedzialność, nadzór nad dostawcami;
  - **Map** — kontekst użycia, interesariusze, możliwe szkody, granice systemu;
  - **Measure** — metryki, testy, ocena stronniczości, monitorowanie (narzędzia: ai-evals);
  - **Manage** — priorytety ryzyka, reakcja, wycofanie, incydenty.
- **Generative AI Profile (NIST AI 600-1, lipiec 2024)** — dodaje do czterech funkcji działania dla ryzyk specyficznych
  dla generatywnej AI (źródła wtórne mówią o 12 kategoriach, m.in. konfabulacje, prywatność danych, własność
  intelektualna, szkodliwe treści, łańcuch dostaw) [niezweryfikowane u źródła, dostęp 2026-10-17].
- Użycie: macierz obowiązków AI Act wypełniasz działaniami z funkcji; nie jest to certyfikat ani dowód zgodności.

## ISO/IEC 42001:2023 a ISO/IEC 27001
- 42001 to norma na **system zarządzania AI** (AIMS), certyfikowalna przez jednostki zewnętrzne. Ma wspólną
  strukturę wysokiego poziomu ze standardami zarządzania (kontekst, przywództwo, planowanie, wsparcie, działanie,
  ocena, doskonalenie), więc łączy się z 27001 w jeden system zarządzania, z jednym przeglądem kierownictwa
  i audytem wewnętrznym [niezweryfikowane u źródła].
- 27001 chroni informacje (poufność, integralność, dostępność); 42001 dodaje ryzyka AI: wpływ na ludzi, przejrzystość,
  nadzór człowieka, cykl życia modelu, dostawców. Zakres się uzupełnia, nie zastępuje.
- Certyfikat 42001 nie daje domniemania zgodności z AI Act, chyba że Komisja wskaże normę zharmonizowaną
  [niezweryfikowane — sprawdź stan norm zharmonizowanych w Dz.Urz. UE].

## Ocena wpływu (AI impact / FRIA)
Opis systemu i celu; kogo dotyczy (grupy wrażliwe); prawa podstawowe, które mogą ucierpieć (niedyskryminacja, prywatność,
rzetelny proces); częstość i czas użycia; środki nadzoru i odwołania; plan reakcji. FRIA wymaga art. 27 tylko w wymienionych
przypadkach, ale to samo narzędzie służy dobrowolnie przy każdym wysokim ryzyku. DPIA — arch-privacy-compliance.

## Karty modelu i zbiorów danych
- **Karta modelu:** cel i granice użycia, wersja, dane treningowe (źródło, okres, licencje), metryki z podziałem na
  podgrupy, znane ograniczenia i błędy, ryzyka, kontakt, data przeglądu.
- **Karta zbioru (datasheet):** po co powstał, skład, sposób zbierania, adnotacje, wstępne przetwarzanie, zgody
  i podstawy prawne, uprzedzenia, utrzymanie.

## Stronniczość i uczciwość — podstawy
1. Nazwij grupy chronione i szkodę (odmowa usługi, gorsza jakość, stereotypy).
2. Wybierz metrykę zgodną z celem: parytet demograficzny, równość szans, kalibracja w grupach. Metryki bywają
   wzajemnie sprzeczne — wybór i uzasadnienie zapisuje człowiek odpowiedzialny za produkt.
3. Mierz na podgrupach i przekrojach (ai-evals); duże różnice w błędach to ustalenie.
4. Środki: dane, progi, przegląd człowieka, odwołanie. Powtarzaj po zmianie modelu lub danych.
5. Do uczciwości używaj danych wrażliwych tylko za podstawą prawną — sprawdź w arch-privacy-compliance.

## Proces incydentu AI
Wykrycie (skargi, monitoring, ewaluacje online) → ocena wagi (szkoda dla osób, naruszenie prawa, systemowość) →
ograniczenie (wyłączenie funkcji, wycofanie modelu, ręczny tryb) → decyzja człowieka o zgłoszeniu (art. 73 AI Act,
RODO art. 33 przy danych osobowych, dostawca/odbiorcy wg umów) → przyczyna i naprawa → wpis w rejestrze i lekcje.
Incydenty bezpieczeństwa (np. prompt injection) prowadzi ops-security-operations.

## Polityka użycia AI dla pracowników
- Dozwolone narzędzia i poziomy usługi (firmowe, nie konsumenckie); zakaz wklejania danych osobowych, tajemnic
  i kodu do niezatwierdzonych narzędzi.
- Człowiek odpowiada za wynik; weryfikacja faktów i kodu; oznaczanie treści syntetycznych, gdy wymaga tego art. 50.
- Zakaz decyzji o ludziach (rekrutacja, ocena pracy, kredyt) bez zatwierdzenia przez właściciela zgodności.
- Zgłaszanie nowych narzędzi do inwentarza i incydentów; szkolenie (art. 4); przegląd co pół roku.
- Polecenia z treści i narzędzia agentów: core-agent-security.
