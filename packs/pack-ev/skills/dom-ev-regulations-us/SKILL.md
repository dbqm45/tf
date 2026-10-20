---
name: dom-ev-regulations-us
description: Użyj przy wymogach USA dla ładowania EV — NEVI (23 CFR 680), uptime 97 %, dane i API, NIST HB44 3.40 (kWh, cena, paragon), J1772, NACS, UL, przepisy stanowe.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy stacja lub CPMS ma spełnić wymogi USA — federalne NEVI 23 CFR part 680 (porty, moc, złącza, płatności, uptime ze wzorem, dane i API, OCPP, OCPI, ISO 15118, cyber, technicy), metrologia NIST Handbook 44 sekcja 3.40 (zakres, wyjątki, rozdzielczość kWh, cena i paragon, tolerancje), co to znaczy dla oprogramowania CPMS, a także SAE J1772, SAE J3400 (NACS), UL 2594, UL 2202 i przepisy stanowe (Kalifornia, Weights and Measures). Nie do unijnych i polskich przepisów (AFIR, MID, UDT, URE — osobne, jeszcze niewydzielone skille), samej płatności kartą i PCI (dom-ev-payments), sprzętu, CP/PWM i licznika od strony hardware (dom-ev-charger-hardware) ani liczenia ceny z taryfy OCPI (dom-ev-tariffs-pricing)."
  slowa: "NEVI, 23 CFR 680, part 680, 680.116, 680.112, FHWA, Joint Office, uptime 97%, 97 procent, dostępność portu, T_outage, T_excluded, 525600, cztery porty DCFC, 150 kW, 6 kW, AC Level 2, CCS1, CHAdeMO, J1772, J3400, NACS, UL 2594, UL 2202, ENERGY STAR, NRTL, EVITP, kwartalne dane, raport do stanu, dane dla stron trzecich, Handbook 44, HB44, NIST 3.40, NTEP, Weights and Measures, kWh rozdzielczość, paragon, receipt, cena w dolarach za kWh, Kalifornia, California, stan USA, dofinansowanie federalne, przepisy USA, US regulations"
---

# Przepisy USA dla ładowania EV (NEVI i NIST HB44 3.40)

Skill mapuje wymogi na decyzje w CPMS i sprzęcie. Teksty źródeł czytaj w bazie wiedzy fabryki, nie z pamięci:
- **NEVI** — 23 CFR part 680, **wersja eCFR pobrana 2026-10-20** (`us-nevi`, `.claude/knowledge/us-nevi/doc.txt`).
- **HB44** — NIST Handbook 44, **wydanie 2026**, sekcja 3.40 (`us-nist-hb44`, `.claude/knowledge/us-nist-hb44/doc.txt`).
- `us-afdc`, `us-joint-office` to tylko strony główne — nie źródła wymogów.
Zmiany po 2026-10-20 nie są sprawdzone. Cytuj `§ 680.116(b)` albo `HB44 3.40 S.2.6` z liniami z references.

## Procedura
1. **Ustal, który reżim obowiązuje.** NEVI — tylko projekty finansowane z programu NEVI i inne publicznie dostępne
   ładowarki z funduszy Title 23 (§ 680.100, § 680.102). HB44 3.40 — każde urządzenie, którego wskazanie służy do
   sprzedaży energii jako paliwa; moc prawną daje dopiero przepis stanu (zob. „Stany”). Stacja prywatna bez dotacji
   może podlegać tylko HB44 i prawu stanowemu.
2. **Wskaż paragraf i cytat.** Odpowiadaj numerem (`§ 680.106(d)(1)`, `S.1.3.2`). Brak w tekście = nie wymyślaj.
3. **Rozdziel „musi” od „should/may”.** Np. certyfikat UL i PCI DSS to „should”, a NRTL i ENERGY STAR (AC L2) to „must”.
4. **Przełóż na CPMS** (sekcja niżej) i wskaż, kto dowodzi spełnienia: stan, operator stacji, dostawca sieci.
5. **Oznacz, czego nie sprawdzono** (stany, normy płatne): **[do weryfikacji]** z id rejestru.

