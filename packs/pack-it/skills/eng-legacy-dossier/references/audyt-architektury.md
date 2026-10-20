# Audyt architektury — Inventory → Assessment → Recommendations

> **Spis treści:** 1. Zasada · 2. Etapy i wyniki · 3. Kryteria oceny · 4. Ustalenie (`ARCH-NNN`) · 5. Kategorie · 6. Rekomendacja (`REC-NNN`) i szczeble decyzji · 7. Priorytety i roadmapa · 8. Docelowe zasady · 9. Szablony plików · 10. Harmonogram orientacyjny · 11. Kiedy audyt jest skończony

## 1. Zasada
Nie zaczynasz od pytania „co przebudować?”, tylko „jak działa obecna architektura, jakie problemy rzeczywiście
powoduje i czy zmiana da mierzalną korzyść?”. Rozwiązanie niezgodne z popularnym wzorcem nie jest problemem, dopóki
nie wykażesz skutku (koszt zmian, błędy, blokada rozwoju) albo ryzyka.

## 2. Etapy i wyniki
| Etap | Działanie | Wynik (plik teczki) |
|---|---|---|
| 1. Zakres | aplikacje, biblioteki współdzielone i ich konsumenci, czy build/testy/CI, istniejące standardy zespołu | `assessment.md` § Zakres i metoda, § Kryteria oceny |
| 2. Inventory (as-is) | struktura, projekty, zależności, rozwiązania — bez ocen | `README.md` + `modules/*.md` |
| 3. Assessment | stan obecny vs oczekiwany, dowody, kategorie, mocne strony | `assessment.md` § Ustalenia, Mocne strony |
| 4. Recommendations | decyzja na najniższym skutecznym szczeblu, docelowe zasady | `recommendations.md` § Rekomendacje, Docelowe zasady |
| 5. Priorytety | P1–P3, wysiłek, ryzyko, kolejność, fazy | `recommendations.md` § Roadmapa, Kryteria sukcesu |

Ustalenia zapisujesz na bieżąco (z dowodem i pytaniem do weryfikacji), nie na końcu.

## 3. Kryteria oceny
Checklistę obszarów ustalasz w etapie 1 (dla Nx + Angular: `nx-angular.md` § 1). Każdy obszar oceniasz pytaniami:
- **Clarity** — czy strukturę da się zrozumieć bez długiej analizy kodu?
- **Consistency** — czy podobne problemy rozwiązano podobnie?
- **Coupling** — czy zmiana w jednym miejscu wymusza zmiany w innych?
- **Cohesion** — czy to, co należy do jednej odpowiedzialności, leży razem?
- **Testability** — czy istotną logikę można testować niezależnie od widoku?
- **Enforceability** — czy zasady wymusza narzędzie (lint, reguły zależności), czy tylko pamięć ludzi?
- **Maintainability** i **Complexity** — czy korzyść uzasadnia złożoność?

Sprzężenie mierzone dowodem w kodzie (stopień connascence) — ddd-connascence-analysis.

## 4. Ustalenie (`ARCH-NNN`)
```markdown
### ARCH-004 — Biblioteka współdzielona importuje implementację aplikacji
Obszar: granice bibliotek
Kategoria: potwierdzony problem
Stan obecny: libs/shared/ui importuje OrdersFacade z apps/shop
Stan oczekiwany: biblioteki współdzielone nie zależą od aplikacji
Luka: zmiana w aplikacji może zepsuć wszystkich konsumentów shared/ui
Dowód: libs/shared/ui/src/lib/order-badge.component.ts:3
Wpływ: sprzężenie; shared/ui nie da się użyć w drugiej aplikacji
```
- **Dowód** to `plik:linia` (kilka po przecinku). Wynik polecenia (np. graf zależności) zapisz w teczce
  (`evidence/graph.json`) i wskaż `evidence/graph.json:1` — `dossier_check.py` sprawdza istnienie pliku i linii.
- **Fakt vs interpretacja:** „jest import” to fakt (Dowód); „to szkodzi” to interpretacja (Wpływ) — musi wynikać
  z dowodu albo trafić do „Do dalszego zbadania”.

## 5. Kategorie
| Kategoria | Znaczenie | Dowód |
|---|---|---|
| potwierdzony problem | wykazany skutek, np. cykl blokujący niezależne zmiany | wymagany; wymaga rekomendacji |
| ryzyko | może się ujawnić, np. brak kontroli zależności | zalecany |
| niespójność | podobne rzeczy rozwiązane różnie | wymagany (oba miejsca) |
| możliwość poprawy | da się prościej, bez krytycznego problemu | zalecany |
| preferencja | inny styl, bez wykazanego skutku | — ; nie uzasadnia refaktoryzacji strukturalnej |

