# Poza zakresem fabryki — DSA, prawa konsumenta, KSeF, ViDA (stan na 2026-10-18)

**Poza zakresem fabryki.** Fabryka IT zajmuje się prawem tylko w zakresie budowy oprogramowania, także z AI
(decyzja człowieka z 2026-10-20). Poniższe notatki zostają jako materiał pomocniczy: skill ich nie stosuje w mapie
obowiązków, a pytanie o te akty kierujesz do prawnika, księgowości lub właściciela produktu. Fakty ze źródeł wtórnych
[wtórne] (dostęp 2026-10-18), nie sprawdzone w EUR-Lex ani ISAP.

## Wiersze dawnej mapy aktów
| Akt | Kiedy dotyczy | Termin |
|---|---|---|
| DSA, rozp. (UE) 2022/2065 | hosting treści, platformy internetowe | od 17.02.2024 [wtórne] |
| Prawa konsumenta, dyr. 2011/83/UE z Omnibusem 2019/2161 | B2C online, treści i usługi cyfrowe, także „płatne danymi” | Omnibus od 28.05.2022 [wtórne] |
| Przycisk odstąpienia, art. 11a dyr. 2011/83 (dyr. 2023/2673) | umowy B2C zawierane online | stosowanie 19.06.2026; w PL brak transpozycji (stan 18.10.2026) [wtórne] |
| KSeF, ustawa z 5.08.2025 (Dz.U. 2025 poz. 1203) | faktury w Polsce | 1.02.2026 duzi, 1.04.2026 pozostali; kary od 1.01.2027 [wtórne] |
| ViDA, dyr. (UE) 2025/516 | e-faktury i raportowanie VAT B2B wewnątrz UE | 1.07.2030 [wtórne] |

Dawne pytania kwalifikujące: „Klientami są konsumenci (B2C)?” → prawa konsumenta i przycisk odstąpienia;
„Przechowujecie lub publikujecie treści użytkowników?” → DSA; „Wystawiacie faktury w Polsce albo B2B w UE?” → KSeF, ViDA.
Dawne luki w kodzie: przycisk odstąpienia, zgłaszanie treści, uzasadnienie blokady konta, integracja KSeF.

## DSA — rozp. (UE) 2022/2065
- Stosowanie od 17.02.2024.
- **Art. 17:** uzasadnienie dla użytkownika przy ograniczeniu treści, płatności lub konta [wtórne].
- **Art. 16:** mechanizm zgłaszania nielegalnych treści — treści nie odczytano [niezweryfikowane].
- **Art. 25:** zakaz manipulacyjnych interfejsów (dark patterns) dla dostawców platform internetowych; nie obejmuje
  praktyk objętych dyrektywą 2005/29/WE ani RODO [wtórne].
- **Art. 19:** mikro i małe przedsiębiorstwa wyłączone z sekcji o platformach internetowych (poza art. 24 ust. 3);
  nie dotyczy bardzo dużych platform (VLOP). Art. 29 to osobna sekcja dla platform handlowych [wtórne].
- **W kodzie:** formularz zgłoszeń, rejestr decyzji moderacyjnych z uzasadnieniem, przegląd interfejsu pod kątem
  manipulacji (rezygnacja tak łatwa jak zapis).
- Źródło: springlex.eu (DSA, art. 19 i 25).

## Prawa konsumenta — dyr. 2011/83/UE po Omnibusie (2019/2161)
- Treści cyfrowe: konsument traci prawo odstąpienia po wyraźnym żądaniu natychmiastowego dostarczenia i przyjęciu
  do wiadomości utraty prawa (art. 16 lit. m); przy usłudze prawo wygasa po pełnym wykonaniu (art. 16 lit. a) [wtórne,
  brzmienie [niezweryfikowane]].
- Dyrektywa obejmuje też umowy, w których konsument „płaci” danymi osobowymi (art. 3 ust. 1a) [wtórne].
- Omnibus stosowany od 28.05.2022 [wtórne].
- Reguła ceny sprzed obniżki (art. 6a dyr. 98/6/WE): zakres wobec usług cyfrowych [niezweryfikowane].
- **Przycisk odstąpienia (art. 11a, dodany dyr. 2023/2673):** transpozycja do 19.12.2025, stosowanie od 19.06.2026.
  W Polsce brak transpozycji na 18.10.2026: projekt UC82 wycofany w maju 2026, nowy projekt od początku procedury
  [wtórne, jedno źródło: akademialtca.pl]. Sprawdź stan w ISAP przed decyzją.
- **W kodzie:** informacje przedkontraktowe przed płatnością, potwierdzenie na trwałym nośniku (e-mail), zgoda na
  natychmiastowe dostarczenie z utratą prawa odstąpienia (osobne pole), funkcja odstąpienia online.
- Źródła: fieldfisher.com (Omnibus), iubenda.com (right of withdrawal), akademialtca.pl (dyr. 2023/2673).

## KSeF — ustawa z 5.08.2025 (Dz.U. 2025 poz. 1203)
- Obowiązek: od 1.02.2026 podatnicy ze sprzedażą powyżej 200 mln zł w 2024 r.; od 1.04.2026 pozostali.
- Kary (art. 106ni ustawy o VAT): brak sankcji do 31.12.2026; od 1.01.2027 [wtórne].
- Zwolnienie przy sprzedaży do 10 tys. zł brutto miesięcznie: źródła sprzeczne (do końca 2026 albo inaczej)
  [niezweryfikowane].
- **W kodzie:** integracja z API KSeF (wysyłka, numer KSeF na fakturze, odbiór faktur zakupowych), tryb awaryjny,
  uprawnienia i tokeny w menedżerze sekretów.
- Źródła: mddp.pl (Tax Alert KSeF 2.0, 2.09.2025), amavat.pl, ksiegowosc.infor.pl.

## ViDA — dyr. (UE) 2025/516
- Opublikowana 25.03.2025, w mocy od 14.04.2025.
- Obowiązkowe e-fakturowanie i e-raportowanie transakcji wewnątrzunijnych B2B od 1.07.2030; harmonizacja krajowych
  systemów do 2035 [wtórne].
- Krajowe e-faktury bez zgody odbiorcy i bez derogacji Rady — data różni się w źródłach (25.03 albo 14.04.2025).
- Źródła: kpmg.com (ViDA publication), accountancyeurope.eu.
