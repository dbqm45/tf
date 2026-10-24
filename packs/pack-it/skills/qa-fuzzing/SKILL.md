---
name: qa-fuzzing
description: Użyj przy fuzzingu kodu przyjmującego niezaufane wejście — kiedy, harness, korpus, sanitizery, crash → test regresyjny, CI (Go, Atheris, libFuzzer).
metadata:
  przeglad: 2027-04-24
  widocznosc: nazwa
  katalog: "Użyj, gdy kod przyjmuje niezaufane lub złożone wejście (parsery, dekodery, protokoły, formaty plików, deserializacja, uploady) i trzeba automatycznie szukać wejść, które go wywracają — kiedy fuzzować, a kiedy wystarczą testy właściwości, harness (jedno wejście → jedno wywołanie, oczekiwane błędy odróżnione od znalezisk, właściwości jak round-trip), korpus startowy i słowniki, sanitizery (AddressSanitizer, UBSan) dla kodu natywnego, znalezisko → minimalizacja → test regresyjny, fuzzing w CI (krótko w PR, długo nocą, ClusterFuzzLite, OSS-Fuzz), narzędzia: natywny fuzzing Go (testing.F), Atheris (Python), libFuzzer (C/C++), Jazzer (Java). Nie do testów właściwości w Hypothesis lub fast-check bez fuzzera (tool-pytest, eng-testing), testów obciążeniowych (qa-performance-testing), skanowania podatności w zależnościach (ops-supply-chain-security) ani analizy wariantów znalezionej podatności (sec-variant-analysis)."
  slowa: "fuzzing, fuzzer, fuzz test, sfuzzować, go test -fuzz, testing.F, f.Fuzz, f.Add, Atheris, libFuzzer, LLVMFuzzerTestOneInput, AFL++, Jazzer, cargo-fuzz, AddressSanitizer, ASan, UBSan, sanitizer, korpus, corpus, harness, crash, minimalizacja crasha, złośliwe wejście, parser binarny, dekoder, panika na wejściu, ClusterFuzzLite, OSS-Fuzz"
---

# Fuzzing

Fuzzer generuje i mutuje wejścia, kierując się pokryciem kodu, i szuka takich, które wywołują crash, panikę,
nieoczekiwany wyjątek, zawieszenie albo złamanie właściwości. Uzupełnia testy przykładami i testy właściwości
(eng-testing): tamte sprawdzają reguły, fuzzer szuka wejść, o których nikt nie pomyślał.

## Kiedy fuzzować
- **Tak**: parser, dekoder, deserializacja, obsługa protokołu, format pliku, kompresja, wyrażenia i szablony —
  zwłaszcza na wejściu z sieci lub od użytkownika i w kodzie natywnym (C, C++, `unsafe`).
- **Testy właściwości wystarczą**: logika biznesowa na typowanych danych (kwoty, daty, reguły) — Hypothesis
  lub fast-check (tool-pytest, tool-vitest).
- **Nie fuzzer**: wydajność pod obciążeniem (qa-performance-testing), błędy w zależnościach (SCA,
  ops-supply-chain-security).

## Procedura
1. **Cel**: jedna funkcja na granicy zaufania (`Decode(bytes)`, `parse(text)`), bez sieci, plików, zegara
   i stanu globalnego — wynik zależy tylko od wejścia, więc każde znalezisko da się odtworzyć.
2. **Harness**: wejście fuzzera → typ funkcji (bajty, tekst, struktura przez `FuzzedDataProvider`), jedno
   wywołanie, potem sprawdzenie:
   - oczekiwane, udokumentowane błędy (`ErrShort`, `ConfigError`) przepuszczasz; każdy inny wyjątek, panika lub
     crash to znalezisko;
   - właściwości zamiast samego „nie wywraca się”: round-trip (`Encode(Decode(b))`), wynik w granicach bufora,
     zgodność z implementacją wzorcową.
3. **Korpus startowy**: kilka poprawnych i brzegowych wejść (`f.Add`, katalog `corpus/`), dla formatów z
   tokenami — słownik. Korpus rośnie podczas fuzzingu; trzymaj go w repozytorium albo w cache CI.
