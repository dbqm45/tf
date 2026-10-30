---
name: dom-ev-fleet-charging
description: Użyj przy ładowaniu floty, w domu pracownika, w pracy i dla klientów B2B — karta flotowa, zwrot za prąd, ładowarki za szlabanem, ładowanie za darmo, centra kosztów.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy klientem nie jest kierowca ad hoc, tylko organizacja — flota z kartami (karta na kierowcę czy na auto, polityki, limity, raport per auto, kierowca i centrum kosztów), zamawianie ładowarki domowej dla pracownika i zwrot kosztów energii (licznik, stawka, oddzielenie sesji służbowych od prywatnych, RODO, lista płac), ładowarki firmowe za szlabanem z grupami uprawnionych, darmowe ładowanie klientów B2B (taryfa zerowa, a nie brak CDR), podział kosztów między najemców, EPBD i polskie przepisy o budynkach, model danych organizacja – centrum kosztów – kierowca – token – auto i uprawnienia tokenu do lokalizacji. Nie do platformy eMSP i aplikacji (dom-ev-emsp-platform), budowy taryfy (dom-ev-tariffs-pricing), mocy zajezdni i DLM (dom-ev-energy-management) ani profili ładowania (dom-ev-smart-charging)."
  slowa: "flota, karta flotowa, fleet card, kierowca floty, centrum kosztów, cost center, raport kosztów ładowania, polityka ładowania floty, limit miesięczny, ładowanie domowe pracownika, wallbox pracownika, zwrot kosztów prądu, zwrot za ładowanie w domu, ryczałt za prąd, ładowanie w pracy, parking firmowy, za szlabanem, goście, klienci B2B, darmowe ładowanie, ładowanie za darmo, taryfa zerowa, free of charge, najemcy, podział kosztów energii, lista płac, auto służbowe, company car, home charging, workplace charging, reimbursement, RODO dane domowe, telematyka floty, whitelist tokenów, token do lokalizacji, EPBD parking, punkty ładowania w budynku"
---

# Ładowanie floty, domu pracownika, pracy i B2B

Skill dotyczy klientów **zorganizowanych**: ktoś płaci za wielu kierowców, a koszt trzeba przypisać do auta,
osoby lub centrum kosztów. Klucz do wszystkiego jest jeden: **token identyfikuje kierowcę lub nośnik, a nie
koszt**. Koszt przypisuje model danych (niżej), a sesja zawsze zostaje zapisana — także darmowa.

## Procedura
1. Ustal **segment** i **kto płaci**: flota (publiczna sieć + depot), dom pracownika, parking firmowy, klient B2B.
2. Ustal **jednostkę rozliczenia**: auto, kierowca, centrum kosztów, najemca (tabela „Dwie osie”).
3. Zamodeluj **organizację → centrum kosztów → kierowca → token → auto** (`references/model-danych-i-uprawnienia.md`).
4. Ustal **uprawnienia**: gdzie, kiedy, ile (polityka) i jak wymusza je CSMS (whitelist, `AuthorizationInfo`).
5. Każda sesja daje CDR, także z kosztem 0; wyłączenie z rozliczenia robi **taryfa zerowa**, nie brak rekordu.
6. Raport: sesje → przypisanie token→auto→centrum kosztów **na datę sesji** → agregacja → eksport (CSV, płace).

## Dwie osie, których nie mieszaj
| Oś | Pytanie | Przykład |
|---|---|---|
| Kto **autoryzuje** | jaki token i gdzie wolno mu ładować | karta RFID kierowcy ważna na lokalizacjach A, B |
| Komu **przypisać koszt** | auto, kierowca, centrum kosztów, najemca | sesja kierowcy X na aucie Y, centrum „Sprzedaż” |
| Kto **płaci** | flota, pracownik, klient B2B, najemca | faktura zbiorcza floty; zwrot pracownikowi |

