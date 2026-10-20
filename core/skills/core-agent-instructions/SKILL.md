---
name: core-agent-instructions
description: Użyj przy pisaniu i przeglądzie CLAUDE.md lub AGENTS.md — test włączenia, karta kontroli, moduły.
metadata:
  przeglad: 2027-10-10
  katalog: "Użyj, gdy powstaje, puchnie, starzeje się albo nie działa plik instrukcji agenta w projekcie (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/) — test włączenia reguły, gdzie co trzymać (reguła, skill, hook, pamięć), szkic z inspekcji repo, karta pięciu kontroli ze skryptem, aktualizacja z historii gita, kalibracja reguły A/B, drabina plików w modułach z indeksem w root, AGENTS.md obok CLAUDE.md. Nie do pisania skilli (core-skill-authoring), lekcji i dziennika projektu (core-project-record) ani README i dokumentacji dla ludzi (skill dokumentacji, pack-docs)."
  slowa: "CLAUDE.md, AGENTS.md, CLAUDE.local.md, plik instrukcji agenta, reguły dla agenta, reguły AI, zasady dla agenta, cursor rules, .claude/rules, /init, CLAUDE.md za długi, CLAUDE.md puchnie, agent ignoruje reguły, agent łamie konwencję, porządki w CLAUDE.md, przegląd reguł, onboarding agenta, monorepo CLAUDE.md, CLAUDE.md w module, reguły per katalog, AGENTS.md i CLAUDE.md razem, Codex i Claude Code, Copilot, Cursor, kilka narzędzi AI, wspólne reguły agentów, reguły się rozjechały, czy reguła działa"
---

# Instrukcje dla agentów w projekcie (CLAUDE.md, AGENTS.md, reguły)

Plik instrukcji to wdrożenie agenta, który zna język i framework, ale nie zna Waszych lokalnych umów. Każda linia
kosztuje kontekst w każdej sesji i u każdego wykonawcy, a reguły z długiego pliku są przestrzegane słabiej.
Skill daje kryteria, co wpisać, gdzie to trzymać, jak plik przejrzeć i jak sprawdzić, że reguła działa.
Architektura plików w dużym repo (moduły, indeks, wiele repozytoriów): `references/skalowanie-kontekstu.md`.

## 1. Test włączenia (przed dopisaniem każdej linii)
„Czy agent wiedziałby to bez tego pliku — z danych treningowych, dokumentacji frameworka, README, konfiguracji
lintera albo z samego kodu?” Tak → nie dopisuj (najwyżej odnośnik). Nie → dopisz.
- **Należą:** nieoczywiste konwencje (kształt błędu API, nazewnictwo plików, dozwolone importy), pułapki projektu,
  obejścia wynikające z historii lub błędu zależności, polecenia build/test/lint, wskazanie pliku-wzorca
  (`src/users/user.service.ts` zamiast wklejonego przykładu).
- **Nie należą:** dokumentacja frameworka, treść README, zasady już wymuszone konfiguracją (`strict` w tsconfig),
  opis struktury katalogów i listy zależności (agent odczyta je z repo), intencje („pisz czysty kod”) — zamień na
  zachowanie sprawdzalne w diffie albo usuń.
- Reguła bez powtarzalnego błędu agenta nie trafia do pliku „na zapas”. Sygnały, że trzeba dopisać: ten sam błąd
  agenta drugi raz, ta sama poprawka wpisywana w kolejnej sesji, uwaga z przeglądu kodu, której agent nie mógł znać.

## 2. Gdzie co trzymać
| Treść | Miejsce |
|---|---|
| obowiązuje zawsze, w całym repo | główny `CLAUDE.md` / `AGENTS.md`, najważniejsze zakazy na górze |
| dotyczy części kodu | `CLAUDE.md` w katalogu tej części albo reguła `.claude/rules/*.md` z polem `paths` |
| procedura uruchamiana, gdy trzeba | skill (core-skill-authoring) |
| kontrola, której nie wolno pominąć (format, sekrety, blokada polecenia) | hook albo reguła uprawnień — CLAUDE.md to kontekst, nie wymuszenie |
| preferencja osobista | `CLAUDE.local.md` (w `.gitignore`) albo `~/.claude/CLAUDE.md` |
| pułapka z incydentu | `docs/project/lessons.md` (core-project-record); wraca drugi raz → propozycja do CLAUDE.md |
| referencje: PRD, plany, decyzje, mapy | `docs/project/` czytane w razie potrzeby, z odnośnikiem w CLAUDE.md |

Jedna reguła żyje w jednym miejscu. Kilka narzędzi AI w zespole: `AGENTS.md` jako źródło prawdy, a `CLAUDE.md`
z jedną linią `@AGENTS.md` (i ewentualnie regułami tylko dla Claude Code pod nią). Jak Claude Code ładuje te pliki
(podkatalogi na żądanie, importy, AGENTS.md bez CLAUDE.md): `references/skalowanie-kontekstu.md`, sekcja 4.

