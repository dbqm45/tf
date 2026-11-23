# D8 — lokalna pamięć podręczna decyzji suity (mode-pdi)

**Data:** 2026-11-23 · **Źródło:** pdi `docs/plan-budowy-suity.md` §3a (krok D8, model pkt 5) · **Zależy od:** D3
(tf #412: publikacja decyzji fabryki), D7 (pdi #200: `pdi-records changes`, odczyt przyrostowy)

## Cel
Agent fabryki zna decyzje innych aplikacji suity (bramki w pdi, decyzje DI Definition, decyzje z innych repo) zanim
zacznie zadanie, także bez połączenia z pdi, i widzi, jak stara jest jego kopia.

## Ustalenia
1. **Skąd dane:** `pdi-records changes` (pdi D7) uruchamiane lokalnie — rejestr pdi leży dziś na komputerze właściciela,
   API HTTP przyjdzie z usługą pdi (DA4). Polecenie z `TF_DECISION_CACHE_CMD` (np.
   `uv run --directory ~/pdi pdi-records`), domyślnie `pdi-records`; rejestr z `PDI_REGISTRY_PATH`. Włączone tylko,
   gdy jedno z nich jest ustawione; `TF_DECISION_CACHE=0` wyłącza.
2. **Hook `decision_cache.py`** na SessionStart (`startup|resume`) odświeża kopię przyrostowo (znacznik `next`
   z poprzedniego razu, strony do `complete`, limit czasu) i wypisuje jedną linię do kontekstu sesji: ile decyzji
   obowiązuje, ile zastąpionych, wiek kopii i jak szukać. Na żądanie: `refresh`, `status`, `search <słowa>`.
3. **Kopia tylko do odczytu, poza gitem:** `.tf/cache/suite-decisions/DEC-n.md` — plik Decision Record dosłownie
   z pdi, z komentarzem „kopia z indeksu suity, nie edytuj” pod nagłówkiem, uprawnienia tylko do odczytu; stan
   w `meta.json` (znacznik, chwila pobrania, skróty plików). Zmieniony ręcznie plik wykryty po skrócie → kopia
   pobierana od nowa, a zdarzenie w dzienniku błędów hooków.
4. **Zakres:** cały indeks poza decyzjami tego repo opublikowanymi przez fabrykę (`origin.app: tf` i `scope` = to
   repo) — te są lokalnie. Organizacji i filtrów zakresu w pdi jeszcze nie ma (usługa tożsamości); indeks jest mały.
   Decyzje zastąpione zostają w kopii ze statusem `superseded`, więc nie wyglądają na obowiązujące.
5. **Bez połączenia:** błąd polecenia albo przekroczony czas → ostatnia kopia zostaje, linia w kontekście mówi
   „nieaktualna” z jej wiekiem; sesja nigdy nie jest blokowana.
6. **Szukanie przed zadaniem:** `search` przeszukuje kopię i lokalne decyzje (`docs/project/decisions.md`, ADR)
   razem, fragmenty słów bez wielkości liter, z oznaczeniem pochodzenia, statusu i linku; skill `pdi-decisions` mówi,
   żeby wywołać je przed planem zadania.

## Pliki
| Plik | Zmiana |
|---|---|
| `modes/mode-pdi/hooks/decision_cache.py` (nowy) | odświeżanie, kopia, stan, szukanie |
| `modes/mode-pdi/settings.json` | hook na SessionStart, zgoda na polecenie |
| `modes/mode-pdi/tests/test_decision_cache.py` (nowy) | z udawanym `pdi-records` |
| `modes/mode-pdi/skills/pdi-decisions/SKILL.md`, `modes/mode-pdi/GUIDE.md` | kiedy szukać, jak włączyć |

## Kolejność (TDD)
1. Test (czerwony): wyłączony bez konfiguracji; pierwsze pobranie (pliki, znacznik „nie edytuj”, tylko odczyt, bez
   decyzji tego repo, linia w kontekście); drugie z `--since`; strony; zastąpienie nadpisuje status; pdi niedostępne
   → stara kopia i „nieaktualna”; ręczna zmiana → pobranie od nowa; `search` w kopii i lokalnie.
2. Kod, ustawienia, opis; bramka skilla `pdi-decisions`.

Bramki: `python3 tools/workspace.py check --packs mode-pdi` i `--packs all`, `refs`, `for t in tests/test_*.py`,
`scripts/check_commit_message.py`.
