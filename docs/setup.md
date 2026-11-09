# Instalacja komendy `tf`

Fabryka nie jest programem instalowanym raz na komputerze, tylko zestawem plików, które trafiają do każdego projektu
(`.claude/` i `.tf/`). Na komputer instaluje się jedna rzecz: komenda `tf`. W katalogu projektu `tf install` pobiera
najnowsze wydanie fabryki i ją instaluje, a `tf` (albo `tf update`) później ją aktualizuje.

Wymagania: **Python 3.9+** i **git**. Skrypt sprawdza oba i podpowiada, jak je doinstalować.

## Jedna linijka

Repozytorium `dbqm45/tf` jest prywatne, więc pobranie skryptu i samej fabryki wymaga dostępu do niego. Najprościej
przez [GitHub CLI](https://cli.github.com/) (`gh auth login` raz na komputerze — git korzysta z tego samego logowania).

**macOS, Linux:**

```sh
gh api repos/dbqm45/tf/contents/scripts/install.sh -H "Accept: application/vnd.github.raw" | sh
```

**Windows (PowerShell):**

```powershell
gh api repos/dbqm45/tf/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw" | Out-String | iex
```

Bez `gh`, z tokenem GitHuba (uprawnienie do odczytu repozytorium) w zmiennej `GITHUB_TOKEN`:

```sh
curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.ps1 -Headers @{Authorization = "Bearer $env:GITHUB_TOKEN"} | iex
```

Gdy repozytorium stanie się publiczne, wystarczy samo
`curl -fsSL https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.sh | sh`
(Windows: `irm https://raw.githubusercontent.com/dbqm45/tf/main/scripts/install.ps1 | iex`).

## Co robi skrypt

1. Sprawdza Pythona 3.9+ (`python3`, `python`; na Windows najpierw `py`) i gita.
2. Pobiera fabrykę (`git clone --depth 1`) do katalogu tymczasowego.
3. Instaluje komendę `tf` w `~/.local/bin` (`core/factory/tf.py --install-launcher`) z adresem repozytorium zapisanym
   w środku; na Windows także `tf.cmd`.
4. Usuwa katalog tymczasowy. Jeśli `~/.local/bin` nie ma w PATH, mówi, co dopisać (na Windows pyta, czy dopisać do PATH
   użytkownika).

Komunikaty skryptów są po angielsku i tylko w ASCII, bo Windows PowerShell 5.1 czyta `irm … | iex` w innym
kodowaniu niż UTF-8 i psuje polskie litery i symbole.

Poza plikiem `tf` (i `tf.cmd`) skrypt niczego nie instaluje i nie zmienia profilu powłoki. Skrypt pobrany z sieci
przeczytaj przed uruchomieniem: `scripts/install.sh`, `scripts/install.ps1`.

## Ustawienia

| Zmienna | Domyślnie | Po co |
|---|---|---|
| `TF_REPO` | `https://github.com/dbqm45/tf.git` | inne repozytorium (np. fork) albo SSH: `git@github.com:dbqm45/tf.git` |
| `TF_BIN` | `~/.local/bin` | inny katalog na komendę `tf` |
| `TF_PYTHON` | `python3 python` (Windows: `py python3 python`) | konkretny Python |
| `TF_GIT` | `git` | konkretny git |
| `TF_NO_PATH` | — | Windows: bez pytania o PATH |

Przykład: `curl … | TF_BIN=~/bin sh`.

## Dalej

```sh
cd ~/projects/moja-aplikacja
tf install            # wybór nakładek i języka; zapisuje fabrykę do .claude/ i .tf/
tf                    # później: aktualizacja do najnowszego wydania
```

Przewodnik po fabryce w projekcie: `.tf/factory/PRZEWODNIK.md`; najczęstsze pytania: `.tf/factory/FAQ.md`.
Z klonu repozytorium działa też `sh scripts/install.sh` albo `python3 core/factory/tf.py --install-launcher`.
