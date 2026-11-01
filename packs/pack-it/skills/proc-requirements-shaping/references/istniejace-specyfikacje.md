# Repo z istniejącymi specyfikacjami (Spec Kit, OpenSpec) i delta zmiany

Spis treści: 1. Najpierw rozpoznaj · 2. Spec Kit · 3. OpenSpec · 4. Delta zmiany i scalenie do bieżącego stanu

## 1. Najpierw rozpoznaj
Zanim zaczniesz sesję, sprawdź, czy repo ma już wymagania w narzędziu SDD. Jeśli tak, **czytasz je jako istniejące
wymagania, zasady i plan** i dopisujesz deltę we wskazanym miejscu. Równoległego dokumentu nie piszesz: dwa źródła
prawdy szybko się rozjeżdżają. Konwencji narzędzia nie zmieniasz bez decyzji człowieka.

## 2. Spec Kit (github/spec-kit)
| Plik | Czym jest dla tej procedury |
|---|---|
| `.specify/memory/constitution.md` | zasady projektu, czytane obok CLAUDE.md (nie kopiujesz ich do wymagań) |
| `specs/<NNN-funkcja>/spec.md` (np. `specs/003-user-auth`) | wymagania funkcji. Lint EARS i wyzwanie FR robisz jako raport, bez przepisywania pliku |
| znaczniki `[NEEDS CLARIFICATION: …]` w `spec.md` | otwarte pytania do człowieka (faza „Wyzwanie”) |
| `specs/<NNN-funkcja>/plan.md` | plan z sekcją zgodności z constitution |
| `specs/<NNN-funkcja>/tasks.md`, zadania `T001 [P] …` | `[P]` = można równolegle (różne pliki, bez zależności): kolumna „Równolegle z” w planie cięć |

Polecenia (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks` i inne) i rozszerzenia (`.specify/extensions.yml`)
zmieniają się między wersjami, więc przed użyciem sprawdzasz wersję w repo projektu.

## 3. OpenSpec (Fission-AI/OpenSpec)
- `openspec/specs/<obszar>/spec.md` — **bieżący stan** systemu: `### Requirement: <nazwa>` ze scenariuszami
  `#### Scenario: <nazwa>`.
- `openspec/changes/<nazwa-zmiany>/` — propozycja, zadania i **delta specyfikacji**: sekcje `## ADDED Requirements`,
  `## MODIFIED Requirements`, `## REMOVED Requirements` (i zmiany nazw).
- **Archiwizacja** scala deltę z `openspec/specs/`, a folder zmiany przenosi do `openspec/changes/archive/` z datą.
  Wymagania czytasz z `openspec/specs/`, a deltę bieżącej zmiany dopisujesz w jej folderze.

## 4. Delta zmiany i scalenie do bieżącego stanu (także bez narzędzia SDD)
Dokument zmiany opisuje różnicę, a jeden główny dokument opisuje, jak system działa dziś. Bez scalania po 30 zmianach
nikt nie wie, co obowiązuje.
- Zmiana zapisuje wymagania jako **deltę**: dodane, zmienione (pełna nowa treść, nie tylko różnica) i usunięte
  (z powodem). Wymagania mają stabilne nazwy lub klucze, bo scalanie dopasowuje po nazwie.
- **Zamknięcie zmiany = scalenie** delty do głównego dokumentu wymagań. Dokument zmiany zostaje jako historia (po co
  i kto zdecydował), a nie jako źródło bieżącego stanu.
- **Kontrola po scaleniu:**
  - wymaganie dodane lub zmienione w delcie bez odpowiednika w głównym dokumencie to ustalenie;
  - wymaganie usunięte, które nadal jest w głównym dokumencie, to ustalenie;
  - zmienione wymaganie, które zgubiło scenariusz lub kryterium akceptacji bez wpisu w „usunięte”, to ustalenie.
- Zmiana w istniejącym systemie: gwarancje zatwierdzone jako chronione zachowania wchodzą do delty jako dodane
  (pierwszy zapis wymagania) razem z testem (eng-behavior-preserving-refactoring).

Źródła (sprawdzone 2026-11-01 w repozytoriach): github.com/github/spec-kit (1.2.5, 2026-10-28; `templates/`,
`templates/commands/specify.md`, `tasks-template.md`); github.com/Fission-AI/OpenSpec (1.16.0, commit 2026-10-30;
`docs/overview.md`, `docs/writing-specs.md`, `docs/agent-contract.md`). Artykuły: Chimin, „OpenSpec + Superpower”
(2026-05-30); P. Qian, „From OpenSpec to AIDLC” (2026-09-04).
