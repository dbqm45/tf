---
name: ux-research-methods
description: Użyj przy badaniach z użytkownikami (UX Research, ResearchOps) — pytanie badawcze, dobór metody, plan, rekrutacja, zgody RODO, synteza, repozytorium.
metadata:
  przeglad: 2027-10-17
  katalog: "Użyj, gdy trzeba zaplanować i przeprowadzić badanie z użytkownikami — od pytania badawczego przez dobór metody (wywiady, testy użyteczności moderowane i niemoderowane, ankiety, badania dzienniczkowe, benchmark konkurencji, badania włączające), plan badania, rekrutację i screener, zgodę i RODO uczestników, prowadzenie sesji, heurystyki wielkości próby z zastrzeżeniami, syntezę (mapowanie powinowactwa, atomowe nuggets, synteza wspomagana AI ze sprawdzeniem przez człowieka), repozytorium badań i ResearchOps (panel, backlog, playbooki) aż po zamianę ustaleń na decyzje; artefakty research-plan.md i research-report.md. Nie do decyzji co budować, drzewa szans, JTBD i testów założeń (proc-product-discovery), heurystyk i testu użyteczności w trakcie projektowania (ux-feature-design), UAT (qa-exploratory-manual), statystyki (data-analysis), DPIA (arch-privacy-compliance) ani architektury informacji (ux-information-architecture)."
  slowa: "badania użytkowników, UX research, wywiady z użytkownikami, wywiad pogłębiony, badanie jakościowe, test użyteczności, ankieta, diary study, badanie dzienniczkowe, rekrutacja uczestników, screener, panel badawczy, zgoda uczestnika, nagrywanie sesji, ilu uczestników, ile osób, synteza badań, mapowanie powinowactwa, insighty, repozytorium badań, ResearchOps, raport z badań, pytanie badawcze, plan badania, moderowanie sesji"
---

# Badania z użytkownikami — od pytania do decyzji

Badanie istnieje po to, by zmienić konkretną decyzję. Bez decyzji, którą ma ustawić, zostaje zbiór cytatów.
Skill prowadzi od pytania do raportu; **co** budować (drzewo szans, JTBD, testy założeń) rozstrzyga
**proc-product-discovery**, a heurystyki i szybkie testy w trakcie projektowania **ux-feature-design**
(`.claude/skills/ux-feature-design/references/heurystyki-i-testy.md`). Ten skill zaczyna się tam, gdzie potrzebne jest prawdziwe badanie.

## Procedura
1. **Decyzja i pytanie.** Zapisz: jaką decyzję zmieni wynik, kto ją podejmie i do kiedy. Z niej wyprowadź 1–3
   pytań badawczych (nie pytań do uczestników). Złe: „Czy podoba się nowy onboarding?”. Dobre: „Gdzie w pierwszym
   tygodniu użytkownicy porzucają konfigurację i z jakiego powodu?”. Wiadomo już, co robią (dane) — pytaj dlaczego.
2. **Metoda** — tabela w `references/metody-i-proba.md`. Reguła skrótu: *dlaczego i jak* → jakościowe (wywiad,
   test moderowany, dzienniczek); *ile i jak często* → ilościowe (ankieta, analityka, test niemoderowany na próbie);
   *kontekst w czasie* → dzienniczek lub obserwacja; *jak wypadamy na tle innych* → benchmark. Dwie metody
   o różnej naturze (jakościowa + ilościowa) dają mocniejszy wniosek niż jedna.
3. **Plan badania** `docs/project/01-discovery/research-plan.md` wg `references/szablon-planu-i-raportu.md`: decyzja,
   pytania, metoda z uzasadnieniem, uczestnicy i liczba, harmonogram, materiały, ryzyka, kto obserwuje, sposób
   zapisu i retencja danych. Plan pokaż interesariuszom **przed** rekrutacją — zgoda na pytania kosztuje mniej niż spór o wyniki.
