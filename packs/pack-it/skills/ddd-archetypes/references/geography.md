# Archetyp Geographic Location — mapper (lokalizacje, obszary, adresy)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **miejscu** (kraj, gmina, strefa dostaw, adres, współrzędne) na model, w którym lokalizacja jest
osobnym bytem, a nazwa, rola obszaru, adres i geometria to oddzielne, zmieniające się w różnym rytmie informacje.
Efekt: ten sam obszar ma wiele nazw i języków, bywa strefą dostaw i jurysdykcją podatkową naraz, a faktura pamięta adres
z dnia sprzedaży.
Protokół wspólny (pytania, „To zależy”, kontrola R/A/X, zapis): `SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy odpowiedź zależy od tego, GDZIE coś jest lub do jakiego obszaru należy?*
Tak → pasuje. Adres to tylko tekst wpisany przez klienta i nigdzie nie służy do decyzji → wystarczy pole w Party.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „dostarczamy do wybranych gmin / kodów pocztowych”, strefy dostaw | ✅ |
| kraj → województwo → powiat → gmina; „wszystko w tym regionie” | ✅ |
| ten sam obszar pod kilkoma nazwami lub w kilku językach (Gdańsk / Danzig) | ✅ |
| adres wg szablonu kraju (PL, DE), walidacja kodów | ✅ |
| faktura, zamówienie lub umowa z adresem „z dnia zdarzenia” | ✅ |
| obszar sprzedaży, jurysdykcja podatkowa, strefa serwisowa | ✅ |
| „kim jest odbiorca, jaki ma telefon i e-mail” | ❌ → Party (mechanizmy kontaktu) |
| „czy w tym punkcie odbioru jest wolne miejsce?” | ❌ → Availability |
| „ile kosztuje dostawa do strefy 2?” | ❌ → Pricing (strefa jest tylko parametrem) |
| „jaka trasa kuriera przez 40 adresów?” | ❌ → General assignment (algorytm tras) |
| wyświetlanie mapy, wyszukiwarka adresów jako usługa zewnętrzna | ⚠️ graniczny |

**Przypadki graniczne:**
- *Usługa zewnętrzna (geokoder, mapy)* — model przechowuje wynik i identyfikator z rejestru; samo wyszukiwanie to
  integracja (ACL), nie archetyp.
- *Adres jako pole tekstowe* — jeśli nikt nie filtruje, nie waliduje i nie liczy strefy, nie buduj hierarchii „na zapas”.
- *Magazyn / punkt odbioru* — lokalizacja tak, stan zapasów i wolne miejsca nie (Product, Availability).

## Model (istota)
Poniższy podział to wniosek modelowy fabryki; źródła w sekcji „Źródła” potwierdzają tylko to, co tam opisano.
### Lokalizacja i nazwa
- **GeographicLocation** — punkt albo obszar na Ziemi z własnym, technicznym identyfikatorem (generowanym w aplikacji).
  Typ (kraj, jednostka podziału, miejscowość, ulica, punkt) to cecha ze słownika, nie osobna klasa.
- **GeographicName** — osobny byt: nazwa, język, rodzaj (oficjalna, potoczna, historyczna), okres ważności. Lokalizacja
  ma 1..n nazw; nazwa nie jest kluczem ani nie identyfikuje obszaru.
- **ExternalIdentifier** — identyfikator z rejestru zewnętrznego: schemat (np. ISO 3166-1, ISO 3166-2, TERC, SIMC, ULIC,
  kod pocztowy) + wartość + okres ważności. To **atrybut z rejestru**, nie klucz modelu: rejestry zmieniają kody,
  łączą i dzielą jednostki. Jedna lokalizacja może mieć identyfikatorów wiele (po jednym na schemat).

### Hierarchia i zawieranie
- **Zawieranie obszarów** — relacja „obszar A leży w B” jako osobny rekord z okresem (kraj → województwo → powiat →
  gmina; w DE inne poziomy). Nie `parentId` w lokalizacji: struktur bywa kilka (administracyjna, pocztowa, handlowa),
  a granice się zmieniają. Zasięg bywa liczony z zawierania albo z geometrii — wybór to decyzja (A).
- **Zbiory obszarów** — strefa to zbiór obszarów (gmin, kodów pocztowych) z okresem, nie osobna geometria rysowana ręcznie;
  wtedy zmiana granicy gminy nie psuje strefy.

### Rola obszaru
- **AreaRole** — „ten obszar odgrywa rolę X dla Y”: strefa dostaw sklepu, obszar sprzedaży handlowca, jurysdykcja
  podatkowa. Osobny byt z okresem i właścicielem roli. Rola jest informacją o **zastosowaniu**; stawka, limit czy cena
  zależna od strefy należą do Pricing lub warstwy reguł, które dostają strefę jako parametr.

### Adres
- **Address** — opis lokalizacji według **szablonu kraju** (kolejność i wymagane elementy różnią się: PL, DE, GB). Szablon
  to dane (element, wymagalność, format kodu pocztowego), nie `if` w kodzie. Adres wskazuje lokalizację (np. TERC +
  SIMC + ULIC w PL) i ma pola tekstowe do wydruku; jedno bez drugiego bywa niewystarczające.
- **Adres strony** — mechanizm kontaktu należy do Party (adres rozliczeniowy, dostawy, zastosowania). Granica:
  Party wie, *kto* pod jakim adresem jest dostępny; Geographic Location wie, *czym ten adres jest* i *w jakich obszarach
  leży*.
- **Adres zamrożony vs aktualny** — dokument (zamówienie, faktura, umowa) trzyma **kopię** adresu z chwili zdarzenia
  (snapshot: tekst + odniesienie do lokalizacji z datą). Zmiana adresu klienta nie przepisuje historii. Adres aktualny
  strony to osobny, zmienny stan. To samo dotyczy nazw: faktura pamięta nazwę z dnia sprzedaży.

### Geometria
- **Geometry** — osobny byt lub referencja (punkt, wielokąt) w ustalonym układzie współrzędnych, z okresem i źródłem.
  Zapis w GeoJSON z WGS 84 w stopniach dziesiętnych; współrzędne w kolejności **długość, szerokość**.
  **Pułapka osi:** oznaczenie EPSG:4326 w wielu narzędziach i bazach zakłada kolejność szerokość, długość — odwrócenie
  osi daje punkt w innym miejscu świata bez błędu walidacji. Ustal kolejność w kontrakcie i testuj na znanym punkcie.
- Obszar zawierania liczony z geometrii (punkt w wielokącie) to algorytm przestrzenny za interfejsem; model przechowuje
  wynik i datę wersji granic.

## Pytania
**A — decyzje standardowe:**
- Jakie kraje i szablony adresów obsługujemy teraz (PL, DE), a które dojdą? Czy kod pocztowy jest walidowany formatem czy rejestrem?
- Strefa dostaw to zbiór gmin, zbiór kodów pocztowych, czy rysowany wielokąt? Co przy konflikcie (kod przecina gminy)?
- Hierarchia z zawierania (rekordy) czy z geometrii? Ile poziomów naprawdę potrzeba?
- Czy dokument zamraża adres w całości (kopia), czy kopia + odniesienie do lokalizacji z datą?
- Które identyfikatory zewnętrzne zapisujemy i kto aktualizuje je z rejestru (import okresowy)?

**B — luki** (przykłady): zmiana granic gminy a istniejące strefy? · nazwy w kilku językach na dokumentach? · adres bez
ulicy (wieś)? · punkty odbioru i paczkomaty jako lokalizacje? · strefa czasowa obszaru? · strefa wyłączona na święta
(→ Availability)? · RODO: adres osoby fizycznej a retencja (→ Party, `document.md`)?

## Kroki mapowania
1. **Lokalizacje** — każde „miejsce” z wymagań → typ lokalizacji; odetnij nazwy od identyfikatorów.
2. **Nazwy** — języki, rodzaje, okresy; która nazwa idzie na dokument.
3. **Identyfikatory zewnętrzne** — schemat, wartość, źródło rejestru, częstość aktualizacji.
4. **Hierarchia** — relacje zawierania z okresem; poziomy per kraj.
5. **Role obszarów** — strefa dostaw, obszar sprzedaży, jurysdykcja; właściciel i okres roli.
6. **Adres** — szablon per kraj (dane), walidacje, związek z lokalizacją.
7. **Granica z Party i dokumentami** — adres aktualny w Party; kopia w dokumencie (zdarzenie zamrażające).
8. **Geometria** — czy potrzebna, układ współrzędnych, kolejność osi, wersjonowanie granic.

## Decyzje do kontroli (R/A/X)
kraje i szablony adresów · źródło hierarchii (rekordy vs geometria) · strefa jako zbiór obszarów vs wielokąt · zamrażanie
adresu na dokumencie · identyfikatory zewnętrzne i ich aktualizacja · nazwy wielojęzyczne · kolejność osi · wersjonowanie granic ·
walidacja kodów · kto utrzymuje strefy.

## Format wyniku
```markdown
# Model Geographic Location: <obszar>
## Mapowanie pojęć    — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Lokalizacje i nazwy — | Typ lokalizacji | Nazwy (język, rodzaj) | Identyfikatory zewnętrzne (schemat) | Uwagi |
## Hierarchia         — | Relacja zawierania | Poziomy | Okres | Źródło (rekordy/geometria) |
## Role obszarów      — | Rola | Obszary (zbiór) | Właściciel roli | Okres | Parametr dla Pricing/reguł |
## Adresy             — | Kraj | Szablon (elementy, wymagalność) | Walidacja | Powiązanie z lokalizacją |
## Zamrożenie na dokumentach — | Dokument | Co kopiujemy | Zdarzenie zamrażające |
## Geometria          — | Układ | Kolejność osi | Wersjonowanie | Gdzie liczone |
## Decyzje (R/A/X)    — | Decyzja | Źródło |
## Uwagi              — założenia (X), przypadki brzegowe, parametry polityk zmiennych
```

## Wzorce i pułapki
- **Kod pocztowy lub nazwa miasta jako klucz** — kody i nazwy się zmieniają, jeden kod obejmuje kilka miejscowości.
  Klucz techniczny, kod jako identyfikator zewnętrzny.
- **Jedno pole `address` w zamówieniu odsyłające do aktualnego adresu klienta** — po przeprowadzce historyczna faktura
  pokazuje nowy adres. Zamrażaj w chwili zdarzenia.
- **`if (kraj == "DE")` w walidacji adresu** — szablon jako dane.
- **Strefa jako ręcznie rysowany wielokąt** obok granic gmin — rozjazd po zmianie granic; zbiór obszarów jest odporniejszy.
- **Pomieszanie roli i obszaru** — „strefa 2” nie jest rodzajem lokalizacji, tylko rolą obszaru w kontekście dostaw.
- **Oś współrzędnych** — odwrócona kolejność długość/szerokość; kontrakt i test na punkcie kontrolnym.
- **Poza archetypem:** „czy punkt odbioru ma wolny slot?” (Availability), „ile za dostawę?” (Pricing), „w jakiej kolejności
  jechać?” (General assignment). Autoryzacja („kto może zmienić strefę”) leży w warstwie aplikacji.
- **Polityki zmienne jako parametry:** zasięg dostaw zależny od pory roku → archetyp dostaje gotowy zbiór obszarów.

## Kontrola jakości
- [ ] nazwa, identyfikator zewnętrzny i klucz techniczny to trzy różne rzeczy
- [ ] hierarchia z okresem, nie `parentId`; strefa jako zbiór obszarów (lub uzasadniony wielokąt)
- [ ] szablony adresów jako dane; kraje wymienione
- [ ] dokumenty zamrażają adres; adres aktualny tylko w Party
- [ ] kolejność osi i układ współrzędnych jawne (jeśli jest geometria)
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** „Sklep internetowy dostarcza w Polsce i Niemczech. W PL strefy dostaw to zestawy gmin, w DE zestawy kodów
pocztowych. Faktura ma pokazywać adres nabywcy z dnia sprzedaży. Gdańsk bywa wpisywany jako Danzig.”

```markdown
## Mapowanie pojęć
| gmina, kraj | GeographicLocation (typ: jednostka podziału) | identyfikator TERC jako atrybut |
| Gdańsk / Danzig | GeographicName (pl, de, oficjalna / potoczna) | jedna lokalizacja, dwie nazwy |
| strefa dostaw | AreaRole nad zbiorem obszarów | okres obowiązywania |
| adres nabywcy | Address wg szablonu kraju | PL i DE: dwa szablony (R) |
## Role obszarów
| DOSTAWA_PL_1 | zbiór gmin | Sklep | od–do | parametr `strefa` dla Pricing |
| DOSTAWA_DE_1 | zbiór kodów pocztowych | Sklep | od–do | parametr `strefa` |
## Zamrożenie na dokumentach — faktura | kopia adresu nabywcy + odniesienie do lokalizacji | wystawienie (R)
## Decyzje
| strefa PL jako zbiór gmin | R |
| kod pocztowy DE: format czy rejestr | A: format na start |
| zmiana granic gminy a strefy | X → hot spot |
## Niezmapowane pojęcia — cena dostawy (→ Pricing), nabywca i jego telefon (→ Party), kurier i trasa (→ General assignment)
```

## Źródła
Odczyt 2026-10-17.
- Hay, „Enterprise Model Patterns: Describing the World (UML Version)”, Technics Publications, 2011 (ISBN 978-1-935504-05-4) —
  bierzemy: rozdział „Geographic Locations” obejmuje lokalizację, nazwy geograficzne i role; rozdział o ludziach i organizacjach
  jest osobny. Ranga: pierwotne (spis wydawcy). Hierarchii obszarów nie przypisujemy tej książce.
- Silverston, Agnew, Vol. 3, „Universal Patterns for Data Modeling”, Wiley, styczeń 2009 — bierzemy:
  wzorzec Geographic Boundary powiązany z adresem pocztowym oraz rozdziały o rolach, hierarchiach, mechanizmach kontaktu. Ranga:
  wtórne dla treści wzorca (opis O'Reilly).
- ISO 3166-1:2020 (kody krajów) i ISO 3166-2:2020 (kody jednostek podziału) — bierzemy: identyfikatory z rejestru jako atrybuty.
  Ranga: pierwotne (iso.org).
- ISO 19160-1:2015, „Addressing — Part 1: Conceptual model” — bierzemy: adres jako opis lokalizacji. Ranga: pierwotne (iso.org).
- ISO 19112:2019 — bierzemy: odniesienia przestrzenne przez identyfikatory geograficzne, schemat pojęciowy gazetteera. Ranga: pierwotne.
- UPU S42 (International postal address components and templates) — bierzemy: szablony adresów per kraj jako dane. Ranga:
  pierwotne, ale tylko częściowo zweryfikowane; aktualność wydania [niezweryfikowane] (najnowsza znaleziona S42-8, 2017).
- RFC 7946, GeoJSON (sierpień 2016) — bierzemy: WGS 84, stopnie dziesiętne, kolejność długość–szerokość. Ranga: pierwotne.
- EPSG:4326 (WGS 84, oś szerokość–długość wg epsg.io) — bierzemy: różnica kolejności osi jako pułapka. Ranga: wtórne.
- GUS, TERYT (eTERYT): TERC, SIMC, ULIC — bierzemy: identyfikatory jednostek, miejscowości i ulic; adres kodowany TERC + SIMC +
  ULIC. Ranga: pierwotne.
- PRG i PRNG (GUGiK) oraz EMUiA (gminy, geoportal.gov.pl) — bierzemy: rejestry granic, nazw i adresów jako źródła importu. Ranga:
  pierwotne, zweryfikowane częściowo.
- Dyrektywa INSPIRE 2007/2/WE (14.03.2007), załącznik I — bierzemy: nazwy geograficzne, jednostki administracyjne, adresy i układy
  współrzędnych jako ustandaryzowane tematy danych. Ranga: wtórne (kopia legislation.gov.uk). Przepisy tylko jako kontekst do
  potwierdzenia przez prawnika, nie porada.

Podział na nazwę, rolę obszaru, adres i geometrię oraz zamrażanie adresu na dokumencie to wnioski modelowe fabryki, nie tezy autorów.
Opisane własnymi słowami; treść książek i norm nie była cytowana.
