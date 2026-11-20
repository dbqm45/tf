# Plan: fabryka poza repozytorium, dane projektu w `.tf-project/`

Data: 2026-11-20. Status: propozycja do realizacji po teście dodatków `dna` i `standards` na repozytorium firmy.
Podstawa: rozmowa z człowiekiem z 2026-11-20 (sekcja 2). Każdy kawałek to osobny PR, kod metodą TDD.

## 1. Cel

Silnik fabryki jest jak `node_modules`: odtwarzalny, podmieniany przy aktualizacji, niezależny od repozytorium
projektu. Wszystko, co należy do projektu, jest w jednym katalogu `.tf-project/` i trafia do gita:
- przypięta wersja fabryki, nakładek i dodatków;
- ustawienia zespołu, w tym linki do standardów;
- wynik `learn`, do przeglądu w PR.

Ustawienia osobiste są poza gitem. Po `git clone` wystarczy `tf install`, żeby odtworzyć fabrykę z lockfile'a
(jak `npm ci`).

## 2. Decyzje

| # | Decyzja | Uzasadnienie |
|---|---|---|
| U1 | `.tf/` — tylko silnik i stan roboczy, nigdy w gicie | silnik jest odtwarzalny; stan roboczy bywa poufny (kopie stron Confluence) |
| U2 | `.tf-project/` — dane projektu w gicie, poza `*.local.*` | jedna reguła, jedno miejsce; zmiana standardów i stacku widoczna w PR |
| U3 | Ustawienia firmy zostają w nakładce firmy (własne repozytorium i wersje); projekt tylko je przypina | kopia ustawień firmy w każdym repo rozjedzie się z oryginałem przy pierwszej zmianie |
| U4 | Jeden katalog zamiast plików `.tf.settings.*` w głównym katalogu repo | mniej plików w katalogu głównym, prostsza reguła ignorowania |
| U5 | Ustawienia osobiste: `~/.tf/preferences.yaml` (wszystkie projekty, już istnieje) i `.tf-project/settings.local.yaml` (wyjątek w jednym projekcie) | styl pracy (np. step-by-step) jest cechą osoby, nie projektu |
| U6 | Pliki fabryki w `.claude/` (skille, agenci, hooki, reguły dodatków, ustawienia) — generowane i ignorowane, jak dziś w trybie prywatnym; własne skille i reguły projektu zostają w `.claude/` w gicie | Claude Code czyta skille, agentów, hooki i reguły tylko z `.claude/` |
| U7 | Zmiana niezgodna wstecz: wersja główna rdzenia (MAJOR) i migracja istniejących instalacji (`migrations.py`) | ścieżki zmieniają się w instalatorze, aktualizatorze, hookach i skillach |

## 3. Układ docelowy

```
.tf/                               nigdy w gicie (cały katalog w .gitignore)
  factory/                         silnik (dziś też tu)
  addons/<nazwa>/                  kod dodatków (bez out/; pamięć podręczna w cache/)
  cache/  runs/  logs/  wip/  locks/  worktrees/  backup/  reports/  register/

.tf-project/                       w gicie
  factory.lock.yaml                wersja fabryki i źródło, nakładka firmy i zespołu (źródło + wersja), nakładki,
                                   tryby, dodatki z wersjami; skróty plików fabryki (dziś .claude/factory-lock.json)
  settings.yaml                    ustawienia zespołu (dziś .tf/config/config.yaml): tryby, limity, profil kosztów,
                                   addons.<nazwa> (np. addons.standards.sources — linki do standardów)
  settings.local.yaml              osobiste ustawienia w tym projekcie (w .gitignore)
  personas/  roles/  traits/       własne persony, role i cechy (dziś .tf/config/…)
  operations.json                  karta operacyjna: tracker, prefiksy (dziś .tf/config/operations.json)
  knowledge/<dodatek>/             wynik learn: INDEX.md, rules/, catalog/, decisions.md, knowledge.json
                                   (dziś .tf/addons/<dodatek>/out/)

.claude/                           Claude Code
  skills/<własne>/  rules/<własne>  w gicie
  skills/<fabryki>/, agents/_generated/, hooks/, rules/addon-*, settings.local.json, catalog.md
                                   generowane przez tf install / build — w .gitignore

docs/project/                      bez zmian (dziennik projektu, zadania, decyzje — w gicie)
```

`.gitignore` dostaje stały blok fabryki, który zapisuje instalator, oparty na liście plików fabryki z
`factory.lock.yaml` (nie na wzorcach, żeby nie objąć własnych skilli projektu).

## 4. Zachowanie

- **`git clone` → `tf install`:** czyta `factory.lock.yaml`, pobiera tę wersję fabryki, nakładki i dodatki,
  odtwarza `.tf/` i pliki fabryki w `.claude/`, uruchamia `build`. Nic w `.tf-project/` się nie zmienia.
- **`tf install --frozen` (CI):** jak wyżej; różnica między lockfile'em a źródłem to błąd, nie aktualizacja.
- **`tf update`:** nowa wersja fabryki → nowy `factory.lock.yaml` (diff do przeglądu w PR), pliki fabryki
  odtworzone.