## 1. Floty
**Karta na kierowcę czy na auto:**
| Model | Zalety | Wady | Kiedy |
|---|---|---|---|
| Karta na **kierowcę** (osobowy token) | wiadomo, kto ładował; blokada przy odejściu pracownika | auto współdzielone → koszt trzeba przypisać do auta osobno | samochody przypisane, polityka „firma płaci, pracownik odpowiada” |
| Karta na **auto** | koszt per auto bez dodatkowej logiki; auto pool | nie wiadomo, kto ładował; karta zostaje w aucie → ryzyko nadużyć | pule aut, auta techniczne, leasing krótkoterminowy |
| **Obie** (kierowca + auto z okresem przypisania) | pełny raport per auto i per kierowca | najwięcej administracji | floty średnie i duże; zalecany domyślny wybór |

Reguła: token wskazuje nośnik, a **przypisanie token → auto i kierowca → auto ma okres ważności** (od–do), bo auta
zmieniają kierowców. Raport łączy sesję z przypisaniem obowiązującym w chwili startu, nie z dzisiejszym.

**Polityki** (definiuje flota, wymusza CSMS/eMSP): lokalizacje dozwolone lub zakazane (np. tylko własne depo i sieć
publiczna bez ładowarek ultraszybkich), godziny, limit miesięczny kWh lub kwoty, limit na sesję, zakaz ładowania
po zakończeniu pracy poza domem, blokada po zgłoszeniu kradzieży karty. Limity kwotowe wymagają kosztu sesji w
czasie sesji — to praca eMSP (dom-ev-emsp-platform); CPO wymusza tylko lokalizację i ważność tokenu.

**Raport kosztów:** wiersz = sesja (czas, lokalizacja, kWh, koszt netto i brutto, token, auto, kierowca, centrum
kosztów); agregaty per auto (koszt na 100 km — wymaga przebiegu), per kierowca, per centrum kosztów, per miesiąc;
osobno ładowanie publiczne, depo i dom. Pułapka: kierowca ładuje w kilku miejscach — porównuj **koszt na kWh i
na 100 km**, nie samą kwotę.

**Telematyka:** przebieg i SoC z API producenta lub z dongla uzupełniają raport (zużycie kWh/100 km, wykrycie
ładowania poza polityką). SoC i krzywa ładowania to temat dom-ev-vehicle-battery. Zgody kierowcy na dane lokalizacyjne:
`references/ladowanie-domowe-zwrot.md` (sekcja RODO). **Zajezdnie:** moc, DLM i plan ładowania pod limit przyłącza —
dom-ev-energy-management i dom-ev-smart-charging; działający przykład `examples/depot-smart-charging/`.

## 2. Ładowanie domowe pracownika
Dwa niezależne procesy: **zamówienie ładowarki** i **zwrot kosztów energii**.

**Zamówienie ładowarki (kolejność):** kwalifikacja (pracownik, auto służbowe, tytuł do garażu — własny dom, najem,
wspólnota) → **audyt instalacji** (zabezpieczenie przedlicznikowe, liczba faz, przekrój i długość przewodu, rozdzielnica,
zasięg Wi-Fi/LTE) → zgoda właściciela lub wspólnoty, jeśli wymagana → montaż przez uprawnionego elektryka z protokołem
pomiarów → uruchomienie (konfiguracja OCPP, `BootNotification`, test sesji) → **podłączenie do CSMS** i przypisanie
do pracownika → szkolenie i umowa użyczenia. Wymogi różnią się w krajach (zgłoszenie do OSD, wymogi dla liczników,
dopłaty); Dania jako przykład kraju z rozwiniętym rynkiem ładowarek domowych — szczegóły krajowe [do weryfikacji].
W Polsce montaż w budynku wielorodzinnym wymaga zgody zarządu wspólnoty (art. 12b ustawy o elektromobilności,
`references/praca-b2b-budynki.md`).

