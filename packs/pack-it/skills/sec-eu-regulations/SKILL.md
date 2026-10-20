---
name: sec-eu-regulations
description: Użyj przy unijnych wymogach cyber — NIS2 (KSC), DORA, Cyber Resilience Act; zakres, obowiązki, terminy zgłaszania incydentów, jeden incydent a wiele zgłoszeń.
metadata:
  przeglad: 2027-01-17
  katalog: "Użyj, gdy trzeba ustalić, czy i jak firma podlega unijnym regulacjom cyberbezpieczeństwa — NIS2 (dyrektywa (UE) 2022/2555, w Polsce nowelizacja ustawy o krajowym systemie cyberbezpieczeństwa): podmioty kluczowe i ważne, reguła wielkości, odpowiedzialność zarządu (art. 20), środki zarządzania ryzykiem (art. 21), zgłaszanie incydentów (art. 23: 24 h, 72 h, miesiąc), kary; DORA (rozporządzenie (UE) 2022/2554) dla sektora finansowego: ryzyko ICT, klasyfikacja i zgłaszanie incydentów, testy odporności z TLPT, rejestr informacji o dostawcach ICT; Cyber Resilience Act (rozporządzenie (UE) 2024/2847) dla produktów z elementami cyfrowymi: obowiązki producenta, obsługa podatności, zgłaszanie aktywnie wykorzystywanych podatności, znak CE; styk z art. 33 RODO i przepisami sektorowymi, jeden incydent a kilka zegarów, jeden playbook zgłoszeń z tabelą decyzyjną. Wynik: ocena stosowalności i macierz obowiązków z zegarami zgłoszeń. Nie do RODO i DPIA (arch-privacy-compliance), AI Act (ai-governance-compliance), ISO 27001 i SOC 2 (sec-governance-compliance), technicznej obsługi incydentu (ops-security-operations) ani strategii i rozmów z zarządem (sec-security-leadership). Nie jest poradą prawną."
  slowa: "NIS2, dyrektywa NIS2, KSC, krajowy system cyberbezpieczeństwa, podmiot kluczowy, podmiot ważny, DORA, odporność operacyjna, TLPT, rejestr informacji, dostawca ICT, Cyber Resilience Act, CRA, produkty z elementami cyfrowymi, znak CE, zgłoszenie incydentu, zgłaszanie incydentów, early warning, CSIRT, ENISA, odpowiedzialność zarządu, regulacje UE, czy podlegamy NIS2, jeden incydent wiele zgłoszeń, termin zgłoszenia, playbook zgłoszeń, kary NIS2, komu zgłosić incydent, komu i kiedy zgłosić, zgłosić do UODO i CSIRT, ransomware obowiązek zgłoszenia, fintech instytucja płatnicza, DORA i RODO jednocześnie, kilka zgłoszeń, obowiązek zgłoszenia do regulatora"
---

# Regulacje UE w cyberbezpieczeństwie (NIS2, DORA, CRA)

**Rola agenta:** przygotowuje wstępną ocenę stosowalności, macierz obowiązków z zegarami zgłoszeń i szkic playbooka
zgłoszeń. **To nie jest porada prawna.** Przepisy krajowe i wytyczne organów nadzoru mają pierwszeństwo przed tym
skillem; zakres, klasyfikację i zgłoszenia rozstrzyga prawnik. Każdy artykuł i datę sprawdź w EUR-Lex (akty UE)
i ISAP/Dzienniku Ustaw (akty polskie). Artefakt: `docs/project/04-architecture/eu-cyber-regulations.md`.
RODO i DPIA — **arch-privacy-compliance**; AI Act — **ai-governance-compliance**; ISO 27001, SOC 2 —
**sec-governance-compliance**; techniczna obsługa incydentu — **ops-security-operations**; rozmowa z zarządem
i program — **sec-security-leadership**; rejestr ryzyk — **sec-risk-management**.

## Procedura
1. **Fakty o firmie.** Kraje działalności (UE/EOG, także klienci), sektor i podsektor (NACE), liczba osób, obrót
   i suma bilansowa (z powiązanymi przedsiębiorstwami), rola w łańcuchu (usługodawca, producent, dostawca ICT dla
   banków), czy wprowadzasz na rynek UE produkty z oprogramowaniem. Bez tego ocena jest zgadywaniem.
2. **Stosowalność — sprawdzaj w tej kolejności:**
   1. **DORA** (finanse): jeśli jesteś podmiotem finansowym z art. 2, DORA jest aktem szczególnym względem NIS2
      (art. 21 i 23 NIS2 się nie stosują), ale podlegasz RODO. Dostawca ICT dla takich podmiotów podlega im umownie.
   2. **NIS2:** średnie i duże przedsiębiorstwa (reguła wielkości: ≥50 osób lub obrót/suma bilansowa >10 mln euro)
      z sektorów załącznika I (o wysokiej krytyczności) lub II (inne sektory krytyczne). **Kluczowy** — duży podmiot
      z zał. I oraz niezależnie od wielkości m.in. kwalifikowani dostawcy usług zaufania, rejestry TLD, DNS. **Ważny** —
      pozostałe. Wyjątki niezależne od wielkości i krajowe rozszerzenia — tylko według ustawy krajowej (krok 5).
   3. **CRA:** produkt z elementami cyfrowymi (sprzęt lub oprogramowanie, łączony z urządzeniem lub siecią) wprowadzany
      na rynek UE. Rola: producent, importer, dystrybutor, steward open source. Usługi SaaS same w sobie poza zakresem,
      chyba że to zdalne przetwarzanie danych niezbędne dla funkcji produktu.
   4. **RODO art. 33** stosuje się zawsze, gdy naruszenie dotyczy danych osobowych — niezależnie od pozostałych aktów.
