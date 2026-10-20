---
name: dom-ev-market-roles
description: Użyj przy rolach rynku ładowania i przepływach danych oraz pieniędzy — CPO, eMSP, hub, host, OSD, flota, NAP, roaming, white-label, ad hoc.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba ustalić, kto jest kim na rynku ładowania EV i co przepływa między stronami — CPO, eMSP, hub roamingowy (P2P vs hub), właściciel lokalizacji (host), OSD/DSO i sprzedawca energii, producent ładowarek, flota, kierowca, NAP; jedna firma w wielu rolach; kto jest właścicielem jakich danych; przepływ pieniędzy w sesji roamingowej; modele biznesowe (white-label CPMS, CPO+eMSP, ad hoc, karta flotowa). Nie do słownika pojęć (dom-ev-glossary), formatów identyfikatorów (dom-ev-identifiers) ani szczegółów protokołu OCPI (dom-ev-charging)."
  slowa: "kto wystawia fakturę, rola CPO, rola eMSP, CPO i eMSP jednocześnie, hub roamingowy, Hubject, Gireve, roaming, peer-to-peer, bilateralnie, host parkingu, właściciel lokalizacji, udział w przychodach, revenue share, white label, CPMS, płatność ad hoc, bez umowy, karta flotowa, flota, kto jest właścicielem danych, rozliczenie hurtowe, przepływ pieniędzy, OSD, DSO, sprzedawca energii, NAP, punkt dostępu do danych, kto komu płaci, who invoices the driver, charge point operator, e-mobility service provider, market roles"
---

# Role rynku ładowania — kto jest kim i co przepływa

**Procedura: ustal rolę strony i kierunek komunikacji, zanim projektujesz integrację.** Pytaj o rolę w danym
przepływie, nie o rodzaj firmy: ta sama firma bywa CPO, eMSP i hubem naraz, a o jej obowiązkach w sesji
decyduje rola, jaką w niej pełni.

## Kroki
1. Wypisz strony zdarzenia (kierowca, kto operuje ładowarką, kto ma kontrakt z kierowcą, kto jest właścicielem
   miejsca, kto dostarcza energię).
2. Każdej stronie przypisz **rolę w tej sesji** (tabela niżej); jedna firma może mieć kilka.
3. Dla każdego przepływu (dane, pieniądze, odpowiedzialność) ustal nadawcę i odbiorcę oraz **czyja umowa** go pokrywa.
4. Dopiero potem wybierz kanał: OCPP (sprzęt ↔ CSMS), OCPI (CPO ↔ eMSP/hub), API własne, plik, faktura.

## Role
| Rola | Co robi | Typowa umowa / uwaga |
|---|---|---|
| **CPO** | operuje punktami ładowania (CSMS/CPMS), ustala taryfy, odpowiada za dostępność i sprzęt | sprzedaje usługę ładowania eMSP lub kierowcy ad hoc |
| **eMSP** | ma kontrakt z kierowcą: aplikacja, karta RFID, kontrakt Plug & Charge, faktura | płaci CPO za sesje hurtowo |
| **Hub roamingowy** | pośredniczy CPO↔eMSP: jedno przyłącze zamiast wielu, często też rozliczenia | bywa opłata za pośrednictwo; wzorce z huba — `references/roaming-modele.md` |
| **Host** (właściciel lokalizacji) | udostępnia miejsce (parking, sklep, zakład); zwykle nie operuje ładowarkami | umowa z CPO: dzierżawa, udział w przychodach, czasem zakup energii |
| **OSD / DSO** | dostarcza przyłącze i sieć dystrybucyjną; bywa ograniczeniem mocy | umowa przyłączeniowa; to nie sprzedawca energii |
| **Sprzedawca energii** | sprzedaje energię CPO (lub hostowi) | liczniki, taryfa energii; rozdzielony od OSD w modelu rynku UE [do weryfikacji dla PL] |
| **Producent ładowarek** | dostarcza sprzęt i firmware, często gotowy CSMS | gwarancja, serwis; własny backend ≠ rola CPO |
| **Flota** | zarządza wieloma kierowcami i pojazdami; płaci za ładowanie | karta flotowa wydana przez eMSP albo własne depot |
| **Kierowca** | zamawia ładowanie; rozlicza się z eMSP albo płaci ad hoc | podmiot danych osobowych (RODO) |
| **NAP** | krajowy punkt dostępu do danych o infrastrukturze | CPO udostępnia dane statyczne i dynamiczne [zakres: AFIR, do weryfikacji] |

## Kto jest właścicielem jakich danych
| Dane | Właściciel (źródło prawdy) | Kto je dostaje |
|---|---|---|
| Lokalizacje, EVSE, connectory, dostępność | CPO | eMSP, hub, NAP (OCPI Locations) |
| Taryfy | CPO | eMSP przed startem sesji (OCPI Tariffs) |
| Sesje i CDR | CPO (wytwarza je z OCPP) | eMSP (OCPI Sessions, CDRs) |
| Tokeny (RFID, ID aplikacji), kontrakt, faktura kierowcy | eMSP | CPO dostaje tokeny do autoryzacji (OCPI Tokens) |
| Dane płatnicze kierowcy | eMSP albo operator płatności | CPO ich nie widzi w roamingu |
| Odczyty licznika sieciowego | OSD (licznik główny), CPO (liczniki ładowarek) | sprzedawca energii |

