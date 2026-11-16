# Projekt potoku MLOps i lista gotowości

Spis treści: Szablon dokumentu · Lista gotowości do produkcji · Kryteria doboru narzędzi · Typowe pułapki

## Szablon dokumentu
```markdown
# Projekt potoku MLOps — <model>
Właściciel: … · Data przeglądu: … · Poziom: obecny X → docelowy Y (powód)

## 1. Kontekst
Cel biznesowy, koszt błędu, opóźnienie etykiety, częstość zmian danych, wymogi prawne.

## 2. Artefakty
| Artefakt | Gdzie | Wersjonowanie | Właściciel |
|---|---|---|---|
| dane treningowe | … | hash / migawka | … |
| cechy | … | definicja w repo | … |
| model | rejestr | wersja + alias | … |
| karta modelu | rejestr | z wersją | … |

## 3. Potok i wyzwalacze
Etapy (dane → walidacja → trening → ocena → rejestracja), orkiestrator i uzasadnienie wyboru,
wyzwalacze CT z limitem częstości i kosztu.

## 4. Bramki
| Bramka | Warunek | Skutek niezaliczenia |
|---|---|---|

## 5. Wdrożenie i wycofanie
Shadow → canary → pełne; kryterium wycofania; kto decyduje.

## 6. Monitoring
| Sygnał | Częstość | Próg | Akcja |
|---|---|---|---|

## 7. Luki i kolejność wdrożenia
```

## Lista gotowości do produkcji
Odpowiedzi: tak / nie / nie dotyczy (z powodem). Każde „nie” trafia do sekcji 7 z właścicielem.

**Odtwarzalność**
- Czy z zapisu przebiegu odtworzysz model: dane, kod, środowisko, ziarna, cechy?
- Czy środowisko treningu i serwowania ma przypięte wersje bibliotek?

**Dane i cechy**
- Czy schemat i rozkłady danych są sprawdzane przed treningiem?
- Czy cechy mają jedną definicję dla treningu i serwowania oraz test skew?
- Czy odczyt historyczny jest point-in-time (brak wycieku przyszłości)?

**Model**
- Czy jest punkt odniesienia (prosty model lub reguła) i metryka na plastrach?
- Czy fairness sprawdzono dla grup istotnych dla przypadku użycia?
- Czy karta modelu ma przeznaczenie, ograniczenia i właściciela?

**Wdrożenie**
- Czy wycofanie jest jednym krokiem i przećwiczonym?
- Czy nowy model przeszedł shadow lub canary przed pełnym ruchem?

**Monitoring**
- Czy jest drift cech i predykcji oraz jakość na dojrzałych kohortach?
- Czy każdy alert ma akcję i właściciela?
- Czy koszt na predykcję (lub na zapytanie LLM) jest mierzony i ma budżet?

**LLM (dodatkowo)**
- Czy prompty są w rejestrze z wersjami, a zmiana przechodzi przez PR i zestaw ewaluacyjny?
- Czy tracing obejmuje tokeny, narzędzia i latencję, a próbka ruchu jest oceniana?
- Czy są metryki barier ochronnych (odmowy, dane osobowe, wstrzyknięcia, brak oparcia w źródłach)?

## Kryteria doboru narzędzi
| Decyzja | Wybierz | Gdy |
|---|---|---|
| wersjonowanie danych | DVC | jeden projekt, dane w magazynie obiektowym, potrzebny potok obok kodu |
| | lakeFS | wiele zespołów na wspólnym jeziorze, gałęzie i atomowe commity na dużych danych |
| | migawka tabeli (Iceberg, Delta) | dane już w takich tabelach |
| magazyn cech | Feast | cechy współdzielone przez modele, odczyt online, potrzebny point-in-time |
| | wspólna biblioteka | jeden model, cechy liczone w partii |
| orkiestracja | Kubeflow Pipelines | Kubernetes jest, kroki w kontenerach, GPU |
| | Airflow | orkiestrator już działa w organizacji |
| | Dagster | model jako zasób danych, lineage, testy lokalne |
| śledzenie | MLflow | potrzebny rejestr, tracing LLM i ewaluacje w jednym miejscu; inne narzędzie, gdy platforma je narzuca |

Reguła nadrzędna: narzędzie, które zespół już utrzymuje, wygrywa z lepszym narzędziem do wdrożenia od zera,
chyba że brakuje mu wymaganej funkcji (np. point-in-time).

## Typowe pułapki
- Metryka offline rośnie, a produkcyjna spada — zwykle skew cech albo wyciek przyszłości w zbiorze treningowym.
- Automatyczny retrening na zdryfowanych danych bez bramki utrwala błąd; retrening zawsze przez bramkę.
- Jakość liczona na „wczorajszych danych” przy etykiecie po 90 dniach nic nie mówi — użyj dojrzałych kohort.
- Średnia metryka ukrywa pogorszenie w segmencie; bramka ma plastry.
- Zmiana wersji modelu LLM u dostawcy bez uruchomienia zestawu ewaluacyjnego.
