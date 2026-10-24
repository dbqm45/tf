# Harness i przykłady — sprawdzone 2026-10-24

Każdy przykład uruchomiony: fuzzer znalazł zasiany błąd, znalezione wejście stało się testem regresyjnym, po
naprawie test przechodzi, a ponowny fuzzing nic nie znajduje.

## Go — natywny fuzzing (`testing.F`, go1.24.7)
Dekoder ramek: 1 bajt typu, 2 bajty długości (big endian), treść.
```go
func Decode(b []byte) (Frame, error) {
	if len(b) < 3 {
		return Frame{}, ErrShort
	}
	n := int(binary.BigEndian.Uint16(b[1:3]))
	if len(b) < 3+n { // tego warunku brakowało — błąd zasiany w przykładzie
		return Frame{}, ErrShort
	}
	return Frame{Type: b[0], Payload: b[3 : 3+n]}, nil
}
```
```go
func FuzzDecode(f *testing.F) {
	f.Add([]byte{0x01, 0x00, 0x02, 'h', 'i'}) // poprawna ramka
	f.Add([]byte{0x02, 0x00, 0x00})           // pusta treść
	f.Fuzz(func(t *testing.T, b []byte) {
		b = b[:len(b):len(b)] // pojemność = długość: odczyt poza danymi panikuje
		fr, err := Decode(b)
		if err != nil {
			if !errors.Is(err, ErrShort) {
				t.Fatalf("nieoczekiwany błąd: %v", err)
			}
			return
		}
		// właściwość: zdekodowana ramka koduje się z powrotem do prefiksu wejścia
		if enc := Encode(fr); !bytes.Equal(enc, b[:len(enc)]) {
			t.Fatalf("Encode(Decode(b)) = %x, wejście %x", enc, b)
		}
	})
}
```
- `go test -fuzz=FuzzDecode -fuzztime=40s` znalazł panikę dla wejścia `"000"` (długość 0x3030) w ułamku sekundy
  i zapisał ją w `testdata/fuzz/FuzzDecode/<hash>`. Zwykłe `go test` uruchamia ten plik jako przypadek testu
  (`FuzzDecode/c2501043394e49f2`) — z błędem test oblewa, po naprawie przechodzi. Plik commitujesz.
- **Pułapka (sprawdzona):** bez linii `b = b[:len(b):len(b)]` dwa czyste przebiegi po 40 s (≈5 mln wykonań każdy,
  `go clean -fuzzcache` przed każdym) **nie znalazły** błędu. Fuzzer podaje wycinek z pojemnością większą niż
  długość, a w Go wycinek do pojemności (`b[3:3+n]` przy `3+n ≤ cap(b)`) nie panikuje — odczyt poza danymi zostaje
  niewidoczny. Ograniczenie pojemności albo jawne sprawdzenie długości wyniku w celu fuzzingu ujawnia błąd.
- Po naprawie 30 s fuzzingu bez znalezisk.

## Python — Atheris 3.1.0 (CPython 3.13)
```python
#!/usr/bin/env python3
import sys

import atheris

with atheris.instrument_imports():
    import miniconf


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(len(data))
    try:
        miniconf.parse(text)
    except miniconf.ConfigError:
        pass  # udokumentowany błąd składni — oczekiwany; każdy inny wyjątek to znalezisko


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
```
- Uruchomienie: `PYTHONPATH=src ./fuzz/fuzz_miniconf.py corpus -max_total_time=60 -artifact_prefix=crashes/`
  (katalog `corpus` z jednym poprawnym plikiem konfiguracji). Po ~80 wykonaniach: `ValueError: substring not
  found` z `line.index("]")` — sekcja bez `]`. `ConfigError` dziedziczy po `ValueError`, ale harness łapie tylko
  `ConfigError`, więc nieudokumentowany `ValueError` jest znaleziskiem.
- Odtworzenie: `./fuzz/fuzz_miniconf.py crashes/crash-<hash>`. Minimalizacja:
  `./fuzz/fuzz_miniconf.py -minimize_crash=1 -runs=2000 -exact_artifact_path=crashes/min crashes/crash-<hash>`
  (8 → 2 bajty). libFuzzer uruchamia przy tym `argv[0]` jako program — skrypt musi mieć shebang i prawo
  wykonania, a `python3` ze środowiska z Atheris musi być pierwszy w `PATH`; inaczej minimalizacja nic nie robi.
- **Pułapka (sprawdzona):** `FuzzedDataProvider` dekoduje tekst po swojemu — pierwszy bajt wybiera kodowanie
  (`b"[["` → `"["`, `b"\x02\x00a\x00b"` → dwa znaki UTF-16). W teście regresyjnym zapisuj tekst po dekodowaniu,
  nie surowe bajty:
```python
def test_unclosed_section_is_config_error():
    with pytest.raises(miniconf.ConfigError, match="linia 1"):
        miniconf.parse("[db\nhost = x\n")
```
  Przed naprawą test oblewał, po naprawie (`ConfigError` dla linii bez `]`) przechodzi; 60 s fuzzingu
  (5,15 mln wykonań) bez znalezisk.

## C — libFuzzer + AddressSanitizer + UBSan (clang 18.1.3)
```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    uint8_t *out = malloc(64);           /* osobna alokacja: ASan widzi każdy bajt poza nią */
    int r = rle_decode(data, size, out, 64);
    if (r > 64)
        abort();                          /* właściwość: wynik nie większy niż bufor */
    free(out);
    return 0;
}
```
Kompilacja: `clang-18 -g -O1 -fsanitize=fuzzer,address,undefined fuzz_rle.c rle.c -o fuzz_rle` (w Ubuntu potrzebny
pakiet `libclang-rt-18-dev`), uruchomienie `./fuzz_rle -max_total_time=60 corpus`. Zasiany błąd: warunek
`o + count > cap + 16` zamiast `> cap`.

Ten sam błąd w trzech konfiguracjach:
| Konfiguracja | Wynik |
|---|---|
| `-fsanitize=fuzzer,address,undefined` | `heap-buffer-overflow`, `WRITE of size 77`, `rle.c:12` — dokładne miejsce |
| `-fsanitize=fuzzer` + `abort()` w harnessie | `deadly signal` z wejściem, bez wskazania miejsca zapisu |
| `-fsanitize=fuzzer`, bez warunku w harnessie | raz zawieszenie procesu, raz SEGV w `free` wewnątrz libFuzzera i zapis pustego, błędnego wejścia |

Po naprawie zapisany crash przechodzi (`./fuzz_rle crash-<hash>`), a 46 s fuzzingu (29,5 mln wykonań) nic nie
znajduje.

## CI
- Krótki przebieg w PR: Go `go test -run='^$' -fuzz=FuzzDecode -fuzztime=60s .` (jeden pakiet naraz; zapisany
  korpus wchodzi do bazowego pokrycia — „gathering baseline coverage: 5/5”); libFuzzer i Atheris
  `-max_total_time=60`; korpus z repozytorium lub z cache CI.
- Znalezione wejścia: Go — `testdata/fuzz/` w repozytorium; Python i C — katalog przypadków regresyjnych
  odtwarzanych w zwykłych testach.
- ClusterFuzzLite (GitHub Actions, google/clusterfuzzlite commit 52ecc61): tryby `code-change` (PR, np.
  `fuzz-seconds: 600`), `batch` (dłużej, harmonogram), `prune` (przycinanie korpusu), `coverage` (raport
  pokrycia); `sanitizer` w macierzy (address, undefined). Konfiguracji nie uruchamiano w tej sesji.
