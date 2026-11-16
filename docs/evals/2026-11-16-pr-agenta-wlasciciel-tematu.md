# PR agenta: jeden właściciel tematu (core-git-workflow) — 2026-11-16

Pliki: `2026-11-16-pr-agenta-holdout.{md,jsonl}` (holdout, 2 powtórzenia), `2026-11-16-pr-agenta-strojenie.{md,jsonl}`
(nowe scenariusze strojenia). Workspace `--packs pack-it`, `--isolated`, haiku i sonnet, ze skillami i bez
(`--baseline`). Koszt: 2,71 + 0,60 = 3,31 USD.

## Diagnoza przed zmianą
W holdoucie `core-agent-security` wynik ze skillem był niższy niż bez skilli (59% wobec 73% treści, pomiary
2026-10-30, 2026-11-01, 2026-11-02). Cała strata pochodziła z jednego scenariusza, `ho-pr-agenta-sciezki-chronione`
(auto-merge PR agenta, który zmienia `.github/workflows` i płatności):
- `core-agent-security` nie wczytał się w żadnym z 11 przebiegów; model wczytywał `core-git-workflow`
  i `core-async-delegation`, bo to ich opisy mówią o PR, ochronie gałęzi i CODEOWNERS;
- wiedza o PR agenta była w dwóch skillach: sekcja 5 `core-agent-security` (oznaczenie PR, ścieżki chronione)
  i `core-git-workflow` (chronione testy akceptacyjne) — bez oznaczenia PR agenta w tym drugim;
- treść ze skillami 2/11, bez skilli 6/11; najczęściej brakowało oznaczenia PR agenta;
- sprawdzenie „agent nie może zmienić testów akceptacyjnych” nie przyjmowało poprawnego sformułowania
  „osobny PR i check w CI odrzuca” (co najmniej jedna z czterech porażek tej grupy).

## Zmiana
- „PR napisany przez agenta” (oznaczenie, ścieżki chronione, auto-merge, zakres, testy akceptacyjne, IaC, atestacja)
  przeniesione do `core-git-workflow`; w `core-agent-security` sekcja 5 odsyła tam i zostawia uprawnienia agenta w CI.
- Opis, `katalog` i `slowa` obu skilli z granicą tematu; nowy scenariusz strojenia `pr-agenta-oznaczenie-i-infra`
  (`core-git-workflow`) i scenariusz granicy `pr-agenta-to-git-workflow` (`core-agent-security`, `no-trigger`).
- Scenariusz holdout przeniesiony do `holdout/core-git-workflow.json` (właściciel tematu); grupa testów akceptacyjnych
  przyjmuje też „osobny PR” i „CI odrzuca”. To poprawka oceniającego, a jej autor czytał wcześniejsze odpowiedzi
  z tego scenariusza — wynik tego scenariusza traktować ostrożnie; świeże `h2-*` nie były czytane przed pomiarem.

## Wynik (treść z poprawnymi sprawdzeniami / przebiegi)
| Skill | Scenariusz | Ze skillami | Bez skilli | Właściwy skill wczytany |
|---|---|---|---|---|
| core-git-workflow | `ho-pr-agenta-sciezki-chronione` | 4/4 | 3/4 | 4/4 (przed zmianą 0/11) |
| core-agent-security | `ho-serwer-narzedzi-zewnetrzny` | 4/4 | 4/4 | 4/4 |
| core-agent-security | `h2-issue-curl` | 4/4 | 4/4 | 4/4 |
| core-agent-security | `h2-mcp-token` | 4/4 | 4/4 | 4/4 |
| core-git-workflow | `pr-agenta-oznaczenie-i-infra` (strojenie) | 2/2 | 2/2 | 2/2 |
| core-agent-security | `pr-agenta-to-git-workflow` (granica) | nie wczytany 2/2 | — | wybrany `core-git-workflow` |

## Wnioski
- **Wybór skilla naprawiony:** pytanie o PR agenta trafia do skilla, który ma odpowiedź, a granica działa w obie
  strony. Ujemny wynik `core-agent-security` znika.
- **Holdout nie pokazuje wkładu treści `core-agent-security`:** po zmianie 12/12 ze skillem i 12/12 bez skilli,
  także na świeżych `h2-*`. Modele same odmawiają uruchomienia polecenia z issue i ograniczają token MCP. Wartość
  skilla, jeśli jest, leży w regułach fabryki (hooki, `autonomy.operations`, `skill_audit.py`), których te pytania
  nie sprawdzają. Do decyzji: scenariusz holdout na te reguły albo odchudzenie skilla do części specyficznej dla
  fabryki (test „no-op”).
- Mała próba: 2 powtórzenia na model; różnica jednego przebiegu to szum.