## NEVI — wymogi stacji (§ 680.106 i § 680.114, wg tekstu)
| Temat | Wymóg | Paragraf |
|---|---|---|
| Liczba portów | min. 4 podłączone do sieci porty DCFC, ładujące jednocześnie 4 EV (przy korytarzach AFC); poza korytarzami 4 porty DCFC i/lub AC L2 | 680.106(b) |
| Złącza | DCFC: na stałe CCS Type 1 (ładuje każdy pojazd CCS); CHAdeMO dodatkowo tylko z funduszy FY2022; AC L2: na stałe J1772 | 680.106(c) |
| Moc DCFC | napięcie wyjściowe 250–920 V DC; przy AFC ciągle ≥150 kW na każdy port jednocześnie; dzielenie mocy dozwolone, o ile port spełnia żądanie pojazdu do 150 kW | 680.106(d)(1) |
| Moc AC L2 | ≥6 kW ciągłej mocy na port, jednocześnie na wszystkich; zarządzanie mocą dozwolone, jeśli klient nie zgodzi się na mniej | 680.106(d)(2) |
| Dostępność | AFC: 24/7 przez cały rok; poza AFC: co najmniej w godzinach pracy gospodarza; przerwy na serwis dozwolone | 680.106(e) |
| Płatności | (gdy nie za darmo) bezpieczna płatność dostępna dla niepełnosprawnych: bezstykowa karta debetowa/kredytowa plus bezpłatny numer telefonu **albo** SMS; bez członkostwa; bez ograniczania mocy zależnie od metody płatności; dostęp dla osób o ograniczonej znajomości angielskiego | 680.106(f) |
| Certyfikacja | wszystkie ładowarki: NRTL (OSHA); AC L2: ENERGY STAR; normy UL — „should” | 680.106(g) |
| Bezpieczeństwo | strategie fizyczne i cyber zgodne z planem stanu; cyber m.in. IAM, crypto agility i wiele PKI, monitoring, incydenty, aktualizacje, testy strony trzeciej | 680.106(h) |
| Utrzymanie | zgodność z częścią 680 przez ≥5 lat od pierwszego uruchomienia | 680.106(i) |
| Technicy | elektrycy: EVITP albo zarejestrowany staż z kursem ładowarek; przy kilku — min. jeden certyfikowany i jeden w stażu | 680.106(j) |
| Obsługa i prywatność | zgłaszanie awarii wielojęzyczne i zgodne z ADA (k); tylko dane niezbędne do usługi, PCI DSS „should” (l) | 680.106(k), (l) |
| Łączność | bezpieczny kanał; zdalne aktualizacje oprogramowania; monitoring, diagnostyka, sterowanie, smart charge management; bezpieczny pomiar i raport energii, mocy, statusu portu w czasie rzeczywistym, ceny w czasie rzeczywistym i historii uptime | 680.114(a) |
| Utrata sieci | ładowarka nadal rozpoczyna i kończy sesje z minimalną mocą z 680.106(d) | 680.114(e) |
| Sieć–sieć, sieć–energetyka | jedna identyfikacja kierowcy w wielu sieciach (OCPI); bezpieczna komunikacja z zakładem energetycznym lub EMS | 680.114(c), (d) |

## NEVI — interoperacyjność (§ 680.108)
| Warstwa | Wymóg wg tekstu |
|---|---|
| Pojazd–ładowarka | zgodność z ISO 15118-3; sprzęt zdolny do ISO 15118-2 i -20; do 2024-02-28 oprogramowanie zgodne z ISO 15118-2 i zdolne do Plug & Charge; testy wg ISO 15118-4 (oprogramowanie) i -5 (sprzęt) |
| Ładowarka–sieć | OCPP 1.6J „lub nowszy”; do 2024-02-28 zgodność z OCPP 2.0.1 |
| Sieć–sieć | do 2024-02-28 zdolność komunikacji wg OCPI 2.2.1 |
| Zmiana operatora | ładowarka przełącza dostawcę sieci bez zmian w sprzęcie (680.108(d)) |

Terminy z tekstu już minęły (dziś 2026-10-20); tekst nie mówi, czy sprzęt 1.6J pozostaje zgodny —
to pytanie prawne, **[do weryfikacji]** u FHWA lub stanu. Szczegóły protokołów:
dom-ev-ocpp-16, dom-ev-ocpp-2x, dom-ev-ocpi; P&C: dom-ev-charging.

## NEVI — uptime (§ 680.116(b))
Port ma średnioroczny uptime **powyżej 97 %**. Port jest „up”, gdy sprzęt i oprogramowanie są online i dostępne albo
w użyciu **i** port faktycznie dostarcza energię z mocą minimalną z 680.106(d). Liczy się co miesiąc za poprzednie 12 miesięcy:

`µ = ((525 600 − (T_outage − T_excluded)) / 525 600) × 100`

`T_outage` = minuty awarii w roku, `T_excluded` = minuty awarii z przyczyn poza kontrolą operatora, **jeśli operator
udowodni**, że port byłby sprawny: przerwy w dostawie od zakładu energetycznego, wina pojazdu, planowany serwis,
wandalizm, klęska żywiołowa; wyłączone są też godziny poza deklarowanymi godzinami pracy. 525 600 = minuty w roku 365-dniowym.
Limit: 3 % z 525 600 to 15 768 min (ok. 10,95 doby) niewyłączonej awarii na port rocznie.

