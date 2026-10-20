# Archetyp Resource / Service — mapper (zasoby, aktywa, usługi, katalog usług)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **rzeczach i zdolnościach, którymi organizacja dysponuje albo które świadczy** (maszyny, sprzęt, pojazdy,
technicy, licencje, usługi techniczne), na model: typ zasobu i egzemplarz, cykl życia aktywa, usługa jako zdolność, katalog
usług oraz przypisanie zasobu do pracy. Efekt: zasób nie jest ani „wierszem produktu”, ani „kalendarzem”, a usługa nie jest
mylona z ofertą handlową. Protokół wspólny: `SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy modelujemy rzeczy i zdolności, którymi organizacja dysponuje lub które świadczy — niezależnie od
tego, jak je sprzedaje?* Tak → pasuje. Jeśli kluczowe jest „co i za ile sprzedajemy” → Product / Pricing.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „rejestr maszyn / pojazdów / sprzętu”, „historia serwisu urządzenia” | ✅ aktywo z cyklem życia |
| „katalog usług”, „usługa X dostępna dla klientów grupy Y” | ✅ usługa i oferta usługi |
| „usługa składa się z usług technicznych / podusług” | ✅ usługa dla klienta vs techniczna |
| „technik i narzędzie przypisane do zlecenia” | ✅ przypisanie zasobu do pracy |
| „środki zużywalne (filtry, części)” | ✅ jeśli to zasób; saldo ilościowe → Quantity / Accounting |
| „oferta handlowa, warianty, pakiety do sprzedaży” | ❌ → Product (i Pricing) |
| „czy sala/technik jest wolny we wtorek?” | ❌ → Availability |
| „kogo przydzielić, by zminimalizować koszt dojazdów?” | ❌ → General assignment |
| „amortyzacja, wartość bilansowa” | ❌ → Accounting |
| „kara za przekroczenie czasu reakcji” | ❌ warunek umowy → `agreement.md` |
| „kroki przeglądu, wykonanie, czas pracy” | ❌ → `activity-process.md` |
| „zasób, który się rezerwuje” | ⚠️ graniczny |

**Przypadki graniczne:**
- *Zasób rezerwowany* — samo istnienie i cykl życia to Resource; pytanie „wolny w terminie” i blokada to Availability.
  Zwykle oba archetypy naraz, z jasnym podziałem: Resource mówi **czym jest**, Availability **kiedy jest dostępny**.
- *Usługa = produkt?* — jeśli wymaganie dotyczy tego, co klient kupuje (nazwa, cena, warianty), to Product; jeśli tego, co
  organizacja **potrafi wykonać** i z czego się to składa — Service. Jedna usługa bywa podstawą wielu produktów.
- *Aktywo klienta vs aktywo własne* — winda klienta, którą serwisujemy, jest dla nas obiektem pracy, nie naszym środkiem
  trwałym; model musi rozróżnić właściciela (Party) od użytkownika i od serwisującego.

## Model (istota)
Poniżej jest rozumowanie modelowe fabryki; źródła w sekcji `## Źródła` potwierdzają tylko wskazane tam fakty.

- **Typ zasobu vs egzemplarz** — typ opisuje klasę (model windy, kwalifikacja „elektryk SEP”), egzemplarz konkretną sztukę
  z numerem seryjnym, lokalizacją i stanem. Konwencja typ/egzemplarz jest znana z literatury wzorców, ale jej zastosowanie do
  zasobów to nasz wniosek `[założenie]`.
- **Aktywo trwałe z cyklem życia** — zakup → eksploatacja → serwis → wycofanie. Stan aktywa to maszyna stanów z historią
  zdarzeń (przekazanie, naprawa, przegląd), a nie jedno pole `status`. Według ISO 55000:2024 aktywo to rzecz lub byt mający
  dla organizacji potencjalną lub rzeczywistą wartość; **wartość księgową** liczy Accounting, tu jej nie ma.
- **Zasób zużywalny vs trwały** — to nasz wniosek, nie podział przypisywany autorom wzorców. Trwały: jest egzemplarz,
  wraca po użyciu, ma historię. Zużywalny: liczy się ilość i zużycie (→ Quantity / Accounting). Ten sam typ bywa jednym
  i drugim zależnie od kontekstu (narzędzie wypożyczane vs jednorazowe) — rozstrzygnij per typ.
- **Usługa jako zdolność** — usługa to coś, co organizacja potrafi dostarczyć, nie rzecz do postawienia na półce. W modelu TM
  Forum SID rozróżnia się usługę widoczną dla klienta (CustomerFacingService, realizuje produkt) i usługę techniczną ukrytą
  przed klientem (ResourceFacingService); przykład z SID: VPN to CFS, BGP to RFS; istnieją też specyfikacje CFSSpec i RFSSpec.
  Wniosek: usługa dla klienta składa się z usług technicznych, a te opierają się na zasobach.
