# Transkrypcja sesji proba-pelna-1 (scenariusz: weterynaria, wersja: pelna)
> Materiał treningowy (symulacja) — nie jest źródłem wiedzy o prawdziwej domenie.

## Runda 1
**Facylitator:** Dzień dobry. Zaczynamy od chaosu: napiszcie na kartkach wszystkie zdarzenia, które dzieją się w przychodni — od pierwszego telefonu klienta do zapłaty. Jedno zdarzenie na kartkę, w czasie przeszłym.
**Robert (apteka):** Ja zacznę od swojego podwórka. Dostawa przyjęta, lek wydany, zamówienie złożone. No i niestety ostatnio też utylizacja całej partii szczepionek. Szkoda gadać.
**Kamil (it):** No dobra, ja zacznę od tego, co widzę w systemie. Formularz z www wpada, SMS-y wychodzą... a właściwie wczoraj bramka SMS padła i nic nie wychodziło, więc jeszcze się trochę gotuję. Piszę co mam z logów.
**Halina (ksiegowa):** Dzień dobry. Ja zajmuję się tym od strony dokumentów, więc moje kartki będą z końca tej drogi: paragon, faktura, rozliczenie pakietu. Co dzieje się w gabinecie, tego nie znam, pierwszy raz widzę to z bliska, więc chętnie posłucham. Przy okazji: faktura to dla mnie moment zakończenia wizyty, bo wtedy powstaje obowiązek rozliczenia.
**dr Paweł (lekarz):** Oj, to ja wam powiem, że zdarzeń to jest tyle, że głowa mała! Mieliśmy kiedyś kota, który połknął igłę z nitką, i operacja o północy, a dyżur sam, bez nikogo do pomocy... Takie rzeczy się pamięta, nie papiery. Ale dobra, piszę to, co ja widzę od strony gabinetu: pacjent przyjęty, badanie, zabieg, no i karta leczenia, którą zamykam zwykle dopiero rano, bo wieczorem już nie mam siły. Szczerze, to ja czasem myślę, że lekarze się tu wypalają, bo człowiek kocha zwierzaki, a ciągle ktoś mu każe coś wpisać.
**Beata (recepcja):** No… ja zacznę od tego, co mam na ladzie. Przypomnienia u nas idą z zeszytu, więc to też napiszę.
**Grażyna (wlascicielka):** Proszę państwa, ja zacznę, bo to jest moja firma i wiem, jak to wygląda! Klient dzwoni, przychodzi, zwierzak wychodzi zadowolony, klient wraca. I kupuje pakiet opieki, bo to jest nasz produkt, na którym budujemy markę. Zaczynamy od garażu po ojcu, a dziś mamy cztery placówki i myślimy o piątej. Mamy świetny miesiąc, więc ja chcę, żebyśmy myśleli o rozwoju, a nie o tym, kto co kliknął. Zdarzenia? Proszę bardzo, te najważniejsze: pakiet sprzedany, placówka otwarta, klient wrócił. Resztę niech dopiszą lekarze i recepcja, to ich działka.
- 🟧 `ev_001` Zamówienie leków złożone — apteka
- 🟧 `ev_002` Dostawa przyjęta — apteka
- 🟧 `ev_003` Lek wydany — apteka
- 🟧 `ev_004` Lek przeterminowany zutylizowany — apteka
- 🟧 `ev_005` Formularz rezerwacji wysłany — it
- 🟧 `ev_006` SMS wysłany — it
- 🟧 `ev_007` Eksport do Excela wykonany — it
- 🟧 `ev_008` Paragon wystawiony — ksiegowa
- 🟧 `ev_009` Faktura wystawiona — ksiegowa
- 🟧 `ev_010` Pakiet rozliczony — ksiegowa
- 🟧 `ev_011` Korekta faktury wystawiona — ksiegowa
- 🟧 `ev_012` Pacjent przyjęty — lekarz
- 🟧 `ev_013` Badanie wykonane — lekarz
- 🟧 `ev_014` Zabieg przeprowadzony — lekarz
- 🟧 `ev_015` Karta leczenia zamknięta — lekarz
- 🟧 `ev_016` Pacjent skierowany do kliniki — lekarz
- 🟧 `ev_017` Wizyta umówiona — recepcja
- 🟧 `ev_018` Przypomnienie wysłane — recepcja
- 🟧 `ev_019` Wizyta odwołana — recepcja
- 🟧 `ev_020` Klient nie przyszedł — recepcja
- 🟧 `ev_021` Płatność przyjęta — recepcja
- 🟧 `ev_022` Pakiet opieki sprzedany — wlascicielka
- 🟧 `ev_023` Nowa placówka otwarta — wlascicielka
- 🟧 `ev_024` Klient wrócił na kolejną wizytę — wlascicielka
- 🟧 `ev_025` Wizyta zakończona — wlascicielka
_Runda 1: +25 zdarzeń, +0 hot spotów, odrzucone kartki: 0, milczą: —_

