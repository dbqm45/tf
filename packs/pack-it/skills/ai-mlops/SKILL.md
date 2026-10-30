---
name: ai-mlops
description: Użyj przy cyklu życia modelu ML lub LLM w produkcji — rejestr, cechy, trenowanie w potoku, wdrożenie, drift, prompty (MLOps, LLMOps).
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy model uczenia maszynowego albo funkcja LLM ma przejść z notebooka do utrzymywanej produkcji — poziom dojrzałości MLOps (Google 0–2), śledzenie eksperymentów (MLflow), wersjonowanie danych (DVC, lakeFS), rejestr modeli z aliasami i bramkami promocji, magazyn cech (Feast) i training-serving skew, dobór orkiestratora trenowania (Kubeflow Pipelines, Airflow, Dagster), continuous training, testy danych i bramki jakości modelu (także fairness), wdrożenie modelu (shadow, canary, A/B, wycofanie), monitoring (drift danych i koncepcji, jakość przy opóźnionych etykietach, opóźnienie, koszt), reprodukowalność, karta modelu, LLMOps (rejestr promptów, ewaluacje w CI, tracing, koszt zapytania, metryki barier ochronnych); wynik to projekt potoku MLOps albo lista gotowości. Nie do samych potoków danych (data-engineering), ogólnego CI/CD (ops-ci-cd) i strategii wydań (ops-release-engineering), ogólnego monitoringu (ops-observability), hostowania modeli na GPU (ops-ai-inference), metod ewaluacji (ai-evals) ani doboru modelu statystycznego (data-analysis)."
  slowa: "mlops, llmops, model w produkcji, wdrożenie modelu, notebook do produkcji, MLflow, rejestr modeli, model registry, feature store, Feast, training-serving skew, DVC, lakeFS, wersjonowanie danych, retraining, dotrenowanie modelu, continuous training, drift, data drift, concept drift, opóźnione etykiety, shadow deployment, canary modelu, karta modelu, model card, reprodukowalność, Kubeflow, Dagster, prompt registry, wersjonowanie promptów, zmiana promptu w produkcji, regresja po zmianie promptu, rachunek za tokeny, koszt na zapytanie, tracing LLM, guardrails"
---

# MLOps i LLMOps — od notebooka do utrzymywanej produkcji

Model jest kodem, danymi i parametrami naraz, a psuje się bez zmiany kodu (zmieniły się dane). Skill prowadzi od
poziomu dojrzałości do projektu potoku: co wersjonować, co testować, co monitorować i kiedy dotrenować.
Nie buduj więcej, niż wymaga poziom ryzyka i częstość zmian.

## Procedura
1. **Kontekst.** Ustal: rodzaj (klasyczny ML czy LLM), koszt błędu, jak często zmieniają się dane, **jak późno
   przychodzi etykieta** (godziny czy 90 dni), kto utrzymuje model. Brakujące odpowiedzi zapisz jako założenia.
2. **Poziom dojrzałości** (model Google; źródło w Źródłach). Wybierz cel, nie najwyższy:

   | Poziom | Cecha | Wystarcza, gdy |
   |---|---|---|
   | 0 — ręczny | notebook, ręczne przekazanie modelu do wdrożenia | model zmienia się rzadko, błąd tani |
   | 1 — potok trenowania | zautomatyzowany potok, walidacja danych i modelu, continuous training, rejestr | dane się zmieniają, retrening co tydzień/miesiąc |
   | 2 — CI/CD potoku | testy i budowa potoku w CI, automatyczne wdrożenie potoku i modelu | wiele modeli lub zespołów, częste zmiany kodu |

   Pierwszy krok od notebooka do potoku to **walidacja danych przed treningiem** (schemat, zakresy, rozkład względem
   poprzedniej wersji); bez niej continuous training automatycznie uczy model na zepsutych danych.
3. **Eksperymenty i reprodukowalność.** Każdy przebieg zapisuje: parametry, metryki, **hash danych**, commit,
   środowisko (lockfile lub obraz), ziarna losowości, wersję cech. Test: czy za 6 miesięcy odtworzysz model
   z samego zapisu? MLflow Tracking to standard; wybór narzędzia mniej ważny niż kompletność zapisu (lineage).
4. **Wersjonowanie danych.** DVC — dane i potok (`dvc.yaml`, `dvc.lock`) obok kodu w repo, dowolny magazyn
   obiektowy; lakeFS — gałęzie i commity na całym jeziorze danych bez kopiowania. Dane już w tabelach z podróżą
   w czasie (Iceberg, Delta) → zapisz identyfikator migawki zamiast osobnego narzędzia. Potoki danych: data-engineering.