- **Trzy pojęcia, których nie wolno zlewać** (GB922, częściowo): specyfikacja produktu (projekt), oferta (prezentacja rynkowa),
  produkt w użyciu (instancja u klienta). Szczegóły relacji między nimi nie są tu potwierdzone `[niezweryfikowane]`; w modelu
  trzymaj trzy osobne byty i zapytaj, którego dotyczy dane wymaganie.
- **Oferta usługi i katalog usług** (ITIL 4, parafraza): oferta usługi to formalny opis jednej lub więcej usług dla
  określonej grupy odbiorców (może obejmować dobra, dostęp do zasobów, działania usługowe); katalog usług to uporządkowana
  informacja o usługach i ofertach, dopasowana do odbiorcy. Katalog jest więc **widokiem**, a nie nową encją sprzedażową.
- **Przypisanie zasobu do pracy** — osobny byt łączący zasób (sprzęt, osoba) z pracą, z okresem i rolą. W modelach danych
  Silverstona występują przypisania aktywów trwałych i przypisania aktywów stronom; Fowler opisuje wzorzec Resource
  Allocation. Podziału zużywalne/trwałe nie przypisujemy żadnemu z nich.
- **SLA** (np. czas reakcji 4 h) jest warunkiem umowy (`agreement.md`); usługa tylko **wskazuje**, czego dotyczy.

## Pytania
**A — decyzje standardowe:**
- Co jest **typem**, a co **egzemplarzem** (numer seryjny, lokalizacja, właściciel)? Które egzemplarze są własne, a które klienta?
- Które zasoby są **trwałe**, a które **zużywalne**? Kto prowadzi ilości (Quantity)?
- Jakie **etapy cyklu życia** istnieją i kto może je zmieniać (zakup, uruchomienie, serwis, wycofanie)?
- Czy jest rozdział **usługa dla klienta** vs **usługa techniczna**? Z czego składa się usługa (podusługi, zasoby, kwalifikacje)?
- Czy **katalog usług** ma różne widoki dla różnych grup odbiorców?
- Czy zasób może być przypisany do pracy **równolegle** (jeden technik – dwa zlecenia)?

**B — luki** (przykłady):
- zastępowalność zasobów (zamiennik egzemplarza) · hierarchia zasobu (część – całość) · lokalizacja i przenoszenie ·
  kwalifikacje wymagane do obsługi · wersje specyfikacji usługi · zależności między usługami · wycofywanie usługi
  z katalogu przy istniejących instancjach · historia przypisań (audyt) · dane osobowe techników (RODO).

## Kroki mapowania
1. **Inwentarz zasobów** — lista typów i egzemplarzy; właściciel, użytkownik, serwisujący (Party).
2. **Trwałe vs zużywalne** — decyzja per typ; zużywalne odeślij do Quantity / Accounting.
3. **Cykl życia** — stany, zdarzenia przejść, kto zmienia; historia jako zdarzenia.
4. **Usługi** — usługa dla klienta, usługi techniczne, zależności od zasobów i kwalifikacji.
5. **Oferta i katalog** — kto jest odbiorcą oferty, jakie widoki katalogu; styk z Product (co jest sprzedawane).
6. **Przypisania** — zasób ↔ praca (rola, okres, wyłączność); styk z Availability i `activity-process.md`.
7. **Granice** — SLA → `agreement.md`, amortyzacja → Accounting, optymalny przydział → General assignment.

## Decyzje do kontroli (R/A/X)
Typ vs egzemplarz · właściciel aktywa (własne/klienta) · trwały vs zużywalny · stany cyklu życia · usługa dla klienta vs
techniczna · skład usługi · widoki katalogu · przypisanie równoległe · zastępowalność · wycofanie usługi przy aktywnych instancjach.

## Format wyniku
```markdown
# Model Resource / Service: <obszar>
## Zasoby                — | Typ | Egzemplarz (klucz) | Trwały/zużywalny | Właściciel | Lokalizacja |
## Cykl życia aktywa     — | Stan | Zdarzenie | Następny stan | Kto zmienia |
## Usługi                — | Usługa | Poziom (dla klienta / techniczna) | Składa się z | Wymaga zasobów/kwalifikacji |
## Oferta i katalog      — | Oferta usługi | Odbiorca | Usługi w ofercie | Widok katalogu |
## Przypisania           — | Zasób | Praca | Rola | Okres | Wyłączność |
## Mapowanie pojęć       — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Integracje            — | Zdarzenie | Z / do archetypu | Reakcja |
## Decyzje (R/A/X)       — | Decyzja | Źródło |
## Uwagi                 — założenia (X), parametry polityk zmiennych, [niezweryfikowane]
```

## Wzorce i pułapki
- Zlanie usługi z produktem: zmiana ceny lub pakietu nie powinna ruszać opisu zdolności. Trzy pojęcia – trzy byty.
- Pole `status` zamiast zdarzeń cyklu życia gubi historię serwisu, a ta jest zwykle wartością samą w sobie.
- Zasób z wbudowanym kalendarzem: dostępność to osobny archetyp (Availability); Resource trzyma tożsamość i stan.
- Technik jako „konto użytkownika” zamiast strony i zasobu: uprawnienia (autoryzacja poza archetypem) to nie kwalifikacje.
- Przypisanie jako pole `technik_id` na zleceniu uniemożliwia wielu techników, role i historię zmian.
- SLA wpisane w usługę – to warunek umowy i może się różnić między klientami; wstaw je jako parametr z `agreement.md`.
- Wartość i amortyzacja w obiekcie aktywa – to wpisy księgowe (Accounting), nie atrybuty zasobu.