## Runda 2
**Facylitator:** Pani Grażyno, dziękuję — zapiszmy to na kartkach. Beato, jak to wygląda od strony recepcji: ile umówionych wizyt naprawdę się odbywa?
**Kamil (it):** Jak już Beata będzie liczyć, to niech pamięta, że przez tę awarię bramki część przypomnień w ogóle nie poszła. Więc te liczby mogą być zaniżone. Zresztą w systemie to wyciągnę w pięć minut, wystarczy status wizyty i eksport.
**Beata (recepcja):** No… no to tak: z dziesięciu umówionych osiem przychodzi, a dwie nie. To mniej więcej 18 procent. I one nie odwołują, ja to widzę dopiero po godzinie, jak pacjenta nie ma. Przypomnienia mamy w zeszycie, ręcznie, i jak ktoś zapomni zadzwonić, to właśnie wtedy jest pusty termin. Wczoraj miałam dwa takie okienka rano.
- 🟧 `ev_026` Bramka SMS przestała działać — it
- 🟧 `ev_027` Klient nie przyszedł na wizytę (bez odwołania) — recepcja
- 🟧 `ev_028` Przypomnienie zapisane w zeszycie — recepcja
- 🟪 `hs_001` 18% umówionych wizyt się nie odbywa, a recepcja widzi to dopiero po godzinie — recepcja
_Runda 2: +3 zdarzeń, +1 hot spotów, odrzucone kartki: 0, milczą: apteka, ksiegowa, lekarz, wlascicielka_

## Runda 3
**Facylitator:** Beato, a przypomnienia o szczepieniach — jak je dziś robicie? Proszę o przykład z wczoraj.
**Kamil (it):** Ja tylko wtrącę, bo to się wiąże z bramką: SMS-y z przypomnieniami szły z systemu, ale od awarii nie idą, więc Beata pewnie dlatego pisze w zeszycie. Technicznie wystarczyłaby tabela przypomnień ze statusem i by to samo poszło... no dobra, mówcie, Beata, jak to było wczoraj.
**Beata (recepcja):** No… ja to robię z zeszytu. Wczoraj, wtorek, miałam na kartce pięć szczepień na dziś i na jutro. Wpisuję przy wizycie dopisek „szczepienie, przypomnieć”, a potem rano, jak jest chwila między telefonami, to dzwonię albo wysyłam SMS-a. Wczoraj do dwóch osób zadzwoniłam, a trzeciej nie zdążyłam, bo była kolejka przy ladzie. I ona nie przyszła. A to, co pan z IT mówi o bramce, to się zgadza, bo przez te dni, jak nie działała, to wszystko szło tylko ode mnie, z zeszytu. No i szczerze, nikt mi nie mówi, kiedy szczepienie się kończy, tylko ja to widzę po dopisku.
**Grażyna (wlascicielka):** Moment, moment, w zeszycie? Przecież płacimy za system i bramkę SMS, a u nas przypomnienia chodzą po staremu, długopisem? Przepraszam, Beato, mów dalej, ale to mnie zaskoczyło. 18 procent to nie jest mało.
- 🟧 `ev_029` Termin szczepienia wpisany do zeszytu — recepcja
- 🟧 `ev_030` Klient poinformowany telefonicznie o szczepieniu — recepcja
- 🟪 `hs_002` Przypomnienie o szczepieniu pominięte, gdy jest kolejka przy ladzie — recepcja
- 🟪 `hs_003` Przypomnienia w zeszycie zamiast w systemie? Skąd to się wzięło i jak często? — wlascicielka
_Runda 3: +2 zdarzeń, +2 hot spotów, odrzucone kartki: 0, milczą: apteka, ksiegowa, lekarz_