5. **Rejestr i promocja.** Wersja modelu w rejestrze wskazuje przebieg, dane, metryki i kartę modelu. Promocję
   oznacz **aliasami** (`champion`, `challenger`), nie etapami — w MLflow etapy są wycofywane od 2.9. Promocja to
   bramka (krok 8), nie ręczne kliknięcie. Kod ładuje model po aliasie, więc wycofanie = przestawienie aliasu.
6. **Cechy i skew.** Training-serving skew powstaje, gdy cecha jest liczona inaczej offline i online, albo gdy
   trening „widzi przyszłość”. Dwie drogi: magazyn cech (Feast: spójne definicje, odczyt historyczny
   **point-in-time**, magazyn online) albo jedna biblioteka transformacji używana w obu miejscach. Magazyn cech
   opłaca się od ~kilku modeli współdzielących cechy lub online ze świeżymi cechami. **Test skew:** dla próbki
   encji i znaczników czasu porównaj cechy online z offline; zbyt duża różnica blokuje wdrożenie.
7. **Orkiestracja trenowania** (ogólne zasady orkiestracji — data-engineering). Dobór wg kryteriów:
   - Kubeflow Pipelines — już jest Kubernetes, kroki jako kontenery, GPU, wielu zespołów; koszt: utrzymanie klastra;
   - Airflow — orkiestrator już działa, trening to jeden z wielu przepływów, harmonogram i integracje;
   - Dagster — model jako zasób danych z lineage i partycjami, nacisk na testowalność lokalną;
   - usługa chmurowa (Vertex AI Pipelines, SageMaker), gdy chmura jest ustalona i nie chcesz utrzymywać platformy.
