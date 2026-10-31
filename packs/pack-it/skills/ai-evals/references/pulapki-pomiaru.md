# Pułapki pomiaru i regresja ze śladów

Spis treści: 1. Granice wyniku · 2. Jedna zmienna naraz · 3. Dobór konfiguracji a test · 4. Etykieta i metryka składowa ·
5. Niezmienniki · 6. Manifest pary model + harness · 7. Regresja ze śladów · 8. Reguły jako podłoga · 9. Bramka zmiany harnessu ·
10. Raport i dobór wyroczni · 11. Klasyfikator decyzji · 12. Użyteczność z karą (agent odpowiadający liczbami)

Ciche błędy pomiaru częściej *poprawiają* metrykę niż ją psują, więc dobry wynik sprawdzasz tak samo jak zły.

## 1. Granice wyniku
Wynik systemu da się zinterpretować tylko wtedy, gdy znasz trzy punkty odniesienia policzone na tym samym zbiorze:
- **stała klasa większościowa** — model zawsze odpowiada „tak” (albo najczęstszą etykietą). 72% trafności przy 70%
  odpowiedzi „tak” w zbiorze to prawie nic;
- **ramię ślepe** — ten sam model bez kontekstu (bez wyszukiwania). Pokazuje, ile wie z samych wag;
- **wyrocznia** — model dostaje tylko złoty fragment. To sufit dla wyszukiwania.

System leży między ślepym ramieniem a wyrocznią. Jeśli oba przegrywają ze stałą klasą, to zbiór albo model nie
rozróżnia architektur: najpierw popraw zbiór, a dopiero potem porównuj grafy z wektorami.

## 2. Jedna zmienna naraz
- Każda stała w przetwarzaniu (obcięcie dokumentu, limit kandydatów, próg, liczba fragmentów) to hiperparametr.
  Zmieniasz jedną, pozostałe zamrażasz i zapisujesz.
- Ramiona porównawcze dostają **te same stałe**. Wyrocznia czytająca 4000 znaków wobec systemu czytającego 1100
  mierzy obcięcie, nie wyszukiwanie.
- Sprawdzaj, czy stała nie wyrzuca złotej odpowiedzi przed modelem. Przykład: limit kandydatów odcina złoty dokument
  w części pytań, czego nie naprawi żaden prompt.

## 3. Dobór konfiguracji a test
- Konfigurację wybierasz na zbiorze doboru, a wynik raportujesz **tylko z osobnego, odłożonego zbioru testowego**.
  Najlepsza z 40 konfiguracji na tych samych 200 przykładach jest zawyżona przez sam wybór.
- **Kontrola na przetasowanych etykietach:** powtórz wybór najlepszej konfiguracji po losowym przemieszaniu etykiet.
  Przewaga, którą dostajesz na szumie, to próg, poniżej którego zysk nic nie znaczy.
- Jeśli optimum leży na krawędzi siatki parametru, siatka jest za wąska — poszerz zakres, zanim ogłosisz wynik.

## 4. Etykieta i metryka składowa
- **Etykieta z rozkładu, nie z regexa.** Gdy model klasyfikuje, decyzję bierz z prawdopodobieństw tokenów etykiet
  (zsumuj warianty pisowni). Parsowanie wolnego tekstu daje ciche błędy, a ta sama wartość daje pewność, od której
  zależy odmowa odpowiedzi.
- **Metryka składowa musi modelować to, co dzieje się dalej.** Gorsza precyzja składnika (np. dopasowania pojęć) może
  dać lepszy system, gdy dalszy filtr odrzuca fałszywe trafienia. Oceniaj parę: pokrycie oraz przeciek na pytaniach
  kontrolnych (pytanie z jednym pojęciem podmienionym na losowe), a nie samą metrykę składnika.

## 5. Niezmienniki
- Struktury pochodne (równoległe tablice etykiet, identyfikatorów, wyników) mają asercję zgodności długości i kolejności
  oraz niezależne przeliczenie ze źródła na próbce. Rozjechane tablice nie rzucają błędu, tylko zmieniają wynik.
- Cache wyników ewaluacji kluczujesz **całym** wejściem (prompt, model, parametry, wersja zbioru), nie samym pytaniem.
- Walidator (cytatów, formatu) testujesz na przypadkach brzegowych, np. nawias z kilkoma identyfikatorami.

## 6. Manifest pary model + harness
Wynik ewaluacji należy do pary, nie do modelu. Do każdego raportu zapisz:
`model (pełny identyfikator) | skrót promptu | wersja schematów narzędzi | wersja polityki/rubryki | skrót obrazu
środowiska | wersja zestawu ewaluacji`. Zmiana dowolnego pola, także cicha zmiana modelu u dostawcy, to nowa para
do ponownego pomiaru.

## 7. Regresja ze śladów
- Każdy ślad z produkcji niesie **wersję kontraktu**: skrót promptu oraz politykę ewaluacji (słowa wymagane, minimum
  i maksimum wywołań narzędzi i modelu, wersja rubryki sędziego).
- Nową regułę deterministyczną puszczasz na **zapisanych śladach bez ponownego uruchamiania agenta**: tanio
  i powtarzalnie. Dolny limit wywołań narzędzia („musiał wyszukać”) łapie odpowiedź „sprawdź w serwisach X” bez
  wyszukania.
- Sędziego LLM puszczasz tylko na losowej próbce albo na śladach z negatywną oceną użytkownika (👎, ponowienie,
  eskalacja).
- **Niezmienne kopie wejść.** Dane wejściowe produkcji (logi, które wygasają po 7–30 dniach) archiwizujesz
  asynchronicznie, bez nadpisywania. Ewaluacje czytają archiwum, więc zmiana wyniku wynika z systemu, nie ze źródła.
