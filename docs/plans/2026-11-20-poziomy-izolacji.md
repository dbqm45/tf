# Poziomy izolacji fabryki: podstawowy, sandbox, kontener

Data: 2026-11-20. Prośba właściciela: po uruchomieniu fabryki ani fabryka, ani Claude nie mogą nic zrobić poza
folderem projektu. Uzasadnienie i ocena poziomów: `docs/insights/isolation.md`. Decyzje właściciela zapisane 2026-11-22
(sekcja „Decyzje właściciela”). Stan: I1 i I2 zrobione (2026-11-22), I3–I9 otwarte.

## Cel

Trzy poziomy do wyboru per projekt, każdy z jasnym opisem tego, co gwarantuje:

| Poziom | Nazwa w konfiguracji | Co gwarantuje |
|---|---|---|
| 1 | `basic` | tylko reguły uprawnień fabryki (filtr na wzorcach poleceń; **to nie jest izolacja**) |
| 2 | `sandbox` (domyślny) | polecenia Bash i ich procesy zapisują tylko w projekcie, nie czytają katalogów z kluczami, sieć tylko z listy |
| 3 | `container` | cała sesja (Claude, fabryka, hooki, skrypty, MCP) widzi tylko folder projektu i osobny `~/.claude`; zapora na cały ruch |

## Stan dziś (`main` fb4cfc8, 2026-11-20)

- **Poziom 1 jest zawsze:** `core/settings.json` ma `allow`, `ask` i `deny` (sekrety, `sudo`, `rm -rf`, force-push).
- **Szablon sandboxa** `core/factory/templates/sandbox.settings.json`: zakaz odczytu `~/.ssh`, `~/.aws`, `~/.kube`,
  `~/.config/gh` itd., sieć do rejestrów pakietów i GitHuba, `allowUnsandboxedCommands: false`. Włączany ręcznie
  przez użytkownika w `.claude/settings.local.json` (opis i pomiary: `core-agent-security`,
  `references/permissions-and-production.md` §4a; pomiar Linux/bubblewrap 2026-10-18).
- **Pomiar na macOS** (`scripts/sandbox_check.py`, płatny, ok. 0,03 USD) — nieuruchomiony.
- **Launcher `tf code`** (`core/factory/tf.py`, `cmd_code`) uruchamia `claude --plugin-dir .tf/plugin --settings
  .tf/plugin/session-settings.json` w układzie wtyczki (plan `docs/plans/2026-11-20-tryb-fabryki-plan.md`).
- **Brak:** zapisanego poziomu, pokazywania go, kontrolera w kodzie, obrazu kontenera.

## Docelowy układ

**Konfiguracja.** `isolation: basic | sandbox | container` w `.tf/config/config.yaml` (plik użytkownika, instalator go
nie nadpisuje). Domyślnie `sandbox`. Wybór przy instalacji: `install.py --isolation <poziom>`, zmiana: `tf isolation
<poziom>` (tylko z terminala człowieka, patrz „Bez obniżania z wnętrza sesji”).

**Poziom 2 przez launcher.** `tf code` dokłada ustawienia sandboxa do `session-settings.json` podawanego w
`--settings`. Według dokumentacji Claude Code ustawienia z wiersza poleceń mają pierwszeństwo przed projektowymi
i lokalnymi, więc projektowe `"enabled": false` nie wyłączy sandboxa w sesji fabryki
(pomiar 2026-11-22 za zgodą właściciela: Claude Code 2.1.330, Linux z bubblewrap, haiku, 2 przebiegi `claude -p`,
0,0067 USD — projekt `{"sandbox": {"enabled": false}}` bez `--settings`: zapis do katalogu domowego przeszedł;
ten sam projekt z `--settings` z szablonem: zapis do katalogu domowego odrzucony „Read-only file system”, zapis
w projekcie przeszedł). W układzie domyślnym (bez wtyczki) instalator wpisuje sandbox do
`.claude/settings.local.json`, jak dziś opisuje skill.

**Poziom 3: `tf code --container` albo `isolation: container`.**
- Obraz `tf-sandbox` (Dockerfile w `core/factory/container/`): Node, Claude Code w przypiętej wersji, Python, git,
  narzędzia z wykrytego stosu projektu (lista z `detect_stack.py`), skrypt zapory.
- Uruchomienie: `docker run` (albo `podman run`) z montażem **tylko** folderu projektu (`/workspace`) i nazwanego
  woluminu na `~/.claude` kontenera. Bez montowania katalogu domowego, gniazda Dockera, `~/.ssh`, `~/.gitconfig`.
  Użytkownik bez uprawnień roota w kontenerze; system plików obrazu tylko do odczytu tam, gdzie się da.
- Zapora (iptables/nftables w kontenerze, jak w referencyjnym devcontainerze Claude Code): domyślnie blokada, dozwolone
  API Anthropic, GitHub i rejestry pakietów; dodatkowe domeny z `isolation_allow_domains` w konfiguracji projektu.
- Wewnątrz kontenera działa poziom 2 (sandbox Bash) jako druga warstwa.
- Szablon `devcontainer.json` na tym samym obrazie dla VS Code i JetBrains (opcjonalnie, decyzja D2).

**Widoczność.**
- Hook `SessionStart` wypisuje poziom i to, czego on nie chroni (jedna linia), np. „Izolacja: sandbox — narzędzia
  plików Claude, hooki i MCP działają poza sandboxem”.
- `tf doctor` porównuje poziom zapisany z faktycznym: czy sandbox jest włączony, czy sesja jest w kontenerze (znacznik
  środowiska ustawiany przez obraz), czy sesja startuje z korzenia repo.