8. **CI/CD/CT modelu** (mechanika pipeline'u — ops-ci-cd). Cztery warstwy testów:
   - kod: testy jednostkowe transformacji i funkcji straty;
   - **dane:** schemat, zakresy, braki, rozkład względem referencji; pod kontraktem danych;
   - **model (bramka jakości):** metryka nie gorsza niż `champion` o ustalony margines, **na plastrach** (segmenty,
     rzadkie klasy), nie tylko średnio; latencja i rozmiar; **fairness** — różnice metryk między grupami poniżej
     progu uzgodnionego z biznesem i prawnikiem;
   - integracja: kontrakt serwowania (wejście, wyjście, wersja cech).

   Wyzwalacze continuous training: harmonogram, nowe dane, alert driftu — każdy z limitem częstości i kosztu.
9. **Wdrożenie modelu** (mechanika — ops-release-engineering; serwowanie — ops-ai-inference). Specyfika:
   **shadow** (nowy model liczy równolegle, bez wpływu na wynik — porównujesz predykcje i latencję) → **canary**
   (mały ułamek ruchu z bramką metryk) → **A/B** (gdy liczy się metryka biznesowa; policz moc i czas trwania
   z góry). Wycofanie: alias na poprzednią wersję; sprawdź, że stare cechy nadal są dostępne.
10. **Monitoring** (ogólne metryki i alerty — ops-observability). Warstwy ponad nimi:
    - **drift cech** (PSI, test Kołmogorowa–Smirnowa, odległość Jensena–Shannona) i jakość danych (braki, nowe kategorie);
    - **drift predykcji** (rozkład score lub klas) — działa bez etykiet;
    - **jakość przy opóźnionych etykietach:** metryka liczona na dojrzałych kohortach (np. rocznik sprzed 90 dni)
      plus wskaźniki zastępcze (drift predykcji, odsetek niskiej pewności); alert na etykietach zamiast na wczorajszych danych jest spóźniony;
    - **concept drift** (zmieniła się zależność cech od celu) widać dopiero w etykietach lub w eksperymencie;
    - opóźnienie, błędy i koszt na predykcję.

    Każdy alert ma akcję: dotrenuj, wycofaj albo zbadaj; progi PSI traktuj jako punkt startu do kalibracji.
11. **Dokumentacja.** Karta modelu (przeznaczenie, dane, metryki na plastrach, ograniczenia, ryzyka, właściciel,
    data przeglądu) trafia do rejestru razem z wersją. Wymogi prawne — arch-privacy-compliance.
12. **LLMOps.** Różnice względem klasycznego ML:
    - **prompt jako artefakt:** rejestr z wersjami i aliasami, zmiana przez PR, nie edycja na żywo;
    - **zestaw ewaluacyjny w CI** uruchamiany przy zmianie promptu, modelu, parametrów i narzędzi (metoda, sędzia,
      dobór przypadków — ai-evals); zmiana wersji modelu u dostawcy to zmiana wydania;
    - **tracing** każdego zapytania (kroki, narzędzia, tokeny, latencja) i ocena próbki ruchu produkcyjnego tymi samymi ocenami;
    - **koszt na zapytanie** = tokeny wejścia i wyjścia × cennik, z podziałem na funkcję; budżet i alert;
    - **metryki barier ochronnych:** odsetek odmów, wykrytych danych osobowych, prób wstrzyknięcia poleceń,
      odpowiedzi bez oparcia w źródłach. Kod aplikacji z LLM — eng-llm-features.

## Wynik
Dokument „Projekt potoku MLOps” (`docs/project/…`): poziom docelowy, diagram etapów, tabela
artefaktów (co, gdzie, kto), bramki z progami, plan monitoringu z akcją na alert, luki i kolejność wdrożenia.
Szablon i lista gotowości: `references/projekt-i-gotowosc.md`.

## Przykład
Wejście: „Model churnu, trenowany w notebooku, wdrażany ręcznie co kwartał; etykieta po 90 dniach.”
Wynik (fragment): poziom 0 → cel 1 (nie 2: jeden model, jeden zespół). Dane w DVC (`dvc.lock` w repo), przebiegi
w MLflow z hashem danych, rejestr z aliasem `champion`. Airflow już działa → potok `train_churn` raz w miesiącu.
Bramka: AUC ≥ champion − 0,005 oraz AUC w segmencie „nowi klienci” ≥ 0,70; różnica recall między grupami wiekowymi
≤ 5 pp. Wdrożenie: shadow 7 dni, potem canary 10%. Monitoring dziennie: PSI cech (>0,25 = alert), drift score;
jakość tygodniowo na kohorcie sprzed 90 dni. Alert driftu → decyzja człowieka, nie automatyczny retrening.

## Checklista
- [ ] poziom obecny i docelowy uzasadnione; opóźnienie etykiety zapisane
- [ ] przebieg odtwarzalny: dane (hash), kod (commit), środowisko, ziarna, cechy
- [ ] rejestr z aliasami; promocja tylko przez bramkę; wycofanie = zmiana aliasu
- [ ] test skew i point-in-time dla cech; brak wycieku przyszłości
- [ ] bramki: dane, jakość na plastrach, fairness, latencja; wyzwalacze CT z limitem kosztu
- [ ] wdrożenie shadow lub canary z kryterium wycofania; A/B z policzoną mocą
- [ ] monitoring: drift cech i predykcji, jakość na dojrzałych kohortach, koszt; alert ma akcję
- [ ] karta modelu w rejestrze; LLM: prompty wersjonowane, ewaluacje w CI, tracing, koszt na zapytanie

## Materiały dodatkowe
- `references/projekt-i-gotowosc.md` — szablon dokumentu projektu potoku, lista gotowości i kryteria doboru narzędzi.

## Źródła
- Google Cloud Architecture Center, „MLOps: Continuous delivery and automation pipelines in machine learning” — poziomy 0–2;
  strony pierwotnej nie udało się pobrać, opis poziomów potwierdzony tylko w źródłach wtórnych, dostęp 2026-10-17 [niezweryfikowane].
- MLflow: etapy rejestru wycofane na rzecz aliasów od 2.9 (RFC `mlflow/mlflow#10336`, komunikat `FutureWarning`);
  MLflow 3 — LoggedModel, tracing, rejestr promptów, `mlflow.genai.evaluate()` (docs 3.1.3 i 3.5.x), dostęp 2026-10-17;
  czy etapy usunięto w obecnym wydaniu — [niezweryfikowane].
- DVC: `dvc.yaml`, `dvc.lock`, dowolny magazyn obiektowy; lakeFS jako warstwa nad jeziorem danych (dokumentacja DVC
  i porównania, dostęp 2026-10-17); przejęcie DVC przez lakeFS (2025) — jedno źródło [niezweryfikowane].
- Feast: odczyt historyczny point-in-time, magazyn offline i online (dokumentacja, wersje 0.x, dostęp 2026-10-17);
  numer bieżącego wydania [niezweryfikowane].
- Evidently, Arize: monitoring bez etykiet przez drift cech i predykcji (dokumentacja, dostęp 2026-10-17).
- Mitchell i in., „Model Cards for Model Reporting” (2019) — karta modelu [niezweryfikowane w tej sesji].
- Progi PSI 0,1 i 0,25 to reguła kciuka ze scoringu kredytowego [niezweryfikowane].
