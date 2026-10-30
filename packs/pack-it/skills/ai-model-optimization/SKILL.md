---
name: ai-model-optimization
description: Użyj przy zmniejszaniu lub przyspieszaniu modelu jako artefaktu — pomiar, kwantyzacja, GGUF, ONNX, TensorRT, OpenVINO, budżet pamięci wag, dobór rozmiaru.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy model ma być mniejszy, szybszy lub tańszy jako plik i środowisko uruchomienia — pomiar wyjściowy (jakość, opóźnienie, koszt, pamięć), kwantyzacja po treningu (INT8, INT4, GPTQ, AWQ, FP8, FP4, GGUF z llama.cpp), ocena utraty jakości po kwantyzacji, destylacja dla rozmiaru, przycinanie, eksport i kompilacja modeli klasycznych i wizyjnych (ONNX, TensorRT, OpenVINO, torch.compile), dekodowanie spekulatywne jako wybór po stronie modelu, budżet pamięci GPU na wagi (parametry razy bajty), dobór rozmiaru modelu. Nie do serwerów, KV cache, batchingu i routingu (ops-ai-inference), trenowania i dostrajania (ai-fine-tuning), złożoności algorytmów w kodzie (eng-algorithms-data-structures) ani metody ewaluacji (ai-evals)."
  slowa: "kwantyzacja, quantization, INT8, INT4, FP8, GPTQ, AWQ, GGUF, llama.cpp, Q4_K_M, zmniejszyć model, model za duży, nie mieści się w GPU, ile pamięci potrzebuje model, ile VRAM, ONNX, TensorRT, OpenVINO, torch.compile, przyspieszyć model, model za wolny, dekodowanie spekulatywne, speculative decoding, przycinanie, pruning, mniejszy model, Ollama, lokalnie na laptopie, wnioskowanie na CPU, ResNet, model wizyjny"
---

# Optymalizacja modelu — mniejszy i szybszy plik, bez ślepego ryzyka dla jakości

Ten skill dotyczy **artefaktu modelu** (wagi, format, kompilacja). Serwer, KV cache, batching i routing opisuje
**ops-ai-inference** (`.claude/skills/ops-ai-inference/SKILL.md`) — nie powtarzaj tam treści. Trenowanie i dostrajanie to
**ai-fine-tuning**, metoda ewaluacji — **ai-evals**, złożoność kodu — **eng-algorithms-data-structures**.

## Procedura
1. **Cel i pomiar wyjściowy.** Zapisz, co ma się poprawić i do jakiej wartości (np. p95 < 40 ms, mieści się w 24 GB,
   koszt na 1000 żądań). Zmierz stan obecny na **docelowym sprzęcie**: jakość na zbiorze ewaluacyjnym zadania, opóźnienie
   (dla LLM: czas do pierwszego tokenu i tokeny na sekundę; dla modelu wizyjnego: p50 i p95 na obraz), przepustowość,
   pamięć szczytowa, koszt. Rozgrzewka przed pomiarem, wiele powtórzeń, ten sam rozmiar wsadu co w produkcji.
   Profil (gdzie idzie czas) przed wyborem techniki: wąskie gardło w I/O, w przetwarzaniu wstępnym lub w pamięci
   nie zniknie po kwantyzacji.
2. **Budżet pamięci wag:** liczba parametrów × bajty na parametr (FP16/BF16: 2, FP8 i INT8: 1, INT4: 0,5; formaty z blokami
   skal dodają kilka procent, np. NVFP4 ok. 4,5 bita na wartość wg źródeł wtórnych).
   70 mld × 2 B = 140 GB; w INT8 70 GB; w INT4 ok. 35–40 GB. Do tego dochodzą aktywacje i KV cache (jego budżet:
   **ops-ai-inference**). Model „mieszczący się” bez zapasu na kontekst się nie mieści.
3. **Dobór rozmiaru modelu.** Najmniejszy model, który przechodzi ewaluację zadania, wygrywa. Porównaj na swoim zbiorze
   warianty o podobnej pamięci: większy skwantyzowany vs mniejszy w wyższej precyzji vs mniejszy dostrojony (**ai-fine-tuning**).
   Nie zakładaj kolejności — sprawdź.
4. **Kwantyzacja** (tabela formatów i sprzętu: `references/kwantyzacja.md`):
   - najpierw najłagodniejszy wariant: FP8 lub INT8 (na GPU z natywnym wsparciem), potem 4 bity (AWQ, GPTQ);
   - GGUF dla llama.cpp, Ollamy i CPU lub laptopa; wybór poziomu (`Q8_0`, `Q5_K_M`, `Q4_K_M`) wg pamięci RAM;
   - dane kalibracyjne z rozkładu produkcyjnego (język, domena, długość), nie z cudzego benchmarku;
   - format musi być obsługiwany przez docelowy silnik i GPU; sprawdź macierz zgodności wersji, którą masz.