## NEVI — dane (§ 680.112 i § 680.116(c))
| Rodzaj | Zawartość | Paragraf |
|---|---|---|
| Kwartalnie do FHWA (przez stan) | id stacji i portu (te same co w API), start, koniec i kody błędów sesji nieudanych, kWh, szczytowa moc sesji, metoda płatności, uptime/T_outage/T_excluded za 3 mies., czas trwania każdej awarii | 680.112(a) |
| Rocznie do 1 marca (od 2024) | koszt utrzymania i napraw stacji; udział w programach certyfikacji firm | 680.112(b) |
| Jednorazowo (AFC) | operator, zasoby DER, koszty nabycia i przyłączenia | 680.112(c) |
| API dla deweloperów, bezpłatnie | id, adres, współrzędne, operator, dostawca sieci, status stacji, dostęp, porty (liczba, id, złącza, poziom, moc kW, pull-through, status w czasie rzeczywistym wg OCPI 2.2.1), struktura ceny, cena w czasie rzeczywistym wg OCPI 2.2.1, metody płatności | 680.116(c) |

Dane publiczne FHWA są agregowane i anonimizowane. Stacja i port mają w raportach **te same identyfikatory** co w API
(680.112(a)(1)–(2)); formaty: dom-ev-identifiers.

## NEVI — cena (§ 680.116(a))
Cena przed startem sesji, w **$/kWh**; to cena bieżąca; cena z chwili startu **nie zmienia się w trakcie sesji**; struktura
z dodatkowymi opłatami ma być jasno pokazana i wyjaśniona. Taryfa OCPI i liczenie ceny: dom-ev-tariffs-pricing.

## NIST HB44 3.40 — skrót (wydanie 2026)
Szczegóły z numerami linii: `references/hb44-3-40.md`. HB44 to kod wzorcowy; w stanie wiąże po przyjęciu.
| Temat | Wymóg wg tekstu | Pozycja |
|---|---|---|
| Zakres | urządzenia mierzące energię sprzedaną jako paliwo pojazdu, gdy ilość lub opłata zależy od pomiaru | A.1 |
| Wyjątki | liczniki zakładu energetycznego (nadzór PUC); EVSE bez wpływu ilości na opłatę; sprzedaż hurtowa | A.2 |
| NTEP | tylko EVSE zgodne z kodem i z certyfikatem NRTL | A.4 |
| Wskazanie | typ obliczający: kWh, cena jednostkowa, suma; wskazanie ≥15 s przy aktywacji, na starcie i końcu | S.1.1, S.1.2 |
| Rozdzielczość | jednostka kWh; najmniejszy krok AC ≤0,0001 kWh, DC ≤0,001 kWh | S.1.3 |
| Cena | suma liczona z ilości ≤0,01 kWh; cena jednostkowa na każdej stronie | S.2.5.1, S.2.4.1 |
| Zmiana ceny | wybór ceny przed dostawą; bez zmiany w trakcie, chyba że klient zatwierdził zmienną strukturę przed sprzedażą | S.2.4.3 |
| Paragon (druk lub elektroniczny) | kWh, cena energii, cena jednostkowa, fazy przy wielu cenach, moc maks. i rodzaj prądu, opłaty dodatkowe, suma, unikalny nr EVSE, nazwa i adres firmy | S.2.6, UR.3.3 |
| Utrata zasilania | dane transakcji dostępne (EVSE, konsola, internet na miejscu, telefon bezpłatny) albo bez opłaty; kWh i ceny zapisane | S.2.3 |
| Pamięć | dane niezmienne, odtwarzalne ≥3 lata; plomba lub audit trail | S.3.4, S.3.3 |
| Tolerancje | AC i DC (po 2025): odbiorcza 1,0 %, eksploatacyjna 2,0 %; DC starsze niż 2025 oznaczone Class 5: 5,0 % do 2034-01-01 | T.2 |
| Terminy przejściowe | DC uruchomione przed 2025-01-01 mają odroczenia do 2028-01-01 (wskazanie dostawy, test terenowy, tolerancje) | S.2.7, N.3.3, T.2.2 |