4. **Uczestnicy i screener.** Kryteria wynikają z pytania (zachowanie, nie demografia: „fakturowało w ostatnich
   3 miesiącach”). Screener: 5–10 pytań, nie zdradza kryteriów, pytania o zachowanie z odpowiedziami do wyboru
   i opcją „żadne z powyższych”, pytanie wykluczające pracowników firmy i konkurencji. Włącz osoby z potrzebami
   dostępności i z niską biegłością cyfrową — to część prób, nie dodatek (`references/rekrutacja-zgody-rodo.md`).
   Rekrutuj z zapasem na niestawiennictwo (zwykle +20–30% [założenie — dostosuj do własnego panelu]).
5. **Zgoda i RODO — przed pierwszą sesją.** Informacja (administrator, cel, podstawa, odbiorcy, okres
   przechowywania, prawa), osobna zgoda na nagrywanie, wycofanie w dowolnym momencie bez konsekwencji, dane
   minimalne. Szczegóły i wzór: `references/rekrutacja-zgody-rodo.md`. Duża skala, dane szczególne, dzieci albo
   profilowanie → ocena skutków (DPIA) w **arch-privacy-compliance**.
6. **Pilotaż** na 1 osobie z zespołu lub spoza niego: czy zadania i pytania są zrozumiałe, czy narzędzia nagrywają,
   ile naprawdę trwa sesja. Poprawki przed właściwymi sesjami.
7. **Sesja.** Neutralny moderator, pytania otwarte („opowiedz o ostatnim razie, gdy…”), ciche sekundy, brak
   podpowiadania; w teście zadań myślenie na głos. Drugi obserwator notuje na bieżąco (czas, cytat, zdarzenie),
   bez interpretacji w czasie sesji. Uczestnik może przerwać w każdej chwili. Pytania i pułapki:
   `references/prowadzenie-sesji.md`.
8. **Synteza** — po 2–3 sesjach zaczynasz porządkować, nie dopiero na końcu. Obserwacje → atomowe nuggets
   (jedna obserwacja, cytat, źródło) → grupowanie (mapowanie powinowactwa) → wzorce → ustalenia z pewnością
   (ilu uczestników, jaka jakość dowodu). AI może streszczać i proponować grupy, ale **każde ustalenie człowiek
   sprawdza z cytatem w transkrypcie**; ustalenie bez cytatu odpada. Szczegóły: `references/synteza-i-repozytorium.md`.
9. **Raport** `docs/project/01-discovery/research-report.md`: TL;DR z decyzją i rekomendacją na górze, ustalenia
   z dowodami i pewnością, rekomendacje z właścicielem i terminem, ograniczenia badania (próba, metoda), czego nie
   wiemy. Kończ zapisem w repozytorium badań (tagi, nuggets, zgody i daty usunięcia danych). Panel, backlog
   badań i playbooki to ResearchOps — `references/synteza-i-repozytorium.md`.
10. **Z ustaleń do decyzji.** Warsztat z zespołem w ciągu tygodnia: ustalenie → decyzja (zrobić / zmienić / zbadać
    dalej / odrzucić) → właściciel. Po wdrożeniu sprawdź, czy wskaźnik z planu się poruszył. Hipotezy do dalszych
    testów przekaż do proc-product-discovery; wyniki liczbowe z dużych prób do data-analysis.

## Wielkość próby — heurystyki z zastrzeżeniami
- Test jakościowy: ok. 5 osób na segment, w **kilku małych rundach** z poprawkami między nimi; to nie jest gwarancja
  wykrycia 85% problemów — model zakłada podobne zadania i jednorodną grupę.
- Wywiady: licz do nasycenia (nowe sesje nie dają nowych wątków); zwykle 5–8 na segment na start [założenie].
- Ilościowo (ankieta, niemoderowany test): liczba wynika z potrzebnej precyzji, nie z reguły kciuka; policz ją
  z data-analysis. Dla pomiarów w teście użyteczności kilkadziesiąt osób (`references/metody-i-proba.md`).
