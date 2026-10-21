# Archetyp Agreement — mapper (umowy, warunki, aneksy, zamówienia)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **wzajemnych zobowiązaniach stron** (umowa, warunki, aneks, zamówienie, oferta) na model z umową
jako bytem o tożsamości, warunkami obowiązującymi w czasie i zamówieniami składanymi na jej podstawie. Efekt: da się
odpowiedzieć na pytanie „co obowiązywało w dniu X i co wiedzieliśmy o tym w dniu Y”, a aneks jest nową wersją warunków,
a nie nadpisaniem pól. Protokół wspólny (pytania, „To zależy”, kontrola R/A/X, zapis): `SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy strony przyjmują wzajemne zobowiązania na warunkach, które obowiązują w określonym czasie
i mogą się zmieniać?* Tak → pasuje. Jednorazowy koszyk bez warunków i bez historii zmian → wystarczy zamówienie
(patrz niżej), bez pełnej umowy.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „umowa serwisowa”, „aneks zmienia cenę od 1 dnia miesiąca” | ✅ |
| „warunki obowiązują od–do”, „jaka stawka obowiązywała w marcu?” | ✅ |
| „zamówienia w ramach umowy ramowej”, „zamówienie z pozycjami i statusem” | ✅ |
| „oferta ważna 14 dni, po akceptacji staje się umową” | ✅ (oferta → umowa) |
| „jak policzyć cenę wg cennika i rabatu” | ❌ → Pricing |
| „rozliczenie płatności, salda, faktury” | ❌ → Accounting |
| „skan umowy, podpis, wersja pliku” | ❌ → Document (`document.md`) |
| „kim jest strona, jakie ma role” | ❌ → Party |
| „rezerwacja sali na termin” | ⚠️ graniczny |
| „kontrakt na instrumencie finansowym” | ⚠️ graniczny |

**Przypadki graniczne:**
- *Rezerwacja jako umowa?* — liczy się tylko „czy termin wolny” → Availability. Gdy rezerwacja ma warunki (kara,
  cennik, zmiany w czasie), umowa opisuje zobowiązanie, a Availability blokuje zasób.
- *Instrumenty finansowe* — Contract w finansach (Fowler, rozdz. „Trading” i „Derivative Contracts”) to osobna,
  specjalistyczna rodzina; ten plik jej nie rozstrzyga, potwierdź z ekspertem.

## Model (istota)
Łańcuch pojęć (nazwy podrozdziałów rozdz. 4 Silverstona): **zapotrzebowanie (requirement) → zapytanie (request) → oferta
(quote) → umowa (agreement) → zamówienia na podstawie umowy (agreement to orders)**. Nie każdy etap jest potrzebny;
zacznij od tych, o których mówią wymagania.

- **Umowa (Agreement)** — tożsamość, **strony w rolach** (Party: np. zleceniodawca, wykonawca; role z Party, nie flagi),
  rodzaj, status, forma czynności, okres obowiązywania całości.
- **Pozycje umowy (agreement items)** — co jest przedmiotem (produkt, usługa, zakres); odwołanie do Product, nie kopia.
- **Warunki (agreement terms)** — typ warunku + wartość + **okres obowiązywania**. Warunek jest danymi, nie kodem:
  termin płatności, kara, czas reakcji serwisu.
- **Ustalenia cenowe (agreement pricing)** — umowa **wskazuje** cennik, stawkę lub parametry; liczy je Pricing.
- **Zamówienie (order)** — jedno zobowiązanie: pozycje, strony, korekty (adjustments), status i warunki. Może wskazywać
  umowę; wtedy bierze jej warunki **z dnia zamówienia** (kopia lub odwołanie do wersji — decyzja).
- **Umowa ramowa vs zamówienie** — własny wniosek: umowa ramowa ustala warunki wspólne i nie rodzi wykonania sama
  z siebie; każde zamówienie to osobne zobowiązanie z własnym statusem i cyklem.

### Czas: okres obowiązywania i aneksy
- Warunek ma **zakres dat obowiązywania** (od–do). To wzorzec Effectivity / Temporal Property (Fowler, eaaDev): wartość
  zależna od daty.
- **Aneks = nowa wersja warunku z datą skutku**, a nie edycja. Stara wersja zostaje; kończy się dniem przed datą skutku.
- **Odtworzenie stanu na dzień**: zapytanie „warunki umowy U w dniu D” zwraca wersje, których zakres obejmuje D.
- **Drugi zakres dat** (bitemporalność): oprócz „kiedy obowiązuje” zapisujemy „**kiedy zapisano**”. Aneks wsteczny
  nie niszczy wtedy wcześniejszej wiedzy systemu, a spór rozstrzygają dwa pytania: *co obowiązywało w dniu D*
  i *co system wiedział w dniu W*.

### Status i reguły
- **Status** — wzorzec przekrojowy (Silverston Vol. 3: rozdział Status): umowa i zamówienie mają typ statusu, wartość
  i datę nadania; dozwolone przejścia to reguła, nie struktura.
- **Reguły biznesowe** (Silverston Vol. 3: Business Rules; Arlow & Neustadt mają archetyp Rule) — „aneks wymaga
  akceptacji dwóch stron” liczy warstwa polityk i woła archetyp.
- **Forma czynności** — atrybut umowy (pisemna, dokumentowa, elektroniczna). Kontekst prawny do potwierdzenia przez
  prawnika: forma dokumentowa (art. 77² KC, od 8.09.2016), forma elektroniczna z kwalifikowanym podpisem
  (art. 78¹ KC). Archetyp zapisuje wybraną formę; **czy czynność jest ważna**, ocenia prawnik, nie model.

## Pytania
**A — decyzje standardowe:**
- Czy jest **umowa ramowa**, czy tylko pojedyncze zamówienia? Czy zamówienie musi wskazywać umowę?
- Czy aneks może działać **wstecz** i czy potrzebny **drugi zakres dat** (kiedy zapisano)?
- Czy zamówienie **kopiuje** warunki w chwili złożenia, czy wskazuje wersję umowy?
- Jakie **statusy** i przejścia ma umowa, aneks, zamówienie? Kto zatwierdza (poza archetypem)?

**B — luki** (przykłady): wypowiedzenie · automatyczne przedłużenie · kilka aneksów o tej samej dacie skutku · umowa
wielostronna · limity wartości zamówień w umowie ramowej · cesja.

## Kroki mapowania
1. **Zobowiązanie** — umowa trwała czy zamówienie jednorazowe; czy jest umowa ramowa.
2. **Strony i role** — kto, w jakiej roli (odesłanie do Party; role jako dane).
3. **Pozycje i warunki** — co jest przedmiotem; które warunki jako typ + wartość + okres.
4. **Cena** — ustalenia w umowie; liczy Pricing.
5. **Czas** — okres obowiązywania, aneksy jako wersje, data skutku, ewentualny drugi zakres dat.
6. **Zamówienia** — powiązanie z umową, dziedziczenie warunków.
7. **Status** — stany i przejścia jako reguły; zdarzenia zmiany.
8. **Integracje** — Pricing, Accounting (skutki finansowe), Availability, Product, Document.

## Decyzje do kontroli (R/A/X)
umowa ramowa vs zamówienia · aneks wsteczny · drugi zakres dat · kopia vs odwołanie do wersji warunków · statusy
i przejścia · etap oferty · kto zatwierdza aneks · wypowiedzenie · forma czynności.

## Format wyniku
```markdown
# Model Agreement: <obszar>
## Mapowanie pojęć    — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Umowy              — | Rodzaj | Strony i role (→ Party) | Pozycje | Forma czynności | Okres | Ramowa? |
## Warunki w czasie   — | Typ warunku | Wartość/parametr | Obowiązuje od–do | Zapisano od–do (opcjonalnie) |
## Aneksy             — | Aneks | Co zmienia | Data skutku | Wstecz? | Zatwierdza (poza archetypem) |
## Zamówienia i statusy — | Zamówienie | Umowa | Warunki: kopia/odwołanie | Status | Przejście |
## Integracje          — | Zdarzenie | Z / do archetypu | Reakcja |
## Decyzje (R/A/X)    — | Decyzja | Źródło |
## Uwagi              — założenia (X), przypadki brzegowe, parametry polityk zmiennych
```

## Wzorce i pułapki
- **Nadpisanie warunku aneksem** — ginie historia; spór „jaka stawka była w marcu” jest nierozstrzygalny. Wersja z datą
  skutku zamiast `UPDATE`.
- **Jedna data** („ważne do”) przy aneksach wstecznych — bez drugiego zakresu dat nie odróżnisz „obowiązywało” od
  „wtedy wiedzieliśmy”. Dodaj go tylko, gdy wymagania dopuszczają korekty wsteczne lub spory o stan.
- **Cena jako logika w umowie** — umowa wskazuje cennik i parametry; liczy Pricing.
- **Umowa jako plik** — skan i podpis to Document; umowa ma warunki i status niezależnie od pliku.
- **Zamówienie dziedziczące warunki „na żywo”** — późniejszy aneks zmieni stare zamówienie; zdecyduj: kopia czy
  wersja z dnia zamówienia.
- **Autoryzacja poza archetypem**: „kto zatwierdza aneks” liczy warstwa polityk; archetyp pilnuje struktury (okresy
  jednego typu warunku bez nakładania).
- **Oferta to nie zamówienie:** oferta to propozycja jednej strony z terminem ważności, wersjami i negocjacją;
  nie rezerwuje zasobów i nikogo nie wiąże do akceptacji. Zamówienie to zobowiązanie z realizacją, płatnością
  i reklamacją. „Zamówienie ze statusem oferta” miesza dwa cykle życia i dwa zestawy reguł. Akceptacja oferty to
  zdarzenie przełomowe, które **tworzy** zamówienie albo umowę z warunkami skopiowanymi z zaakceptowanej wersji.
- **Zakup to nie zamówienie:** zamówienie wyraża, czego klient chce; zakup (transakcja sprzedaży) to fakt rozliczenia,
  czyli płatność, faktura i przeniesienie własności (Accounting). Jedno zamówienie bywa realizowane kilkoma zakupami
  lub dostawami, a zakup w sklepie stacjonarnym nie ma zamówienia. Wspólna tabela `orders` ze statusem `paid` ukrywa te
  różnice.

## Kontrola jakości
- [ ] strony występują w rolach z Party, bez flag
- [ ] każdy warunek ma typ, wartość i okres obowiązywania; okresy tego samego typu się nie nakładają
- [ ] aneks jest nową wersją z datą skutku; da się odtworzyć stan na dzień
- [ ] decyzja o drugim zakresie dat (kiedy zapisano) podjęta jawnie
- [ ] granice wskazane (Pricing, Accounting, Document, Availability); forma czynności tylko jako atrybut
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** „Firma serwisowa: umowa serwisowa z klientem na 24 miesiące, stawka za godzinę i czas reakcji. Aneksy
zmieniają stawkę i zakres od wskazanej daty, czasem wstecz. Klient zamawia wizyty w ramach umowy. Klient twierdzi, że
w marcu stawka wynosiła 100, my mamy 120.” [przykład]

```markdown
## Mapowanie pojęć
| umowa serwisowa | Agreement (ramowa) | warunki trwają dłużej niż jedna wizyta |
| stawka, czas reakcji | Agreement terms (typ + wartość + okres) | zmieniają się aneksami |
| wizyta zamówiona | Order na podstawie umowy | osobne zobowiązanie ze statusem |
## Aneksy — | A1 | stawka 100 → 120 | od 1 kwietnia | wstecz: nie | zatwierdza: polityka (poza archetypem) |
## Warunki w czasie — | stawka | 100 | 1 stycznia–31 marca | zapisano: od podpisania |
                       | stawka | 120 | od 1 kwietnia | zapisano: od A1 |