## Kontrola jakości
- [ ] każdy zasób ma typ, egzemplarz i właściciela; rozstrzygnięto trwały/zużywalny
- [ ] cykl życia ma stany, zdarzenia i historię
- [ ] usługa dla klienta i techniczna są rozdzielone (lub świadomie połączone — decyzja zapisana)
- [ ] oferta, specyfikacja i instancja nie są zlane; katalog to widok
- [ ] przypisania są osobnym bytem z rolą i okresem
- [ ] SLA, amortyzacja, dostępność i przydział odesłane do właściwych archetypów
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** `[przykład]` „Firma serwisująca windy. Windy należą do klientów, każda ma numer fabryczny i historię przeglądów.
Technicy mają uprawnienia i narzędzia pomiarowe. Sprzedajemy usługę »konserwacja z czasem reakcji 4 h«.”

```markdown
## Zasoby — | typ windy | winda nr fabr. (egz.) | trwały | klient (Party) | adres budynku |
   | technik | osoba (Party) | trwały | firma | — | · | miernik | egzemplarz | trwały | firma | magazyn |
## Cykl życia — winda: w eksploatacji → w serwisie → wyłączona → wycofana (zdarzenia z datą)
## Usługi — | konserwacja | dla klienta | przegląd okresowy + reakcja na awarię | kwalifikacja „dźwigi” |
## Oferta — | konserwacja 4 h | klienci z umową ramową | konserwacja | widok katalogu B2B |
   czas reakcji 4 h → parametr z `agreement.md`, nie atrybut usługi
## Przypisania — | technik + miernik | zlecenie (activity-process) | wykonawca | okres zlecenia | nie |
## Niezmapowane — wolny termin technika (→ Availability) · dobór najbliższego technika (→ General assignment) ·
   cena abonamentu (→ Pricing) · kara za przekroczenie 4 h (→ Agreement)
## Decyzje — windy klienta nie są aktywami firmy (R) · technik = zasób trwały (X, małe) · wycofanie usługi
   przy aktywnych umowach (X → zapytaj)
```

## Źródła
Odczyt 2026-10-17.
- ISO 55000:2024 „Asset management — Vocabulary, overview and principles” (wyd. 2, zastąpiło wydanie z 2014) — **norma, pierwotne**; bierzemy pojęcie aktywa jako bytu o wartości dla organizacji. Definicję znamy z opisów wtórnych, więc parafrazujemy.
- TM Forum, Information Framework (SID), Browsable SID R20.0 — **pierwotne**; rozróżnienie CustomerFacingService i ResourceFacingService, specyfikacje CFSSpec i RFSSpec, przykład VPN/BGP.
- TM Forum GB922 Product (najnowsza znaleziona v24.5.0, zatwierdzona 7.03.2025) — **pierwotne, potwierdzone częściowo**; bierzemy tylko trzy pojęcia: specyfikacja produktu, oferta, produkt w użyciu; relacje między nimi `[niezweryfikowane]`.
- AXELOS, ITIL 4 — **pierwotne (parafraza)**; definicje oferty usługi i katalogu usług. Definicji „service” i „SLA” z tej rodziny nie bierzemy (niepotwierdzone).
- L. Silverston, „The Data Model Resource Book”, Vol. 1 Revised Edition, Wiley 2001, ISBN 978-0-471-38023-8 — **książka; spis potwierdzony w O'Reilly (wtórnie)**; spis rozdziału o zapotrzebowaniu na pracę potwierdzony częściowo (m.in. Fixed Asset Assignments, Party Fixed Asset Assignments). Vol. 2 (Wiley 2001, ISBN 978-0-471-35348-5) to modele branżowe, w tym usługi profesjonalne i telekomunikacja.
- M. Fowler, „Analysis Patterns: Reusable Object Models”, Addison-Wesley 1997 (autor podaje 1996), ISBN 0-201-89542-0 — **książka; spis potwierdzony u wydawcy (InformIT)**; rozdz. 8 „Planning” zawiera wzorzec Resource Allocation. Podziału zużywalne/trwałe w nim nie potwierdzono.
- D. Hay, „Enterprise Model Patterns: Describing the World (UML Version)”, Technics Publications, ISBN 978-1-935504-05-4 (rok 2011, potwierdzony częściowo) — **książka; spis potwierdzony u wydawcy**; rozdz. 6 „Assets”. Treść rozdziału (typ aktywa vs aktywo) niepotwierdzona; to konwencja typ/egzemplarz `[założenie]`.

Opisane własnymi słowami; treść książek i norm nie była cytowana.