## Runda 4
**Facylitator:** Doktorze Pawle, kiedy dla Pana wizyta jest zakończona? Beato, Halino, Grażyno — a dla Was?
**Kamil (it):** Ja tylko wtrącę, bo to się kręci w kółko: w programie to jest po prostu status „zakończona” i tyle. Ktoś go klika albo nie klika. Po co my to rozpisujemy na karteczkach, zróbmy od razu porządny system, tabela wizyt ze statusem i po sprawie. A tak w ogóle, jak bramka padła, to nikt tych statusów nie pilnował.
**Halina (ksiegowa):** Z mojej strony, z punktu widzenia przepisów, wizyta jest zakończona w momencie wystawienia faktury albo paragonu. U mnie to jest ten dokument, bo od niego liczy się sprzedaż usługi i VAT. Jak wygląda koniec wizyty w gabinecie, nie wiem, to pytanie do Doktora i do recepcji. Ja widzę dopiero to, co przychodzi na papierze.
**dr Paweł (lekarz):** Dla mnie wizyta kończy się, jak zamknę kartę leczenia. Tylko że szczerze? Często zamykam ją dopiero następnego dnia rano, bo wieczorem już nie mam siły. Pacjent dawno wyszedł, właściciel zapłacił, a karta jeszcze wisi otwarta. Wiem, że to nie jest ładne, ale czasem po całym dniu i po nocnym dyżurze człowiek ma po prostu dość. Mówię to też dlatego, że wielu moich kolegów lekarzy się wypala i ta papierologia dokłada swoje. Płatności i tego, co dzieje się przy recepcji, nie umiem ocenić, to Beata wie lepiej.
**Beata (recepcja):** No… dla mnie wizyta jest zakończona, jak klient zapłaci przy ladzie. Dopóki nie zapłaci, to jeszcze nie koniec, bo może wrócić z jakimś pytaniem albo coś mu się dolicza. Wczoraj pan z kotem wyszedł z gabinetu koło 10:20, a zapłacił dopiero po 10:40, bo była kolejka. Dla lekarza to już było skończone, a u mnie dopiero potem. Więc to nie zawsze jest to samo.
**Grażyna (wlascicielka):** Dla mnie to proste: wizyta jest zakończona, kiedy zwierzę wychodzi od nas zadowolone, a właściciel ma poczucie, że warto wrócić. To jest moment prawdy dla marki, proszę państwa. Wiem, że doktor Paweł powie pewnie coś o dokumentacji, ale ja patrzę na to z wyższego poziomu: klient wychodzi i my chcemy, żeby wrócił. A skoro co piąty umówiony w ogóle nie dociera, to jeszcze mocniej mnie to uwiera, bo tego nie widzę w żadnych liczbach.
- 🟧 `ev_031` Status wizyty zmieniony na „zakończona” w programie — it
- 🟧 `ev_032` Faktura wystawiona — ksiegowa
- 🟧 `ev_033` Paragon wystawiony — ksiegowa
- 🟧 `ev_034` Karta leczenia zamknięta — lekarz
- 🟧 `ev_035` Zwierzę opuściło placówkę — wlascicielka
- 🟪 `hs_004` Wizyta zakończona: kiedy wychodzi pacjent, kiedy płatność, czy kiedy zamknięta karta? Karta często zamykana dopiero następnego dnia. — lekarz
- 🟪 `hs_005` Kiedy wizyta jest zakończona: po wyjściu z gabinetu czy dopiero po płatności przy ladzie? — recepcja
_Runda 4: +5 zdarzeń, +2 hot spotów, odrzucone kartki: 0, milczą: apteka_

