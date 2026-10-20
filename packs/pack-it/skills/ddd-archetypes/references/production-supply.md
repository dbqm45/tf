# Archetyp Production / Supply — mapper (struktura wyrobu, produkcja, zaopatrzenie, identyfikowalność)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **wytwarzaniu wyrobów** albo **przepływie towaru przez łańcuch dostaw** na model ze strukturą
wyrobu, marszrutą, zleceniem i śladem partii. Efekt: wiadomo, z czego, gdzie i kiedy coś powstało i dokąd trafiło. Protokół wspólny (pytania, „To zależy”, kontrola R/A/X, zapis):
`SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy z materiałów powstają wyroby (albo towar przechodzi przez łańcuch dostaw) i trzeba wiedzieć,
z czego, gdzie i kiedy?* Tak → pasuje. Jeśli firma tylko kupuje i sprzedaje, nie wiedząc nic o pochodzeniu partii —
wystarczy Product z Accounting.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „receptura”, „lista materiałów”, „wyrób składa się z…” | ✅ |
| „zlecenie produkcyjne”, „marszruta”, „etapy procesu” | ✅ |
| „co zamówić, żeby zrealizować plan produkcji” (potrzeby materiałowe) | ✅ |
| „z jakiej partii surowca powstała ta partia wyrobu?”, „wycofaj partię” | ✅ identyfikowalność |
| katalog, warianty, typy produktu, numery seryjne | ❌ → Product (`product.md`) |
| „kolejność etapów i ścieżka krytyczna” | ❌ → Planning |
| „czy maszyna jest wolna w środę?” | ❌ → Availability |
| „które zlecenie na którą maszynę, by zmaksymalizować wartość” | ❌ → General assignment |
| „stan magazynowy i wycena zapasów” | ❌ → Accounting |
| „montaż u klienta jako usługa” | ⚠️ graniczny |

**Przypadki graniczne:**
- *Usługa a wyrób* — jeśli nic nie powstaje materialnie, a liczy się praca w czasie → activity-process (operacje)
  i resource-service; Production / Supply pasuje, gdy powstaje partia wyrobu ze śladem materiałów.
- *Sama dystrybucja* — pasuje tylko identyfikowalność (partie, zdarzenia); struktura i marszruta zbędne.
- *Maszyna* — aktywo to resource-service, pojemność w czasie → Availability; tu tylko miejsce wykonania segmentu.

## Model (istota)
### Struktura wyrobu i proces
- **Struktura wyrobu (BOM)** — wiedza ogólna z produkcji: wyrób składa się z komponentów w określonych ilościach.
  Nasz wniosek modelowy: BOM to **asocjacja między produktami** (wyrób → komponent, ilość → Quantity, okres
  obowiązywania, wersja); produkt pozostaje w Product, BOM nie jest jego polem.
- **Marszruta / segmenty procesu** — kolejność kroków z miejscem, czasem i materiałami; krok jako czynność →
  activity-process.
- **Definicja produktu, zdolności produkcyjne, harmonogram i wykonanie produkcji** — modele ISA-95 / IEC 62264
  (wtórne, zob. „Źródła”): „co potrafimy”, „co zaplanowano”, „co zrobiono”. Bierzemy tylko **rozdzielenie
  plan / wykonanie**.
- **Zlecenie produkcyjne** — wyrób, ilość, struktura i marszruta **w wersji z dnia zlecenia**, status, zużycie
  i wynik (partie, braki). Wersje struktury z datą skutku jak w `agreement.md`, nie nadpisanie.

### Zaopatrzenie
- **Planowanie potrzeb materiałowych (MRP)** — z planu wyrobów i struktur wynikają potrzeby materiałów w czasie, po
  uwzględnieniu zapasów (ujęcie demand-driven: Ptak & Smith 2011). Archetyp **przyjmuje wynik** (potrzeby, terminy)
  jako dane; wyliczenie to algorytm pod interfejsem. Dostawca to strona w roli (Party), zakup — Agreement.

### Dyskretna vs procesowa
Własny wniosek, wsparty tym, że Hay ma osobne rozdziały „Material requirements planning” i „Process manufacturing”:
- **dyskretna** — policzalne sztuki, montaż; kluczowe: struktura, numery seryjne lub partie;
- **procesowa** — receptury, mieszanie, **współprodukty i odpady**, wydajność zmienna; kluczowe: receptura z tolerancją,
  partia jako jednostka śladu, przeliczenia ilości (Quantity).

### Identyfikowalność
- **Partia / lot** — jednostka śledzenia (Product); powiązania wejście → wyjście tworzą graf pochodzenia.
- **Zdarzenia** — zapisujemy fakty (co, kiedy, gdzie, dlaczego). Standard
  GS1 EPCIS 2.0 (z CBV 2.0, 2022) wyróżnia rodzaje zdarzeń: ObjectEvent (obserwacja obiektu), AggregationEvent
  (pakowanie w opakowanie zbiorcze), TransformationEvent (wejścia → wyjścia), AssociationEvent (powiązanie, nowe
  w 2.0), TransactionEvent (powiązanie z transakcją); opisy w nawiasach to skrót autorów fabryki, definicji normatywnych
  nie czytano. Dla modelu to **słownik rodzajów faktów**, niekoniecznie format wymiany.
- **GS1 Global Traceability Standard 2.0 (2017)** — ramy procesu identyfikowalności w łańcuchu dostaw.
- **Wymóg „jeden krok wstecz, jeden krok naprzód”** w żywności (rozp. (WE) 178/2002, art. 18; potwierdzone
  częściowo, pośrednio) — kontekst do potwierdzenia przez prawnika: podmiot wie, od kogo wziął i komu przekazał.
  Minimalny ślad = ten wymóg; pełny graf partii to rozszerzenie.
- **Identyfikatory GS1** (np. GTIN, SSCC, GLN) — [niezweryfikowane] w tym pliku; ustal z ekspertem, czy firma ich używa.

## Pytania
**A — decyzje standardowe:**
- Produkcja **dyskretna czy procesowa** (receptury, współprodukty, tolerancje)?
- Jaka jest **jednostka śledzenia**: partia, sztuka (numer seryjny), opakowanie zbiorcze?
- Jak głęboko **wstecz i naprzód** trzeba sięgać: jeden krok czy pełny graf pochodzenia?
- Czy struktura wyrobu **ma wersje** i czy zlecenie zamraża wersję z dnia zlecenia?
- Kto liczy potrzeby materiałowe (nasz system, ERP, ręcznie) i czy archetyp tylko przyjmuje wynik?

**B — luki** (przykłady): zamienniki składników · współprodukty i odpady · partie mieszane · rework · okres
przydatności · kwarantanna · wycofanie partii i powiadomienie odbiorców (poza archetypem).

## Kroki mapowania
1. **Rodzaj produkcji** — dyskretna, procesowa, tylko łańcuch dostaw.
2. **Wyroby i składniki** — produkty z Product; struktura jako asocjacja z ilością (Quantity) i okresem.
3. **Marszruta** — segmenty, miejsca, materiały na krok.
4. **Plan a wykonanie** — zlecenie, zużycie, wynik, braki.
5. **Potrzeby materiałowe** — źródło wyniku MRP; terminy; powiązanie z zakupem (Party, Agreement).
6. **Partie i graf pochodzenia** — jednostka śledzenia, powiązania wejście → wyjście.
7. **Zdarzenia** — rodzaje faktów i ich pola.
8. **Zapytania** — „wstecz”, „naprzód”, „na dzień”.

## Decyzje do kontroli (R/A/X)
dyskretna vs procesowa · jednostka śledzenia · głębokość śladu · wersje struktury i marszruty · zamienniki i
współprodukty · źródło potrzeb materiałowych · status partii · rodzaje zdarzeń.

## Format wyniku
```markdown
# Model Production / Supply: <obszar>
## Mapowanie pojęć    — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Struktury i marszruty — | Wyrób (→ Product) | Składnik | Ilość | Okres/wersja | Segment i miejsce |
## Zlecenia           — | Zlecenie | Wyrób | Wersja struktury | Plan vs wykonanie | Status |
## Partie i pochodzenie — | Partia | Typ | Partie wejściowe | Okres przydatności | Status |
## Zdarzenia i zapytania — | Rodzaj faktu / pytanie (wstecz, naprzód, na dzień) | Dane | Głębokość |
## Integracje         — | Zdarzenie | Z / do archetypu | Reakcja |
## Decyzje (R/A/X)    — | Decyzja | Źródło |
## Uwagi              — założenia (X), przypadki brzegowe, parametry polityk zmiennych
```

## Wzorce i pułapki
- **Struktura jako kolumny w produkcie** (`skladnik1`, `skladnik2`) — brak wersji i głębokości.
- **Bieżąca lokalizacja zamiast zdarzeń** — brak odpowiedzi „gdzie była w czwartek”.
- **Partia = produkt** — katalog mieszany ze śladem; trzymaj granicę z Product.
- **Plan i wykonanie w jednym rekordzie** — fakt nadpisuje plan.
- **Ilości bez jednostek** psują zużycie i wydajność → Quantity.
- **Autoryzacja poza archetypem**: kto zwalnia partię z kwarantanny lub zarządza wycofaniem, rozstrzyga warstwa
  polityk; archetyp zapisuje fakt i pilnuje niezmienników (np. nie zużyjesz więcej niż jest na partii).
- Bez wymogu śladu nie buduj grafu pochodzenia; wystarczy partia i dostawca.

## Kontrola jakości
- [ ] rodzaj produkcji (dyskretna/procesowa) wskazany; jednostka śledzenia nazwana
- [ ] struktura wyrobu to asocjacja z ilością (Quantity) i okresem, a nie pola produktu
- [ ] plan i wykonanie rozdzielone; zlecenie zamraża wersję struktury; głębokość śladu zgodna z wymaganiem
- [ ] granice wskazane (Product, Planning, Availability, General assignment, Accounting, Quantity)
- [ ] identyfikatory GS1 [niezweryfikowane] lub pominięte; wymóg prawny tylko jako kontekst
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** „Piekarnia: chleb powstaje z mąki, wody, drożdży i soli według receptury. Mąkę kupujemy od kilku dostawców,
każda dostawa ma numer partii. Pieczywo wydajemy do sklepów partiami dziennymi. Gdy dostawca zgłosi wadę partii mąki,
musimy wskazać, które partie pieczywa i do których sklepów trafiły.” [przykład]

```markdown
## Mapowanie pojęć
| receptura chleba | struktura wyrobu (asocjacja produkt → składnik, ilość z tolerancją) | produkcja procesowa |
| partia mąki | partia wejściowa (dostawca = Party) | jednostka śledzenia |
| wypiek dnia | zlecenie produkcyjne → partia pieczywa | partie wejściowe zużyte w zleceniu |
| wydanie do sklepu | zdarzenie przepływu (przesunięcie partii) | ślad naprzód |
## Zapytania — wstecz: z jakich partii mąki powstała partia P · naprzód: do których sklepów trafiły partie z partii
   mąki M (głębokość: pełny graf, bo wycofanie) (A: „To zależy” od wymogu → parametr `głębokość_śladu`)