## 3. Procedura: pierwszy szkic
1. Wbudowane `/init` albo inspekcja: README, manifest i jego skrypty, konfiguracje lint/format/typów/testów,
   1–2 pliki CI, dwa poziomy drzewa, `git log --oneline -n 30` (konwencja commitów). Każde twierdzenie z pliku,
   polecenia lub commita (core-grounding); czego nie ustalisz, wpisz jako pytanie do człowieka, nie domysł.
2. Kolejność wg dźwigni: twarde zakazy → 3–6 poleceń (build, test, lint) → konwencje z plikiem-wzorcem →
   testy → commit i PR → bezpieczeństwo. Bez misji, wartości i przedstawiania zespołu.
3. Bez bloków kodu dłuższych niż 1–2 linie (odnośnik do pliku) i bez definicji pojęć ogólnych.
4. Budżet: plik poniżej ~200 niepustych linii (zalecenie Anthropic na plik CLAUDE.md); plik modułu zwykle 10–40 linii.
5. Uwagi dla ludzi w komentarzach HTML `<!-- … -->` — Claude Code usuwa je przed wstrzyknięciem do kontekstu.

## 4. Procedura: przegląd (karta pięciu kontroli)
Najpierw skrypt — **uruchom**, nie czytaj:
`python3 .claude/skills/core-agent-instructions/scripts/instructions_lint.py --root .` (albo ścieżka pliku; `--json`).
Liczy kontrole 1, 2, 3 i 5 oraz importy `@`, a w trybie `--root` także pliki modułów spoza indeksu i reguły
skopiowane z pliku głównego. Kod 1 = co najmniej jeden BŁĄD. Kontrolę 4 robisz sam.

| # | Kontrola | OK | UWAGA | BŁĄD |
|---|---|---|---|---|
| 1 | długość (niepuste linie bez komentarzy HTML) | ≤200 | 201–500 | >500 |
| 2 | bloki kodu/konfiguracji > 3 linii (poza diagramami) | 0 | 1–2 | ≥3 |
| 3 | sformułowania-intencje | 0 | 1–3 | ≥4 |
| 4 | wiedza zbędna: bez zaskoczenia dla agenta, domyślne zachowanie frameworka, definicja, brzmi jak poradnik, mogłaby być odnośnikiem | 0 | 1–3 | ≥4 |
| 5 | kolejność: krytyczne reguły w pierwszej trzeciej, bez wstępu na górze | tak | mieszana | krytyczne po linii 200 / brak nagłówków |

- Każde ustalenie z `plik:linia`. Dla każdej intencji propozycja sprawdzalna oparta na sygnale z projektu
  („dbaj o błędy” → „handlery zwracają `{ error: { code, message } }`, wzorzec `src/api/errors.ts`”); bez sygnału
  w repo → domyślna dla stacku z oznaczeniem [założenie].
- Sprzeczne reguły w dwóch plikach to błąd: model może wybrać dowolną z nich.
- Domyślnie tylko raport. Przestawienie sekcji lub cięcia — za zgodą człowieka, bez zmiany treści reguł.

Schemat wyniku:
```
Przegląd instrukcji — <ścieżka>   Ocena: <jedno zdanie>
| # | Kontrola | Werdykt | Liczba |      (pięć wierszy)
Ustalenia: <kontrola> — plik:linia — problem — propozycja
3 działania o największej dźwigni: 1. … 2. … 3. …
```

## 5. Procedura: aktualizacja istniejącego pliku
1. `git log -1 --format=%H -- CLAUDE.md` → ostatnia zmiana pliku (`OSTATNIO`).
2. `git diff OSTATNIO..HEAD --stat -- package.json pyproject.toml .github/ README.md <konfiguracje lint/testów>` —
   co się zmieniło od tamtej pory (szczególnie skrypty i polecenia).
3. Każdy plik i polecenie, na które CLAUDE.md się powołuje, sprawdź, że istnieje
   (`python3 .claude/skills/core-grounding/scripts/grounding_check.py CLAUDE.md`).
4. Klasyfikuj linie: ZOSTAW / POPRAW / USUŃ / BRAKUJE, każdą z `plik:linia` źródła.
5. Pokaż listę i edytuj punktowo za zgodą — nie przepisuj całości. Niezacommitowane zmiany człowieka w pliku = ZOSTAW.
6. Po większej zmianie modelu przejrzyj reguły-obejścia słabości starszego modelu: część stała się zbędna.

## 6. Kalibracja reguły (A/B) — czy reguła coś zmienia
1. To samo zadanie 3–5 razy w świeżej sesji z tego samego stanu repo, **bez reguły**. Zanotuj: złamania konwencji,
   czas, liczbę przeczytanych plików, iteracje, koszt (jeśli widoczny).
