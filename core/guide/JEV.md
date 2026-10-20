# Jev (TypeSafe) w fabryce

Jev to **model decyzyjny** („System One”). Nie pisze tekstu ani kodu. Dla stanu (tekst albo JSON) i pytań zwraca
prawdopodobieństwa i pewność. Typy pytań:
- **noul** — tak/nie;
- **choice** — wybór spośród do 255 opcji;
- **score** — skala 2–10 poziomów.

Parametry:
- czas: ~0,1–0,5 s;
- cena: $0,042 za 1 mln tokenów wejścia, wyjście bezpłatne;
- okno: 64 tys. tokenów.

W fabryce Jev **nie zastępuje** Claude. Robi szybkie, tanie i powtarzalne rozstrzygnięcia, a przy niepewności
przekazuje sprawę zwykłemu modelowi albo człowiekowi.

## Gdzie fabryka go używa

Każde zastosowanie jest opcjonalne i ma rezerwę: bez klucza, przy błędzie sieci albo niepewnej odpowiedzi działa tak
jak bez Jev.

| Zastosowanie | Wzorzec z dokumentacji TypeSafe | Włączenie | Co poprawia |
|---|---|---|---|
| Podpowiedź skilli | cookbook „Skill suggestion” | `CLAUDE_SKILL_HINT_JEV=1` | mniej błędnych i zbędnych wczytań skilli |
| Weryfikacja odwołań `plik:linia` w dokumentach | cookbook „Double-checking citations” | `grounding_check.py --jev` | wykrywa odwołania, które nie potwierdzają zdania (halucynacje) |
| Osłona treści z sieci | cookbook „Guardrails for LLMs” | `CLAUDE_JEV_GUARD=1` | ostrzega przed poleceniami ukrytymi w stronach (ClickFix, prompt injection) |
| Kontrola raportów wykonawców | cookbook „SDE cascade” (sprawdź → popraw) | `CLAUDE_JEV_REPORT_CHECK=1` | wykonawca nie odda raportu „działa” bez dowodu ani „gotowe” z otwartymi punktami |
| Ocena treści w ewaluacjach | „Confidence-gated routing” | `run_skill_evals.py --judge jev` | tańsza ocena; niepewne przypadki ocenia haiku |
| Sugestia tieru modelu | „Composite scoring” | `jev_client.py --tier "<opis>"` | spójna ocena trudności zadania (rubryka core-cost-control) |

Szczegóły działania:
- **Podpowiedź skilli.** Etap 1 to wybór spośród wszystkich skilli oraz 3 pytania bramki (praca projektowa?
  procedura specjalistyczna? wystarczy krótka odpowiedź?). Etap 2 to wybór spośród 3 najlepszych z pełnym opisem
  i początkiem SKILL.md oraz pytanie „czy pasuje” dla każdego. Progi wynoszą 0,30 jak w cookbooku. W cookbooku
  (182 skille, agent na Haiku 4.5) błędnych wczytań było 2,3 raza mniej.
- **Weryfikacja odwołań.** Werdykt brzmi „potwierdza”, „przeczy” albo „nic nie mówi”. Pewność ≥0,8 daje werdykt
  automatyczny, niższa oznacza przejrzenie przez człowieka.
- **Osłona treści z sieci.** Progi „strict”: od 0,35 uwaga, od 0,70 ostrzeżenie.
- **Kontrola raportów.** Jedna prośba o poprawę; potem hook nie blokuje (bez pętli).
- **Sugestia tieru.** 5 pytań noul, a decyzję składa kod. „NIEPEWNE” oznacza, że rozstrzyga model.

## Konfiguracja

Zmienne środowiskowe (te same nazwy co w oficjalnym SDK). Klucza **nigdy** nie zapisuj w plikach repozytorium.

```bash
export TYPESAFE_API_KEY=...                    # z console.typesafe.ai
# opcjonalnie: TYPESAFE_BASE_URL (domyślnie https://api.typesafe.ai), TYPESAFE_DEFAULT_MODEL (domyślnie jev-latest)
python3 .claude/hooks/jev_client.py --check    # jedno tanie zapytanie: czy klucz i usługa działają
```

## Najpierw pomiar, potem włączenie

Dokumentacja TypeSafe podaje, że angielski działa najlepiej, a inne języki słabiej. Fabryka zadaje pytania po
angielsku, ale stan (polecenia, dokumenty) jest po polsku. Dlatego przed włączeniem zmierz Jev na danych fabryki:

```bash
python3 factory/jev_calibration.py --routing                                   # słowa vs Jev
python3 factory/jev_calibration.py --judge docs/evals/2026-10-02-sonnet.jsonl  # zgodność ocen
```

Podpowiedź skilli zmierzysz na wszystkich ~270 scenariuszach za ułamek centa. Włącz:
- `CLAUDE_SKILL_HINT_JEV=1`, gdy Jev ma mniej błędnych i zbędnych podpowiedzi niż słowa przy podobnej liczbie
  trafnych;
- `--judge jev`, gdy zgodność pewnych ocen wynosi ≥95%.

Strażników (`CLAUDE_JEV_GUARD`, `CLAUDE_JEV_REPORT_CHECK`) włącz na kilka dni i przejrzyj ich ostrzeżenia:
- czy blokady raportów były zasadne;
- czy ostrzeżenia o stronach dotyczyły podejrzanej treści.

Zużycie Jev trafia do `.claude/logs/jev.jsonl` (bez treści zapytań).

## Ograniczenia

Według dokumentacji „model jaggedness” dla jev-1.13 Jev:
- czyta instrukcje dosłownie;
- nie liczy niezawodnie;
- źle porównuje daty;
- traci dokładność przy dużym stanie z nieistotną treścią;
- nie traktuje stanu jako wrogiego (polecenia w treści mogą wpłynąć na wynik).

Fabryka:
- zadaje jedno pytanie o jeden warunek, a wysoka wartość zawsze oznacza „tak”;
- wysyła tylko pola potrzebne do decyzji;
- liczy w kodzie;
- strażników traktuje jako dodatkową warstwę, a nie jedyną ochronę.

Prywatność:
- stan trafia do usługi TypeSafe;
- klient wycina znane wzorce sekretów, ale nie wysyłaj nim danych, których nie wolno przekazać poza firmę;
- zerowa retencja danych jest dostępna dla klientów enterprise.

Dostępność: usługa wystartowała 15.09.2026, a rejestracja w konsoli bywa wstrzymywana. Limity: 100 tys. tokenów
i 80 zapytań na sekundę („mogą się zmienić bez uprzedzenia”).

**Uwaga na podróbki.** Domena jevtypesafeai.com i jej „skill” nie należą do TypeSafe. Oficjalny skill dla agentów
(potrzebny, gdy **Twój projekt** ma korzystać z Jev w kodzie aplikacji) instalujesz poleceniami:
`claude plugin marketplace add typesafe-ai/skills`, potem `claude plugin install typesafe@typesafe-ai`.

## Źródła (dostęp 2026-10-03)
- docs.typesafe.ai: `introduction`, `models`, `api`, `confidence`, `concepts/state`, `introduction/coding-agents`,
  `model-jaggedness/jev-1.13`, `primitives/noul`, `patterns/confidence-routing`, `agent-skill`,
  `sdk/python/api/constants`.
- Cookbooki TypeSafe: `skill_suggestion`, `citation_check`, `llm_guardrails`, `sde_cascade`,
  `consistency_noul_cookbook`, `parallel_questions`.

Opisane własnymi słowami.
