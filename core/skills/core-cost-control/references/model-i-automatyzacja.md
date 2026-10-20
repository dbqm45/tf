# Ocena nowego modelu, kontekst i agenci w automatyzacji
> i dane · 4. Kontekst — MCP, dryf, skan repo · 5. Przykład: decyzja o zmianie modelu

## 1. Ocena nowego modelu
**Jak czytać ranking.** Liczba w tabeli = zestaw zadań + metryka + protokół (harness, limit kroków, liczba prób).
Zanim ją porównasz, sprawdź wszystkie trzy:
- **zestaw** — czy mierzy Twój typ pracy (naprawa zgłoszonego błędu ≠ budowa nowej funkcji ≠ praca w terminalu);
  starsze zestawy się nasycają, a wyniki mogą odzwierciedlać zadania zapamiętane z danych treningowych;
- **metryka** — pass@1 („udało się przy pierwszej próbie”) zawyża niezawodność pętli. Agent wykonuje kroki
  po kolei, więc liczy się powtarzalność: przy 90% na krok pięć kroków z rzędu udaje się w ok. 59% (0,9⁵),
  dziesięć — w ok. 35%;
- **protokół** — ten sam model w różnych harnessach (inne narzędzia, prompt systemowy, plik instrukcji) potrafi
  różnić się o kilkanaście punktów; część pozycji w rankingach to harnessy strojone pod sam benchmark.
  Przy każdym wyniku zapisz, czy harness był **stały** (ten sam dla wszystkich modeli), czy **dowolny** (strojony
  pod model), oraz wersję modelu i ustawienia inferencji — bez tego liczby nie są porównywalne. W jednym preprincie
  sam harness dopasowany do modelu podniósł wynik z 29% do 78% bez zmiany wag (Yu i in., arXiv:2609.09134, v1
  8.09.2026, za omówieniem J. Wasowskiego, ok. 12.10.2026; jedno badanie [niezweryfikowane]).

**Jak decydować.**
1. Kandydat musi przejść ten sam test co obecny model: 3–5 prawdziwych zadań projektu (z historii zgłoszeń),
   ta sama weryfikacja (testy, build, `grounding_check`), najlepiej kilka powtórzeń.
2. Liczysz **koszt rozwiązanego zadania**: tokeny wejścia i wyjścia × liczba iteracji do zielonej weryfikacji +
   czas przeglądu człowieka. Tańszy token przy dwóch dodatkowych rundach poprawek to droższe zadanie.
3. Dla agentów zbudowanych w kodzie (recenzent w CI, triaż) — macierz przypadków × modeli w zestawie ewaluacji
   (eng-llm-features §8), także po zmianie harnessu przy tym samym modelu.
4. Zmianę domyślnego modelu zespołu zapisujesz z wynikiem testu (profil kosztów, `factory/config.yaml`), a nie
   z nagłówka ogłoszenia. Przegląd nowości co ok. 2 tygodnie wystarcza.

**Polecenie dla modelu rozumującego:** cel + twarde ograniczenia + mierzalne kryterium sukcesu. Nie narzucaj kroków
myślenia ani przykładowego rozwiązania — chyba że proces jest obowiązkowy (migracja danych, płatności,
bezpieczeństwo) albo model po 1–2 próbach nie trafia; wtedy poproś o 2–3 podejścia do wyboru.

## 2. Agenci w automatyzacji — koszt
| Dźwignia | Reguła |
|---|---|
| wyzwalacz | zdarzenie, które ma znaczenie (otwarcie PR, czerwony build, nowe zgłoszenie); filtr ścieżek lub etykieta, żeby PR z samą dokumentacją nie płacił za przegląd |
| triaż przed agentem | tani krok (liczba i ścieżki plików, rozmiar diffu, etykiety) przypisuje poziom ryzyka: niski → szybki tani przebieg, ścieżki krytyczne → mocniejszy model i zawsze człowiek |
| limit przebiegu | liczba tur **i** budżet w dolarach; pętla bez górnego limitu kroków zakazana |
| narzędzia | oceniacz bez narzędzi (1–2 tury); każde dodane narzędzie to kolejne tury i tokeny |
| wejście | z diffu odfiltrowane lockfile'e, kod generowany, zrzuty — koszt i szum |
| model per rola | triaż/etykiety — najtańszy; rozumowanie nad kodem — średni; drogi tylko dla ścieżek krytycznych |
| pomiar | koszt, tury i czas z wyniku każdego przebiegu do tabeli lub dashboardu: per PR, per poziom triażu, per tydzień |
| pętla zwrotna | co miesiąc: gdzie człowiek tylko przyklepał werdykt (można poluzować triaż), gdzie błąd przeszedł przez zielony przegląd (nowy przypadek w ewaluacji) |

