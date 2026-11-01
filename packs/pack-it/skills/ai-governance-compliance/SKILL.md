---
name: ai-governance-compliance
description: Użyj przy zgodności systemu AI z AI Act — rola, klasa ryzyka, obowiązki i terminy, NIST AI RMF, ISO 42001, polityka AI, incydenty.
metadata:
  przeglad: "2027-01-17"
  katalog: "Użyj, gdy trzeba ustalić, co AI Act (rozporządzenie (UE) 2024/1689) i ramy zarządzania AI oznaczają dla systemu lub firmy — inwentarz systemów AI, rola (dostawca, podmiot stosujący, importer, dystrybutor, art. 25), klasa ryzyka (praktyki zakazane, wysokie ryzyko wg załącznika III i produktów, przejrzystość z art. 50, ryzyko minimalne, modele AI ogólnego przeznaczenia), obowiązki na rolę (zarządzanie ryzykiem, dane, dokumentacja techniczna, rejestrowanie zdarzeń, nadzór człowieka, ocena zgodności, rejestracja, monitorowanie po wprowadzeniu, poważne incydenty, kompetencje w zakresie AI, FRIA), terminy stosowania z uwzględnieniem Digital Omnibus, NIST AI RMF i profil generatywnej AI (AI 600-1), ISO/IEC 42001 i relacja do 27001, ocena wpływu, karty modelu i zbiorów danych, podstawy uczciwości i stronniczości, proces incydentu AI, polityka użycia AI dla pracowników, styk z RODO (art. 22). Nie do RODO, DPIA i retencji (arch-privacy-compliance), modelu zagrożeń (arch-threat-modeling), pomiaru jakości i ewaluacji (ai-evals), bezpieczeństwa pracy agenta (core-agent-security) ani strategii produktu AI (ai-product-management). Nie jest poradą prawną."
  slowa: "AI Act, akt o sztucznej inteligencji, rozporządzenie o AI, zgodność AI, system wysokiego ryzyka, praktyki zakazane, dostawca AI, podmiot stosujący, deployer, provider, ocena zgodności, znak CE, NIST AI RMF, ISO 42001, 42001, zarządzanie AI, AI governance, polityka AI, polityka użycia AI, regulamin AI dla pracowników, rejestr systemów AI, FRIA, ocena wpływu na prawa podstawowe, karta modelu, model card, stronniczość, bias, fairness, incydent AI, kompetencje AI, AI literacy, Digital Omnibus, model ogólnego przeznaczenia, GPAI, etyka AI, odpowiedzialna AI, czy nasz system podlega AI Act, znak wodny, watermark, oznaczanie treści ai, c2pa, content credentials, kodeks praktyk oznaczania, art. 50 ust. 2, treści generowane przez ai"
---

# Zgodność i zarządzanie AI (AI Act, NIST, ISO 42001)

**Rola agenta:** przygotowuje inwentarz, wstępną klasyfikację, macierz obowiązków i listę dowodów, a także wskazuje
decyzje. **To nie jest porada prawna.** Rolę, klasę ryzyka, wyjątki i zgłoszenia rozstrzyga człowiek z prawnikiem
lub inspektorem ochrony danych (IOD). Artefakt: `docs/project/04-architecture/ai-compliance.md`.
RODO, DPIA, retencja — **arch-privacy-compliance**; zagrożenia bezpieczeństwa — **arch-threat-modeling**; pomiar
jakości — **ai-evals**; strategia produktu — **ai-product-management**; polecenia z treści — **core-agent-security**.

## Procedura
1. **Inwentarz.** Dla każdego systemu AI (własnego, kupionego, wbudowanego w SaaS, „cienia” używanego przez
   pracowników): cel, model i dostawca, dane wejściowe i wyjściowe, kto go używa, kogo dotyczą decyzje, rynek (UE?),
   właściciel. Bez inwentarza reszta jest zgadywaniem.
2. **Zakres i rola** (art. 2–3, 23–25). Ustal osobno dla każdego systemu:
   - **dostawca** — rozwija system lub model albo wprowadza pod własną nazwą i marką;
   - **podmiot stosujący** (deployer) — używa systemu w działalności zawodowej;
   - **importer** i **dystrybutor** — łańcuch dostaw do UE;
   - rola **zmienia się** (art. 25): podmiot stosujący staje się dostawcą, gdy nadaje system pod własną marką, istotnie go
     zmienia albo zmienia przeznaczenie (np. dostrojenie pod ocenę kredytową). Zapisz podstawę.
   - Rozporządzenie obejmuje też dostawców spoza UE, jeśli wynik systemu jest używany w UE. „Nie jesteśmy w UE” nie
     zamyka sprawy.
