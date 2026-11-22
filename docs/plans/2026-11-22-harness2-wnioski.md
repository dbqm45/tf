# Wnioski z Harness² dla fabryki

Data: 2026-11-22. Źródło: artykuł „Forget Harness Agent. Recursive Agent Harness² 10x Better” (Gao Dalie, Medium,
listopad 2026), omawiający projekt Harness² (Google Cloud AI Research i Northwestern University, październik 2026).
Prośba właściciela: zapisać trzy rzeczy warte wzięcia. Nic z tej notatki nie jest jeszcze zrobione.

## Co mówi artykuł (krótko)

- Harness = wszystko wokół modelu (pamięć, narzędzia, zabezpieczenia, skille, prompt systemowy). Zwykle poprawia go
  człowiek; Harness² oddaje tę poprawę modelowi.
- **Poziom zadania:** przebieg bazowy ze śladem → **sugestia** (poprawki ogólne: powtarzające się błędy narzędzi, słabe
  zarządzanie kontekstem; poprawki dziedzinowe) → **weryfikacja** (kandydat uruchomiony na tym samym zadaniu,
  porównanie z bazowym) → **synteza** (do harnessu tylko zmiany sprawdzone w działaniu).
- **Poziom harnessu:** „reflektor doświadczeń” zapisuje lekcje w `EXPERIENCE.md`; kolejne zadanie startuje z czystego
  harnessu, ale edytor uczy się, *kiedy* dana zmiana pomaga. Wagi modelu stałe.
- Wyniki (wg artykułu): WorkBuddy-Bench do +11,5 pkt (GLM-5: 64,2 → 75,7 po jednym kroku), JobBench do +4,5,
  LAB do +11,8; poprawki przenoszą się między benchmarkami. „10x” i „99%” z tytułu i grafiki nie mają pokrycia w tekście.
- Ograniczenia przyznane w artykule: każda runda to dodatkowy koszt (równoległość skraca czas, nie koszt), brak
  uniwersalnego budżetu, baza doświadczeń to prosty indeks (łączenie, wygaszanie, wyszukiwanie — przyszła praca),
  porównanie z bazowym przebiegiem nie gwarantuje poprawności.

## Co fabryka już ma (pętla poprawy z człowiekiem w środku)

| Harness² | Fabryka |
|---|---|
| ślad przebiegu | `.tf/runs/`, logi kosztów i delegacji, dowody `run_state.py verify` |
| sugestia poprawki | `core-agent-retro`: retrospektywa z dowodami z logów i gita, propozycje zmian fabryki |
| weryfikacja na tym samym zadaniu | `core-skill-authoring` (najpierw scenariusz odtwarzający problem), `skill_gate.py`, `tools/workspace.py flow-evals --baseline previous` |
| synteza sprawdzonych zmian | PR z bramkami i CI; zatwierdza człowiek |
| `EXPERIENCE.md` | `docs/project/lessons.md` (reguła z `Instead:`), `tf task close --lesson` |
| ochrona przed przeuczeniem | zbiór holdout w ewaluacjach skilli |

## Trzy rzeczy warte wzięcia

### 1. Weryfikacja różnicowa przy każdej zmianie skilla lub promptu (największa wartość)

Zmiana treści fabryki (skill, persona, prompt agenta, kroki pętli) przechodzi przez ponowne uruchomienie tych samych
scenariuszy i porównanie z poprzednim wynikiem — wynik **i** koszt. Narzędzie istnieje: `workspace.py flow-evals
--baseline previous` (workflow `.github/workflows/flow-evals.yml`), ale pełny przebieg w CI jest pomijany bez klucza
API i jest płatny.

Do ustalenia:
- kiedy przebieg różnicowy jest obowiązkowy (np. zmiana `tf-task/SKILL.md`, promptów agentów w `config.yaml`, kroków
  `steps`), a kiedy wystarczy bezpłatna bramka;
- budżet na przebieg i kto go uruchamia (zgoda człowieka, jak dziś przy `skill_gate.py --model`);
- jak raport różnicy trafia do opisu PR (wynik, koszt, które scenariusze się pogorszyły).

### 2. Lekcja jako wiedza „kiedy pomaga”, nie „zawsze rób X” (najmniejsza zmiana)

Dziś wpis w `lessons.md`: `- <data> **<reguła>** — Context: … · Instead: … · Applies to: plan|implementation|review|all`
(`core/skills/core-project-record/SKILL.md`). `Applies to` mówi *w której fazie*, ale nie *w jakich warunkach*.
Propozycja: opcjonalne pole `When:` (warunek, w którym reguła pomaga, np. „migracja z danymi > 1 mln wierszy”,
„zmiana publicznego API”), żeby lekcja nie zamieniała się w regułę stosowaną zawsze. Do tego zasada z artykułu:
przechowujemy wiedzę o tym, kiedy modyfikacja ma sens, a nie cały poprzedni sposób pracy.

Do ustalenia: czy `When:` jest wymagane, czy opcjonalne; jak `tf task close --lesson` i walidacja w
`core/factory/task_state.py` traktują nowe pole; czy lekcje bez trafienia przez dłuższy czas są wygaszane (to, co
artykuł zostawia na przyszłość).

### 3. Retrospektywa, która proponuje gotową poprawkę z testem

`core-agent-retro` zwraca dziś propozycje zmian fabryki. Propozycja: każda propozycja w gotowej postaci do bramki —
**problem** (z dowodem z logu lub przebiegu), **scenariusz odtwarzający** (wpis do `tests/skill_evals/<skill>.json`),
**proponowana zmiana** treści skilla. Człowiek akceptuje lub odrzuca, a fabryka przepuszcza zmianę przez
`skill_gate.py` i (punkt 1) przebieg różnicowy. To odpowiednik etapów sugestia → weryfikacja → synteza, z człowiekiem
w miejscu automatycznej syntezy.

## Czego świadomie nie bierzemy

- **Automatycznej przebudowy harnessu bez człowieka.** Hooki, reguły uprawnień i bezpieczeństwa to część harnessu,
  której model nie powinien sam „ulepszać”; decyzje o zmianie fabryki zostają u człowieka.
- **Rekurencji z wieloma kandydatami w codziennej pracy.** Koszt rośnie z każdą rundą, a fabryka zakłada najtańszy
  wystarczający model. Ewentualnie jako okresowy, płatny przebieg na zbiorze ewaluacji, za zgodą człowieka.
