# Onboarding: pierwsza instalacja fabryki

Ten plik prowadzi od zera do działającej fabryki w projekcie. Codzienna praca: `PRZEWODNIK.md`, częste pytania:
`FAQ.md` (oba trafiają przy instalacji do `factory/` w projekcie).

## 1. Raz na komputerze: polecenie `tf`
Potrzebny jest Python 3 i git.

```bash
git clone <adres repozytorium fabryki> ~/tools/tf
python3 ~/tools/tf/core/factory/tf.py --install-launcher
```

- Skrypt kopiuje `tf` do `~/.local/bin` (inny katalog: `--bin <katalog>`; w Windows powstaje też `tf.cmd`).
- W `tf` zapisuje adres repozytorium: z `--repo <url>`, ze zmiennej `TF_REPO` albo z `origin` klonu.
- `~/.local/bin` musi być w `PATH`.
- `tf` uruchamia kod z tego repozytorium, więc wskaż tylko takie, któremu ufasz.

## 2. W projekcie: instalacja
```bash
cd ~/projects/moja-aplikacja
tf
```

Bez fabryki w projekcie `tf` instaluje najnowsze wydanie (najwyższy tag `vX.Y.Z`). Przy pierwszej instalacji pyta o:
- język pracy (rozmowa, dokumentacja; domyślnie `pl`);
- język commitów i PR (domyślnie `en`);
- nakładki (`pack-*`) i tryby (`mode-*`).

Wymagane nakładki i nakładka języka (dla `pl`: `pack-editorial-pl`) dochodzą same. Na koniec instalator składa
agentów (`factory/build.py`).

Bez pytań, na przykład w skrypcie:

```bash
tf install --packs pack-it,pack-docs --language pl --commit-language en --yes
```

Podgląd bez zmian: `python3 ~/tools/tf/core/factory/install.py --dry-run`.

## 3. Prywatnie czy zespołowo
| | Prywatnie (domyślnie) | Zespołowo (`tf install --shared`) |
|---|---|---|
| Ustawienia i hooki | `.claude/settings.local.json` | `.claude/settings.json` |
| Zasady | `CLAUDE.local.md` | `CLAUDE.md` |
| Git | nic nie trafia do repozytorium; ścieżki fabryki w `.git/info/exclude` (`--gitignore`: w `.gitignore`) | fabryka commitowana z projektem, do tego workflow CI |

Prywatnie — gdy fabryka jest tylko Twoim narzędziem. Zespołowo — gdy ma działać u wszystkich i w CI.

## 4. Pierwsze uruchomienie
1. W katalogu projektu uruchom `claude` i zaakceptuj zaufanie do folderu. Bez tego hooki i uprawnienia nie
   działają.
2. Sprawdź instalację: `tf doctor` (naprawa: `tf doctor --fix`), lista nakładek i trybów: `tf list`.
3. Wybierz personę z `.claude/catalog.md` i uruchom ją: `claude --agent <nazwa>`. Dalej: `factory/PRZEWODNIK.md`.

## 5. Sesje w chmurze (claude.ai/code)
- Hooki fabryki działają tylko w sesji uruchomionej w katalogu repozytorium projektu.
- Fabryka musi być w repozytorium (`--shared`) albo instalowana w skrypcie startowym środowiska.
- Sesja z kilkoma repozytoriami albo z katalogu nadrzędnego nie wczytuje hooków (nie ma komunikatów startowych).
  Testy i bramki uruchamiasz wtedy ręcznie.

## 6. Potem
| Polecenie | Co robi |
|---|---|
| `tf` | aktualizacja (`tf update --check` — co się zmieni, bez zmian) |
| `tf add <id>` / `tf remove <id>` | dodanie lub usunięcie nakładki albo trybu |
| `tf language <kod>` / `tf commit-language <kod>` | zmiana języków |
| `python3 factory/update.py --rollback` | powrót do poprzedniej wersji |

Pliki fabryki zmienione przez Ciebie aktualizacja zostawia; nowa wersja ląduje obok jako `*.factory-new`. Wszystkie
opcje: `python3 ~/tools/tf/core/factory/install.py --help` i `tf --help`.
