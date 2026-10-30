---
name: arch-eu-product-law
description: Użyj, gdy trzeba ustalić, które przepisy UE dotyczą budowy produktu cyfrowego z AI — Data Act, PLD, mapa obowiązków z terminami i sąsiednie akty.
metadata:
  przeglad: "2027-01-18"
  katalog: "Użyj, gdy trzeba ustalić, które przepisy UE dotyczą budowy produktu cyfrowego (SaaS, aplikacja webowa lub mobilna, oprogramowanie z AI) i od kiedy — pytania kwalifikujące (dane osobowe, AI, produkt z elementami cyfrowymi, zmiana dostawcy, sektor finansowy, usługa z listy EAA), mapa obowiązków z aktem, artykułem, datą stosowania i datą sprawdzenia, miejsce w kodzie; tematy bez osobnego skilla: Data Act (zmiana dostawcy chmury i SaaS, opłaty za zmianę i transfer danych, eksport danych), PLD (odpowiedzialność za wadliwe oprogramowanie). Kieruje do sąsiadów: RODO i DPIA → arch-privacy-compliance, NIS2, DORA i CRA → sec-eu-regulations, AI Act → ai-governance-compliance, EAA i WCAG → ux-accessibility. Poza zakresem fabryki (notatki w references/poza-zakresem-fabryki.md): DSA, prawa konsumenta, KSeF, ViDA. Nie jest poradą prawną; decyzje podejmuje prawnik lub IOD."
  slowa: "które przepisy UE dotyczą, jakie przepisy nas dotyczą, mapa obowiązków prawnych, prawo UE dla SaaS, prawo UE dla oprogramowania z AI, zgodność produktu z prawem, Data Act, akt w sprawie danych, zmiana dostawcy chmury, zmiana dostawcy SaaS, przeniesienie danych do konkurencji, opłaty za eksport danych, egress, PLD, odpowiedzialność za produkt, wadliwe oprogramowanie"
---

# Prawo UE dla produktu cyfrowego — mapa obowiązków

**Rola agenta:** przygotowuje wstępną mapę przepisów i obowiązków dla produktu, z artykułem, terminem, źródłem
i miejscem w kodzie. **To nie jest porada prawna** — mapa idzie do prawnika lub IOD, który decyduje o kwalifikacji.
Każdy fakt ma datę sprawdzenia; czego nie potwierdzono w tekście aktu, oznaczasz [niezweryfikowane] albo [wtórne].

**Zakres:** fabryka IT zajmuje się prawem tylko w zakresie budowy oprogramowania, także z AI. DSA, prawa konsumenta
(odstąpienie, przycisk odstąpienia), KSeF i ViDA są poza zakresem — dawne notatki w
`references/poza-zakresem-fabryki.md`; pytania o nie kierujesz do prawnika, księgowości lub właściciela produktu.

## 1. Pytania kwalifikujące (najpierw, zanim wymienisz akty)
Odpowiedzi bierzesz z kodu i dokumentów projektu (`scout`), o resztę pytasz człowieka:

| # | Pytanie | „Tak” włącza |
|---|---|---|
| Q1 | Przetwarzacie dane osobowe? | RODO → arch-privacy-compliance |
| Q2 | Produkt używa lub udostępnia AI (czat, generowanie treści, scoring)? | AI Act → ai-governance-compliance |
| Q3 | Sprzedajecie oprogramowanie lub urządzenie instalowane u klienta (nie czysty SaaS)? | CRA → sec-eu-regulations; PLD |
| Q4 | Jesteście dostawcą chmury lub SaaS, z którego klient może przejść do konkurencji? | Data Act (zmiana dostawcy) |
| Q5 | Sektor finansowy albo usługa krytyczna (NIS2)? | DORA, NIS2 → sec-eu-regulations |
| Q6 | Produkt to sklep, bankowość, e-book, bilety lub inna usługa z listy EAA? | EAA → ux-accessibility |

PLD dotyczy praktycznie każdego oprogramowania wprowadzanego do obrotu w ramach działalności (także SaaS).

## 2. Mapa aktów (stan na 2026-10-18, PLD 2026-10-20, źródła wtórne — szczegóły w `references/akty-i-obowiazki.md`)

| Akt | Kiedy dotyczy | Termin | Skill |
|---|---|---|---|
| Data Act, rozp. (UE) 2023/2854 | dostawca usług przetwarzania danych (chmura, SaaS): zmiana dostawcy, eksport danych | stosowanie 12.09.2025 [niezweryfikowane]; opłaty za zmianę obniżone do kosztów bezpośrednich, od 12.01.2027 zakaz (art. 29) [wtórne] | ten |
| PLD, dyr. (UE) 2024/2853 | oprogramowanie jako produkt, odpowiedzialność bez winy za szkodę | transpozycja do 9.12.2026; produkty wprowadzone do obrotu po tej dacie; w PL projekt UC163 (konsultacje zakończone 22.09.2026, ryzyko opóźnienia) [wtórne] | ten |
| RODO 2016/679 | dane osobowe | od 25.05.2018 | arch-privacy-compliance |
| AI Act 2024/1689 po rozp. 2026/1744 | systemy AI | wg skilla; art. 50 [niezweryfikowane] | ai-governance-compliance |
| CRA 2024/2847, NIS2, DORA | produkty z elementami cyfrowymi; sektory kluczowe; finanse | CRA: zgłaszanie od 11.09.2026, reszta 11.12.2027 | sec-eu-regulations |
| EAA, dyr. 2019/882 | wybrane produkty i usługi B2C | od 28.06.2025 | ux-accessibility |