## Runda 5
**Facylitator:** Dyżur nocny: kto decyduje, czy w nocy przyjmujemy pacjenta? Doktorze, Grażyno, Beato — proszę każde po kolei.
**Kamil (it):** Dobra, ja się nie wypowiem, kto decyduje w nocy, bo to nie moja działka. Ale słuchajcie, to już piąta runda i my dalej tylko przyklejamy karteczki. Po co to wszystko? Technicznie wystarczy tabela wizyt ze statusem i jedno pole „przyjęty w nocy”. Zróbmy od razu system, a nie będziemy tu pisać o tym samym po raz kolejny.
**dr Paweł (lekarz):** No to wam opowiem... Pamiętam owczarka, którego właściciel przywiózł taksówką na dyżur, grubo po pierwszej w nocy. Taksówkarz pomagał go wnosić, pies ledwo oddychał, a facet w panice nie wiedział, czy ma płacić za kurs, czy dzwonić do mnie. Nikt mi nie powiedział, że mam go przyjąć, po prostu stał w drzwiach. No więc odpowiadam: w nocy decyduję ja, lekarz dyżurny. Czasem przez telefon, czasem dopiero jak zobaczę zwierzaka w drzwiach. Nie ma przy mnie nikogo, kto by powiedział: przyjmij albo odeślij do kliniki. Jak brakuje mi leku albo rąk do pomocy, to sam ważę, czy dam radę, czy skieruję dalej. Szczerze, po takich nocach człowiek jest wypalony. Siedzisz sam, decyzja jest na tobie, a rano i tak czeka karta do uzupełnienia. Co robi Grażyna albo Beata w nocy, tego nie wiem, bo ich wtedy nie ma.
**Beata (recepcja):** No... ja w nocy mnie nie ma, więc nie powiem, kto tam decyduje. Rano widzę tylko, że ktoś był, bo zostaje kartka albo wpis na kartę, i dopiero wtedy ja to wpisuję w grafik. Czy ktoś mu wtedy powiedział, że płaci albo że ma pakiet, tego nie wiem.
**Grażyna (wlascicielka):** Powiem wprost: formalnie to ja odpowiadam za to, jak sieć działa w nocy, bo to jest nasza przewaga nad całodobową kliniką. Ale kto dokładnie w danej chwili kiwa głową, że przyjmujemy? No, lekarz dyżurny, tak mi się wydaje, i tyle. Grafik dyżurów to już wiedzą lepiej doktor i Beata, ja patrzę na to z góry. Pamiętam klienta, który przyjechał z kotem o trzeciej w nocy i potem mówił, że przecież go przyjęliśmy. I przyjęliśmy! Tylko nie wiem, kto wtedy podjął decyzję i czy ktoś to gdzieś zapisał. Ważne, żeby klient czuł, że Łapa jest zawsze dla niego, a nie żeby szukał, do kogo dzwonić.
- 🟧 `ev_036` Pacjent przyjęty na dyżurze nocnym — lekarz
- 🟧 `ev_037` Pacjent przyjęty na dyżurze nocnym — wlascicielka
- 🟪 `hs_006` Kto decyduje o przyjęciu pacjenta w nocy? Lekarz dyżurny sam, bez wsparcia, a lek bywa niedostępny akurat wtedy — lekarz
- 🟪 `hs_007` Kto decyduje o przyjęciu pacjenta w nocy? Recepcja widzi tylko ślad rano — recepcja
- 🟪 `hs_008` Kto ostatecznie decyduje, czy w nocy przyjmujemy pacjenta? — wlascicielka
_Runda 5: +2 zdarzeń, +3 hot spotów, odrzucone kartki: 0, milczą: apteka, ksiegowa_

## Runda 6
**Facylitator:** Robercie, co dzieje się z lekami w aptece: zamówienia, terminy ważności, ewidencja?
**Robert (apteka):** No, wreszcie ktoś pyta. Od początku: zamówienie składamy na podstawie stanów w ewidencji, ale często dostaję je bez danych, ile realnie zeszło na placówkach. Dostawa przychodzi, przyjmuję ją na stan, sprawdzam serie i terminy ważności. Potem wydania, każde ma iść do ewidencji obrotu, tak wymagają przepisy. Raz w miesiącu przeglądam terminy, a to, co przeterminowane, idzie do utylizacji z protokołem. Wychodzi około 4% asortymentu i dopiero co poszła u mnie cała partia szczepionek. Nie chcę o tym więcej mówić.
**Kamil (it):** Robert to chyba pytanie do lekarza albo do księgowej. Ja o aptece nic nie wiem, leków i przepisów nie ruszam. Mogę tylko powiedzieć, że w naszym programie nie ma żadnego modułu do leków, więc pewnie jest to w papierach albo w Excelu u kogoś innego.
- 🟧 `ev_038` Zamówienie leków złożone — apteka
- 🟧 `ev_039` Dostawa przyjęta na stan — apteka
- 🟧 `ev_040` Lek wydany i wpisany do ewidencji obrotu — apteka
- 🟧 `ev_041` Lek przeterminowany zutylizowany — apteka
- 🟪 `hs_009` Zamówienia składane bez danych o faktycznym zużyciu na placówkach — apteka
_Runda 6: +4 zdarzeń, +1 hot spotów, odrzucone kartki: 0, milczą: ksiegowa, lekarz, recepcja, wlascicielka_

