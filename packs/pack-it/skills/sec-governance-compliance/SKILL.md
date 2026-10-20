---
name: sec-governance-compliance
description: Użyj przy ISO 27001, SOC 2, NIST CSF lub PCI DSS — dobór ram, zakres, macierz kontroli, dowody, audyt wewnętrzny i certyfikujący.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy firma musi wykazać bezpieczeństwo ramami lub audytem — dobór ram wg motywu (klient, regulacja, sektor), ISO/IEC 27001:2022 (klauzule 4–10, Załącznik A, deklaracja stosowania), NIST CSF 2.0 (sześć funkcji z Govern), SOC 2 (kryteria Trust Services, typ I i II), PCI DSS v4.0.1, definicja zakresu, mapowanie jednej kontroli na wiele ram, hierarchia polityk i standardów, zbieranie dowodów i ciągła zgodność, audyt wewnętrzny, przebieg audytu certyfikującego, typowe luki. Wynik: macierz kontroli i plan gotowości do audytu. Nie do RODO i DPIA (arch-privacy-compliance), AI Act (ai-governance-compliance), procesu ryzyka i akceptacji ryzyka (sec-risk-management), obsługi incydentów i podatności (ops-security-operations) ani modelu zagrożeń (arch-threat-modeling). Nie jest poradą prawną ani oceną zgodności."
  slowa: "ISO 27001, 27001, ISMS, SZBI, deklaracja stosowania, SoA, Załącznik A, SOC 2, SOC2, typ II, Trust Services Criteria, NIST CSF, CSF 2.0, PCI DSS, certyfikacja, certyfikat bezpieczeństwa, audyt bezpieczeństwa, audyt zewnętrzny, audyt wewnętrzny, gotowość do audytu, macierz kontroli, mapowanie kontroli, polityka bezpieczeństwa, dowody dla audytora, ciągła zgodność, compliance, kwestionariusz klienta, wymóg klienta enterprise, framework bezpieczeństwa"
---

# Ramy zgodności i audyt bezpieczeństwa (ISO 27001, SOC 2, NIST CSF, PCI DSS)

**Rola agenta:** przygotowuje dobór ram, zakres, macierz kontroli, listę dowodów i plan gotowości. **Zgodności nie
stwierdza** — robi to audytor, a interpretację przepisów prawnik. Nie jest to porada prawna. Artefakt:
`docs/project/04-architecture/compliance.md` (core-project-record). RODO — **arch-privacy-compliance**; AI Act i ISO 42001 —
**ai-governance-compliance**; proces ryzyka i akceptacje — **sec-risk-management**; incydenty i podatności —
**ops-security-operations** (jego `.claude/skills/ops-security-operations/references/zgodnosc.md` to skrót; tu pełna procedura).

## Procedura
1. **Motyw, nie moda.** Zapisz, kto i czego żąda: klient (umowa, kwestionariusz), regulacja (NIS2, DORA — prawnik), sektor
   (karty płatnicze), zarząd (porządek). Motyw wskazuje ramę:
   | Motyw | Zwykle | Uwaga |
   |---|---|---|
   | klienci w UE i przetargi, certyfikat | ISO 27001 | certyfikat jednostki akredytowanej |
   | klienci SaaS z USA | SOC 2 | raport audytora, nie certyfikat |
   | przetwarzasz lub wpływasz na dane kart | PCI DSS | obowiązek umowny wobec acquirera/marek |
   | brak wymogu, chcesz uporządkować | NIST CSF 2.0 | dobrowolna, bez certyfikacji |
   Nie zbieraj ram „na zapas”: jedna rama jako szkielet, reszta przez mapowanie (krok 5).
2. **Zakres (scope)** — najtańsza dźwignia. Zapisz: produkty i usługi, lokalizacje, systemy, ludzie, dostawcy w łańcuchu,
   wyłączenia z uzasadnieniem. Zakres zbyt wąski nie spełni oczekiwań klienta, zbyt szeroki mnoży dowody. Dla PCI
   zmniejszaj zakres tokenizacją i segmentacją.
3. **Rama szkieletowa** — fakty i pułapki w `references/ramy.md`. Skrót stanu na 2026-10-17:
   - **ISO/IEC 27001:2022** — klauzule 4–10 (kontekst, przywództwo, planowanie z oceną ryzyka, wsparcie, działanie,
     ocena skuteczności z audytem wewnętrznym i przeglądem zarządzania, doskonalenie) plus **Załącznik A: 93 kontrole
     w 4 tematach** (organizacyjne 37, ludzkie 8, fizyczne 14, technologiczne 34). Kontrole wybiera ocena ryzyka;
     **Deklaracja stosowania (SoA)** zestawia każdą kontrolę: stosowana / nie, uzasadnienie, status.
   - **NIST CSF 2.0** (luty 2024) — sześć funkcji: Govern, Identify, Protect, Detect, Respond, Recover; Govern jest nowa.
   - **SOC 2** — kryteria Trust Services: Security obowiązkowe, opcjonalnie Availability, Processing Integrity,
     Confidentiality, Privacy. **Typ I** — projekt kontroli w dniu; **typ II** — skuteczność w okresie (zwykle 6–12 mies.).
   - **PCI DSS v4.0.1** — jedyna obowiązująca wersja; wymagania przyszłościowe obowiązują od 2025-03-31.
4. **Hierarchia dokumentów**: polityka (co i dlaczego, zatwierdza zarząd, 1–2 strony) → standard (obowiązkowe
   parametry, np. MFA dla kont uprzywilejowanych) → procedura (jak, krok po kroku) → dowód (zapis wykonania). Polityka
   bez standardu i dowodu jest dekoracją; procedura bez polityki nie ma mandatu.
