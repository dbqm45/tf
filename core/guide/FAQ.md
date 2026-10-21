# FAQ

Codzienna praca: `factory/PRZEWODNIK.md`.

## Czym jest fabryka?
Zestaw do pracy z agentami Claude Code. Instaluje w projekcie persony (agentów, z którymi rozmawiasz), ich
wykonawców, skille z wiedzą i procedurami, hooki pilnujące zasad (TDD, sekrety, bezpieczne polecenia) i skrypty,
które robią mechaniczną pracę bez tokenów. Składa się z rdzenia, nakładek dziedzinowych (`pack-*`) i trybów pracy
na żądanie (`mode-*`).

## Jak dodać fabrykę do projektu?
W katalogu projektu uruchom `tf` (albo `python3 <fabryka>/core/factory/install.py`). Przy pierwszej instalacji
wybierasz język pracy, język commitów oraz nakładki i tryby.
- **Prywatnie** (domyślnie): nic nie trafia do repozytorium. Ustawienia są w `.claude/settings.local.json`, zasady
  w `CLAUDE.local.md`, a ścieżki fabryki w `.git/info/exclude`.
- **Zespołowo** (`--shared`): fabryka jest commitowana razem z projektem. Ustawienia są w `.claude/settings.json`,
  zasady w `CLAUDE.md`, do tego workflow CI.

Potem uruchom raz `claude` w katalogu projektu i zaakceptuj zaufanie do folderu. Bez tego hooki i uprawnienia
nie działają.

## Jak zaktualizować fabrykę?
- `tf update --check` pokazuje, czy jest nowa wersja i co się zmieni, niczego nie zmieniając.
- `tf` (albo `python3 factory/update.py`) aktualizuje.

Przed aktualizacją skille nowej wersji przechodzą audyt narzędziem z wersji zainstalowanej. Pliki fabryki, które
zmieniłeś, zostają, a nowa wersja ląduje obok jako `*.factory-new`. Powrót: `python3 factory/update.py --rollback`.

## Czy aktualizacje mogą działać same?
Tak: `python3 factory/update.py --auto on` (wyłączenie: `--auto off`). Automatycznie wchodzą tylko wydania PATCH
i MINOR. Wydanie MAJOR, które zmienia publiczne API fabryki, wymaga Twojej decyzji.

## Jak dodać albo usunąć nakładkę lub tryb?
- `tf add <id>` i `tf remove <id>`. Usunięte pliki trafiają do `.claude/factory-backup/`.
- Lista dostępnych i zainstalowanych: `tf list`.
- Domyślna nakładka lub tryb, które pojawią się w nowej wersji, dochodzą przy aktualizacji raz. Usunięte przez
  Ciebie nie wracają.

## Który model i ile to kosztuje?
- Role mają tiery: `fast` (Haiku), `std` (Sonnet), `deep` (Opus).
- Profil zespołu przestawia je jednym poleceniem: `python3 factory/profile.py oszczedny|zrownowazony|jakosc`.
- Koszt mierzysz poleceniem `python3 factory/cost_report.py --days 7`, a pasek stanu pokazuje koszt bieżącej sesji.

Funkcje płatne z natury (ewaluacje skilli na modelu, agent teams) uruchamiasz świadomie.

## Czym są hooki fabryki?
Skrypty uruchamiane przez Claude Code przy zdarzeniach, niezależnie od decyzji modelu:
- `guard_bash` — groźne polecenia powłoki;
- `guard_paths` — pliki z sekretami;
- `cleanroom_guard` — izolacja informacji między agentami;
- `tdd_guard` — kod dopiero po czerwonym teście;
- `scan_secrets` — sekrety w zapisanych plikach;
- `skill_hint` — podpowiedzi skilli;
- `context_guard` — ostrzeżenie o długim kontekście;
- `log_usage` — zapis zużycia;
- `update_notice` — informacja o nowym wydaniu.

Strażnicy blokują akcję także wtedy, gdy sam hook zawiedzie. Stan hooków: `python3 factory/hooks_status.py`.

## Dlaczego agent pyta o zgodę na polecenie?
Uprawnienia są celowo wąskie: agent bez pytania uruchamia tylko polecenia z listy `allow` w ustawieniach. Polecenie,
którego używasz często, dopisz do `allow` w `.claude/settings.local.json`. Zasady i tryby uprawnień opisuje skill
`core-agent-security`.

## Agent podał nieprawdziwy fakt — co robić?
Poproś o źródło. Zasada fabryki to fakt z pliku, polecenia albo źródła z datą, a czego nie sprawdzono — ze
znacznikiem [założenie]. Powtarzającą się pomyłkę zapisz w `docs/project/lessons.md`, żeby następne sesje jej
unikały.

## Jak odinstalować fabrykę?
Polecenia odinstalowania nie ma. Instalator zapisuje w `.claude/factory-manifest.json` listę wszystkich swoich
plików (`files`). Usuń:
- te pliki;
- blok między `<!-- team-factory:begin -->` a `<!-- team-factory:end -->` w `CLAUDE.local.md` albo `CLAUDE.md`;
- blok `# team-factory:begin` … `# team-factory:end` w `.git/info/exclude` albo `.gitignore`;
- wpisy fabryki w `.claude/settings.local.json` albo `.claude/settings.json`;
- sam manifest.

Kopie z aktualizacji leżą w `.claude/factory-backup/`.

## Gdzie czytać dalej?
- `.claude/catalog.md` — persony, role i skille tej instalacji.
- `factory/packs/<id>/GUIDE.md` — przewodniki trybów (np. `mode-talos`, `mode-team`).
- `factory/PUBLIC_API.md` — co jest publicznym API fabryki i jak są numerowane wersje.
- `factory/CHANGELOG.md` — co zmieniło się w kolejnych wersjach.
