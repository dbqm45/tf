# Formaty kwantyzacji — dobór i zastrzeżenia

Stan z wyszukiwania 2026-10-17; większość źródeł to blogi i porównania (wtórne), oficjalnych dokumentacji vLLM,
llm-compressor i llama.cpp w tej sesji nie otwarto. Liczby z blogów traktuj orientacyjnie, własny pomiar jest rozstrzygający.

| Format | Do czego | Uwagi |
|---|---|---|
| FP8 | GPU NVIDIA nowszych generacji, serwowanie (np. vLLM) | zwykle pierwszy wybór: mała strata, kalibracja bywa opcjonalna; schemat „FP8 dynamic” z wagami skalowanymi na kanał i aktywacjami skalowanymi dynamicznie (wtórne). Natywne wsparcie zależy od generacji GPU [niezweryfikowane] |
| INT8 | szeroko, także starsze GPU i CPU | zwykle niewielka strata; wymaga kalibracji przy kwantyzacji aktywacji |
| AWQ (INT4, tylko wagi) | serwowanie na GPU | wg wtórnych źródeł zwykle nie gorszy od GPTQ; wsparcie zależy od GPU i silnika (np. brak na AMD w vLLM wg jednego źródła). Tworzenie nowych punktów kontrolnych: llm-compressor (AutoAWQ wg jednego źródła zarchiwizowany) [niezweryfikowane] |
| GPTQ (INT3–4, tylko wagi) | gdy brak AWQ, szerokie wsparcie CUDA | metoda drugiego rzędu, kwantyzacja jednorazowa; autorzy: model 175 mld w ok. 4 godziny GPU |
| GGUF (llama.cpp) | laptop, CPU, mieszane CPU/GPU, Ollama, LM Studio | plik z wagami i metadanymi; to nie jest format dla vLLM. Presety: `Q8_0` (blisko bez straty), `Q5_K_M`, `Q4_K_M` (częsty kompromis). Niższe poziomy (Q3 i niżej) wymagają macierzy ważności (`imatrix`) |
| NVFP4 / MXFP4 | najnowsze GPU (Blackwell) | ok. 4,5 / 4,25 bita na wartość; NVIDIA deklaruje spadek ≤ 1% względem FP8 na jednym modelu (źródło wtórne, wymaga własnej weryfikacji) |
| bitsandbytes NF4 | dostrajanie (QLoRA), szybkie próby | wolniejszy w serwowaniu; wyniki wrażliwe na model (Mekala i in.) |

## Dobór w trzech pytaniach
1. **Gdzie działa?** Serwer GPU → FP8, potem AWQ/GPTQ; laptop lub CPU → GGUF; Intel CPU z klasycznym DL → OpenVINO.
2. **Ile pamięci?** Policz parametry × bajty (SKILL.md, krok 2) i zostaw zapas na kontekst.
3. **Ile jakości można stracić?** Próg z ewaluacji zadania; im mniej bitów, tym ważniejsza kalibracja i podział na kawałki.

## Ocena po kwantyzacji
- Zadanie docelowe w podziale na język, długość wejścia i trudność. Badanie Cohere nad Command A: języki z pismem nielacińskim
  i trudne zadania (matematyka) pogarszały się najszybciej, a metryki automatyczne niedoszacowały straty (średnio 1,7% w testach
  automatycznych wobec 16% w ocenie ludzi dla japońskiego; wyszukiwanie 2026-10-17, pracy nie otwarto [niezweryfikowane]).
- llama.cpp: `llama-perplexity` na własnym tekście do porównań wariantów; `llama-imatrix` + `llama-quantize --imatrix`
  dla niskich bitów. Tabele „procent straty perplexity na poziom” z blogów różnią się metrykami i modelami — nie przenoś ich.
- Zestaw regresji: kilkadziesiąt przykładów, na których pełna precyzja jest poprawna; sprawdź, ile przestaje być poprawnych.