**Zwrot kosztów energii (decyzje):**
| Decyzja | Opcje | Uwaga |
|---|---|---|
| Pomiar | licznik w ładowarce (MID) | dowód kWh; odsyłacz dom-ev-metering-calibration; telemetria `MeterValues` bez podpisu to szacunek |
| Stawka | taryfa domowa pracownika, ryczałt, cena dynamiczna, średnia ważona | wybór i skutki podatkowe [do weryfikacji w danym kraju]; stawka obowiązuje od daty i jest wersjonowana |
| Zakres | tylko sesje **auta służbowego** | sesje auta prywatnego/partnera nie podlegają zwrotowi |
| Wypłata | przez listę płac lub notę kosztową | eksport: pracownik, okres, kWh, stawka, kwota |

**Oddzielenie sesji służbowych:** ładowarka widzi token, nie auto. Rozwiązania: karta/token **przypisany do auta
służbowego** i autoryzacja tylko nim (reszta — tryb prywatny bez zwrotu), VIN/ISO 15118 (EMAID) tam, gdzie auto to
wspiera, albo potwierdzenie przez pracownika w aplikacji. Sesja bez rozpoznanego tokenu trafia do kolejki „do
potwierdzenia”, a nie do zwrotu automatycznie. Pełny proces, wzór obliczenia i RODO — `references/ladowanie-domowe-zwrot.md`.

## 3. Ładowanie w pracy i B2B
| Grupa | Uprawnienie | Cena |
|---|---|---|
| Pracownicy | token pracownika, godziny pracy | zwykle taryfa wewnętrzna lub zerowa |
| Goście | token tymczasowy lub kod z recepcji, czas ważności | taryfa gościa |
| Klienci B2B | token klienta wydany pod umowę | taryfa zerowa lub preferencyjna |
| Publiczni (poza godzinami) | ad hoc | taryfa publiczna |

**Darmowe ładowanie B2B — taryfa zerowa, nie wyłączenie z rozliczenia.** Sesja nadal ma CDR z `total_cost` = 0 i
taryfą „Free of Charge” (jeden element `FLAT` z ceną 0.00 wg OCPI), bo na tych rekordach działają: raport zużycia
energii per klient, rozliczenie z hostem, koszt energii do zafakturowania w umowie, kontrola nadużyć, KPI i dowód
dla audytu. Brak rekordu = brak danych. Cennik: dom-ev-tariffs-pricing; CDR: dom-ev-cdr-settlement.

**Podział kosztów między najemców:** źródło prawdy to **licznik ładowarki** (nie licznik główny budynku). Każdy
najemca ma centrum kosztów i grupę tokenów; koszt energii = kWh sesji × cena + udział w kosztach stałych (opłata za
moc, zarządzanie) wg klucza z umowy [klucz do ustalenia z hostem]. Rozdziel koszty zmienne od stałych.

**Przepisy o budynkach:** EPBD (dyrektywa 2024/1275) art. 14 — punkty i pre-okablowanie na parkingach, smart
charging i otwarte protokoły; polska ustawa o elektromobilności art. 12–12b — `references/praca-b2b-budynki.md`.

## Przykład
Wejście: firma ma 30 aut, 24 kierowców, 3 centra kosztów; kierowcy ładują w sieci publicznej i w domu; biuro ma
ładowarki za szlabanem, a klienci B2B ładują tam za darmo.
Wynik:
- Model: organizacja → 3 centra → 24 kierowców → po 1 tokenie na kierowcę (`group_id` firmy) + karta na każde z 6
  aut puli; przypisanie token→auto z okresem od–do.
- Uprawnienia: tokeny floty tylko na lokalizacjach z polityki; goście i klienci B2B — osobne grupy z biała listą
  lokalizacji biura.
- Biuro: taryfa „Free of Charge” (`FLAT` 0.00) dla grupy B2B; każda sesja daje CDR z kosztem 0; raport miesięczny
  zużycia kWh per klient.
- Dom: licznik MID w wallboxie, stawka zwrotu wersjonowana od daty, tylko sesje tokenu auta służbowego; reszta
  „do potwierdzenia”; eksport do płac.
