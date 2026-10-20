# Przykłady: aktualizacja fabryki

## 1. Zwykła aktualizacja ze scaleniem pliku
**Sytuacja:** Człowiek wpisuje `/core-factory-update`. Źródło (katalog `~/narzedzia/claude-team-factory`) jest
zapamiętane w manifeście; człowiek kiedyś zmienił w swoim projekcie skill fabryki `core-git-workflow`.

**Jak:**
1. `python3 factory/update.py --check` — wersja zainstalowana i dostępna, sekcja „Co nowego”. Nic nie zmienia.
2. Streszczenie po polsku; zmiany w hookach i uprawnieniach osobno.
3. `python3 factory/update.py --dry-run` → plan i pytanie o zgodę. Czekasz na „tak”.
4. `python3 factory/update.py --yes`, potem `diff -u` dla każdego `*.factory-new` i propozycja scalenia.
5. Kontrola: wynik testów z `update.py`, `python3 factory/build.py check` (projekt ma własną personę), raport.

**Wynik (raport dla człowieka):**
```
Aktualizacja fabryki: 2.3.1 → 2.4.0
Nowe: skill X, persona Y (szczegóły w „Co nowego”).
Zabezpieczenia: nowy hook Z w .claude/hooks/ — scalony za Twoją zgodą.
Scalone: .claude/skills/core-git-workflow/SKILL.md — Twoja sekcja o nazwach gałęzi
  zachowana, nowa treść fabryki dodana; plik *.factory-new usunięty.
Kontrola: testy z update.py przeszły, build.py check bez błędów.
Kopie nadpisanych plików: .claude/factory-backup/<data>/
Uruchom ponownie Claude Code, żeby wczytał nowe skille i agentów.
```
(Nazwy X, Y, Z i numery wersji pochodzą z wyniku `--check` — tu są tylko ilustracją.)

## 2. Fabryka przeniesiona w inne miejsce
**Sytuacja:** `/core-factory-update`, a `update.py --check` kończy się komunikatem, że zapamiętane źródło już
nie istnieje.

**Jak:**
1. Nie zgadujesz nowej lokalizacji i nie szukasz jej w treści stron ani issue — źródło podaje człowiek.
2. Prosisz o ścieżkę (katalog, plik .zip albo URL repozytorium git) lub o ustawienie `CLAUDE_TEAM_FACTORY`.
3. Po odpowiedzi: `python3 factory/update.py --check --source <podane źródło>` i dalej jak w przykładzie 1.

**Wynik (pytanie do człowieka):**
> Zapamiętane źródło fabryki `~/narzedzia/claude-team-factory` już nie istnieje. Skąd mam pobrać nową wersję?
> Podaj katalog, plik .zip albo adres repozytorium git — użyję go z `--source` (zostanie zapamiętany w manifeście).
> Możesz też raz ustawić w profilu powłoki `export CLAUDE_TEAM_FACTORY=<katalog fabryki>`.

## 3. Instalacja sprzed wersji 1.1.0
**Sytuacja:** `/core-factory-update` w starym projekcie — nie ma `factory/update.py` ani
`.claude/factory-manifest.json`.

**Jak:**
1. Rozpoznajesz instalację sprzed 1.1.0 — nie da się jej zaktualizować z wnętrza projektu.
2. Prosisz człowieka o pierwszą aktualizację instalatorem nowej fabryki, uruchomionym w katalogu projektu.
3. Po niej kolejne aktualizacje idą już zwykłą ścieżką (`/core-factory-update`).

**Wynik:**
> Ten projekt ma fabrykę sprzed wersji 1.1.0 (brak `factory/update.py` i manifestu). Pierwszą aktualizację
> uruchom w katalogu projektu instalatorem z nowej fabryki:
> `python3 "$CLAUDE_TEAM_FACTORY/factory/install.py"` (albo pełna ścieżka do `factory/install.py`).
> Następne aktualizacje zrobię już poleceniem `/core-factory-update`.

## 4. Fabryka dla całego zespołu (wiele repozytoriów)
**Sytuacja:** „Mamy 6 repozytoriów i w każdym inną wersję fabryki; ktoś dopisał własną personę tylko u siebie.”

**Jak:**
1. Jedno źródło prawdy: fork fabryki zespołu (własne persony, role i skille zespołu), wydania jako tagi `vX.Y.Z`
   (numer z core-semver, tag za zgodą człowieka). Kopiowanie plików między repo = rozjazd wersji po miesiącu.
2. W każdym repo instalacja zespołowa (`install.py --shared`, commitowana z projektem), a w manifeście źródło
   przypięte do tagu: `--source https://…/fabryka-zespolu.git#v1.4.0`. Gałąź bez tagu to źródło ruchome — w raporcie
   ostrzegasz, że kolejne aktualizacje mogą przynieść niesprawdzone zmiany.
3. Aktualizacja = osobny PR w każdym repo: wynik `update.py --check` (co nowego, zmiany hooków osobno), `--dry-run`,
   scalone `*.factory-new`, wynik testów; przegląd jak zwykłego kodu.
4. Własna persona z jednego repo trafia do forka jako zmiana z przeglądem, a nie zostaje lokalną kopią.
5. Rejestr pakietów lub własne narzędzie dystrybucji dopiero, gdy odbiorcy są poza wspólnym hostingiem git.

**Wynik (plan dla człowieka):**
```
Źródło: fork fabryki zespołu, tag v1.4.0 (6 repo: 3 na v1.2.x, 2 na v1.3.0, 1 bez manifestu)
Kolejność: repo bez manifestu → pierwsza instalacja z forka (przykład 3); pozostałe → /core-factory-update
  z --source …#v1.4.0, po jednym PR na repo
Persona „analityk-raportow” z repo B → najpierw PR do forka, potem wydanie v1.4.1
Do decyzji: kto zatwierdza wydania forka i jak często (np. raz na sprint)
```