3. **Obowiązki** — macierz w `references/macierz-obowiazkow.md`. Skrót:
   - **NIS2:** zarząd zatwierdza środki i nadzoruje je, odpowiada za naruszenia i przechodzi szkolenia (art. 20);
     minimum 10 grup środków (art. 21 ust. 2: m.in. analiza ryzyka, obsługa incydentów, ciągłość działania,
     bezpieczeństwo łańcucha dostaw, obsługa podatności, kryptografia, kontrola dostępu, MFA, szkolenia);
     zgłaszanie (art. 23).
   - **DORA:** ramy zarządzania ryzykiem ICT, klasyfikacja i zgłaszanie poważnych incydentów, testy odporności (co
     najmniej roczne; TLPT co najmniej raz na 3 lata dla wskazanych podmiotów), ryzyko dostawców ICT i rejestr
     informacji, nadzór nad krytycznymi dostawcami ICT.
   - **CRA:** bezpieczeństwo w projekcie i domyślnie, obsługa podatności i aktualizacje (okres wsparcia zwykle ≥5 lat),
     dokumentacja techniczna, SBOM, ocena zgodności i znak CE, zgłaszanie.
4. **Zegary zgłoszeń** (tabela niżej) i **jeden playbook**: z jednego zdarzenia wynika kilka zgłoszeń do różnych adresatów.
   Prowadź jedną oś czasu i jedną tabelę decyzyjną (krok 6), a nie osobne procedury na akt.
5. **Polska (NIS2).** Sprawdź w ISAP tekst ustawy; stan na 2026-10-17 (źródła wtórne, patrz Źródła): ustawa z 2026-01-23
   o zmianie ustawy o KSC (Dz.U. 2026 poz. 252) weszła w życie 2026-04-03. Wniosek o wpis do wykazu podmiotów
   kluczowych i ważnych — termin 2026-10-03 (**już minął** — sprawdź skutki i tryb nadrobienia w ustawie); wdrożenie
   obowiązków do 2027-04-03, kolejny etap do 2028-04-03 [niezweryfikowane — z komunikatu Ministerstwa Cyfryzacji].
   Wniosek Prezydenta do Trybunału Konstytucyjnego o część przepisów (m.in. dostawcy wysokiego ryzyka, polecenia
   zabezpieczające, kary) [niezweryfikowane]. Wysokość kar i dokładne terminy zgłoszeń wg KSC: [niezweryfikowane].
6. **Tabela decyzyjna zgłoszeń** (wstaw własne role, adresatów i numery kontaktowe):
   | Pytanie o zdarzenie | Jeśli tak | Zegar, adresat |
   |---|---|---|
   | Dotyczy danych osobowych i grozi ryzyko dla osób? | RODO | 72 h od stwierdzenia, UODO; osoby bez zbędnej zwłoki przy wysokim ryzyku |
   | Podmiot finansowy, poważny incydent ICT? | DORA | wstępne zgłoszenie krótko po klasyfikacji, nie później niż 24 h od wykrycia; dalsze etapy wg tabeli |
   | Kluczowy lub ważny, incydent poważny? | NIS2 | 24 h wczesne ostrzeżenie, 72 h zgłoszenie, miesiąc raport końcowy, CSIRT/organ |
   | Producent: aktywnie wykorzystywana podatność lub poważny incydent produktu? | CRA | 24 h, 72 h, 14 dni po poprawce lub miesiąc, platforma ENISA |
   | Umowa lub regulator sektorowy (np. KNF, klient) | umowa, wytyczne | wg dokumentu; sprawdź, nie zgaduj |
   Każdy wiersz „tak” otwiera osobny zegar. Zegary startują od różnych zdarzeń (uzyskanie wiedzy, klasyfikacja,
   dostępność poprawki) — zapisz zdarzenie startowe i godzinę. Zgłoś na tym, co wiesz; uzupełniaj w kolejnych etapach.
7. **Wynik:** fakty o firmie → stosowalność per akt z uzasadnieniem → macierz obowiązków (właściciel, dowód, termin,
   status) → tabela zegarów i playbook → luki → decyzje dla prawnika. Na górze: „Wstępna ocena robocza, nie porada
   prawna; zatwierdza: [prawnik/IOD]”.

