---
name: sec-risk-management
description: Użyj przy rejestrze ryzyk bezpieczeństwa, akceptacji ryzyka, ryzyku dostawcy, FAIR lub ISO 27005 — proces, apetyt, postępowanie, KRI.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy firma prowadzi organizacyjny proces ryzyka bezpieczeństwa informacji — kontekst i kryteria (ISO/IEC 27005:2022), identyfikacja wg aktywów lub scenariuszy, analiza jakościowa (macierz) i ilościowa (FAIR: częstotliwość zdarzeń strat × wielkość straty, przedziały, Monte Carlo), apetyt i tolerancja na ryzyko, opcje postępowania (modyfikacja, utrzymanie z właścicielem i terminem, unikanie, podział i ubezpieczenie cyber), rejestr ryzyk, ryzyko dostawców (kwestionariusze, raporty SOC 2, klauzule umowne, monitoring), zarządzanie akceptacją ryzyka, raportowanie KRI. Wynik: szablon rejestru ryzyk i zapis akceptacji ryzyka. Nie do modelu zagrożeń funkcji i oceny projektu (arch-threat-modeling), ram i audytów (sec-governance-compliance), ryzyk projektu (proc-project-planning) ani obsługi incydentu (ops-security-operations). Nie jest poradą prawną ani ubezpieczeniową."
  slowa: "ryzyko bezpieczeństwa, rejestr ryzyk, akceptacja ryzyka, apetyt na ryzyko, tolerancja ryzyka, ISO 27005, analiza ryzyka, ocena ryzyka, ryzyko rezydualne, plan postępowania z ryzykiem, FAIR, ryzyko ilościowe, macierz ryzyka, KRI, ryzyko dostawcy, ocena dostawcy, vendor risk, due diligence, ankieta bezpieczeństwa dostawcy, ubezpieczenie cyber, polisa cyber, wyjątek od polityki, ile możemy stracić, właściciel ryzyka"
---

# Zarządzanie ryzykiem bezpieczeństwa informacji

**Rola agenta:** przygotowuje kryteria, rejestr, analizy, warianty postępowania i projekty zapisów. **Akceptację ryzyka,
apetyt i zakup polisy decyduje człowiek** (właściciel ryzyka, zarząd); to nie jest porada prawna ani ubezpieczeniowa.
Granice: model zagrożeń konkretnej funkcji i ocena jej projektu — **arch-threat-modeling** (stamtąd bierzesz
zagrożenia jako wejście do rejestru); ramy, SoA i audyty — **sec-governance-compliance**; ryzyka projektu (termin,
budżet) — **proc-project-planning**; incydent w toku — **ops-security-operations**. Artefakt:
`docs/project/04-architecture/risk-register.md` (core-project-record).

## Proces (wg ISO/IEC 27005:2022, zgodny z ISO 31000)
Kontekst → ocena ryzyka (identyfikacja, analiza, ewaluacja) → postępowanie → akceptacja ryzyka rezydualnego →
komunikacja → monitorowanie i przegląd. Proces jest cykliczny; wejście do SoA w ISO 27001.

1. **Kontekst i kryteria.** Zakres, aktywa i właściciele, ograniczenia prawne i umowne. Zapisz **przed oceną**:
   skale prawdopodobieństwa i wpływu (z progami w zł, np. wpływ 3 = strata 100–500 tys. zł [przykład]),
   **apetyt** (ile ryzyka firma chce nieść w dążeniu do celów, np. „brak ryzyka krytycznego bez planu”) i **tolerancję**
   (dopuszczalne odchylenie, próg eskalacji). Kryteria zatwierdza zarząd; bez nich oceny są nieporównywalne.
2. **Identyfikacja.** Dwa podejścia, często łączone:
   - **wg aktywów** — aktywo × zagrożenie × podatność; kompletne, ale żmudne; dobre dla zakresu ISO 27001;
   - **wg scenariuszy** — „kto/co → zdarzenie → skutek” (ransomware w produkcji, kompromitacja konta dostawcy);
     szybsze i zrozumiałe dla zarządu; dobre dla FAIR.
   Źródła: modele zagrożeń, wyniki audytów i testów, incydenty, ryzyka dostawców, zmiany w biznesie. Zapis: przyczyna →
   zdarzenie → skutek, nie „brak patchowania”.
3. **Analiza.** Domyślnie **jakościowo**: macierz (np. 5×5) z jawnymi skalami z kroku 1. **Ilościowo (FAIR)** dla ryzyk
   najwyższych i decyzji budżetowych: ryzyko = **częstotliwość zdarzeń strat × wielkość straty**; oba czynniki jako
   **przedziały** (min, najbardziej prawdopodobna, max) z kalibrowanych ocen ekspertów i danych; **symulacja Monte
   Carlo** daje rozkład rocznej straty (np. mediana i P90). Rozkład porównujesz z kosztem kontroli i apetytem;
   wynik symulacji po wdrożeniu kontroli to **ryzyko rezydualne** — nazwij je tak w raporcie.
   Macierzy nie zastępujesz całkiem: liczysz tylko wybrane scenariusze. Szczegóły: `references/analiza-i-postepowanie.md`.
4. **Ewaluacja.** Porównaj ryzyko z kryteriami: ponad tolerancję → postępowanie obowiązkowe; w granicach apetytu → można
   utrzymać. Rankinguj; ryzyka tej samej klasy grupuj, żeby rejestr nie rósł w setki wierszy.
