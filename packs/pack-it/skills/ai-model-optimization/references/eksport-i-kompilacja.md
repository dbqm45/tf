# Eksport i kompilacja modeli klasycznych i wizyjnych

Stan z wyszukiwania 2026-10-17; dokumentacji producentów nie otwarto (źródła wtórne i streszczenia), więc wersje
i flagi sprawdź w dokumentacji zainstalowanej wersji.

## Kolejność
1. Pomiar wyjściowy i profil (SKILL.md, krok 1).
2. Najtańsze: `torch.compile`, mniejsza rozdzielczość lub wsad dopasowany do sprzętu, FP16/BF16.
3. Eksport do ONNX → silnik docelowy (ONNX Runtime, OpenVINO, TensorRT).
4. Kwantyzacja INT8 z kalibracją na reprezentatywnych obrazach lub danych z produkcji.
5. Zgodność liczbowa (tolerancja na wyjściach, metryka zadania) i pomiar na docelowym sprzęcie.

## Narzędzia
- **ONNX:** `torch.onnx.export`; od PyTorch 2.9 domyślnie ścieżka oparta na `torch.export` (`dynamo=True`), stara ścieżka TorchScript
  wymaga `dynamo=False` i jest wygaszana (notatki wydania 2.9, wyszukiwanie). Zamiast `dynamic_axes` używaj `dynamic_shapes`.
  Nowa ścieżka może ujawnić błędy przechwycenia grafu, które wcześniej były ukryte.
- **TensorRT** (GPU NVIDIA): silnik budowany z ONNX (`trtexec` lub API), domyślnie związany z architekturą GPU i wersją TensorRT;
  tryby zgodności wersji i sprzętu to wyjątki, a tabele kalibracji INT8 buduj od nowa po zmianie wersji (macierz wsparcia 10.8,
  przewodnik DRIVE OS). Buduj na tym typie GPU, na którym działa produkcja.
- **OpenVINO + NNCF** (CPU i GPU Intela): `nncf.quantize()` do INT8; w wydaniu 2026.0 usunięto `create_compressed_model()`
  i część metod eksperymentalnych (notatki wydania). Wejścia zalecane: OpenVINO IR, PyTorch, ONNX. Kontrola dokładności
  (`quantize_with_accuracy_control`) — status w 2026 nie potwierdzony [niezweryfikowane].
- **torch.compile:** tryby `default`, `reduce-overhead` (grafy CUDA, mniej narzutu na małych wsadach, więcej pamięci),
  `max-autotune` (dłuższa kompilacja, szybszy kod); pierwsze wywołanie jest wolne (kompilacja), więc mierz po rozgrzewce.
  Łamania grafu (graph breaks) obniżają zysk — sprawdź je przed strojeniem trybów.

## Pułapki
- Dynamiczne rozmiary: eksport ze stałym kształtem zawyża szybkość i psuje inne rozmiary.
- Przetwarzanie wstępne i końcowe (skalowanie obrazu, NMS) zwykle zostaje poza silnikiem i bywa wąskim gardłem.
- Różnice liczbowe po INT8 rosną w ogonie rozkładu: sprawdź najgorsze przypadki, nie tylko średnią.
- Silnik TensorRT nie jest artefaktem przenośnym; w repozytorium trzymaj ONNX i skrypt budowy, nie plik silnika jako jedyną kopię.
