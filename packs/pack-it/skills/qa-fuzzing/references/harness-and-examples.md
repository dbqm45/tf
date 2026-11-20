# Harness and examples — verified 2026-10-24

> **Contents:** Go — native fuzzing (`testing.F`, go1.24.7) · Python — Atheris 3.1.0 (CPython 3.13) · C — libFuzzer + AddressSanitizer + UBSan (clang 18.1.3) · CI

Every example was run: the fuzzer found the seeded bug, the input it found became a regression test, after
the fix the test passes, and fuzzing again finds nothing.

## Go — native fuzzing (`testing.F`, go1.24.7)
A frame decoder: 1 type byte, 2 length bytes (big endian), the payload.
```go
func Decode(b []byte) (Frame, error) {
	if len(b) < 3 {
		return Frame{}, ErrShort
	}
	n := int(binary.BigEndian.Uint16(b[1:3]))
	if len(b) < 3+n { // this condition was missing — the bug seeded in the example
		return Frame{}, ErrShort
	}
	return Frame{Type: b[0], Payload: b[3 : 3+n]}, nil
}
```
```go
func FuzzDecode(f *testing.F) {
	f.Add([]byte{0x01, 0x00, 0x02, 'h', 'i'}) // a valid frame
	f.Add([]byte{0x02, 0x00, 0x00})           // an empty payload
	f.Fuzz(func(t *testing.T, b []byte) {
		b = b[:len(b):len(b)] // capacity = length: a read beyond the data panics
		fr, err := Decode(b)
		if err != nil {
			if !errors.Is(err, ErrShort) {
				t.Fatalf("unexpected error: %v", err)
			}
			return
		}
		// property: the decoded frame encodes back to a prefix of the input
		if enc := Encode(fr); !bytes.Equal(enc, b[:len(enc)]) {
			t.Fatalf("Encode(Decode(b)) = %x, input %x", enc, b)
		}
	})
}
```
- `go test -fuzz=FuzzDecode -fuzztime=40s` found a panic for the input `"000"` (length 0x3030) in a fraction of a second
  and saved it in `testdata/fuzz/FuzzDecode/<hash>`. A plain `go test` runs that file as a test case
  (`FuzzDecode/c2501043394e49f2`) — with the bug the test fails, after the fix it passes. You commit the file.
- **A pitfall (verified):** without the line `b = b[:len(b):len(b)]` two clean runs of 40 s each (≈5 million executions each,
  `go clean -fuzzcache` before each) **did not find** the bug. The fuzzer passes a slice with a capacity greater than
  the length, and in Go slicing up to the capacity (`b[3:3+n]` with `3+n ≤ cap(b)`) does not panic — a read beyond the data stays
  invisible. Limiting the capacity or an explicit check of the result's length for fuzzing purposes reveals the bug.
- After the fix, 30 s of fuzzing with no findings.

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
        pass  # a documented syntax error — expected; any other exception is a finding


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
```
- Running: `PYTHONPATH=src ./fuzz/fuzz_miniconf.py corpus -max_total_time=60 -artifact_prefix=crashes/`
  (the `corpus` directory with one valid configuration file). After ~80 executions: `ValueError: substring not
  found` from `line.index("]")` — a section without `]`. `ConfigError` inherits from `ValueError`, but the harness catches only
  `ConfigError`, so the undocumented `ValueError` is a finding.
- Reproduction: `./fuzz/fuzz_miniconf.py crashes/crash-<hash>`. Minimization:
  `./fuzz/fuzz_miniconf.py -minimize_crash=1 -runs=2000 -exact_artifact_path=crashes/min crashes/crash-<hash>`
  (8 → 2 bytes). libFuzzer runs `argv[0]` as a program in the process — the script must have a shebang and the execute
  permission, and the `python3` from the environment with Atheris must be first in `PATH`; otherwise minimization does nothing.
- **A pitfall (verified):** `FuzzedDataProvider` decodes text its own way — the first byte picks the encoding
  (`b"[["` → `"["`, `b"\x02\x00a\x00b"` → two UTF-16 characters). In the regression test write the text after decoding,
  not the raw bytes:
```python
def test_unclosed_section_is_config_error():
    with pytest.raises(miniconf.ConfigError, match="line 1"):
        miniconf.parse("[db\nhost = x\n")
```
  Before the fix the test failed, after the fix (`ConfigError` for a line without `]`) it passes; 60 s of fuzzing
  (5.15 million executions) with no findings.

## C — libFuzzer + AddressSanitizer + UBSan (clang 18.1.3)
```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    uint8_t *out = malloc(64);           /* a separate allocation: ASan sees every byte beyond it */
    int r = rle_decode(data, size, out, 64);
    if (r > 64)
        abort();                          /* property: the result is no larger than the buffer */
    free(out);
    return 0;
}
```
Compilation: `clang-18 -g -O1 -fsanitize=fuzzer,address,undefined fuzz_rle.c rle.c -o fuzz_rle` (on Ubuntu the package
`libclang-rt-18-dev` is needed), running `./fuzz_rle -max_total_time=60 corpus`. The seeded bug: the condition
`o + count > cap + 16` instead of `> cap`.

The same bug in three configurations:
| Configuration | Result |
|---|---|
| `-fsanitize=fuzzer,address,undefined` | `heap-buffer-overflow`, `WRITE of size 77`, `rle.c:12` — the exact place |
| `-fsanitize=fuzzer` + `abort()` in the harness | `deadly signal` with the input, with no indication of the write location |
| `-fsanitize=fuzzer`, no condition in the harness | once a process hang, once a SEGV in `free` inside libFuzzer and a save of an empty, wrong input |

After the fix the saved crash passes (`./fuzz_rle crash-<hash>`), and 46 s of fuzzing (29.5 million executions) finds
nothing.

## CI
- A short run in a PR: Go `go test -run='^$' -fuzz=FuzzDecode -fuzztime=60s .` (one package at a time; the saved
  corpus goes into the baseline coverage — "gathering baseline coverage: 5/5"); libFuzzer and Atheris
  `-max_total_time=60`; the corpus from the repository or from the CI cache.
- The inputs found: Go — `testdata/fuzz/` in the repository; Python and C — a directory of regression cases
  replayed in ordinary tests.
- ClusterFuzzLite (GitHub Actions, google/clusterfuzzlite commit 52ecc61): the modes `code-change` (a PR, e.g.
  `fuzz-seconds: 600`), `batch` (longer, on a schedule), `prune` (corpus pruning), `coverage` (a coverage
  report); `sanitizer` in the matrix (address, undefined). The configuration was not run in this session.