5. **Postępowanie** — jedna z opcji (nazwy z ISO 27005:2022):
   | Opcja | Co | Warunek |
   |---|---|---|
   | modyfikacja (mitygacja) | kontrola obniża prawdopodobieństwo lub skutek | zadanie, termin, test skuteczności |
   | utrzymanie (akceptacja) | świadoma zgoda na ryzyko | właściciel, uzasadnienie, **data wygaśnięcia**, zapis |
   | unikanie | rezygnacja z działania lub funkcji | decyzja biznesowa |
   | podział (transfer) | dostawca, umowa, **ubezpieczenie cyber** | przenosi skutek finansowy, nie odpowiedzialność ani szkodę reputacyjną |
   Po wyborze policz **ryzyko rezydualne** i zapisz je osobno.
6. **Akceptacja ryzyka.** Tylko właściciel ryzyka z uprawnieniami adekwatnymi do poziomu (np. średnie — kierownik
   obszaru, wysokie — dyrektor, krytyczne — zarząd). Nie akceptuje ryzyka ten, kto je tworzy ani zespół bezpieczeństwa
   za biznes. Ryzyka ponad tolerancję nie akceptuje się podpisem: wymaga postępowania albo decyzji zarządu o zmianie
   tolerancji. Akceptacja jest **czasowa** (zwykle ≤12 mies. [przykład]), z warunkami kompensującymi i wyzwalaczem
   przeglądu (zmiana zakresu, incydent). Wzór: `references/rejestr-i-akceptacja.md`.
7. **Ryzyko dostawców** (trzecich stron). Tiering wg dostępu do danych i krytyczności; due diligence proporcjonalne:
   kwestionariusz, raport **SOC 2 typu II** lub certyfikat ISO 27001 (sprawdź zakres, okres, wyjątki i kontrole
   uzupełniające użytkownika), testy dowodowe; klauzule umowne (zgłaszanie incydentów w terminie, prawo do audytu,
   podwykonawcy, zwrot i usunięcie danych, wymogi bezpieczeństwa); **monitoring ciągły** (przegląd raportów rocznie,
   zmiany właściciela, incydenty w mediach). Dane osobowe → umowa powierzenia (arch-privacy-compliance). Szczegóły:
   `references/ryzyko-dostawcow.md`.
8. **Monitorowanie i KRI.** Wskaźniki wczesnego ostrzegania z progami i właścicielem, np. odsetek krytycznych podatności
   po terminie, wyjątki bez ważnej akceptacji, dostawcy tier 1 bez aktualnej oceny, czas odtworzenia vs cel. Raport dla zarządu
   kwartalnie: najwyższe ryzyka, zmiany, akceptacje wygasające, trend KRI, decyzje do podjęcia.

## Przykład
Wejście: „Stary panel partnerów nie ma MFA; wdrożenie za 5 miesięcy. Dyrektor sprzedaży chce zaakceptować ryzyko.”

Wynik (zapis akceptacji, fragment) [przykład]:
- R-017: przejęcie konta partnera → wyciek zamówień klientów. Inherentne: P4 × W4 = 16 (wysokie).
- Opcja: modyfikacja (MFA do 2027-03-31) + utrzymanie przejściowe. Kontrole kompensujące: limit prób, alert na nowe urządzenie,
  odcięcie eksportu masowego. Rezydualne: P3 × W3 = 9 (średnie).
- Akceptuje: dyrektor sprzedaży (właściciel procesu, uprawniony do ryzyk średnich). Ważne do 2027-03-31; wcześniej
  przegląd po każdym incydencie na koncie partnera. Informowani: CISO, dział prawny.
- Sprzeciw bezpieczeństwa: brak; gdyby rezydualne było wysokie, decyzja idzie do zarządu.

## Checklista
- [ ] kryteria, apetyt i tolerancja zatwierdzone przed oceną
- [ ] ryzyko jako przyczyna → zdarzenie → skutek; źródła: modele zagrożeń, audyty, dostawcy
- [ ] skale z progami; FAIR tylko dla wybranych scenariuszy, z przedziałami
- [ ] każde ryzyko ponad tolerancję ma opcję postępowania, zadanie i termin
- [ ] ryzyko rezydualne zapisane osobno
- [ ] akceptacja: właściciel z uprawnieniami, uzasadnienie, data wygaśnięcia, warunki
- [ ] dostawcy z tierem, dowodami (SOC 2/ISO: zakres i wyjątki) i klauzulami
- [ ] KRI z progami; raport kwartalny dla zarządu

## Materiały dodatkowe
- `references/rejestr-i-akceptacja.md` — szablon rejestru ryzyk (pola), zapis akceptacji, uprawnienia; czytaj przy tworzeniu `risk-register.md`.
- `references/analiza-i-postepowanie.md` — skale, FAIR krok po kroku, ubezpieczenie cyber, KRI; czytaj przy analizie ilościowej i raporcie.
- `references/ryzyko-dostawcow.md` — tiering, kwestionariusz, czytanie raportu SOC 2, klauzule, monitoring; czytaj przy ocenie dostawcy.

## Źródła
- ISO/IEC 27005:2022 *Information security risk management* (październik 2022; dodaje akceptację ryzyka rezydualnego,
  zgodna z ISO/IEC 27001:2022 i ISO 31000:2018) — iso.org; wg źródeł wtórnych (PECB, EVS), dostęp 2026-10-17 [niezweryfikowane u źródła].
- FAIR — The Open Group, Open FAIR O-RT i O-RA; J. Freund, J. Jones, *Measuring and Managing Information Risk* (2014); wg źródeł wtórnych, dostęp 2026-10-17.
- AICPA, Trust Services Criteria (2017, punkty uwagi 2022) — wg źródeł wtórnych, dostęp 2026-10-17.
Opisane własnymi słowami; nie jest poradą prawną.
