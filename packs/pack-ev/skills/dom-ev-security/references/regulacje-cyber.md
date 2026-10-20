# Regulacje cyberbezpieczeństwa dla ładowania: NIS2, CRA, NEVI, RED

To nie porada prawna. Mapa wszystkich aktów UE: `dom-ev-regulations-eu` (katalog `.claude/skills/dom-ev-regulations-eu/references/`);
prawo polskie: `dom-ev-regulations-pl`; USA: `dom-ev-regulations-us`. Linie dotyczą `.claude/knowledge/<id>/doc.txt`,
teksty pobrane 2026-10-20.

## 1. NIS2 — dyrektywa (UE) 2022/2555 (`eu-nis2`, EN)
| Pytanie | Odpowiedź wg tekstu | Linie |
|---|---|---|
| Czy CPO jest podmiotem? | Aneks I (sektory o wysokiej krytyczności), pkt 1 Energia, (a) Elektryczność: operatorzy punktu ładowania odpowiedzialni za zarządzanie i działanie punktu świadczącego usługę ładowania użytkownikom końcowym, także w imieniu i na rzecz dostawcy usług mobilności | 4199 |
| Kto podlega? | podmioty typu z Aneksu I lub II będące średnimi przedsiębiorstwami lub większymi; mniejsze tylko w wyjątkach Art. 2(2) | Art. 2: 1892 |
| Kluczowy czy ważny? | kluczowy: Aneks I powyżej progów średniego przedsiębiorstwa; ważny: pozostałe | Art. 3: 2003 |
| Dostawca CSMS, eMSP? | nie wymienieni jako typ w Aneksie I sekcji 1; mogą podlegać przez inny typ (np. dostawca usług zarządzanych) lub jako dostawca dla podmiotu (łańcuch dostaw) — **[do weryfikacji]** | — |
| Zarząd | organ zarządzający zatwierdza środki, nadzoruje wdrożenie i może odpowiadać za naruszenia; szkolenia | Art. 20: 3095 |
| Środki | co najmniej: analiza ryzyka, obsługa incydentów, ciągłość działania i zarządzanie kryzysowe, bezpieczeństwo łańcucha dostaw, bezpieczeństwo nabywania, rozwoju i utrzymania (w tym obsługa i ujawnianie podatności), ocena skuteczności środków, higiena i szkolenia, kryptografia, kadry i kontrola dostępu, MFA | Art. 21(2): 3119 |
| Łańcuch dostaw | uwzględnij podatności dostawców i jakość ich produktów oraz procedur bezpiecznego rozwoju | Art. 21(3) |
| Zgłoszenia | poważny incydent: ostrzeżenie wczesne **do 24 h** od uzyskania wiedzy (czy podejrzenie czynu bezprawnego, skutek transgraniczny); zgłoszenie **do 72 h** (ocena początkowa, dotkliwość, skutek, wskaźniki naruszenia); raport pośredni na żądanie; raport końcowy **do miesiąca** po zgłoszeniu 72 h; przy trwającym incydencie raport postępu, końcowy w miesiąc po obsłużeniu | Art. 23(4): 3219 |
| Poważny incydent | spowodował lub może spowodować poważne zakłócenie usług albo stratę finansową albo znaczną szkodę innych osób | Art. 23(3) |
| Odbiorcy usług | powiadom bez zbędnej zwłoki o poważnym incydencie, który może wpłynąć na usługę; przy zagrożeniu podaj środki zaradcze | Art. 23(1)-(2) |
| Kary | podmioty kluczowe: co najmniej do 10 mln EUR lub 2 % światowego obrotu (wyższa kwota), ważne: co najmniej 7 mln EUR lub 1,4 % | Art. 34: 3936, 3941 |
| Wdrożenie | dyrektywa: obowiązek firmy wynika z ustawy krajowej; transpozycja do 17.10.2024 | Art. 41 |

Przykładowa ocena: CPO ze 150 pracownikami zwykle mieści się w pojęciu średniego przedsiębiorstwa (progi z Zalecenia
2003/361/WE nie są w bazie — **[do weryfikacji]**; powiązania i partnerzy zmieniają liczenie), czyli jest podmiotem ważnym.
Mały CPO może wpaść w wyjątek Art. 2(2) tylko w szczególnych przypadkach. Sprawdź, czy ustawa krajowa nie wprowadza
dodatkowych progów lub rejestracji.

Co przygotować: rejestr incydentów z czasem „uzyskania wiedzy”, kryteria „poważnego incydentu” dla sieci ładowania
(np. utrata dostępności znacznej części floty — próg własny **[do ustalenia z prawnikiem]**), kanał do CSIRT i organu,
szablony ostrzeżenia, zgłoszenia i raportu końcowego, kontakty do dostawców, klauzule bezpieczeństwa w umowach.

