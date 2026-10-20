# NEVI — 23 CFR part 680, mapa paragrafów

Źródło: `us-nevi`, wersja eCFR pobrana 2026-10-20, `.claude/knowledge/us-nevi/doc.txt` (numery linii poniżej).
Opis własnymi słowami; w sporze czytaj oryginał w podanym zakresie linii.

## Spis treści
- Zakres i definicje
- § 680.106 (stacja)
- § 680.108 (interoperacyjność)
- § 680.112 (dane do FHWA)
- § 680.114 (łączność)
- § 680.116 (cena, uptime, API)
- § 680.118 (inne wymogi federalne)

## Zakres i definicje
| Paragraf | Linie | Treść |
|---|---|---|
| 680.100 | L12-14 | cel: minimalne standardy dla projektów NEVI Formula Program i innych publicznie dostępnych ładowarek finansowanych z Title 23 |
| 680.102 | L16-18 | stosowanie do wszystkich takich projektów, o ile nie zaznaczono inaczej |
| 680.104 | L20-78 | definicje, m.in. AC Level 2 (208–240 V), AFC, charging port (jeden EV naraz), charging station, charging station operator (właściciel ładowarek) a charging network provider (operator sieci cyfrowej), DCFC, Plug and Charge (uwierzytelnienie certyfikatami ISO 15118 i płatność bez działań klienta), Power Sharing, Smart charge management, cryptographic agility, contactless payment methods |

Ważne dla CPMS: „charging network provider” to rola, którą pełni CPMS/CSMS; „charging station operator” odpowiada za
utrzymanie nawet przy podwykonawcach (rola CPO: dom-ev-market-roles).

## § 680.106 (L80-162)
| Ustęp | Linie | Sedno |
|---|---|---|
| (a) | L82-94 | jawność procesu zamówień i zasad ustalania ceny: podsumowanie, liczba ofert, wybrany wykonawca, umowa, zestawienie płatności, zasady ustalania cen — obowiązek stanu |
| (b) | L96-100 | ≥4 porty podłączone do sieci i ładujące jednocześnie 4 EV; przy AFC porty DCFC |
| (c) | L102 | złącza zgodne z normami; DCFC: CCS Type 1 na stałe; CHAdeMO tylko z funduszy FY2022; AC L2: J1772 na stałe |
| (d) | L104-108 | DCFC 250–920 V DC; AFC: ≥150 kW ciągle na port; AC L2 ≥6 kW na port; power sharing dozwolone pod warunkiem spełnienia żądania mocy |
| (e) | L110 | AFC całodobowo; inne w godzinach gospodarza; przerwy serwisowe i wyłączenia z 680.116(b)(3) dopuszczone |
| (f) | L112-120 | płatności: bezstykowa karta + (telefon bezpłatny lub SMS); bez członkostwa; bez ograniczania mocy ze względu na metodę płatności; dostęp językowy i dla niepełnosprawnych |
| (g) | L122 | certyfikat NRTL dla wszystkich; ENERGY STAR dla AC L2; normy UL „should” |
| (h) | L124-128 | strategie bezpieczeństwa fizycznego i cyber (wymienione tematy „may”) |
| (i) | L130 | utrzymanie zgodności ≥5 lat |
| (j) | L132-142 | technicy: EVITP lub zarejestrowany staż; zasada min. jednego certyfikowanego i jednego w stażu; pozostali pracownicy wg stanu |
| (k) | L144 | zgłaszanie awarii, wielojęzyczność, ADA |
| (l) | L146 | minimalizacja danych osobowych; PCI DSS „should”; rozsądne zabezpieczenie danych |
| (m) | L148-162 | przychody z eksploatacji wolno przeznaczyć na: obsługę zadłużenia, rozsądny zwrot dla prywatnego inwestora, utrzymanie i eksploatację, rozliczenia PPP, inne cele Title 23 |

## § 680.108 (L164-172)
(a) ISO 15118-3 oraz sprzęt zdolny do -2 i -20; do 2024-02-28 oprogramowanie zgodne z -2 i Plug & Charge; testy -4/-5.
(b) OCPP 1.6J lub nowszy; do 2024-02-28 OCPP 2.0.1. (c) do 2024-02-28 OCPI 2.2.1 między sieciami.
(d) ładowarka bezpiecznie zmienia dostawcę sieci bez zmian sprzętu.

## § 680.112 (L180-220)
| Ustęp | Linie | Dane |
|---|---|---|
| (a) kwartalnie | L182-198 | (1) id stacji, (2) id portu, (3) start/koniec/kody błędów sesji nieudanych per port, (4) kWh per sesja, (5) szczytowa moc sesji, (6) metoda płatności, (7) uptime, T_outage, T_excluded za 3 miesiące, (8) czas trwania awarii w minutach |
| (b) rocznie | L200-204 | od 2024, do 1 marca: koszty utrzymania i napraw; udział w programach certyfikacji firm |
| (c) jednorazowo | L206-218 | AFC: operator, zasoby DER, koszty nabycia i instalacji, koszty przyłącza i rozbudowy sieci |
| (d) | L220 | raport z zaangażowania społeczności w planie stanu (tylko NEVI) |

## § 680.114 (L222-240)
(a)(1)-(4) bezpieczna łączność; zdalne aktualizacje; tłumaczenie protokołów, szyfrowanie i autoryzacja; zdalny monitoring,
diagnostyka, sterowanie i smart charge management po stronie sieci; bezpieczny pomiar, komunikacja, przechowywanie i
raportowanie energii, mocy, statusu portu, ceny w czasie rzeczywistym i historii uptime. (b) odsyła do 680.108.
(c) jedna metoda identyfikacji w wielu sieciach (OCPI). (d) komunikacja z zakładem energetycznym / EMS. (e) działanie przy utracie łączności.

## § 680.116 (L242-312)
| Ustęp | Linie | Sedno |
|---|---|---|
| (a) cena | L244-250 | $/kWh przed startem; cena z chwili startu stała w sesji; struktura opłat wyjaśniona; konwersja na $/kWh w ciągu roku od 2023-02-28 |
| (b) uptime | L252-268 | >97 % średnio rocznie; definicja „up”; liczone miesięcznie za 12 mies.; wzór µ z 525 600; lista wyłączeń T_excluded |
| (c) API | L270-312 | pola udostępniane bezpłatnie: stacja, adres, współrzędne, operator, dostawca sieci, status, dostęp i godziny, porty (liczba, id, złącza, poziom, kW, pull-through, status OCPI 2.2.1), cena (struktura, cena bieżąca wg OCPI 2.2.1), metody płatności |

## § 680.118 (L314-332)
Inne wymogi federalne obowiązujące projekty: 2 CFR 200, Buy America i Build America Buy America, Davis-Bacon (NEVI), ADA
(49 CFR 37, 28 CFR 35 i 36), Title VI, Fair Housing, nie obowiązuje DBE dla NEVI, URA, NEPA. To wymogi kontraktowe stanu —
oprogramowanie ich nie wykonuje, ale dostawca sprzętu i CPMS może je dostać w umowie.