- Ten sam zestaw działa lokalnie, na środowisku podglądu PR (progi blokują merge), po promocji (alarm do dyżurnego)
  i cyklicznie na produkcji (dryf).

## 8. Reguły jako podłoga regresji
Gdy LLM zastępuje lub uzupełnia istniejące reguły (regex, heurystyki):
- reguły działają dalej, a wynik LLM jest obok;
- ewaluacja sprawdza **włączenie**: czy to, co znalazła reguła, jest w wyniku LLM. Osobno mierzysz precyzję każdego
  elementu;
- mierzysz **szum na poziomie zbioru**: element obecny w ponad ok. 30% wyników to szum. Trafia na listę wykluczeń
  w kodzie, bo prompt go nie usunie;
- gdy model ma wskazać fragment wejścia, zwraca numery pierwszej i ostatniej linii, a tekst składa kod z własnej kopii.
  Treść nie może być zmyślona, ale zły zakres nadal może się zdarzyć, więc trafność zakresu mierzysz w ewaluacji.

## 9. Bramka zmiany harnessu
Zmiana promptu, skilla, hooka, opisu narzędzia lub schematu, ręczna albo z pętli samodoskonalenia:
1. W PR **przewidywanie**: które przypadki mają przejść z porażki na sukces i co grozi regresją.
2. Wynik względem zamrożonej linii bazowej **i** odłożonego zbioru. Zmianę przyjmujesz, gdy poprawia zbiór roboczy
   i nie pogarsza odłożonego. Różnica „roboczy kontra odłożony” to sygnał, że zmiana uczy się egzaminu.
3. Autor zmiany (człowiek albo agent) nie zmienia w tym samym PR scenariuszy, na których jest oceniany.
4. Potem wdrożenie albo wycofanie, z zapisem w raporcie.

## 10. Raport i dobór wyroczni
- **Główny sygnał gotowości to odsetek zadań zaliczonych w całości** (wszystkie kryteria rubryki). Średnia spełnionych
  kryteriów i rozrzut między powtórzeniami idą obok jako diagnostyka: raport wskazujący 8 z 10 ryzyk nie jest
  „w 80% użyteczny”. Średnia może być nagrodą w treningu, nie miarą w raporcie.
- **Wyrocznię zastępczą dobierasz do odwracalności działania:** asercja deterministyczna w pętli (stan bazy po
  rozmowie, ostatnie żądanie zgodne ze schematem), rubryka i weryfikator faktów pośrodku, człowiek przed działaniem
  nieodwracalnym. Przy pętli samodoskonalenia — zamrożony zbiór testowy i wersjonowany sędzia (§9).
- Porównanie harnessów lub modeli na **tych samych zasobach wykonania** (CPU, pamięć, limity czasu) i z tą samą liczbą
  powtórzeń — różnica wyniku może pochodzić z infrastruktury.

## 11. Klasyfikator decyzji (LLM jako klasyfikator)
- Test kolejności i nazw opcji: przetasuj i przemianuj opcje, policz zmiany odpowiedzi.
- Próg dopasowany na własnych etykietach **osobno dla każdego punktu decyzji**, nigdy domyślne 0,5.
- Kaskada (tani model, a drogi tylko przy niepewności) mierzona względem samego drogiego modelu.
- Szczególna ostrożność przy krokach nieodwracalnych: pewny błędny wybór to typowa porażka — tam niższy próg
  przekazania człowiekowi.
- Przed przypisaniem zysku dostrajaniu: kontrola na zamrożonym modelu bazowym z tym samym promptem.
- Zbiór testowy rozdzielony po przypadku (ten sam dokument nie trafia na obie strony), najlepiej zamknięty;
  publiczny benchmark się nasyca. Zmiana słów w definicjach opcji to zmiana modelu, więc ponowny test.
- Licencję sprawdzasz w pliku wag, modelu bazowym i danych, nie na odznace repozytorium.

## 12. Użyteczność z karą (agent odpowiadający liczbami)
- Cele zapisane przed pierwszą wersją agenta: trafność, odsetek złych odpowiedzi wśród udzielonych **razem
  z pokryciem**, p50 i p95 czasu.
- **Użyteczność z karą:** +1 dobra odpowiedź lub słuszna odmowa, 0 zbędna odmowa, −2 pewna zła liczba. Agent, który
  wszystkiemu odmawia, nie wygrywa, a ten, który zgaduje, przegrywa.
- Zmiana przyjęta, gdy użyteczność rośnie (albo stoi, a czas spada), z **parowanym bootstrapem** na tych samych
  pytaniach. Odkładasz **całe szablony pytań**, nie tylko instancje — wynik na nowych szablonach bywa wyraźnie niższy.
- Czas mierzysz pojedynczym użytkownikiem z pustym cache, nie tylko przy współbieżności ewaluacji.

Źródła: F. Khan, „Structuring 40 Million Documents into an Agentic Knowledge Graph” (2026-08-26, liczby z jego repo
[niezweryfikowane]); A. Punnen, „Eval-Driven Development” (2026-08-18); Netflix Tech Blog, „Making Failure Diagnosis
Reliable with Pensive AI” (2026-10); J. Wąsowski, „AI Harness Evolution: … Overfitting Without a Holdout” (2026-10-22);
F. Khan, „Engineering Multi-Agent AI for a 100 GB Data Warehouse” (2026-10); A. Alcaraz, „Grounded Reasoning For Agents”
(2026-10-20). Liczby autorów [niezweryfikowane].
Progi (30% szumu, 7–30 dni retencji) to przykłady z tych artykułów, nie reguły [założenie].