## Zegary zgłoszeń — stan 2026-10-17
| Akt | Pierwszy sygnał | Drugi etap | Raport końcowy | Start zegara |
|---|---|---|---|---|
| NIS2 art. 23 | 24 h wczesne ostrzeżenie | 72 h zgłoszenie incydentu | miesiąc po zgłoszeniu | uzyskanie wiedzy o incydencie poważnym |
| RODO art. 33 | 72 h (jedno zgłoszenie, uzupełniane etapami) | — | — | stwierdzenie naruszenia |
| DORA (ITS 2025/302, RTS 2025/301) | 4 h od klasyfikacji, nie później niż 24 h od uzyskania wiedzy | raport pośredni 72 h od zgłoszenia wstępnego | miesiąc od raportu pośredniego | klasyfikacja jako poważny; źródła różnią się co do początku zegara [niezweryfikowane] |
| CRA art. 14 | 24 h wczesne ostrzeżenie | 72 h zgłoszenie | podatność: 14 dni po dostępności poprawki; incydent: miesiąc po zgłoszeniu 72 h | uzyskanie wiedzy |

CRA: obowiązki zgłoszeniowe od 2026-09-11 (także dla produktów już na rynku), większość pozostałych od 2027-12-11;
zgłoszenia przez platformę ENISA (Single Reporting Platform), która trafia też do koordynatora CSIRT. DORA stosuje się od
2025-01-17. Terminy transpozycji i krajowe: NIS2 — 2024-10-17 (Polska spóźniona do 2026-04-03).
Digital Omnibus (2025-11-19) proponuje jeden punkt zgłoszeń dla NIS2, RODO, DORA i innych — to **projekt**, nieprzyjęty
[niezweryfikowane]; nie planuj na nim zmian.

## Przykład
Wejście: „Polski dostawca SaaS dla banków, 120 osób, obrót 25 mln euro, wypuszcza też aplikację mobilną. Wyciek danych
klientów banku przez podatność w naszym API.” [przykład]

Wynik (fragment):
- NIS2: usługi ICT B2B (zał. I) i średnia wielkość → wstępnie podmiot ważny; potwierdź kwalifikację w KSC i wpis do wykazu.
- DORA: nie jest podmiotem finansowym, ale jest dostawcą ICT — obowiązki wynikają z umów z bankami (art. 30 DORA),
  a incydent musi trafić do banków na czas, który pozwoli im zgłosić własny.
- RODO: prawdopodobnie procesor — zawiadamia administratora (bank) bez zbędnej zwłoki; 72 h dotyczy administratora.
- CRA: aplikacja mobilna to produkt z elementami cyfrowymi; podatność wykorzystywana aktywnie → 24 h na platformie ENISA.
- Zegary: godzina 0 = uzyskanie wiedzy; +24 h NIS2 i CRA, +72 h oba zgłoszenia i RODO administratora. Jedna oś czasu.

## Checklista
- [ ] fakty o firmie (sektor, wielkość, kraje, rola, produkty) zapisane
- [ ] stosowalność per akt, w kolejności DORA, NIS2, CRA, RODO, z uzasadnieniem
- [ ] macierz obowiązków z właścicielem, dowodem, terminem
- [ ] zdarzenie startowe i adresat dla każdego zegara; jedna oś czasu incydentu
- [ ] stan krajowy (KSC) sprawdzony w ISAP; sprzeczności oznaczone [niezweryfikowane]
- [ ] zapis „nie porada prawna” i zatwierdzający; ćwiczenie playbooka (tabletop)

## Materiały dodatkowe
- `references/macierz-obowiazkow.md` — obowiązki, kary i dowody per akt, sektory i reguła wielkości; czytaj przy budowie macierzy.
- `references/playbook-zgloszen.md` — szkic playbooka z osią czasu i szablonem zgłoszenia; czytaj przy projektowaniu procedury.

## Źródła
- Dyrektywa (UE) 2022/2555 (NIS2), rozporządzenie (UE) 2022/2554 (DORA), rozporządzenie (UE) 2024/2847 (CRA) —
  eur-lex.europa.eu; numery artykułów i kary z wiedzy własnej, w sesji niepotwierdzone u źródła [niezweryfikowane u źródła].
- Polska: Dz.U. 2026 poz. 252 (ELI eli.gov.pl/eli/DU/2026/252), komunikat Ministerstwa Cyfryzacji z 2026-04-02 na gov.pl,
  Forsal 2026-04-04, Clifford Chance 2026-03, Osborne Clarke; dostęp 2026-10-17 (wyniki wyszukiwania, nie tekst ustawy).
- CRA, zgłaszanie: strona Komisji Europejskiej o CRA reporting (digital-strategy.ec.europa.eu) i komentarze kancelarii
  (McCann FitzGerald, 2026-09), dostęp 2026-10-17 (streszczenia z wyszukiwania).
- DORA, zgłaszanie: rozporządzenia delegowane i wykonawcze (UE) 2025/301 i 2025/302; operational instructions ESAs
  (esma.europa.eu, 2026-09), dostęp 2026-10-17 — źródła różnią się co do początku zegara.
- Digital Omnibus (Komisja, 2025-11-19), jeden punkt zgłoszeń: Taylor Wessing, Conventus Law, dokument Rady
  WK 3735/2026, dostęp 2026-10-17 — projekt w toku.
Opisane własnymi słowami; nie jest poradą prawną.