CDR jest niezmienny; korekta to nowy CDR kredytowy (skill `dom-ev-charging`, plik ocpi.md w jego references).

## Przepływ pieniędzy w sesji roamingowej
```
kierowca --faktura/płatność--> eMSP --rozliczenie hurtowe (wg CDR)--> CPO --> host (udział), sprzedawca energii
```
- OCPI przenosi **dane** (Tariffs, Sessions, CDR, Tokens); **nie realizuje płatności ani faktur**.
- eMSP fakturuje kierowcę (lub flotę) i płaci CPO zbiorczo wg zatwierdzonych CDR, nie per sesja w czasie rzeczywistym.
- Cena dla kierowcy (kontrakt eMSP) bywa inna niż cena CPO w taryfie OCPI; różnicę ustala umowa eMSP↔CPO [założenie typowe].
- Hub może dodatkowo agregować CDR i rozliczenia; zależy od usługi huba [do weryfikacji u konkretnego huba].

## Modele biznesowe
| Model | Role | Efekt dla integracji |
|---|---|---|
| CPO + eMSP w jednej firmie | obie role, osobne tożsamości stron w OCPI | własni klienci rozliczani wewnętrznie, obcy przez roaming; dwa strumienie CDR (jako Sender i jako Receiver) |
| White-label CPMS | dostawca software'u, klient jako CPO | dostawca jest procesorem danych i operatorem technicznym; kto wystawia się w OCPI jako strona? ustal w umowie |
| Ad hoc (bez umowy) | CPO przyjmuje płatność od kierowcy | brak eMSP w sesji; CPO sam fakturuje/paragon przez operatora płatności; wymóg wynika z AFIR [do weryfikacji] |
| Flota z kartą | flota ↔ eMSP (kontrakt), kierowca używa tokenu | faktura na flotę; tokeny w OCPI jak każde inne |
| Host z udziałem w przychodach | host nie jest stroną OCPI | rozliczenie host↔CPO poza OCPI, na danych CDR/sesji CPO |
| Hub vs P2P | zob. `references/roaming-modele.md` | od liczby partnerów i kosztu |

## Przykład
Wejście: „Jesteśmy CPO i eMSP. Klient obcego eMSP ładuje u nas, nasz klient ładuje u obcego CPO.”
Wynik:
- Sesja 1 (u nas, obcy kierowca): jesteśmy **CPO** — wysyłamy Sessions/CDR do obcego eMSP; on fakturuje swojego kierowcę i rozlicza się z nami hurtowo.
- Sesja 2 (nasz klient u obcego): jesteśmy **eMSP** — odbieramy CDR od obcego CPO, **my** fakturujemy swojego kierowcę i płacimy obcemu CPO.
- Własny klient na własnej ładowarce: faktura od nas jako eMSP; roaming nie jest potrzebny, ale zachowaj spójny model CDR.
- OCPI w żadnej z tych sesji nie przenosi pieniędzy.

## Pułapki
- Typ firmy zamiast roli: „jesteśmy CPO, więc fakturujemy każdego” — fakturę kierowcy roamingowemu wystawia jego eMSP.
- Uznanie OCPI za system płatności albo fakturowania.
- Host uznany za CPO (albo odwrotnie): host nie operuje ładowarką i nie jest stroną OCPI bez własnej integracji.
- Producent ładowarek z wbudowanym CSMS potraktowany jako CPO.
- OSD i sprzedawca energii zlani w jedną rolę.
- Brak kierunku komunikacji: Tokens płyną od eMSP do CPO, a Locations/Sessions/CDR od CPO do eMSP.
- Ad hoc bez eMSP wymaga własnej ścieżki płatności i dowodu zakupu u CPO.

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| hub czy połączenia bilateralne, koszty, kiedy hybryda, kto komu płaci przy hubie | `references/roaming-modele.md` |
| różnice rynków PL/UE/USA, AFIR, NAP | `references/rynki-i-regulacje.md` |
| mapa „kto z kim i jakim kanałem” | `references/mapa-przeplywow.md` |

## Checklista
- [ ] Dla każdej strony wskazana rola w tej sesji (nie typ firmy)
- [ ] Kierunek komunikacji i kanał (OCPP / OCPI / inny) ustalone dla każdego przepływu
- [ ] Wiadomo, kto fakturuje kierowcę i kto komu płaci hurtowo
- [ ] Właściciel danych wskazany; dane osobowe oznaczone
- [ ] Host, OSD i sprzedawca energii nie zlane z CPO
- [ ] Twierdzenia o prawie i rynku PL oznaczone [do weryfikacji] albo ze źródłem

## Źródła
`.claude/skills/dom-ev-charging/references/ocpi.md` (role, modele roamingu, §7 AFIR; import 2024–2025) i
`cykl-sesji-ladowania.md` (Faza 5, dwa kanały płatności). Reszta — wiedza ogólna, oznaczona [do weryfikacji].
Sprawdzone 2026-10-20: OCPI przenosi dane, nie płatności (ocpi.md §1).