Tabela jest punktem startu, nie wynikiem: przed oddaniem mapy każdą datę i artykuł, z których wynika obowiązek,
sprawdza `researcher` w EUR-Lex lub ISAP (`python3 factory/facts.py`, jeśli projekt prowadzi bazę faktów).

## 3. Procedura
1. **Kwalifikacja:** odpowiedzi na Q1–Q6 z dowodem (plik, dokument) albo z odpowiedzi człowieka.
2. **Rola w każdym akcie:** dostawca, producent, podmiot stosujący, importer — obowiązki zależą od roli.
3. **Mapa obowiązków:** jeden wiersz = jeden obowiązek: akt i artykuł · obowiązek · od kiedy · data sprawdzenia
   i źródło · miejsce w kodzie lub procesie (np. eksport danych, informacja o AI w interfejsie) · właściciel · status.
4. **Sąsiedzi:** RODO, AI Act, NIS2/DORA/CRA i EAA tylko wymieniasz i oddajesz do ich skilli — nie powtarzasz ich treści.
5. **Luki w kodzie:** obowiązki, które wymagają funkcji (eksport danych w formacie do przeniesienia, informacja
   o zmianie dostawcy), idą jako zadania do backlogu z kryterium akceptacji.
6. **Pytania do prawnika:** kwalifikacje niepewne (np. „czy jesteśmy dostawcą usługi przetwarzania danych w rozumieniu
   Data Act?”) wypisujesz osobno; tematy spoza zakresu fabryki też trafiają na tę listę.
7. Zapis: `docs/project/03-architecture/<data>-mapa-prawna.md` (core-project-record) z datą przeglądu.

## Zasady
- Fakty tego skilla pochodzą ze źródeł wtórnych: na początku pracy przypomnij człowiekowi o sprawdzeniu ich w EUR-Lex
  i ISAP (lista: `docs/project/archive/research/20261018-prawo-ue-produkt.md`) i podaj, które pozycje mapy od nich zależą.
- Fakt prawny bez źródła i daty nie trafia do mapy jako pewny; źródło wtórne oznaczasz [wtórne].
- Termin, który już minął, opisujesz jako obowiązujący — z pytaniem, czy produkt go spełnia.
- Dyrektywa działa przez ustawę krajową: podaj stan transpozycji w PL albo [niezweryfikowane].
- Wyłączenia (mikroprzedsiębiorstwa, małe firmy) sprawdzasz w tekście aktu, nie zakładasz.
- Wymiar „prawo” w audycie kodu (eng-code-audit) wykonuje `maja-product-compliance` wg tego skilla.

## Przykład
**Sytuacja:** „SaaS B2B z Polski: asystent AI generuje raporty z danych klienta, klienci mogą przenieść dane do innego
dostawcy. Które przepisy UE nas dotyczą?”
**Wynik (skrót mapy, nie porada prawna — do weryfikacji przez prawnika):**
- Q1 tak, Q2 tak, Q3 nie (czysty SaaS), Q4 tak, Q5 nie, Q6 nie [do potwierdzenia].
- Data Act (2023/2854): zmiana dostawcy i eksport danych od 12.09.2025 [niezweryfikowane]; opłaty za zmianę
  tylko koszty bezpośrednie, od 12.01.2027 zakaz (art. 29) [wtórne].
- PLD (2024/2853): odpowiedzialność za wadliwe oprogramowanie, także SaaS i model AI w produkcie, dla produktów
  wprowadzonych po 9.12.2026; w PL projekt UC163 w toku [wtórne]. W kodzie: ślad wersji i aktualizacji
  bezpieczeństwa, dokumentacja na wypadek domniemania wady.
- AI Act: obowiązek przejrzystości treści generowanych przez AI (art. 50) — termin [niezweryfikowane] → ai-governance-compliance.
- RODO (dane klienta w promptach, procesor modelu) → arch-privacy-compliance.
- Luki w kodzie: brak pełnego eksportu danych klienta w `app/settings/export` (zadanie do backlogu).

## Checklista
- [ ] Q1–Q6 odpowiedziane z dowodem lub odpowiedzią człowieka
- [ ] rola produktu w każdym akcie nazwana
- [ ] każdy obowiązek: akt, artykuł, od kiedy, data sprawdzenia, źródło, miejsce w kodzie lub procesie
- [ ] [niezweryfikowane] / [wtórne] tam, gdzie brak tekstu aktu; stan transpozycji dyrektyw w PL
- [ ] RODO, AI Act, NIS2/DORA/CRA, EAA przekazane do sąsiednich skilli
- [ ] pytania do prawnika i zadania do backlogu wypisane; zastrzeżenie „nie jest poradą prawną”

## Źródła
Tekstów aktów w EUR-Lex i ISAP nie udało się odczytać w sesji (proxy 403, 2026-10-18); daty i artykuły z komentarzy
kancelarii i serwisów branżowych, dostęp 2026-10-18 — lista w `references/akty-i-obowiazki.md`. Opisane własnymi słowami.