3. **Klasa ryzyka** — sprawdzaj w tej kolejności:
   1. **Praktyki zakazane** (art. 5, od 2025-02-02): np. manipulacja podprogowa, scoring społeczny, rozpoznawanie emocji
      w pracy i szkole, nieukierunkowane pozyskiwanie wizerunków. Trafienie = stop i eskalacja do prawnika.
   2. **Wysokie ryzyko** (art. 6): system jako element bezpieczeństwa produktu objętego prawem z załącznika I albo
      przypadek z **załącznika III** (m.in. rekrutacja i zarządzanie pracownikami, edukacja, scoring kredytowy,
      dostęp do usług podstawowych, organy ścigania, migracja, wymiar sprawiedliwości). Wyjątek z art. 6 ust. 3 (system
      bez istotnego wpływu na wynik decyzji) wymaga udokumentowanej oceny i rejestracji; profilowanie osób go wyklucza.
   3. **Przejrzystość** (art. 50): chatbot (poinformuj o kontakcie z AI), treści syntetyczne (oznaczenie
      w formacie maszynowym; warstwy, kodeks praktyk z 2026-06 i granice znaku wodnego:
      `references/znakowanie-techniczne.md`), deepfake, rozpoznawanie emocji. Może się nakładać na klasę 2.
   4. **Ryzyko minimalne** — brak obowiązków poza kompetencjami (art. 4); kodeksy dobrych praktyk dobrowolne.
   5. **Model ogólnego przeznaczenia** (GPAI, art. 51–55) — osobna oś dla dostawcy modelu: dokumentacja techniczna,
      polityka praw autorskich, streszczenie danych treningowych; przy ryzyku systemowym dodatkowo ocena i zgłaszanie
      incydentów. Integrator cudzego modelu zwykle nie jest dostawcą GPAI, ale może być dostawcą systemu.
4. **Obowiązki na rolę** — macierz w `references/macierz-i-dowody.md` (dostawca wysokiego ryzyka: art. 9–15, 17, 43,
   47–49, 72–73; podmiot stosujący: art. 26–27; wszyscy: art. 4). Dla każdego wiersza: właściciel, dowód, termin, status.
   Podmiot stosujący system wysokiego ryzyka wyznacza nadzór człowieka (art. 26 ust. 2): przeszkolone osoby z kompetencjami
   i uprawnieniem do zakwestionowania i odrzucenia wyniku systemu.
5. **Terminy** (stan 2026-10-17): sprawdź tabelę poniżej i **datę dla swojego systemu**. Przy planowaniu podaj datę
   z przypisem źródła; sprzeczne — oba warianty z [niezweryfikowane].
6. **Ramy dobrowolne.** NIST AI RMF 1.0 (Govern, Map, Measure, Manage) i profil AI 600-1 porządkują ryzyka;
   ISO/IEC 42001:2023 to certyfikowalny system zarządzania AI (struktura jak ISO 27001, można je spiąć w jeden
   system zarządzania). Nie zastępują AI Act, ale dostarczają dowodów. Szczegóły: `references/ramy-i-praktyka.md`.
7. **Praktyka:** ocena wpływu (prawa podstawowe), karty modelu i zbiorów danych, test stronniczości, proces incydentu AI,
   polityka użycia AI dla pracowników — wzorce w `references/ramy-i-praktyka.md`.
8. **Styk z RODO.** Decyzja wyłącznie automatyczna z istotnym skutkiem (art. 22 RODO) i DPIA — oceń w arch-privacy-compliance.
   Podmiot stosujący system wysokiego ryzyka korzysta z instrukcji dostawcy przy DPIA (art. 26 ust. 9 AI Act).
9. **Wynik** do `ai-compliance.md`: inwentarz → rola → klasa z uzasadnieniem → macierz obowiązków → luki i dowody →
   decyzje dla człowieka → terminy. Na górze: „Wstępna klasyfikacja robocza, nie porada prawna; zatwierdza: [prawnik/IOD]”.