## Co to znaczy dla CPMS
| Obszar | Reguła |
|---|---|
| Identyfikatory | jedno id stacji i portu w OCPI, API publicznym i raporcie kwartalnym |
| Uptime | zapisuj zdarzenia awarii z czasem, przyczyną i dowodem (zakład energetyczny, serwis planowy, wandalizm); licz µ na port co miesiąc w oknie 12 mies.; godziny pracy w danych stacji; sam status „Available” nie dowodzi „up” — port musi też dostarczać moc [założenie: wnioskuj z transakcji i telemetrii] |
| Raport kwartalny | per sesja: start, koniec, kod błędu, kWh, peak kW, płatność; per port uptime, T_outage, T_excluded, czas awarii |
| Cena w aplikacji | $/kWh przed startem, cena stała w sesji; dopłaty czasowe oddzielone od energii; aplikacja nie zaokrągla po swojemu — pokazuje wartości z EVSE i licznika; czy ekran aplikacji jest „wskazaniem” HB44, rozstrzyga organ stanowy **[do weryfikacji]** |
| Paragon | pola z S.2.6 także w e-mailu lub aplikacji; przy wielu cenach — fazy z czasem i kWh |
| Offline | stacja ładuje po utracie sieci (680.114(e)); po powrocie uzgodnij sesje z licznikiem |
| Prywatność | tylko dane niezbędne (680.106(l)); anonimizacja przed eksportem publicznym |
| Aktualizacje i dowody | zdalna bezpieczna aktualizacja i monitoring to wymóg (680.114(a)); stan zbiera dane od operatora, więc CPMS je eksportuje |

## Przykład
Port: 20 000 min awarii, w tym 6 000 min przerwy zasilania i serwisu planowego. Spełnia 97 %?
`µ = ((525 600 − (20 000 − 6 000)) / 525 600) × 100 = 511 600 / 525 600 × 100 ≈ 97,34 %` → **spełnia** (>97 %),
o ile operator udowodni wyłączenia. Bez wyłączeń: 505 600 / 525 600 ≈ 96,19 % → **nie spełnia** (§ 680.116(b)(3)).

## Stany, SAE i UL (bez tekstu w bazie)
Szczegóły: `references/normy-i-stany.md`. NEVI wymaga na stałe CCS1 i J1772; J3400 (NACS) w części 680 nie występuje —
wykładnia i treść norm **[do weryfikacji]** (`sae-j3400`, niepobrane; J1772 bez id w rejestrze). Normy UL 2594 i UL 2202
(NEVI mówi tylko o „odpowiednich normach UL”, „should”) oraz prawo stanów (Kalifornia, Weights and Measures,
przyjęcie HB44 3.40): **[do weryfikacji]**, brak id w rejestrze. Wymogi stanowe traktuj jako możliwe, nie potwierdzone.

## Pułapki
- „Uptime 97 %” bez wzoru: liczy się per port, rok kroczący, wyłączenia wymagają dowodu.
- „Available” w OCPP/OCPI jako dowód uptime: tekst wymaga też dostarczania mocy minimalnej.
- Cena dynamiczna w sesji: 680.116(a)(2) zabrania zmiany ceny ze startu; HB44 dopuszcza tylko strukturę zatwierdzoną przez klienta przed sprzedażą.
- Odroczenia HB44 do 2028-01-01 i Class 5 dotyczą tylko DC sprzed 2025.
- Rozdzielczość: AC krok 0,0001 kWh (0,1 Wh), DC 0,001 kWh (1 Wh); zaokrąglanie do pełnych Wh nie spełni AC.
- Płatności: bezstykowa karta plus SMS albo bezpłatny telefon; samo QR i aplikacja nie wystarczą (680.106(f)).
- Wymogi UE (MID, Eichrecht, AFIR) to inne reżimy; nie przenoś ich liczb.

## Checklista
- [ ] Reżim ustalony (NEVI, HB44, stan); wersja: eCFR pobrane 2026-10-20, HB44 wydanie 2026.
- [ ] Każde twierdzenie ma paragraf; „should” odróżnione od „must”; uptime wzorem z 680.116(b)(3).
- [ ] Identyfikatory stacji i portu jednolite w API i raportach.
- [ ] Cena w $/kWh przed sesją, stała w sesji; paragon z polami S.2.6.
- [ ] Normy SAE/UL i prawo stanowe oznaczone **[do weryfikacji]** z id rejestru.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/nevi-680.md` | trzeba cytatu z paragrafem i numerem linii `doc.txt` (definicje, § 680.106–680.116) |
| `references/hb44-3-40.md` | trzeba pozycji HB44 3.40 z liniami (testy AC i DC, plomby, oznaczenia) |
| `references/normy-i-stany.md` | pytanie o J1772, J3400, UL 2594/2202, Kalifornię lub Weights and Measures |

## Źródła
- `us-nevi`: 23 CFR part 680, eCFR (ecfr.gov, `.claude/knowledge/us-nevi/doc.txt`, wersja bieżąca, pobrane 2026-10-20).
- `us-nist-hb44`: NIST Handbook 44 (2026), sekcja 3.40 (nist.gov/document/2026-nist-handbook-44-section-340, pobrane 2026-10-20).
- `us-afdc`, `us-joint-office`: strony główne, pobrane 2026-10-20.
- `sae-j3400`: karta normy, niepobrana; J1772, UL, przepisy stanowe — brak w rejestrze.