## Decyzje — receptura z wersjami (X → zapytaj) · powiadomienie sklepów poza archetypem (R)
## Niezmapowane pojęcia — zamówienie mąki u dostawcy (→ Agreement / Party) · piec jako zasób (→ Availability,
   resource-service) · jednostki (kg, worek) (→ Quantity)
```

## Źródła
Odczyt 2026-10-17.
- **IEC 62264-1:2013 „Enterprise-control system integration — Part 1: Models and terminology”** (wyd. 2, zastąpiło
  wydanie z 2003) — norma pierwotna; część 1 definiuje poziom 3 (MOM) i interfejs poziomów 3–4. Aktualność na 2026
  niepewna (EVS: wycofanie 62264-2:2013 z 2026-05-04, możliwe nowsze wydanie).
- **Modele ISA-95** (personel, wyposażenie, materiał, segment procesu, zdolność produkcyjna, definicja produktu,
  harmonogram, wykonanie produkcji) — wtórne, potwierdzone częściowo; poziomy 0–4 i B2MML niezweryfikowane.
- **„Orlicky's Material Requirements Planning”, 3rd ed., Ptak & Smith, McGraw-Hill 2011** — pierwotne dla MRP w ujęciu
  demand-driven. Pojęć cytowanych jako pochodzące od Orlicky'ego z 1975 roku nie weryfikowano.
- **Hay, „Data Model Patterns: Conventions of Thought”, Dorset House 1996** — wyłącznie tytuły rozdziałów „Material
  requirements planning” i „Process manufacturing” (katalog biblioteczny); treści podrozdziałów nie weryfikowano.
- **Silverston, „The Data Model Resource Book, Vol. 2, Revised Edition”, Wiley 2001, ISBN 978-0-471-35348-5** —
  rozdz. 2 „Manufacturing”; podrozdziałów (BOM, MRP) nie weryfikowano (źródła sprzeczne).
- **GS1 EPCIS 2.0 i CBV 2.0** (ratyfikowane czerwiec 2022, ref.gs1.org; EPCIS/CBV Implementation Guideline 2.0 —
  marzec 2023) — pierwotne; rodzaje zdarzeń potwierdzone częściowo.
- **GS1 Global Traceability Standard, Release 2.0, sierpień 2017** — pierwotne; ramy procesu identyfikowalności.
- **Rozporządzenie (WE) nr 178/2002, art. 18** — wymóg „jeden krok wstecz, jeden krok naprzód”; potwierdzone
  częściowo, pośrednio przez motyw 3 rozporządzenia wykonawczego 931/2011 (EUR-Lex). Wyłącznie kontekst prawny,
  do potwierdzenia przez prawnika, nie porada.

Reszta (BOM jako asocjacja produktów, dyskretna vs procesowa, graf pochodzenia, pułapki) to nasze wnioski modelowe,
nieprzypisane autorom. Opisane własnymi słowami; treść książek i norm nie była cytowana.