## 6. Rekomendacja (`REC-NNN`) i szczeble decyzji
```markdown
### REC-002 — Egzekwować kierunek zależności regułą Nx
Dotyczy: ARCH-004, ARCH-007
Decyzja: konfiguracja
Priorytet: P1
Wysiłek: 0,5 dnia
Ryzyko: lint zablokuje istniejące importy — najpierw lista wyjątków
Weryfikacja: przykładowy niedozwolony import jest zgłaszany przez lint, dozwolone przechodzą
```
Szczeble (wybierz najniższy, który rozwiązuje rzeczywisty problem): **bez zmian** (z powodem) → **dokumentacja** →
**konfiguracja** (lint, reguły, tagi) → **refaktoryzacja przyrostowa** → **refaktoryzacja strukturalna** (zmiana
podziału odpowiedzialności) → **przeprojektowanie**. Rekomendacja opisuje też obecne rozwiązanie, problem,
uzasadnienie i oczekiwaną korzyść — w treści pod polami.

## 7. Priorytety i roadmapa
| Priorytet | Kryterium | Działanie |
|---|---|---|
| P1 | istotny wpływ na stabilność, bezpieczeństwo zmian lub rozwój | zaplanować niezwłocznie |
| P2 | podnosi koszt utrzymania lub ryzyko kolejnych zmian | najbliższe iteracje |
| P3 | czytelność lub spójność bez pilnej potrzeby | przy okazji prac |

Poza wpływem uwzględnij wysiłek, ryzyko regresji, zasięg (ile projektów), zależności między zadaniami i możliwość
wdrażania etapami. Fazy roadmapy (przykład, kolejność wynika z ustaleń): **A. Fundamenty** (granice, reguły
zależności, cykle, lint) → **B. Najważniejsze problemy** → **C. Ujednolicenie** (wzorce, dokumentacja standardów,
testy) → **D. Dalsze usprawnienia**. Każde zadanie: zakres, priorytet, wysiłek, zależności, ryzyka, warunek
ukończenia — gotowe do przeniesienia do systemu zadań. Plan wykonania refaktoryzacji: eng-refactor-planning;
wykonanie z zamrożonym zachowaniem: eng-behavior-preserving-refactoring.

## 8. Docelowe zasady
Tylko tyle standardu, ile pomaga tej aplikacji. Rozdziel: **obowiązkowe** (wymuszane narzędziem, gdy się da),
**zalecane** (wyjątki z uzasadnieniem), **zależne od kontekstu** (decyzja w danym przypadku). Typowe obszary:
podział na biblioteki, nazwy i lokalizacje, tagi, dozwolone kierunki zależności, public API, organizacja feature'ów
i UI, dostęp do API, zarządzanie stanem, wymagania testów, dokumentowanie wyjątków. Decyzje o zasadach — ADR
(docs-tech-writing).

## 9. Szablony plików
`assessment.md`:
```markdown
<!-- legacy-dossier:assessment -->
# Architecture Assessment — <system>
## Podsumowanie
## Zakres i metoda
## Kryteria oceny
## Ustalenia
### ARCH-001 — …
## Mocne strony
## Do dalszego zbadania
```
`recommendations.md`:
```markdown
<!-- legacy-dossier:recommendations -->
# Architecture Recommendations & Roadmap — <system>
## Docelowe zasady
## Rekomendacje
### REC-001 — …
## Roadmapa
## Kryteria sukcesu
```

## 10. Harmonogram orientacyjny
Jedna aplikacja z istotnymi bibliotekami — punkt wyjścia ok. 6–9 dni pracy człowieka (założenie z planu audytu,
nie pomiar): zakres i workspace → biblioteki i zależności → Angular, routing, stan, API, testy → ocena → rekomendacje
→ priorytety → konsultacje. Z agentem etapy 1–2 są szybsze (narzędzia + skrypt), ale ocena i konsultacje z zespołem
nie. Duże repo: warstwami lub domenami — najpierw struktura i przepływy, w głąb tam, gdzie są pytania.

## 11. Kiedy audyt jest skończony
- znasz strukturę aplikacji i kluczowych bibliotek, umiesz wyjaśnić najważniejsze zależności i przepływy danych;
- najważniejsze ustalenia mają dowody, a mocne strony są opisane;
- każda istotna rekomendacja ma uzasadnienie, priorytet i sposób weryfikacji;
- `dossier_check.py` → `legacy-dossier-check: OK`; zespół zna wyniki i może z nich planować pracę.
