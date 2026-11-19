---
name: qa-fuzzing
description: Use for fuzzing code that takes untrusted input — when, a harness, a corpus, sanitizers, crash → regression test, CI (Go, Atheris, libFuzzer).
metadata:
  review: "2027-04-24"
  visibility: name
  catalog: "Use when code takes untrusted or complex input (parsers, decoders, protocols, file formats, deserialization, uploads) and you need to automatically search for inputs that break it — when to fuzz and when property tests are enough, a harness (one input → one call, expected errors told apart from findings, properties such as round-trip), a seed corpus and dictionaries, sanitizers (AddressSanitizer, UBSan) for native code, a finding → minimization → a regression test, fuzzing in CI (short in a PR, long overnight, ClusterFuzzLite, OSS-Fuzz), tools: native Go fuzzing (testing.F), Atheris (Python), libFuzzer (C/C++), Jazzer (Java). Not for property tests in Hypothesis or fast-check without a fuzzer (tool-pytest, eng-testing), load tests (qa-performance-testing), scanning dependencies for vulnerabilities (ops-supply-chain-security) or variant analysis of a vulnerability that was found (sec-variant-analysis)."
  keywords: "fuzzing, fuzzer, fuzz test, sfuzzować, go test -fuzz, testing.F, f.Fuzz, f.Add, Atheris, libFuzzer, LLVMFuzzerTestOneInput, AFL++, Jazzer, cargo-fuzz, AddressSanitizer, ASan, UBSan, sanitizer, korpus, corpus, harness, crash, minimalizacja crasha, złośliwe wejście, parser binarny, dekoder, panika na wejściu, ClusterFuzzLite, OSS-Fuzz, to fuzz, crash minimization, malicious input, binary parser, decoder, panic on input"
---

# Fuzzing

A fuzzer generates and mutates inputs, guided by code coverage, and looks for ones that cause a crash, a panic,
an unexpected exception, a hang or a violated property. It complements example tests and property tests
(eng-testing): those check rules, the fuzzer looks for inputs nobody thought of.

## When to fuzz
- **Yes**: a parser, a decoder, deserialization, protocol handling, a file format, compression, expressions and templates —
  especially on input from the network or from a user, and in native code (C, C++, `unsafe`).
- **Property tests are enough**: business logic on typed data (amounts, dates, rules) — Hypothesis
  or fast-check (tool-pytest, tool-vitest).
- **Not a fuzzer**: performance under load (qa-performance-testing), bugs in dependencies (SCA,
  ops-supply-chain-security).

## Procedure
1. **The target**: one function at a trust boundary (`Decode(bytes)`, `parse(text)`), with no network, files, clock
   or global state — the result depends only on the input, so every finding can be reproduced.
2. **The harness**: the fuzzer input → the function's type (bytes, text, a structure through `FuzzedDataProvider`), one
   call, then a check:
   - expected, documented errors (`ErrShort`, `ConfigError`) you let through; any other exception, panic or
     crash is a finding;
   - properties instead of just "does not blow up": round-trip (`Encode(Decode(b))`), a result within the buffer bounds,
     agreement with a reference implementation.
3. **The seed corpus**: a few valid and edge inputs (`f.Add`, the `corpus/` directory), for formats with
   tokens — a dictionary. The corpus grows during fuzzing; keep it in the repository or in the CI cache.
4. **Sanitizers for native code**: `-fsanitize=fuzzer,address,undefined`. Without ASan a memory error shows up
   far from the cause (a hang, a crash in the allocator, a wrongly saved input); with ASan — the line and the size of
   the write. Allocate the buffer in the harness separately (`malloc` of the exact size) so that ASan sees the boundary.
5. **A finding**: reproduce from the saved file, minimize, fix the cause, turn the input into a regression test
   (Go does this itself: `testdata/fuzz/`), run the fuzzer again. A finding in security code → check the variants
   (sec-variant-analysis).
6. **CI**: a short run in every PR (30–600 s, with a fixed corpus), a long one overnight or on a schedule
   (ClusterFuzzLite `code-change` and `batch`; open source projects — OSS-Fuzz); the corpus and findings kept between
   runs. Fuzzing without a time limit does not fit in a PR.
7. **A tool by language**: Go — `testing.F` (`go test -fuzz`); Python — Atheris; C/C++ — libFuzzer (or AFL++);
   Java — Jazzer with JUnit 5.9+ (`jazzer-junit`, `@FuzzTest`) [unverified: not run]. Examples
   with code and results: `references/harness-and-examples.md`.

## Pitfalls (each verified)
- **Go**: slicing up to the capacity does not panic, and the fuzzer passes a `[]byte` with spare capacity — a read beyond the data
  was invisible for 10 million executions. For fuzzing: `b = b[:len(b):len(b)]` or an explicit length check.
- **Atheris**: `FuzzedDataProvider` picks the text encoding with the first byte — write the regression test on the text
  after decoding, not on raw bytes. Minimization (`-minimize_crash=1`) runs the script as a program:
  a shebang, the execute permission and the right `python3` in `PATH`.
- A harness that catches every exception (`except Exception`) will find nothing — catch only the documented ones.

## Example
A frame decoder in Go without a check that the payload has the declared length: `FuzzDecode` with two examples
in `f.Add` and a round-trip property. The fuzzer found the input `"000"`, but only after adding `b[:len(b):len(b)]`
— before that 2 × 40 s with no finding. The file from `testdata/fuzz/FuzzDecode/` fails `go test` before the fix
and passes after it. Likewise: Atheris found an undocumented `ValueError` in a config parser
after ~80 executions, libFuzzer with ASan — a heap overflow in an RLE decoder with the source line.
Code: `references/harness-and-examples.md`.

## Checklist
- [ ] the target is deterministic, at a trust boundary; the harness tells expected errors from findings
- [ ] at least one property beyond "does not blow up"
- [ ] a seed corpus in the repository; native code with ASan and UBSan
- [ ] every finding: reproduce → minimize → fix → regression test → fuzz again
- [ ] short fuzzing in a PR, long overnight; the corpus kept between runs

## Sources
- Go: the `testing` package (`F.Add`, `F.Fuzz`), `go test -fuzz`, go1.24.7 — the example run 2026-10-24.
- Atheris 3.1.0 (PyPI), libFuzzer and sanitizers from clang 18.1.3 (Ubuntu 24.04) — the examples run 2026-10-24.
- ClusterFuzzLite, GitHub Actions documentation (google/clusterfuzzlite, commit 52ecc61); Jazzer, README
  (CodeIntelligenceTesting/jazzer, commit a4e09fb, Apache 2.0) — read 2026-10-24.
- The inspiration for the topic: Trail of Bits `testing-handbook-skills` — the content was not taken over.
Described in our own words.
