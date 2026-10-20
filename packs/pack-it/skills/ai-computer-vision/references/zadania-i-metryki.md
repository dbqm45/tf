# Zadania wizyjne i metryki

Stan z wyszukiwania 2026-10-17 (definicje COCO ze źródeł wtórnych, strony pierwotnej nie otwarto).

## Zadanie → metryka
| Zadanie | Wynik modelu | Metryki podstawowe | Uwagi |
|---|---|---|---|
| Klasyfikacja | etykieta | accuracy (klasy zrównoważone), precision, recall, F1, macierz pomyłek | przy rzadkiej klasie accuracy mylące (98% przy 2% wad to „zawsze OK”) |
| Detekcja | ramki + klasa + pewność | AP/mAP, AP50, AP75, AP small/medium/large; precision i recall przy progu | COCO: AP uśrednione po progach IoU 0,50–0,95 co 0,05; AP50 zbliżone do PASCAL VOC |
| Segmentacja semantyczna | klasa na piksel | IoU na klasę (mIoU), Dice | Dice = 2·|A∩B| / (|A|+|B|); IoU = |A∩B| / |A∪B| |
| Segmentacja instancji | maska na obiekt | mAP na maskach (IoU maski) | jak detekcja, ale IoU liczone na maskach |
| Punkty kluczowe | współrzędne | OKS i AP na OKS, błąd w pikselach | normalizuj do rozmiaru obiektu |
| OCR / Document AI | tekst, pola | CER, WER, dokładne dopasowanie pól, F1 pól | liczy się odległość edycji; pola krytyczne (kwota, NIP) oceniaj osobno |
| Śledzenie w wideo | ścieżki obiektów | metryki śledzenia (zamiany tożsamości, ciągłość) + detekcja | [niezweryfikowane] nazwy metryk sprawdź w dokumentacji wybranej biblioteki |

## Definicje
- IoU = pole części wspólnej ramek przez pole ich sumy. Detekcja jest trafieniem, gdy IoU ≥ próg i klasa się zgadza.
- AP to pole pod krzywą precision–recall dla klasy, mAP to średnia po klasach. W kontekście COCO „mAP” zwykle
  oznacza AP@[.50:.95]. Podając wynik, zawsze pisz, który wariant i jaki próg.
- COCO dzieli obiekty wg powierzchni: small < 32², medium 32²–96², large > 96² pikseli.
- CER = (podstawienia + usunięcia + wstawienia) / liczba znaków wzorca; WER tak samo na słowach.

## Pułapki oceny
- Wynik zależy od progu pewności i progu NMS; zamroź je przed testem końcowym.
- Mały zbiór testowy daje szeroki przedział: raportuj przedział (bootstrap) i liczbę przykładów w kawałku.
- Etykiety w zbiorze testowym sprawdzaj ręcznie; błędna etykieta zaniża wynik modelu.
- Porównuj modele na tym samym zbiorze, rozdzielczości i progu; rozdzielczość wejścia zmienia AP małych obiektów.
- Zbiór z jednego dnia lub kamery zawyża wynik; testuj na nowej kamerze, porze roku, partii.