- Więcej segmentów = próba na każdy segment.

## Przykład
Wejście: „Nowi klienci aplikacji do fakturowania ‘Fakturka’ rezygnują w pierwszym tygodniu. Zaplanuj badanie.”
Wynik (fragment `research-plan.md`):

```markdown
## Decyzja i pytania
Decyzja: czy w Q1 przebudować konfigurację konta (Anna K., PM, do 15.11).
P1: Na którym kroku konfiguracji nowi użytkownicy porzucają ją i co im wtedy przeszkadza?
P2: Czego oczekują od aplikacji po pierwszym dniu?
## Metoda
Wywiady pogłębione 45 min (P2, kontekst) + moderowany test konfiguracji na prototypie (P1), zdalnie.
## Uczestnicy
8 osób zarejestrowanych w ostatnich 30 dni, które nie wystawiły faktury w 7 dni (2 z czytnikiem ekranu);
rekrutacja 10 osób, zapas 2. Screener: 6 pytań o zachowanie.
## Dane
Nagranie ekranu i głosu za osobną zgodą; transkrypty bez nazwisk; usunięcie nagrań 90 dni po raporcie [do uzgodnienia z IOD].
```

W raporcie: „Ustalenie U1: 6/8 osób nie rozumie pola ‘NIP nabywcy’ przy pierwszej fakturze (cytaty C3, C5, C8…)
→ decyzja: dodać podgląd GUS, właściciel Anna K.”

## Checklista
- [ ] decyzja, właściciel i termin zapisane; pytania badawcze odróżnione od pytań do uczestników
- [ ] metoda uzasadniona pytaniem; liczba uczestników z zastrzeżeniem, co z niej wynika
- [ ] screener o zachowaniach, uczestnicy z potrzebami dostępności uwzględnieni
- [ ] informacja i zgoda (nagrywanie osobno), wycofanie, retencja z datą usunięcia
- [ ] pilotaż; moderator neutralny; obserwator notuje
- [ ] każde ustalenie z cytatem i pewnością (także gdy syntezę robiła AI)
- [ ] raport z TL;DR, rekomendacjami z właścicielem i ograniczeniami; zapis w repozytorium

## Materiały dodatkowe
- `references/metody-i-proba.md` — tabela metod, wielkość próby z zastrzeżeniami; czytaj przy wyborze metody.
- `references/szablon-planu-i-raportu.md` — szablony research-plan.md i research-report.md.
- `references/rekrutacja-zgody-rodo.md` — screener, panel, zgoda, RODO uczestników, projekt włączający.
- `references/prowadzenie-sesji.md` — scenariusz, pytania, błędy moderatora.
- `references/synteza-i-repozytorium.md` — nuggets, mapowanie powinowactwa, synteza z AI, ResearchOps.

## Źródła
- Nielsen, „Why You Only Need to Test with 5 Users” (NN/g, 2000) — model 1−(1−L)^n, L≈31%, 5 osób ≈85%; wtórne
  streszczenia sprawdzone 2026-10-17, oryginału nie otwarto [niezweryfikowane].
- GOV.UK Service Manual, „Find user research participants” i „Running research sessions with disabled people”
  (wyszukiwanie 2026-10-17; treści stron nie otwarto) — uczestnicy to rzeczywiści lub potencjalni użytkownicy, w tym osoby
  niepełnosprawne i o niskich umiejętnościach cyfrowych.
- ISO 9241-210:2019 — projektowanie zorientowane na człowieka jako proces iteracyjny (opis z katalogów norm,
  2026-10-17; cztery czynności z wiedzy własnej [niezweryfikowane]).
- RODO (2016/679) art. 5, 6, 7, 13 — numery artykułów z wiedzy własnej, treści rozporządzenia w sesji nie otwarto
  [niezweryfikowane]; wtórny poradnik potwierdził obowiązek informacyjny przed zgodą i prawo wycofania (2026-10-17).
Opisane własnymi słowami.
