# Pytanie o brakującą informację

Agent, który zgaduje brakujące dane, robi błędy, które wyglądają na poprawną pracę: adres z poprzedniego zamówienia,
termin „za tydzień”. Agent, który pyta o wszystko, przerzuca pracę na człowieka i uczy go klikać „tak” bez
czytania. Oba błędy biorą się z tego samego: braku reguły, kiedy szukać, kiedy założyć, a kiedy zapytać.

## 1. Kiedy pytać

| Sytuacja | Co robi agent |
|---|---|
| Informacja jest do znalezienia: w kontekście, w plikach, w CRM, w historii zamówień, przez API | **szuka** narzędziem; nie pyta |
| Brak jest tani i odwracalny (format raportu, kolejność sekcji, drobna wartość) | **zakłada** rozsądną wartość domyślną, zapisuje założenie w wyniku i idzie dalej |
| Potrzebna jest decyzja człowieka: preferencja, kompromis, zgoda na koszt lub ryzyko | **pyta** |
| Brakuje danych, których nie da się uzupełnić (źródła sprzeczne, brak uprawnień, pole puste w systemie) i od których zależy wynik | **pyta** |
| Akcja jest nieodwracalna albo kosztowna, a dane są niepewne | **pyta przed akcją** (zatwierdzenie: `references/wykonawcy-i-bramki.md`, krok 6 SKILL.md) |

Reguła „zawsze pytaj, gdy nie masz pewności” jest za szeroka: pewności nie ma prawie nigdy. Pytaj, gdy błąd byłby
drogi, a odpowiedzi nie da się zdobyć samemu.

## 2. Najpierw narzędzia
- Zanim agent zapyta, sprawdza miejsca, w których informacja może być. Ich listę zapisujesz w prompcie narzędzia
  albo w kodzie: CRM, poprzednie zamówienia, ustawienia konta, dokumenty sprawy.
- W pytaniu pokazuje, co sprawdził („w zamówieniu i w profilu klienta nie ma adresu dostawy”). Człowiek nie musi
  wtedy powtarzać, a ewaluacja widzi, czy agent naprawdę szukał.

## 3. Forma pytania
- **Jedno konkretne pytanie** albo wszystkie niezależne pytania naraz, nie seria po jednym.
- **Opcje z rekomendacją i skutkiem** („A: adres siedziby — dostawa jutro; B: adres magazynu z poprzedniego
  zamówienia — potwierdź, że aktualny; rekomenduję A, bo…”). Wolny tekst tylko wtedy, gdy opcji nie da się podać.
- **Wartość domyślna przy braku odpowiedzi**, jeśli jest bezpieczna, z terminem („bez odpowiedzi do 14:00
  wstrzymuję wysyłkę”). Przy akcji nieodwracalnej brak odpowiedzi oznacza brak akcji, a nie zgodę.
- Pytanie trafia do właściwej osoby kanałem, którego ona używa (zgłoszenie, czat, e-mail), z identyfikatorem
  przebiegu.

## 4. Pauza i wznowienie
- **Punkt kontrolny przed pytaniem:** cel, wykonane kroki z wynikami, pytanie, identyfikator przebiegu. Pauza nie
  może trzymać procesu ani okna kontekstu: odpowiedź przychodzi po godzinach albo dniach.
- **Wznowienie od punktu kontrolnego**, z odpowiedzią jako nowym wejściem, a nie od zera.
- LangGraph (sprawdzone w `langgraph` 1.2.20, `langgraph/types.py`):
  - `interrupt(value)` w węźle zatrzymuje graf i przekazuje `value` (np. pytanie z opcjami) klientowi;
  - wznowienie przez `Command(resume=odpowiedź)`;
  - wymagany jest checkpointer;
  - **po wznowieniu węzeł wykonuje się od początku**, więc kod przed `interrupt` (zapis, wysyłka, płatność)
    musi być idempotentny albo przeniesiony do osobnego węzła po pytaniu.
- Ta sama zasada bez frameworka: stan w bazie z identyfikatorem przebiegu, status „czeka na człowieka”,
  zdarzenie z odpowiedzią wznawia przebieg (trwałe wykonanie: `references/pamiec-i-trwale-wykonanie.md`).
- Pytanie bez odpowiedzi ma termin i eskalację. Przebieg nie wisi bez końca w stanie „czeka”.

## 5. Antywzorce
- Pytanie o coś, co agent ma w narzędziach albo w kontekście.
- Seria pytań po jednym, każde po kolejnym kroku.
- Zgadywanie przy decyzji nieodwracalnej albo cudzej (adres dostawy, kwota, odbiorca).
- Pytanie bez opcji i bez rekomendacji („co mam zrobić?”).
- Pauza bez zapisu stanu: odpowiedź przychodzi, a przebieg zaczyna się od nowa i powtarza skutki uboczne.
- Pytanie zadane, ale niewidoczne w śladzie przebiegu (tracing, krok 8 SKILL.md), więc nie da się go zmierzyć.

## 6. Miary i ewaluacja
- **Zbędne pytania:** odsetek pytań, na które odpowiedź była dostępna narzędziem.
- **Zgadywanie:** odsetek przebiegów, w których agent założył wartość, a powinien był zapytać. Wykrywasz to po
  poprawkach człowieka i reklamacjach.
- **Czas oczekiwania** na odpowiedź i odsetek pytań bez odpowiedzi w terminie.
- Zbiór ewaluacyjny ma oba rodzaje przypadków (ai-evals, pack-it):
  - „trzeba zapytać”: brak, którego nie da się uzupełnić;
  - „nie trzeba”: dane są w narzędziach albo brak jest tani do założenia.
  Sam pierwszy rodzaj nagradza agenta, który pyta o wszystko.