2. Dopisz regułę w 1–3 zdaniach we właściwym miejscu (sekcja 2).
3. Powtórz te same przebiegi. Agent trafiał bez reguły albo brak poprawy → usuń regułę.
4. Zmieniaj jedną rzecz naraz (treść, miejsce, kolejność). Zmiana CLAUDE.md fabryki lub projektu z personami to
   zmiana konfiguracji agenta — ewaluacja jak w core-delivery-lifecycle.

## Anty-wzorce
- Plik-encyklopedia: reguły ze środka długiego pliku giną (modele najsłabiej uwzględniają środek długiego kontekstu).
- Kopia dokumentacji lub README; opis architektury, który agent i tak odczyta z kodu.
- Ta sama reguła w trzech plikach; reguła w root i jej kopia w module.
- Pamięć lokalna (automatyczna pamięć, `CLAUDE.local.md`) jako jedyne miejsce ustaleń zespołu.
- Prośba słowami „przeczytaj AGENTS.md” zamiast importu `@AGENTS.md` — agent może pliku nie otworzyć.
- Import `@plik` jako sposób na oszczędność — importy ładują się przy starcie i liczą się do kontekstu.

## Przykład
Wejście: CLAUDE.md 340 linii; linie 1–40 „O projekcie i wartościach”; linia 287 „nigdy nie wysyłaj danych klienta
do logów”; blok 25 linii z tsconfig; „pisz czysty kod” w linii 52.
Wynik skryptu: długość UWAGA (340), bloki UWAGA (1), intencje UWAGA (1), kolejność BŁĄD (reguła krytyczna l. 287,
wstęp na górze). Kontrola 4 (ręcznie): 6 linii opisu katalogów, które widać w drzewie → UWAGA.
3 działania: (1) zakaz logowania danych klienta do pierwszej sekcji; (2) blok tsconfig → usuń (`strict` wymusza
konfiguracja), w zamian 1 linia o wyjątku, którego konfiguracja nie widać; (3) wstęp do 2 zdań, opis katalogów usuń,
„czysty kod” → „funkcje publiczne w `src/api/` mają typ zwracany i obsługują błąd przez `AppError`”.
Po zmianach: 190 linii, kalibracja A/B dla reguły o `AppError` (3 przebiegi bez i 3 z regułą).

## Checklista
- [ ] każda nowa linia przeszła test włączenia i odpowiada na powtarzalny błąd agenta
- [ ] krytyczne zakazy na górze; plik ≤ ~200 niepustych linii; zero wklejonych bloków konfiguracji
- [ ] intencje przepisane na zachowania sprawdzalne w diffie; jedna reguła w jednym miejscu, bez sprzeczności
- [ ] reguły części kodu w pliku modułu lub `.claude/rules/` z `paths`; procedury w skillach; wymuszenia w hookach
- [ ] `instructions_lint.py --root .` bez BŁĘDÓW; odwołania sprawdzone `grounding_check.py`
- [ ] nowa reguła przetestowana w świeżej sesji (A/B), zbędna usunięta

## Źródła
- Claude Code, „How Claude remembers your project” (code.claude.com/docs/en/memory, dostęp 2026-10-10): cel poniżej
  200 linii na plik, kolejność ładowania, podkatalogi na żądanie, importy `@` (do 4 poziomów, ładowane przy starcie),
  `.claude/rules/` z `paths`, AGENTS.md czytany, gdy brak CLAUDE.md, usuwanie komentarzy HTML, „kiedy dopisać”.
- Claude Code, „Set up Claude Code in a monorepo or large codebase” (code.claude.com/docs/en/large-codebases, dostęp
  2026-10-10): CLAUDE.md w katalogach, reguły per ścieżka, przegląd po większych wydaniach modeli.
- J. L. Lulla i in., „On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents”, arXiv:2601.20404
  (2026): mediana czasu −28,64%, tokeny wyjściowe −16,58% przy porównywalnej skuteczności (10 repo, 124 PR).
- T. Gloaguen i in., „Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?”,
  arXiv:2602.11988 (2026): pliki kontekstu nie podnoszą skuteczności, a koszt rośnie o ponad 20%; przeglądy repo
  nie pomagają; pomagają niestandardowe praktyki projektu (dostęp do streszczeń 2026-10-10).
- N. F. Liu i in., „Lost in the Middle: How Language Models Use Long Contexts”, arXiv:2307.03172 [niezweryfikowane
  w tej sesji — znana praca, cytowana za kursem].
- Kurs 10xDevs, ed. 3 (2026), moduł 1, lekcja 4 (wdrożenie agenta, AGENTS.md, reguły) i moduł 4, lekcja 1
  (skalowanie kontekstu) — materiał szkoleniowy (dostęp 2026-10-09).

Opisane własnymi słowami.
