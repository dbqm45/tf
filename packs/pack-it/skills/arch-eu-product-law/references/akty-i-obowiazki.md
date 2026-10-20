# Akty i obowiązki — szczegóły (stan na 2026-10-18)

Wszystkie fakty pochodzą ze źródeł wtórnych [wtórne] (dostęp 2026-10-18); EUR-Lex, ISAP i gov.pl były z sesji
niedostępne. Przed oddaniem mapy prawnikowi potwierdź w tekście aktu daty i artykuły, na których opiera się obowiązek.
DSA, prawa konsumenta, KSeF i ViDA — poza zakresem fabryki: `poza-zakresem-fabryki.md`.

## Data Act — rozp. (UE) 2023/2854
- **Dotyczy:** dostawców usług przetwarzania danych (IaaS, PaaS, SaaS) w zakresie zmiany dostawcy; także produktów
  skomunikowanych i danych z nich (osobny rozdział).
- **Zmiana dostawcy (art. 23–25):** klient może wypowiedzieć umowę z wyprzedzeniem nie dłuższym niż 2 miesiące;
  okres przejściowy 30 dni kalendarzowych; okres na odzyskanie danych co najmniej 30 dni [wtórne; ustępy i początek
  biegu terminów [niezweryfikowane], źródła różnią się]. Liczby „14 dni roboczych” i „7 miesięcy” krążą w szablonach
  umów — nie przyjmuj ich bez tekstu aktu.
- **Opłaty (art. 29):** do 12.01.2027 opłaty za zmianę i transfer danych (w tym egress) najwyżej w wysokości kosztów
  bezpośrednio związanych ze zmianą; od 12.01.2027 zakaz takich opłat [wtórne; jedno źródło podaje 11.01.2027 jako
  koniec okresu obniżek].
- **Stosowanie:** 12.09.2025 [niezweryfikowane].
- **W kodzie:** pełny eksport danych w formacie ustrukturyzowanym, dokumentacja formatów, brak opłat za egress
  przy zmianie dostawcy w cenniku, procedura zmiany dostawcy w umowie.
- Źródła: penningtonslaw.com (switching rights), maples.com (switching framework), mondaq.com (Data Act cloud contracts).

## PLD — dyr. (UE) 2024/2853
- Oprogramowanie jest produktem, także SaaS i rozwiązania w chmurze (motyw 13); sam kod źródłowy nie jest produktem.
- Wolne i otwarte oprogramowanie jest wyłączone tylko wtedy, gdy rozwijane lub dostarczane poza działalnością
  handlową; płatna usługa albo „płatność danymi osobowymi” przywraca status produktu (motyw 14).
- Transpozycja do 9.12.2026; nowe zasady dla produktów wprowadzonych do obrotu po tej dacie; starsze podlegają
  dawnemu reżimowi, chyba że zostały istotnie zmodyfikowane (np. aktualizacją) [wtórne; numery artykułów [niezweryfikowane]].
- **Stan w PL (2026-10-20) [wtórne]:** projekt ustawy o zmianie Kodeksu cywilnego i Kodeksu postępowania cywilnego
  (RCL, UC163) opublikowany 8.09.2026, skrócone konsultacje zakończone 22.09.2026; komentatorzy widzą ryzyko, że ustawa
  nie wejdzie w życie przed 9.12.2026. Projekt przebudowuje art. 449¹ i nast. k.c.
- **Treść projektu ważna dla budowy oprogramowania [wtórne]:**
  - produktem jest oprogramowanie, także system AI, SaaS i pliki produkcyjne (np. CAD);
  - producent odpowiada za wadę powstałą przez późniejszą modyfikację (aktualizacja, uczenie się systemu) albo przez
    brak aktualizacji bezpieczeństwa, dopóki produkt pozostaje pod jego kontrolą;
  - łagodniejszy ciężar dowodu: sąd może domniemać wadę, gdy sprawa jest technicznie skomplikowana (np. AI), a powód
    ma nadmierne trudności z dowodem; zmiany w k.p.c. dotyczą ujawniania dowodów przez pozwanego;
  - przedawnienie przy szkodzie na zdrowiu ujawniającej się po latach wydłużone z 10 do 25 lat.
- **W kodzie:** ślad wersji i aktualizacji (co, kiedy, komu), obsługa podatności i aktualizacje bezpieczeństwa przez
  cały okres kontroli nad produktem, dokumentacja techniczna i testów gotowa do ujawnienia w sporze (przy domniemaniu
  wady to ona jest dowodem producenta), przechowywana co najmniej tak długo jak okres odpowiedzialności.
- Źródła: arws.cz („Software as a defective product as of 9 December 2026”), ibanet.org (PLD and software), dostęp
  2026-10-18; lex.pl (odpowiedzialność za produkty wadliwe, PLD), gazetaprawna.pl, krk.legal (konsultacje projektu),
  webites.pl (PLD a oprogramowanie), twobirds.com (2025, przedawnienie), bakowski.net.pl (06.2026), wolftheiss.com
  (EU PLD tracker 2026) — dostęp 2026-10-20, przekazane przez człowieka. Tekstu projektu w RCL nie odczytano.

## Sąsiednie akty (szczegóły w ich skillach)
- **AI Act po rozp. (UE) 2026/1744** (Dz.U. UE 24.07.2026, w mocy 27.07.2026): wysokie ryzyko z załącznika III
  od 2.12.2027, z załącznika I od 2.08.2028; nowy zakaz i znakowanie systemów już na rynku od 2.12.2026 [wtórne].
  Ogólny termin art. 50 [niezweryfikowane] → ai-governance-compliance.
- **CRA 2024/2847:** zgłaszanie (art. 14) od 11.09.2026: 24 h wczesne ostrzeżenie, 72 h powiadomienie, raport
  końcowy 14 dni od udostępnienia poprawki (podatność aktywnie wykorzystywana) albo miesiąc (poważny incydent);
  reszta od 11.12.2027. Czysty SaaS zwykle poza zakresem (motyw 9), chyba że to zdalne przetwarzanie danych
  dla produktu [wtórne] → sec-eu-regulations.
- **EAA 2019/882:** w PL ustawa z 26.04.2024 (Dz.U. 2024 poz. 731), od 28.06.2025; wyłączenie mikroprzedsiębiorstw
  świadczących usługi [niezweryfikowane] → ux-accessibility.