- **Start sesji:** hook porównuje zainstalowaną wersję z `factory.lock.yaml`; przy różnicy jedno zdanie
  „uruchom `tf install`” (bez automatycznej instalacji w trakcie sesji).
- **`tf learn` / `tf addon refresh`:** wynik do `.tf-project/knowledge/<dodatek>/`, pamięć podręczna do `.tf/`.
  Dodatki dostają ścieżkę wyniku w zmiennej środowiskowej (`TF_ADDON_OUT`) — kontrakt dodatków wersja 2
  (`provides.*` wskazuje pliki względem katalogu wyniku); fabryka obsługuje kontrakt 1 przez okres przejściowy.
- **Prywatna instalacja bez commitowania niczego:** `.tf-project/` też w `.git/info/exclude` — jak dziś.

## 5. Kawałki

Kolejność: U-A → U-B → U-C → U-D → U-E → U-F → U-G. Każdy kawałek po zielonym `tools/workspace.py check` dla
wszystkich nakładek.

| # | Kawałek | Co powstaje | Testy (czerwone przed kodem) |
|---|---|---|---|
| U-A | Jedno miejsce na ścieżki | moduł ścieżek w rdzeniu (`core/factory/paths.py`): `ENGINE`, `PROJECT`, `KNOWLEDGE`, `STATE`, `LOCAL_SETTINGS`; wszystkie skrypty rdzenia i hooki biorą ścieżki z niego (bez zmiany wartości) | brak literałów `.tf/config`, `.tf/runs` itd. poza modułem (test repozytorium); zachowanie bez zmian |
| U-B | `.tf-project/settings.yaml` | warstwy konfiguracji czytają `.tf-project/settings.yaml` przed `.tf/config/config.yaml` (zgodność wstecz), `settings.local.yaml` jako warstwa osoby w projekcie; `tf config show` pokazuje nowe źródła | kolejność warstw; plik lokalny ignorowany przez git; stary plik działa z ostrzeżeniem w `tf doctor` |
| U-C | `factory.lock.yaml` | lockfile w `.tf-project/` z wersją, źródłami nakładek (w tym firmy) i dodatków; `tf install` z lockfile'a; `--frozen` | odtworzenie po `git clone` w czystym katalogu; `--frozen` przy rozbieżności → kod 1; nakładka firmy z innego repo |
| U-D | Wynik dodatków w `.tf-project/knowledge/` | kontrakt dodatków 2 (`TF_ADDON_OUT`), `dna` i `standards` piszą tam; `sync` czyta stamtąd; kontrakt 1 nadal obsługiwany | wynik w gicie, pamięć podręczna nie; przegląd PR widzi zmianę reguły |
| U-E | `.claude/` bez plików fabryki w gicie | blok `.gitignore` z listy plików fabryki; tryb zespołowy przestaje commitować silnik | własne skille projektu zostają; `tf install` po klonie odtwarza resztę; CI z `tf install --frozen` |
| U-F | Migracja | `migrations.py`: przeniesienie `.tf/config/*` → `.tf-project/`, `.claude/factory-lock.json` → `factory.lock.yaml`, `.tf/addons/*/out/` → `.tf-project/knowledge/`, usunięcie plików fabryki z indeksu gita (`git rm --cached`) z jednym commitem do przeglądu | instalacja prywatna i zespołowa sprzed zmiany → po migracji te same ustawienia i wyniki; ponowne uruchomienie nic nie zmienia |
| U-G | Hook wersji i dokumentacja | ostrzeżenie przy starcie sesji o rozbieżności z lockfile'em; `GUIDE.md`, `ONBOARDING.md`, `org/README.md`, README dodatków, wydanie MAJOR | komunikat tylko przy rozbieżności; brak lockfile'a → brak komunikatu |

## 6. Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| zespół zapomni `tf install` po klonie i pracuje bez fabryki | hook przy starcie sesji; `tf doctor`; krok w CI z `--frozen` |
| własne pliki projektu w `.claude/` przypadkiem w `.gitignore` | ignorowanie wg listy plików z lockfile'a, nie wzorców; test na projekcie z własnymi skillami |
| migracja psuje istniejące instalacje | migracja idempotentna, kopia w `.tf/backup/`, osobny commit do przeglądu, `update.py --rollback` |
| dwa źródła ustawień w okresie przejściowym | stare ścieżki działają jedną wersję główną z ostrzeżeniem w `tf doctor`, potem znikają |
| wynik `learn` w gicie często się zmienia (szum w PR) | `refresh` zapisuje tylko przy zmianie odcisku; wynik deterministyczny (sortowanie, bez dat w treści poza nagłówkiem) |

## 7. Do decyzji przed startem
1. Nazwa katalogu: `.tf-project/` (propozycja) albo krótsza, np. `.tfp/`.
2. Czy wynik `learn` commitować domyślnie, czy tylko na żądanie (`addons.<nazwa>.commit_output`).
3. Okres przejściowy dla starych ścieżek: jedna wersja główna (propozycja).