## 2. CRA — rozporządzenie (UE) 2024/2847 (`eu-cra`, PL)
| Temat | Wg tekstu | Linie |
|---|---|---|
| Zakres | produkty z elementami cyfrowymi z bezpośrednim lub pośrednim połączeniem z urządzeniem lub siecią; ładowarka z firmware i modułem łączności spełnia opisowo | Art. 2: 1948 |
| Zdalne przetwarzanie danych | część produktu, gdy jest projektowane przez producenta i bez niego produkt nie spełnia funkcji (np. chmura producenta ładowarki, aplikacja) | Art. 3: 2002 |
| CSMS jako SaaS operatora | usługa SaaS jako taka podlega NIS2, nie CRA (motyw dot. zdalnego przetwarzania) — kwalifikację sprawdź per przypadek **[do weryfikacji]** | motyw (12) |
| Obowiązki producenta | ocena ryzyka, staranność przy komponentach obcych, obsługa podatności w okresie wsparcia | Art. 13: 2425 |
| Okres wsparcia | co najmniej pięć lat, chyba że produkt ma być używany krócej | motyw (60): 1021 |
| Zgłaszanie | aktywnie wykorzystywana podatność: wczesne ostrzeżenie **24 h**, zgłoszenie **72 h**, raport końcowy **14 dni** po środku zaradczym; poważny incydent wpływający na bezpieczeństwo produktu: analogicznie; jedna platforma (Art. 16) do CSIRT koordynatora i ENISA | Art. 14: 2637 |
| Wymagania | Aneks I część I (m.in. brak znanych podatności, bezpieczna konfiguracja domyślna, aktualizacje, kontrola dostępu, szyfrowanie, integralność, logowanie), część II (obsługa podatności: SBOM, polityka ujawniania, adres zgłoszeń, bezpłatne poprawki) | Aneks I |
| Terminy | **Art. 14 od 11.09.2026**; rozdział IV od 11.06.2026; całość od **11.12.2027** | Art. 71: 4521 |
| Produkty starsze | wprowadzone przed 11.12.2027: CRA po istotnej modyfikacji, lecz Art. 14 dotyczy wszystkich | Art. 69 |
| Klasa produktu | Aneks III nie wymienia wprost ładowarki ani CSMS; klasyfikacja do ustalenia **[do weryfikacji]** | Aneks III |
Skutek dziś (dla producenta ładowarki lub oprogramowania): proces PSIRT i kanał zgłoszeń podatności działają już teraz,
bo Art. 14 stosuje się od 11.09.2026; CPO jako importer lub dystrybutor ma osobne obowiązki — **[do weryfikacji]**.
CPO jako zamawiający: wpisz do umów SBOM, okres wsparcia i czasy reakcji.

## 3. USA — NEVI, 23 CFR 680 (`us-nevi`)
- **680.106(h) Security** (linie 124-128): stany lub bezpośredni odbiorcy wdrażają strategie bezpieczeństwa fizycznego i
  cyberbezpieczeństwa zgodne z planem wdrożenia, aby operacje stacji chroniły dane konsumentów i ryzyko zakłócenia
  infrastruktury ładowania oraz sieci. Wymieniane tematy cyber (mogą, nie muszą): zarządzanie tożsamością i dostępem,
  zwinność kryptograficzna i wiele PKI, monitorowanie i detekcja, zapobieganie i obsługa incydentów, zarządzanie
  konfiguracją, podatnościami i aktualizacjami, testy i certyfikacja stron trzecich, ciągłość działania przy utracie łączności.
- **680.114(a)** (linie 226-228): komunikacja ładowarka–sieć przez bezpieczną metodę; zdolność do odbioru i wdrożenia
  bezpiecznych zdalnych aktualizacji oprogramowania, uwierzytelnienie i autoryzacja w komunikacji z siecią.
- **680.108** (linie 166-170): OCPP 1.6J lub nowszy (OCPP 2.0.1 w terminach z przepisu), OCPI 2.2.1 między sieciami.
- Sformułowanie „mogą obejmować” oznacza, że lista nie jest zamkniętym wymogiem technicznym; szczegóły ustala plan stanu.
Szczegóły NEVI: `dom-ev-regulations-us` (`.claude/skills/dom-ev-regulations-us/references/nevi-680.md`).

## 4. RED i EN 18031
Rozporządzenie delegowane do RED 2014/53/UE (UE) 2022/30 (cyberbezpieczeństwo urządzeń radiowych, normy EN 18031)
dotyczy ładowarek z radiem (Wi-Fi, LTE, Bluetooth) wprowadzanych do obrotu; po wejściu CRA zastępuje je rozp. 2026/339
(zob. `dom-ev-regulations-eu`). Treści 2022/30 nie ma w bazie — szczegóły **[do weryfikacji]**.

## 5. Kto czego pilnuje
| Rola | NIS2 | CRA | NEVI | RED |
|---|---|---|---|---|
| CPO (operator punktów) | tak, jeśli średni lub większy | jako użytkownik/importer — ocena | przez stan, jeśli fundusze federalne | zwykle nie |
| Dostawca CSMS | możliwy (usługa zarządzana) lub dostawca podmiotu | przy produkcie z elementami cyfrowymi | jako „charging network provider” w wymogach sieci | nie |
| Producent ładowarki | zależnie od kodu działalności [założenie] | tak | certyfikacja i funkcje wg 680 | tak (radio) |

## 6. Co jest poza bazą
Progi MŚP (2003/361/WE), tekst rozp. 2022/30, ustawy krajowe transponujące NIS2 (w Polsce: sprawdź `dom-ev-regulations-pl`),
standardy ISO 27001, IEC 62443, ETSI EN 303 645 — wymień jako odniesienia **[do weryfikacji]**, nie jako fakty.

## Źródła
- `eu-nis2`: `.claude/knowledge/eu-nis2/doc.txt:L1892, L2003, L3095-3360, L3920-3945, L4199`, https://eur-lex.europa.eu/eli/dir/2022/2555/oj, pobrane 2026-10-20.
- `eu-cra`: `.claude/knowledge/eu-cra/doc.txt:L1021, L1948, L2002, L2425, L2637, L4521`, https://eur-lex.europa.eu/eli/reg/2024/2847/oj, pobrane 2026-10-20.
- `us-nevi`: `.claude/knowledge/us-nevi/doc.txt:L124-128, L166-170, L226-228`, https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-680, pobrane 2026-10-20.
- `.claude/skills/dom-ev-regulations-eu/references/` (stan repozytorium 2026-10-20).