Uruchamianie z wiersza poleceń: `claude -p "<zadanie>" --max-budget-usd <kwota> --allowedTools "<lista>"`
(budżet działa tylko z `--print`). Limit tur w CLI i w akcjach CI sprawdź w dokumentacji swojej wersji
[`--max-turns` nie jest wypisany w `claude --help` 2.1.296 — niezweryfikowane]. Nazwy opcji SDK:
`.claude/skills/eng-llm-features/references/sdk-api.md`.

## 3. Uwierzytelnienie a rachunek i dane
- **Klucz API** (warunki komercyjne, rozliczenie za tokeny) — domyślny wybór dla kodu firmy i każdej automatyzacji.
- **Login subskrypcji** — SDK i `claude -p` mogą po cichu użyć logowania dewelopera, gdy brak klucza. Obowiązują
  wtedy warunki konsumenckie (inne domyślne ustawienia trenowania i retencji) i limity planu; użycie programistyczne
  na planach subskrypcyjnych bywa liczone z osobnej puli [niezweryfikowane — sprawdź aktualne warunki i cennik
  przed wdrożeniem].
- W CI ustawiasz klucz z sekretu jawnie i sprawdzasz, że przebieg go używa (brak cichego przejścia na login).

## 4. Kontekst — MCP, dryf, skan repo
- **MCP:** definicje narzędzi każdego podłączonego serwera wchodzą do każdego zapytania. Serwer z dziesiątkami
  narzędzi kosztuje nawet wtedy, gdy go nie używasz. Wybieraj serwery z kilkoma uniwersalnymi narzędziami (wyszukaj
  operację + wykonaj), wyłączaj nieużywane przed sesją (nie w trakcie — to kasuje cache), a operacje o znanym
  poleceniu rób przez CLI (jawne, zostają w historii).
- **Dryf kontekstu** (objawy w `SKILL.md` §6): środek długiego wejścia dostaje mniej uwagi, a podobne, lecz
  nietrafne fragmenty działają jak dystraktory — dlatego jakość spada przed zapełnieniem okna. Reakcja: punkt
  kontrolny (core-project-record) → nowa sesja → plan i postęp → faza od początku. Dwie nieudane poprawki tego
  samego błędu to też sygnał do świeżego kontekstu (core-grounding).
- **Szeroki skan repo:** inwentarz, historia gita, graf zależności zbiera skrypt lub CLI, a tani model streszcza
  wynik; mocny model dostaje skondensowany raport i pogłębia jeden przepływ (eng-codebase-mapping).

## 5. Przykład: decyzja o zmianie modelu
**Sytuacja:** nowy model ma w publicznym rankingu o 5 punktów więcej; zespół chce przestawić go dla agentów w CI.

**Jak:**
1. Ranking: zestaw dotyczy naprawy zgłoszeń, a agent w CI robi przegląd PR — inny typ pracy.
2. Test: 5 zamkniętych PR z historii (2 z błędem wykrytym później przez człowieka, 3 czyste) × obecny i nowy model,
   po 3 powtórzenia; zestaw ewaluacji recenzenta z asercjami.
3. Wynik: nowy model łapie oba błędy w 3/3 powtórzeń (obecny w 2/3), ale daje 1 fałszywy alarm na czystym PR
   i zużywa o 40% więcej tokenów na przebieg.

**Wynik:**
```
Decyzja: nowy model tylko dla PR z poziomem triażu „krytyczny” (auth, płatności, migracje);
reszta zostaje na obecnym. Koszt per PR mierzony 2 tygodnie, potem przegląd decyzji.
Fałszywy alarm → nowy przypadek w zestawie ewaluacji i doprecyzowane kryteria przeglądu.
```
