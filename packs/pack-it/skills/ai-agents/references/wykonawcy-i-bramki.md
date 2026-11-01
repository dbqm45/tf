# Wielu wykonawców, świadek kroku i długie przebiegi

Spis treści: 1. Wielu wykonawców nad wspólnym stanem · 2. Kto jest świadkiem tego kroku · 3. Długie przebiegi w wielu
oknach kontekstu · 4. Interfejs harnessu od strony modelu

## 1. Wielu wykonawców nad wspólnym stanem
- **Dzierżawa zadania z wygaśnięciem i biciem serca.** Wykonawca, który zniknął, traci zadanie, a inny wznawia je
  z trwałego stanu.
- **Zakończenie i zapis sprawdzają bieżącego właściciela i wersję rekordu.** Spóźniony wykonawca nie nadpisze
  nowszego wyniku. Zapis całego rekordu ze starej kopii to utracona aktualizacja — przed zapisem sprawdzasz wersję
  (compare-and-set, be-database), używasz transakcji albo scalanie robi jeden koordynator.
- **Trzy różne operacje:** ponowienie (ta sama operacja jeszcze raz), wznowienie (z zapisanego stanu; najpierw
  sprawdzasz, czy wersje dokumentów i konfiguracji nadal pasują do przyjętej pracy) i kompensacja (osobna operacja
  biznesowa, która też może zawieść). Żadna nie jest uniwersalnym „cofnij”.
- **Ukończenie to predykat systemu, nie zdanie modelu:** wymagania spełnione, walidacja przeszła, artefakty są,
  polityki sprawdzone. Jawne wyjścia inne niż sukces: wyczerpany budżet, brak nowych dowodów, wymaganie do
  wyjaśnienia. Wynik częściowy oznaczony jako „szkic z zastrzeżeniami”, nie jako zatwierdzony.
- **Miara odzyskiwania:** ile ukończonej pracy wykonało się ponownie, czy zapisy zewnętrzne się zdublowały, czy
  przyjęte dowody nie zniknęły.

## 2. Kto jest świadkiem tego kroku
Krok, którego jedynym sprawdzeniem jest dalszy tekst tego samego modelu, jest przyjęty na wiarę. Reguła trafia
w miejsce zależne od tego, czego dotyczy:
| Reguła o… | Gdzie | Przykład |
|---|---|---|
| stanie | schemat lub kształt sprawdzany przy zapisie | „oferta ma pole `discount` 0–100” |
| jednej akcji | polityka per żądanie, domyślnie odmowa, `forbid` wygrywa z `permit` | „przelew tylko na konto z listy” |
| sekwencji akcji | reguła czasowa nad dziennikiem zdarzeń | „rabat > 20% tylko po zatwierdzeniu kierownika w ciągu 1 h” |

Werdykt bramki (wykonaj / odmów / eskaluj) jest powtarzalny dla tego samego zapisanego stanu. Reguła tylko w promptcie
albo werdykt zwracany wyłącznie agentowi niczego nie gwarantuje. Log zapisuje, który świadek sprawdził krok. Hook
`tdd_guard` w fabryce to przykład reguły czasowej („edycja kodu dozwolona, jeśli od ostatniej zmiany testu był
czerwony przebieg”).
Źródło: A. Alcaraz, „Grounded Reasoning For Agents…” (2026-10-20).

## 3. Długie przebiegi w wielu oknach kontekstu
Anthropic Engineering, „Effective harnesses for long-running agents” (2025-11-26) i „Harness design for long-running
application development” (2026-03-24), odczyt 2026-10-29:
- pierwsza sesja przygotowuje środowisko i listę zadań, każda kolejna robi jeden przyrost i zostawia artefakty
  przekazania (postęp, stan testów); samo kompaktowanie nie wystarcza — agent próbuje zrobić wszystko naraz
  i ogłasza koniec za wcześnie;
- oddzielny ewaluator z jawnymi kryteriami; reguła końca sprawdzana testem lub ewaluatorem, nie deklaracją agenta;
- recenzent tylko do odczytu (raport, nie poprawka — inaczej znika sygnał);
- narzędzia nieodwracalne z `dry_run` domyślnie włączonym;
- ścieżkę rozwiązujesz **przed** porównaniem z listą dozwolonych: lista zakazów łapie tylko przewidziane zapisy,
  a `work/../secrets` przechodzi (core-agent-security);
- reguła z promptu, która ma działać zawsze, przechodzi do hooka.

## 4. Interfejs harnessu od strony modelu
- Operacja (jednostka intencji) jest realizowana przez narzędzie, narzędzie złożone (kod, deterministycznie) albo
  skill (instrukcje). Dojrzewa od skilla do narzędzia złożonego, gdy kroki się ustalą.
- Skill odwołuje się do narzędzi po id, nie kopiuje ich schematów — jedno miejsce prawdy.
- Mały zestaw prymitywów (np. wyszukaj w pamięci, lista możliwości, wyszukaj i wczytaj operację, wykonaj, uruchom
  kod, zapytaj człowieka); zatwierdzenie wymusza harness, nie model.
- Kanały (Slack, Teams, głos) to adaptery normalizujące zdarzenie do jednej postaci — agent nie należy do kanału.
- Wybór kontekstu (pamięć, narzędzia) to często klasyfikacja, nie generowanie: tańszy selektor przed dużym modelem,
  mierzony na własnych danych (ai-evals).