- Pasek stanu fabryki pokazuje poziom.

**Bez obniżania z wnętrza sesji.**
- `tf isolation` odmawia działania, gdy wykryje sesję agenta (zmienne środowiskowe Claude Code); hook `guard_bash.py`
  blokuje to polecenie i edycję klucza `isolation` w `.tf/config/config.yaml` z wnętrza sesji.
- Hook ochrony ścieżek blokuje edycję `session-settings.json`, `.claude/settings*.json` w zakresie `sandbox` i plików
  obrazu z wnętrza sesji.
- Na poziomie 3 kontener i tak nie ma dostępu do konfiguracji hosta poza projektem.

**Minimum firmowe.** Opis w dokumentacji, jak w managed settings wymusić `sandbox.enabled: true` i
`allowUnsandboxedCommands: false`; `tf doctor` ostrzega, gdy poziom projektu jest niższy niż `isolation_min` z
nakładki firmowej (`org/`).

## Kawałki (każdy osobny PR, TDD)

| # | Co | Testy |
|---|---|---|
| I1 | klucz `isolation` w konfiguracji, `install.py --isolation`, `tf isolation <poziom>` z odmową w sesji agenta; `tf doctor` pokazuje poziom | testy instalatora i polecenia; odmowa przy ustawionych zmiennych sesji |
| I2 | poziom 2 przez `tf code` (sandbox w `session-settings.json`) i w układzie domyślnym (`settings.local.json`); test, że projektowe `"enabled": false` nie wyłącza sandboxa przy `--settings` | testy plików ustawień; jeden płatny pomiar `claude -p` za zgodą (ok. 0,05 USD) |
| I3 | hook `SessionStart` i pasek stanu z poziomem; `guard_bash.py` i ochrona ścieżek blokują obniżenie poziomu z wnętrza sesji | testy hooków (bez modelu) |
| I4 | obraz `tf-sandbox`, skrypt zapory, `tf code --container`, montaż tylko projektu i woluminu `~/.claude` | testy polecenia `docker run` (argumenty, montaże, brak gniazda Dockera i katalogu domowego); test obrazu w CI: zapis poza `/workspace` się nie udaje, ruch poza listą jest blokowany |
| I5 | push z kontenera według decyzji D1; obsługa kluczy | testy według wybranego wariantu |
| I6 | szablon devcontainera (jeśli D2 = tak) | build devcontainera w CI |
| I7 | `isolation_min` w nakładce firmowej, ostrzeżenie w `tf doctor`; dokumentacja managed settings | testy `tf doctor` |
| I8 | aktualizacja skilla `core-agent-security` (§4a) i `docs/setup.md`; bramka skilla | `skill_gate.py`, holdout |
| I9 | pomiar na macOS (`scripts/sandbox_check.py`) — uruchamia właściciel na swoim komputerze | wynik wklejony do §4a skilla |

Kolejność: I1 → I2 → I3 (poziom 2 domyślny i widoczny), potem I4 → I5 → I6 (kontener), na końcu I7–I9.
Do I2 nic się nie zmienia u użytkowników.

## Decyzje właściciela

- **D1. Push z kontenera:** (a) tylko z komputera człowieka, kontener commituje; (b) token GitHub ograniczony do
  jednego repo (fine-grained), przekazany jako zmienna środowiskowa; (c) klucz wdrożeniowy repo tylko do zapisu.
- **D2. IDE:** tylko terminal (`tf code --container`) czy także devcontainer dla VS Code i JetBrains.
- **D3. Sieć na poziomie 3:** stała lista (API Anthropic, GitHub, rejestry pakietów) czy z dopisywaniem domen per
  projekt (`isolation_allow_domains`).
- **D4. Domyślny poziom** dla nowych instalacji: `sandbox` (rekomendacja) czy `basic` do czasu pomiaru na macOS.
- **D5. Docker czy Podman** jako wymagany silnik (albo oba).

Odpowiedzi właściciela (2026-11-22):
- D1 → (a) push tylko z komputera człowieka; kontener tylko commituje.
- D2 → na start tylko terminal (`tf code --container`); I6 odłożone.
- D3 → stała lista i domeny dopisywane per projekt (`isolation_allow_domains`).
- D4 → `sandbox` domyślnie.
- D5 → oba silniki; `tf code --container` wykrywa, który jest zainstalowany.

## Ryzyka

- **Systemy:** sandbox nie działa na samym Windowsie, tylko pod WSL2; na Linuksie bez bubblewrap tylko ostrzega;
  na macOS nie ma pomiaru fabryki (I9).
- **Pułapki konfiguracji:** sesja z podkatalogu nie wczytuje ustawień projektu; projektowe `"enabled": false`
  wyłącza sandbox — I2 i I3 muszą to wykrywać kodem.
- **Ograniczenia sandboxa zmierzone w §4a:** pliki-zaślepki dla brakujących ścieżek psują `git add -A`, usługi na
  localhost hosta są niedostępne, reguły `Read` w `deny` blokują odczyt dla wszystkich programów, narzut 20–60 ms na
  wywołanie.
- **Kontener:** wolniejsze pliki na macOS, osobne logowanie do Claude w kontenerze, narzędzia spoza obrazu (lokalna
  baza danych, emulatory) trzeba dodać do obrazu albo udostępnić przez sieć; nigdy nie montować gniazda Dockera
  (to root na hoście).
- **Granica poziomu 3** zależy od silnika kontenerów i jądra; to izolacja procesów, nie maszyna wirtualna. Dla
  najwyższego ryzyka (cudzy kod, produkcja) rozważyć maszynę wirtualną albo osobnego użytkownika systemu.