4. **Sanitizery dla kodu natywnego**: `-fsanitize=fuzzer,address,undefined`. Bez ASan błąd pamięci ujawnia się
   daleko od przyczyny (zawieszenie, crash w alokatorze, błędnie zapisane wejście); z ASan — linia i rozmiar
   zapisu. Bufor w harnessie przydzielaj osobno (`malloc` na dokładny rozmiar), żeby ASan widział granicę.
5. **Znalezisko**: odtwórz z zapisanego pliku, zminimalizuj, napraw przyczynę, zamień wejście w test regresyjny
   (Go robi to sam: `testdata/fuzz/`), puść fuzzer ponownie. Znalezisko w kodzie bezpieczeństwa → sprawdź warianty
   (sec-variant-analysis).
6. **CI**: krótki przebieg w każdym PR (30–600 s, ze stałym korpusem), długi nocą lub w harmonogramie
   (ClusterFuzzLite `code-change` i `batch`; projekty open source — OSS-Fuzz); korpus i znaleziska zachowane między
   przebiegami. Fuzzing bez limitu czasu nie mieści się w PR.
7. **Narzędzie wg języka**: Go — `testing.F` (`go test -fuzz`); Python — Atheris; C/C++ — libFuzzer (lub AFL++);
   Java — Jazzer z JUnit 5.9+ (`jazzer-junit`, `@FuzzTest`) [niezweryfikowane: nie uruchamiano]. Przykłady
   z kodem i wynikami: `references/harness-i-przyklady.md`.

## Pułapki (każda sprawdzona)
- **Go**: wycinek do pojemności nie panikuje, a fuzzer podaje `[]byte` z zapasem pojemności — odczyt poza danymi
  był niewidoczny przez 10 mln wykonań. W celu fuzzingu: `b = b[:len(b):len(b)]` albo jawne sprawdzenie długości.
- **Atheris**: `FuzzedDataProvider` wybiera kodowanie tekstu pierwszym bajtem — test regresyjny pisz na tekście
  po dekodowaniu, nie na surowych bajtach. Minimalizacja (`-minimize_crash=1`) uruchamia skrypt jako program:
  shebang, prawo wykonania i właściwy `python3` w `PATH`.
- Harness, który łapie każdy wyjątek (`except Exception`), nic nie znajdzie — łap tylko udokumentowane.

## Przykład
Dekoder ramek w Go bez sprawdzenia, czy treść ma zadeklarowaną długość: `FuzzDecode` z dwoma przykładami
w `f.Add` i właściwością round-trip. Fuzzer znalazł wejście `"000"`, ale dopiero po dodaniu `b[:len(b):len(b)]`
— wcześniej 2 × 40 s bez znaleziska. Plik z `testdata/fuzz/FuzzDecode/` oblewa `go test` przed naprawą
i przechodzi po niej. Analogicznie: Atheris znalazł nieudokumentowany `ValueError` w parserze konfiguracji
po ~80 wykonaniach, libFuzzer z ASan — przepełnienie sterty w dekoderze RLE z linią źródła.
Kod: `references/harness-i-przyklady.md`.

## Checklista
- [ ] cel deterministyczny, na granicy zaufania; harness odróżnia oczekiwane błędy od znalezisk
- [ ] co najmniej jedna właściwość poza „nie wywraca się”
- [ ] korpus startowy w repozytorium; kod natywny z ASan i UBSan
- [ ] każde znalezisko: odtworzenie → minimalizacja → naprawa → test regresyjny → ponowny fuzzing
- [ ] krótki fuzzing w PR, długi nocą; korpus zachowany między przebiegami

## Źródła
- Go: pakiet `testing` (`F.Add`, `F.Fuzz`), `go test -fuzz`, go1.24.7 — przykład uruchomiony 2026-10-24.
- Atheris 3.1.0 (PyPI), libFuzzer i sanitizery z clang 18.1.3 (Ubuntu 24.04) — przykłady uruchomione 2026-10-24.
- ClusterFuzzLite, dokumentacja GitHub Actions (google/clusterfuzzlite, commit 52ecc61); Jazzer, README
  (CodeIntelligenceTesting/jazzer, commit a4e09fb, Apache 2.0) — odczyt 2026-10-24.
- Inspiracja tematu: Trail of Bits `testing-handbook-skills` — treści nie przejęto.
Opisane własnymi słowami.