## Runda 7
**Facylitator:** Halino, jak rozliczacie pakiety opieki? Czy zdarzają się pomyłki?
**Kamil (it):** Ja tylko wtrącę, bo pakiety to u nas Excel. Jest tam makro, które kiedyś ktoś napisał i poza mną nikt go nie rozumie. Pomyłki pewnie są, bo program przychodni o pakietach nic nie wie. Dobra, Halina niech powie, jak to robi w praktyce.
**Halina (ksiegowa):** Pakiety rozliczam na podstawie zestawienia, które dostaję w Excelu, zwykle dopiero na koniec miesiąca. Sprawdzam, ile usług z pakietu faktycznie wykorzystano i jak rozbić to na usługi i leki, bo z punktu widzenia VAT to nie są te same stawki. I tak, pomyłki się zdarzają. Miałam pakiet opieki rozliczony dwa razy, bo klient skorzystał z niego w dwóch placówkach i każda wpisała zużycie u siebie. Wyszło to dopiero przy zestawieniu, a nie w momencie wizyty. Przy kontroli to jest bardzo nieprzyjemne ryzyko, bo ktoś ma zapłaconą usługę, której de facto nie powinno już być.
**Beata (recepcja):** Ja jestem Beata, ale jak to do mnie, to powiem, co widzę przy ladzie. Pakietów nie rozliczam, tylko sprawdzam je w kartotece. Pomyłki się zdarzają. Był klient, który wykorzystał „ostatnią” wizytę z pakietu dwa razy, bo pierwsza nie była odhaczona. Zauważyłam to dopiero przy drugiej wizycie.
- 🟧 `ev_042` Pakiet rozliczony — ksiegowa
- 🟪 `hs_010` Pakiety liczone w Excelu makrem, którego nikt poza informatykiem nie rozumie. Czy salda się zgadzają? — it
- 🟪 `hs_011` Pakiety w Excelu, zużycie wpisywane osobno w każdej placówce, więc pakiet może zostać rozliczony dwa razy. Błąd wychodzi dopiero na koniec miesiąca. — ksiegowa
- 🟪 `hs_012` Wizyta z pakietu opieki wykorzystana drugi raz - brak odhaczenia przy pierwszej wizycie — recepcja
_Runda 7: +1 zdarzeń, +3 hot spotów, odrzucone kartki: 0, milczą: apteka, lekarz, wlascicielka_

## Runda 8
**Facylitator:** Jolanto, witamy. Jak wygląda Pani współpraca z przychodnią jako hodowczyni — wizyty, szczepienia miotu, ceny?
**Jolanta (hodowca):** Dziękuję. Jestem u państwa stałą klientką, hoduję psy od lat, więc przychodzę z całymi miotami, nie z jednym zwierzakiem. Szczepienia miotu to dla mnie podstawa, no i oczekuję rabatu „za miot”. Tylko że dziś jestem po prostu zdenerwowana, bo dostałam rachunek za ostatni miot i on mi się zupełnie nie zgadza z tym, co było ustalone. Proszę państwa, u nas w hodowli to by nie przeszło. Rabat jest liczony raz tak, raz inaczej, zależy w której placówce się trafi. I przypomnień o szczepieniach nikt mi nie przysyła, sama muszę pamiętać.
- 🟪 `hs_013` Rabat „za miot” liczony różnie w różnych placówkach — rachunek się nie zgadza — hodowca
- 🟪 `hs_014` Brak przypomnień o szczepieniach miotu — hodowca
_Runda 8: +0 zdarzeń, +2 hot spotów, odrzucone kartki: 0, milczą: apteka, it, ksiegowa, lekarz, recepcja, wlascicielka_

## Runda 9
**Facylitator:** Kamilu, rozwiązania odłóżmy na parking. Jakie zdarzenia widzisz w systemie, których jeszcze nie ma na ścianie?
**Kamil (it):** Dobra, parkuję. Z systemu widzę kilka rzeczy, których chyba nie ma. Formularz rezerwacji wysłany przez klienta ze strony. SMS z przypomnieniem wysłany, a po ostatniej awarii bramki też SMS niedostarczony, bo tego nikt nie zauważa. No i eksport do Excela wykonany, bo z tego księgowa i Halina liczą pakiety. To są rzeczy, które program robi naprawdę, a na ścianie ich nie widzę.
- 🟧 `ev_043` Formularz rezerwacji wysłany — it
- 🟧 `ev_044` SMS z przypomnieniem wysłany — it
- 🟧 `ev_045` SMS nie został dostarczony — it
- 🟧 `ev_046` Eksport do Excela wykonany — it
_Runda 9: +4 zdarzeń, +0 hot spotów, odrzucone kartki: 0, milczą: apteka, ksiegowa, lekarz, recepcja, wlascicielka, hodowca_