- Raport floty: sesja → przypisanie na dzień startu → koszt per auto, kierowca, centrum; osobno publiczne, depo, dom.

## Pułapki
- Karta jako „konto kosztów”: zmiana kierowcy lub auta nie może przepisywać historii — przypisania mają okresy.
- Wyłączenie darmowych sesji z CDR: znika raport zużycia i rozliczenie z hostem; używaj taryfy zerowej.
- Zwrot z licznika całego domu zamiast licznika ładowarki albo z sesji auta prywatnego.
- Zwrot z telemetrii `MeterValues` bez licznika MID, gdy kwota podlega sporowi lub kontroli.
- Stawka zwrotu bez daty obowiązywania: nie da się odtworzyć wyliczenia za miniony okres.
- Dane domowe (adres, godziny ładowania, położenie auta) zbierane „na zapas” — RODO wymaga celu i minimalizacji.
- Polityka kwotowa wymuszana w CPO bez kosztu w czasie sesji: to funkcja eMSP.
- Wymieszanie mocy zajezdni z polityką floty: limit przyłącza to dom-ev-energy-management.

## Checklista
- [ ] Segment, płatnik i jednostka rozliczenia ustalone (auto, kierowca, centrum kosztów, najemca).
- [ ] Model organizacja → centrum kosztów → kierowca → token → auto z okresami przypisań.
- [ ] Uprawnienia tokenów do lokalizacji (whitelist, `AuthorizationInfo`) i polityki flotowe opisane.
- [ ] Darmowe ładowanie: taryfa zerowa + CDR 0, nie wyłączenie.
- [ ] Dom: audyt instalacji, licznik MID, stawka wersjonowana, rozdzielenie sesji służbowych/prywatnych, RODO.
- [ ] Budynek: wymogi EPBD i ustawy (art. 12–12b) sprawdzone; podział kosztów między najemców uzgodniony z hostem.
- [ ] Fakty krajowe (Dania, podatki) oznaczone [do weryfikacji].

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/model-danych-i-uprawnienia.md` | projektujesz tabele, whitelist tokenów (OCPI i OCPP 2.x) albo raport |
| `references/ladowanie-domowe-zwrot.md` | zamówienie wallboxa, wzór zwrotu, sesje służbowe/prywatne, RODO, płace |
| `references/praca-b2b-budynki.md` | szlaban, grupy, taryfa zerowa, najemcy, EPBD art. 14, ustawa art. 12–12b |

## Źródła
- OCPI 2.2.1-d2 i 2.3.0, `mod_tokens.asciidoc` (Token, `whitelist`, `AuthorizationInfo`, `AllowedType`), `mod_cdrs.asciidoc`,
  `mod_tariffs.asciidoc` (taryfa Free of Charge), github.com/ocpi/ocpi, pobrane 2026-10-20 (`.claude/knowledge/ocpi-2.2.1-d2/doc.txt`
  L5071-5107, L5128-5145; ocpi-2.3.0/doc.txt L3929-3931).
- OCPP 2.0.1, AuthorizeResponse.json (`IdTokenInfoType`: `evseId`, `groupIdToken`, `cacheExpiryDateTime`), `.claude/knowledge/ocpp-json-schemas/doc.txt` L2769-2823, pobrane 2026-10-20.
- EPBD, dyrektywa (UE) 2024/1275, art. 14 i 16, eur-lex.europa.eu/eli/dir/2024/1275/oj, `.claude/knowledge/eu-epbd/doc.txt`, pobrane 2026-10-20.
- Ustawa o elektromobilności i paliwach alternatywnych, tekst jedn. Dz.U. 2026 poz. 1243, art. 12, 12a, 12b, `.claude/knowledge/pl-elektromobilnosc/doc.txt` L353-412, pobrane 2026-10-20.
- Praktyka branżowa (karty flotowe, zwrot za ładowanie w domu): wiedza ogólna z przeglądu, bez danych rynkowych [do weryfikacji].