5. **Utrata jakości po kwantyzacji.** Ten sam zbiór co w kroku 1 (**ai-evals**), przed i po, **w podziale na kawałki**:
   język, długość wejścia, rodzaj zadania, trudność. Średnia ukrywa regresje: badanie EMNLP 2025 (Mekala i in.) pokazało
   przy 8 bitach średnio ok. 0,8% straty, a przy 4 bitach spadki do 59% na zadaniach z długim wejściem, silniejsze
   poza angielskim. Perplexity i dywergencja KL względem modelu pełnej precyzji to szybkie wskaźniki
   do porównania wariantów, ale nie zastępują zadania docelowego. Próg akceptacji ustal **przed** pomiarem.
6. **Klasyczne DL i wizja:** eksport do ONNX, uruchomienie w ONNX Runtime, OpenVINO (CPU Intela) albo TensorRT (GPU NVIDIA),
   kwantyzacja INT8 z kalibracją; `torch.compile` gdy zostajesz w PyTorch. Szczegóły i pułapki: `references/eksport-i-kompilacja.md`.
   Po eksporcie sprawdź zgodność liczbową z modelem wyjściowym i metrykę zadania, nie tylko szybkość.
7. **Destylacja dla rozmiaru, przycinanie.** Destylacja (nauczyciel → mniejszy uczeń) zwykle daje większy zysk niż przycinanie;
   mechanika treningu i licencje wyników nauczyciela: **ai-fine-tuning**. Przycinanie nieustrukturyzowane (zerowanie wag)
   rzadko przyspiesza bez wsparcia sprzętu; strukturalne usuwa głowice lub warstwy i wymaga douczenia. Zacznij od kwantyzacji.
8. **Dekodowanie spekulatywne** (LLM, opóźnienie): mały model szkicuje tokeny, duży je weryfikuje w jednym przejściu,
   a rozkład wyjścia zostaje taki jak u dużego (Leviathan i in.). Wymaga zgodnego tokenizera lub wytrenowanych głowic
   (Medusa, EAGLE); zysk zależy od współczynnika akceptacji i rośnie na małych wsadach. Włączenie w serwerze: **ops-ai-inference**.
9. **Wynik:** tabela wariantów i decyzja; wersjonuj artefakt (skrót wag, parametry kwantyzacji, kalibracja, wersje narzędzi),
   bo ponowne zbudowanie na innej wersji daje inny wynik.

## Wynik
Tabela, jedna linia na wariant: wariant · pamięć wag · jakość (zadanie + kawałki) · opóźnienie p50/p95 · koszt na 1000 żądań ·
decyzja (przyjęty/odrzucony i dlaczego).

## Przykład
Wejście: „Llama 70B w BF16 nie mieści się na jednej karcie 80 GB; chcemy czat z kontekstem 8k.”
Wynik:
| Wariant | Wagi | Jakość (zbiór 300 zapytań) | Decyzja |
|---|---|---|---|
| BF16 | 140 GB | baseline | odrzucony, 2 karty |
| FP8 | 70 GB | −0,4 pp [przykład] | odrzucony, 10 GB zapasu na KV cache |
| AWQ INT4 | ok. 38 GB | −1,8 pp, z czego −5 pp na polskich długich dokumentach [przykład] | przyjęty warunkowo |
Następny krok: kalibracja AWQ na polskich dokumentach i ponowny pomiar; próg −2 pp na każdym kawałku.

## Checklista
- [ ] cel liczbowy i pomiar wyjściowy na docelowym sprzęcie (rozgrzewka, p95, pamięć szczytowa)
- [ ] budżet pamięci wag policzony, zapas na KV cache i aktywacje
- [ ] kwantyzacja od najłagodniejszego wariantu; kalibracja na danych z produkcji
- [ ] jakość przed i po na zbiorze zadania, w podziale na kawałki; próg przed pomiarem
- [ ] po eksporcie zgodność liczbowa i metryka zadania, nie tylko szybkość
- [ ] artefakt wersjonowany (skrót, parametry, wersje narzędzi)

## Materiały dodatkowe
- `references/kwantyzacja.md` — formaty (FP8, INT8, GPTQ, AWQ, GGUF, FP4), sprzęt i dobór.
- `references/eksport-i-kompilacja.md` — ONNX, ONNX Runtime, TensorRT, OpenVINO, torch.compile, pułapki.

## Źródła
- Lin i in., „AWQ” (arXiv 2306.00978; MLSys 2024) — ochrona ok. 1% istotnych kanałów wg aktywacji; wyszukiwanie 2026-10-17.
- Frantar i in., „GPTQ” (arXiv 2210.17323; ICLR 2023) — kwantyzacja jednorazowa do 3–4 bitów; wyszukiwanie 2026-10-17.
- Mekala i in., „Does quantization affect models' performance on long-context tasks?” (EMNLP 2025, arXiv 2505.20276)
  — liczby ze streszczenia, wyszukiwanie 2026-10-17.
- Leviathan, Kalman, Matias, „Fast Inference from Transformers via Speculative Decoding” (2022/2023) — zachowany rozkład wyjścia;
  streszczenie z wyszukiwania 2026-10-17.
- Wersje narzędzi i formatów: `references/kwantyzacja.md`, `references/eksport-i-kompilacja.md` (z datami).
Opisane własnymi słowami.
