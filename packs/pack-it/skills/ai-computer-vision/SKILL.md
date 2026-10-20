---
name: ai-computer-vision
description: Użyj przy projekcie rozwiązania wizyjnego — dobór zadania i podejścia, zbiór i adnotacje, podział bez wycieku, metryki, błędy po kawałkach, prywatność obrazów, dryf.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy trzeba zaprojektować lub ocenić system rozpoznawania obrazu i wideo — sformułowanie zadania (klasyfikacja, detekcja, segmentacja semantyczna i instancji, punkty kluczowe, OCR i Document AI, śledzenie w wideo), wybór podejścia (model gotowy lub fundamentalny zero-shot, model wizyjno-językowy, dostrojenie wstępnie wytrenowanego szkieletu, trening od zera rzadko) wg danych, opóźnienia i urządzenia, budowa zbioru (zbieranie, balans klas, przypadki brzegowe, wytyczne adnotacji, kontrola etykiet), augmentacja wg warunków wdrożenia, podział bez wycieku (ta sama scena, pacjent, kamera w jednym zbiorze), metryki (accuracy i F1, mAP przy progach IoU, IoU i Dice, CER i WER), analiza błędów po kawałkach, ewaluacja na danych z wdrożenia, ograniczenia urządzeń brzegowych, prywatność obrazów (twarze, tablice), dryf obrazów. Nie do kwantyzacji i eksportu ONNX/TensorRT (ai-model-optimization), mechaniki dostrajania (ai-fine-tuning), metody ewaluacji funkcji LLM (ai-evals), potoku modelu w produkcji (ai-mlops), podstaw prawnych RODO (arch-privacy-compliance) ani hostowania LLM (ops-ai-inference)."
  slowa: "computer vision, widzenie komputerowe, rozpoznawanie obrazu, detekcja obiektów, klasyfikacja obrazów, segmentacja, YOLO, mAP, IoU, Dice, OCR, CER, WER, faktury skany, adnotacja, etykietowanie zdjęć, zbiór zdjęć, augmentacja, wyciek danych, kamera, linia produkcyjna, kontrola jakości wizyjna, wykrywanie wad, tablice rejestracyjne, twarze, anonimizacja obrazów, urządzenie brzegowe, edge, śledzenie obiektów, wideo, dryf obrazów, model wizyjno-językowy"
---

# Rozwiązania wizyjne — od zadania i danych do oceny na obrazach z wdrożenia

Ten skill projektuje **rozwiązanie wizyjne**: zadanie, podejście, dane, ocenę, ryzyka. Zmniejszanie i eksport modelu
(kwantyzacja, ONNX, TensorRT) to **ai-model-optimization** (`.claude/skills/ai-model-optimization/SKILL.md`),
mechanika dostrajania — **ai-fine-tuning**, metoda ewaluacji i bramki — **ai-evals**, rejestr, potok i dryf
w produkcji — **ai-mlops**, podstawy prawne — **arch-privacy-compliance**, hostowanie LLM — **ops-ai-inference**.

## Procedura
1. **Warunki wdrożenia.** Zapisz: kto korzysta z wyniku i jaki błąd boli bardziej (fałszywy alarm czy przeoczenie),
   kamera lub źródło, oświetlenie, odległość, rozdzielczość, urządzenie (serwer GPU, CPU, urządzenie brzegowe),
   budżet opóźnienia p95. Bez tego nie da się dobrać ani modelu, ani metryki.
2. **Sformułuj zadanie** (tabela i metryki: `references/zadania-i-metryki.md`). Najprostsze zadanie, które rozwiązuje problem:
   „czy jest wada” to klasyfikacja, „gdzie jest” to detekcja, „jaka powierzchnia” to segmentacja, poza tym punkty
   kluczowe, OCR i Document AI, śledzenie w wideo. Zadanie trudniejsze oznacza droższe adnotacje.