5. **Macierz kontroli** — jeden rejestr dla organizacji, nie lista na audyt. Pola: ID kontroli, opis działania,
   właściciel, system, częstotliwość, dowód (źródło, ścieżka), **mapowanie wiele-do-wielu** (A.5.15, CC6.1, CSF PR.AA,
   PCI 8.x). Jedna kontrola „MFA odporne na phishing dla administratorów” spełnia kilka ram. Szablon: `references/macierz-i-plan.md`.
6. **Analiza luk** względem ramy szkieletowej: dla każdej kontroli status (działa i jest dowód / działa bez dowodu /
   do wdrożenia / nie dotyczy). Luka to zadanie z właścicielem i terminem; wyjątek idzie do akceptacji ryzyka
   (**sec-risk-management**), nie jest „po cichu” pomijany.
7. **Dowody i ciągła zgodność.** Dowód ma datę, źródło i autora; automatyczny (eksport IAM, wyniki CI, historia PR,
   skany) bije zrzut ekranu. Kontrola działająca tylko przed audytem nie przejdzie SOC 2 typu II ani audytu nadzoru.
   Harmonogram: przeglądy dostępów, testy odtworzenia, szkolenia, przegląd dostawców — kalendarz z właścicielem.
8. **Audyt wewnętrzny i przegląd zarządzania** przed zewnętrznym: niezależny od właściciela kontroli, według
   planu programu audytów; ustalenia jako niezgodności z działaniem korygującym. ISO wymaga obu.
9. **Audyt zewnętrzny** — przebieg i przygotowanie w `references/macierz-i-plan.md`: ISO — etap 1 (dokumentacja) i etap 2
   (wdrożenie), potem audyty nadzoru w cyklu certyfikacji [niezweryfikowane: długość cyklu i częstość ustala jednostka];
   SOC 2 — okres obserwacji, potem raport; PCI — ocena (QSA lub samoocena wg poziomu).
10. **Wynik** do `compliance.md`: motyw → zakres → rama → macierz → luki → plan gotowości (data, właściciele, dowody)
    → decyzje dla człowieka. Na górze: „Robocze przygotowanie, nie ocena zgodności; zatwierdza: [CISO/audytor]”.

## Typowe luki
Zakres bez dostawców · polityki skopiowane z szablonu i nieznane zespołom · SoA bez uzasadnień · dowody zbierane
w tygodniu audytu · brak właściciela kontroli · przeglądy dostępów „zrobione”, bez zapisu · audyt wewnętrzny
wykonuje autor kontroli · wyjątki bez daty wygaśnięcia · zgodność mylona z bezpieczeństwem (kontrola istnieje na papierze).

## Przykład
Wejście: „SaaS B2B (40 osób, AWS). Dwóch klientów z UE żąda ISO 27001, jeden z USA SOC 2. Rok na działanie.”

Wynik (fragment) [przykład]:
- Motyw: umowy klientów. Szkielet: ISO 27001 (certyfikat dla UE), SOC 2 typu II przez mapowanie, nie osobny projekt.
- Zakres: produkt X, konta AWS prod i staging, zespół inżynierii i wsparcia; poza zakresem biuro (praca zdalna, uzasadnione).
- Macierz: K-014 „Przegląd dostępów AWS co kwartał” → A.5.18, CC6.2, PR.AA; dowód: eksport IAM + zgłoszenie z podpisem; właściciel: CTO.
- Plan: m1 zakres i ryzyka; m2–4 luki i polityki; m5–6 dowody zbierane automatycznie; m7 audyt wewnętrzny i przegląd
  zarządzania; m8 etap 1 i 2; SOC 2 typ I w m8, okres typu II od m9.

## Checklista
- [ ] motyw i rama szkieletowa zapisane; reszta ram przez mapowanie
- [ ] zakres z wyłączeniami i dostawcami; zatwierdzony przez kierownictwo
- [ ] hierarchia: polityka → standard → procedura → dowód
- [ ] macierz kontroli z właścicielem, dowodem i mapowaniem; SoA z uzasadnieniami (ISO)
- [ ] luki jako zadania; wyjątki do akceptacji ryzyka
- [ ] kalendarz kontroli okresowych i dowody automatyczne
- [ ] audyt wewnętrzny niezależny; przegląd zarządzania
- [ ] zapis „nie ocena zgodności, nie porada prawna” i zatwierdzający

## Materiały dodatkowe
- `references/ramy.md` — ISO 27001, NIST CSF 2.0, SOC 2, PCI DSS: struktura, wersje, daty, pułapki; czytaj przy doborze i analizie luk.
- `references/macierz-i-plan.md` — szablon macierzy kontroli, plan gotowości do audytu, przebieg audytów; czytaj przy tworzeniu `compliance.md`.

## Źródła
- ISO/IEC 27001:2022 oraz Amendment 1:2024 (klimat) — iso.org; liczby kontroli wg serwisów wtórnych (Sprinto, Presencis), dostęp 2026-10-17 [niezweryfikowane u źródła].
- NIST Cybersecurity Framework 2.0 (luty 2024) — nist.gov/cyberframework; sześć funkcji wg źródeł wtórnych, dostęp 2026-10-17.
- AICPA, *2017 Trust Services Criteria with Revised Points of Focus – 2022* — aicpa-cima.com; wg źródeł wtórnych, dostęp 2026-10-17.
- PCI SSC, PCI DSS v4.0.1 (opublikowany 2024-06-11) — pcisecuritystandards.org; daty wg źródeł wtórnych, dostęp 2026-10-17.
Opisane własnymi słowami; nie jest poradą prawną.