## Terminy stosowania — stan 2026-10-17
| Data | Co | Status |
|---|---|---|
| 2024-08-01 | wejście w życie rozporządzenia (UE) 2024/1689 | pewne |
| 2025-02-02 | zakazy (art. 5) i kompetencje w zakresie AI (art. 4) | pewne |
| 2025-08-02 | obowiązki GPAI, zarządzanie, kary | pewne |
| 2026-08-02 | ogólne stosowanie, w tym art. 50; art. 50 ust. 2 dla systemów już na rynku do 2026-12-02 | [niezweryfikowane] |
| 2026-12-02 | nowy zakaz (treści intymne bez zgody, CSAM) | [niezweryfikowane] |
| 2027-12-02 | wysokie ryzyko z załącznika III (było 2026-08-02) | [niezweryfikowane] |
| 2028-08-02 | wysokie ryzyko z załącznika I, produkty (było 2027-08-02) | [niezweryfikowane] |

Przesunięcia wprowadza „Digital Omnibus on AI”, rozporządzenie (UE) 2026/1744, opublikowane 2026-07-24, w mocy od
2026-07-27 — wg źródeł wtórnych (kancelarie); EUR-Lex był niedostępny w sesji. Zmiana złagodziła też art. 4: obowiązek
„podejmowania środków wspierających” kompetencje zamiast zapewnienia ich poziomu. Przed cytowaniem potwierdź tekst
w EUR-Lex (OJ L 2026/1744).

## Przykład
Wejście: „Spółka z Warszawy kupuje narzędzie SaaS do szeregowania CV (dostawca z USA) i dodaje własny chatbot rekrutacyjny
na API modelu.”

Wynik (fragment) [przykład]:

| System | Rola | Klasa | Uzasadnienie | Główne obowiązki |
|---|---|---|---|---|
| Szeregowanie CV | podmiot stosujący | wysokie ryzyko (zał. III, zatrudnienie) | ocena i selekcja kandydatów; profilowanie wyklucza wyjątek z art. 6 ust. 3 | instrukcja dostawcy, nadzór człowieka, logi ≥6 mies., informowanie kandydatów, kompetencje; decyzja o FRIA i DPIA — prawnik/IOD |
| Chatbot rekrutacyjny | dostawca systemu (własny produkt na cudzym modelu) | przejrzystość (art. 50) | komunikuje się z ludźmi | informacja „rozmawiasz z AI”; jeśli chatbot ocenia kandydatów, klasa rośnie do wysokiego ryzyka |

Terminy: art. 50 od 2026-08-02 [niezweryfikowane]; wysokie ryzyko wg Omnibus od 2027-12-02 [niezweryfikowane]; art. 4 już teraz.

## Checklista
- [ ] inwentarz systemów AI, także wbudowanych w SaaS i „cienia”
- [ ] rola per system, z ewentualnym art. 25 i uzasadnieniem
- [ ] klasa ryzyka sprawdzona w kolejności: zakazy, wysokie ryzyko, art. 50, minimalne, GPAI
- [ ] macierz obowiązków z właścicielem, dowodem i terminem
- [ ] terminy zweryfikowane w EUR-Lex; sprzeczne oznaczone [niezweryfikowane]
- [ ] polityka użycia AI, kompetencje (art. 4), proces incydentu AI
- [ ] styk z RODO (art. 22, DPIA) przekazany do arch-privacy-compliance
- [ ] zapis „nie porada prawna” i zatwierdzający (prawnik/IOD)

## Materiały dodatkowe
- `references/macierz-i-dowody.md` — macierz obowiązków wg roli, lista dowodów, kary; czytaj przy tworzeniu `ai-compliance.md`.
- `references/ramy-i-praktyka.md` — NIST AI RMF, AI 600-1, ISO 42001 vs 27001, ocena wpływu, karty, stronniczość, incydent, polityka; czytaj przy wdrażaniu zarządzania AI.

## Źródła
- Rozporządzenie (UE) 2024/1689 (AI Act) — eur-lex.europa.eu; numery artykułów z tekstu rozporządzenia znanego
  z wiedzy własnej, w sesji niepotwierdzone u źródła [niezweryfikowane u źródła].
- Rozporządzenie (UE) 2026/1744 (Digital Omnibus on AI) — daty z kancelarii (White & Case, Lewis Silkin, Freshfields,
  Gibson Dunn) i serwisu artificialintelligenceact.eu, dostęp 2026-10-17; komentarze różnią się co do art. 50 ust. 2.
- NIST AI RMF 1.0 (NIST AI 100-1, styczeń 2023) i AI 600-1 Generative AI Profile (lipiec 2024) — nist.gov, źródła wtórne, dostęp 2026-10-17.
- ISO/IEC 42001:2023 — iso.org [niezweryfikowane w sesji].
Opisane własnymi słowami; nie jest poradą prawną.