## Spór o stan — na dzień 15 marca → 100; przy aneksie wstecznym drugi zakres dat pokaże, co system wiedział
## Decyzje — umowa ramowa (R) · aneks jako wersja (R) · drugi zakres dat (A: „To zależy” — tylko dla aneksów wstecznych)
   · zamówienie: kopia warunków w chwili złożenia (X → zapytaj)
## Niezmapowane pojęcia — wyliczenie kwoty za wizytę (→ Pricing) · faktura i płatność (→ Accounting) · skan z podpisem
   (→ Document) · klient (→ Party)
```

## Źródła
Odczyt 2026-10-17.
- **Silverston, „The Data Model Resource Book, Vol. 1, Revised Edition”, Wiley, ISBN 978-0-471-38023-8** (marzec 2001,
  zastępuje wydanie z 1997) — nazwy podrozdziałów rozdz. 4 „Ordering Products” (potwierdzone wtórnie, spisem
  treści O'Reilly); treści rozdziałów nie weryfikowano.
- **Silverston & Agnew, „The Data Model Resource Book, Vol. 3: Universal Patterns for Data Modeling”, Wiley 2009,
  ISBN 978-0-470-17845-4** — tytuły rozdziałów Status i Business Rules (numeracja niepewna); pierwotne.
- **Fowler, „Analysis Patterns: Reusable Object Models”, Addison-Wesley** (rok 1996/1997) — tytuły rozdz. 9 „Trading”
  i 10 „Derivative Contracts”; tylko do wskazania granicy (instrumenty finansowe).
- **Fowler, martinfowler.com/eaaDev: Temporal Property, Effectivity, Audit Log** — szkice z 2004 roku, autor ich nie
  aktualizuje (pierwotne, nieaktualizowane). Nazwy wzorców; opis drugiego zakresu dat jest naszym wnioskiem modelowym.
- **Arlow & Neustadt, „Enterprise Patterns and MDA”, Addison-Wesley, ISBN 0-321-11230-X** (rok: źródła sprzeczne
  2003/2004) — wyłącznie nazwy archetypów Order i Rule; treści nie weryfikowano (wtórne).
- **Kodeks cywilny, art. 77² (forma dokumentowa, od 8.09.2016; ustawa z 10.07.2015, Dz.U. 2015 poz. 1311), art. 77³
  (dokument), art. 78¹ (forma elektroniczna)** — kontekst prawny z komentarza (wtórne); do potwierdzenia przez prawnika.
- Oferta a zamówienie i zakup a zamówienie — na podstawie programu szkolenia „DDD — zaawansowane techniki
  modelowania i archetypy” (Bottega IT Minds, materiał od człowieka, 2026-10-21); opisane własnymi słowami.

Reszta (umowa ramowa vs zamówienie, kopia vs odwołanie do wersji warunków, drugi zakres dat, reguły i pułapki) to
nasze wnioski modelowe, nieprzypisane autorom. Opisane własnymi słowami; treść książek i norm nie była cytowana.