3. **Dobierz podejście, od najtańszego** (kolejne tylko po porażce na zbiorze oceny z kroku 5):
   - model gotowy lub fundamentalny zero-shot (detekcja i segmentacja z opisu lub punktu) albo model wizyjno-językowy
     (VLM) przez API: zero etykiet, dobry do prototypu i przypadków rzadkich; wolny, drogi na obraz i trudny do
     uruchomienia na urządzeniu;
   - dostrojenie wstępnie wytrenowanego szkieletu na własnych danych (mechanika: **ai-fine-tuning**): domyślny wybór
     przy setkach–tysiącach etykietowanych obrazów i twardym opóźnieniu;
   - trening od zera rzadko: tylko przy obrazach bardzo odległych od naturalnych (np. specjalistyczne sensory) i dużej ilości danych;
   - model większy może służyć jako nauczyciel lub narzędzie do wstępnego etykietowania, a mały uczeń jedzie na urządzeniu.
   Licencje wag i danych sprawdź przed wyborem (komercyjne użycie bywa zabronione) [założenie: licencje różnią się między modelami].
4. **Zbiór.** Zbieraj w warunkach wdrożenia (te kamery, pory dnia, tła), nie ze zdjęć w sieci. Ustal balans klas
   i przypadki brzegowe (rzadka klasa, mały obiekt, zasłonięcie, rozmycie, odblaski, obiekt „prawie wada”, puste kadry
   bez obiektu). Rzadkie klasy dozbieraj celowo, a nie tylko przeważaj w stratach.
5. **Adnotacje.** Wytyczne na piśmie z obrazkami: co jest obiektem, jak rysować ramkę (ciasno, obiekt częściowo
   widoczny), co robić przy wątpliwości (osobna etykieta „niepewne”). Pilot na 50–100 obrazach z dwoma adnotatorami,
   zgodność policz (IoU ramek, kappa dla klas), rozbieżności omów i popraw wytyczne. Kontrola etykiet: próbka do
   ponownego przeglądu, a obrazy o największej stracie modelu sprawdź pod kątem błędnej etykiety przed „poprawianiem” modelu.
6. **Podział bez wycieku.** Dziel po **grupie**, nie po obrazie: ta sama scena, ten sam pacjent lub badanie, ta sama
   partia, ten sam film (klatki są prawie identyczne), ta sama kamera tam, gdzie wdrożenie obejmie nowe kamery.
   Zbiór testowy zamroź i nie używaj do strojenia; duplikaty i zdjęcia prawie identyczne wyszukaj przed podziałem
   (skróty percepcyjne lub odległość embeddingów). Zbiór walidacyjny do strojenia, osobny testowy do decyzji.
7. **Augmentacja wg warunków wdrożenia.** Dodawaj tylko zmiany, które realnie wystąpią: jasność i kontrast przy
   zmiennym świetle, rozmycie ruchu, szum, kompresja JPEG, przesunięcia i skala. Odbicie poziome psuje OCR, tekst,
   strony lewa i prawa (np. anatomia); obrót o 90 stopni psuje obiekty zawsze stojące pionowo. Augmentację stosuj
   po podziale i tylko do zbioru treningowego. Sprawdź wzrokiem próbkę augmentowanych obrazów.
8. **Metryki i próg** (`references/zadania-i-metryki.md`). Metrykę wiąż z kosztem błędu z kroku 1, próg
   akceptacji ustal przed pomiarem. Raportuj precision i recall przy konkretnym progu pewności, nie samo mAP.
   Dla wideo osobno metryki śledzenia.
9. **Analiza błędów po kawałkach.** Wynik w podziale na: oświetlenie, kamerę, rozmiar obiektu (mały, średni, duży),
   odległość, tło, klasę. Średnia ukrywa regresje. Obejrzyj 30–50 najgorszych błędów i nazwij ich przyczyny
   (etykieta, dane, model, warunki); każda przyczyna prowadzi do innej poprawki (dozbieranie, wytyczne, augmentacja, model).
10. **Ocena na danych z wdrożenia.** Zbiór z internetu lub laboratorium zawyża wynik. Przed startem uruchom model
    w trybie cienia na prawdziwym strumieniu i porównaj z ludzką oceną próbki (metoda i bramki: **ai-evals**).
11. **Urządzenie brzegowe.** Z budżetu opóźnienia i pamięci wynika rozmiar modelu i rozdzielczość wejścia; mierz
    cały potok (dekodowanie, skalowanie, NMS, śledzenie), nie sam model. Kwantyzacja i eksport:
    **ai-model-optimization**; po nich powtórz ocenę z kroku 9, bo INT8 psuje głównie małe obiekty i ogon rozkładu.
12. **Prywatność obrazów.** Twarz, tablica rejestracyjna, ekran, dokument z danymi to dane osobowe lub wrażliwe.
    Zbieraj minimum, anonimizuj (rozmycie lub maska) możliwie przed zapisem, ogranicz retencję surowych klatek,
    sprawdź dostęp do zbioru adnotacji i zewnętrznych narzędzi etykietowania. Podstawa prawna, DPIA, procesory:
    **arch-privacy-compliance**.
13. **Dryf i monitoring.** Po wdrożeniu śledź rozkład wejścia (jasność, ostrość, rozmiar obiektów, embeddingi),
    rozkład pewności i liczby detekcji na klatkę oraz próbkę z ręczną oceną; zmiana pory roku, kamery, oświetlenia
    czy partii towaru to typowe źródła. Alerty, retrening i rejestr: **ai-mlops**.

## Wynik
Projekt rozwiązania (stały układ): zadanie i warunki · podejście z alternatywą · plan zbioru (liczby, klasy, źródła,
wytyczne) · zasada podziału · metryki i progi akceptacji · plan oceny po kawałkach i na danych z wdrożenia ·
ograniczenia urządzenia · prywatność · monitoring · ryzyka i następny krok.

## Przykład
Wejście: „Linia tłoczni, 3 kamery, ok. 800 zdjęć blach, zarysowania w ok. 2% zdjęć, wynik w < 100 ms na komputerze
przemysłowym bez GPU.”
Wynik:
- zadanie: detekcja zarysowań (ramki), bo operator ma wskazać miejsce; klasyfikacja „wada/OK” jako prosty punkt odniesienia;
- podejście: dostrojony mały szkielet, zero-shot VLM tylko do wstępnego etykietowania; kandydat na CPU sprawdzony w ai-model-optimization;
- zbiór: z ok. 16 zdjęć z wadą dozbierać do min. 150 kadrów z wadą (celowe wywołanie wad na próbkach), drugie tyle „prawie wad” (rysy włosowate, kurz) [przykład];
- podział: po partii blach, nie po zdjęciu; jedna kamera (kamera 3) tylko w teście, by zmierzyć nową kamerę;
- metryki: recall wad ≥ 95% przy precision ≥ 80% na teście, mAP@[.5:.95] pomocniczo; wyniki osobno dla kamery i zmiany (poranek, wieczór);
- następny krok: pilot adnotacji 60 zdjęć z dwoma adnotatorami, wytyczne dla rys włosowatych.

## Checklista
- [ ] warunki wdrożenia i koszt błędu spisane przed doborem modelu
- [ ] podejście od najtańszego (zero-shot, VLM) do dostrojenia; licencje sprawdzone
- [ ] wytyczne adnotacji, pilot z dwoma adnotatorami, kontrola etykiet
- [ ] podział po grupie (scena, pacjent, kamera, film); testowy zamrożony
- [ ] augmentacje tylko realne dla wdrożenia, po podziale
- [ ] metryki dobrane do zadania, próg przed pomiarem, wynik po kawałkach
- [ ] ocena na danych z wdrożenia (tryb cienia), pomiar całego potoku na urządzeniu
- [ ] anonimizacja i retencja obrazów; monitoring dryfu z próbką ręczną

## Materiały dodatkowe
- `references/zadania-i-metryki.md` — zadania, metryki (COCO), CER i WER, pułapki oceny.

## Źródła
- COCO, „Detection Evaluation” (cocodataset.org) i opisy protokołu w pracach cytujących (np. arXiv 1804.07437):
  AP uśrednione po 10 progach IoU 0,50–0,95 co 0,05, AP50, AP75, AP small/medium/large wg powierzchni 32² i 96²;
  wyszukiwanie 2026-10-17, strony COCO nie otwarto [niezweryfikowane w źródle pierwotnym].
- Nazwy rodzin modeli (YOLO, Segment Anything, CLIP) i aktualne wersje: [niezweryfikowane], sprawdź w dokumentacji przed wyborem.
Opisane własnymi słowami.
