# Plan cięć — kolejność pracy przed planem pierwszego kroku

Plan cięć (`docs/project/05-plan/plan.md`, szablon `plan` w core-project-record) odpowiada tylko na pytania: co
najpierw, co od czego zależy, co jest zablokowane i co odkładamy. Nie wybiera frameworków, nie projektuje schematu
i nie rozpisuje plików — to robi plan kroku w raporcie `06-delivery/`.

## Dwa rodzaje pozycji
- **S-NN — cięcie:** jedna zdolność widoczna dla użytkownika, przechodząca przez wszystkie potrzebne warstwy.
  Wynik zaczyna się od „użytkownik może …”. Jeśli tego zdania nie da się napisać, to nie jest cięcie pionowe.
- **F-NN — fundament:** najmniejsza praca wstępna bez własnego efektu dla użytkownika. Musi mieć pole
  **Odblokowuje**: konkretne S-NN, konkretną niewiadomą do rozstrzygnięcia albo ścieżkę weryfikacji, której
  wymaga S-NN. Fundament bez „Odblokowuje” to praca warstwowa — usuń go albo włącz do pierwszego cięcia, które
  go potrzebuje.
- **Granica fundamentu:** nie kończy całej warstwy („cały model danych”, „całe API”, „pełne uwierzytelnianie”).
  Po jego wykonaniu co najmniej jedno S-NN nadal integruje tę warstwę przez prawdziwą funkcję.
- **Element techniczny pojawia się w pierwszym cięciu, które go potrzebuje.** Fundament ma sens tylko wtedy, gdy
  bez niego pierwszego cięcia nie da się zaplanować, zabezpieczyć albo sprawdzić.
- Fundament nie dubluje warstwy, którą **inwentarz repozytorium** zgłasza jako obecną. Inwentarz: frontend,
  backend/API, dane, uwierzytelnianie, wdrożenie, obserwowalność — każda jako obecna / częściowa / brak,
  z plikiem jako dowodem (mapa kodu; pack-it: eng-codebase-mapping).
- Uzasadnione „najpierw poziomo” (integracja z systemem zastanym, wymóg regulacyjny dla modelu danych, rdzeń
  krytyczny wydajnościowo) to nadal F-NN: konkretny, ograniczony i przypięty do S-NN.

## Pola pozycji
| Pole | Zasada |
|---|---|
| Wynik | S: „użytkownik może …”, F: „(fundament) … jest gotowe” |
| Identyfikator zmiany | kebab-case, stabilny; nazwa gałęzi i raportu kroku (nie `S-01`) |
| Wymagania | dosłowne ID z wymagań (`FR-007`, `US-02`), bez parafrazy |
| Warunki wstępne | ID innych pozycji albo konkretny stan zewnętrzny |
| Równolegle z | pozycje bez ścieżki zależności między sobą (osobne worktree — core-git-workflow) |
| Blokery | tylko zewnętrzne (dostawca, decyzja interesariusza); co zespół rozstrzygnie sam, jest niewiadomą |
| Niewiadome | pytanie — właściciel — blokuje: tak/nie |
| Ryzyko | jedno zdanie: dlaczego pozycja stoi właśnie tu w kolejności |
| Status | proponowane / gotowe / zablokowane / w toku / zrobione |

- **Zablokowane** wtedy i tylko wtedy, gdy co najmniej jedna niewiadoma ma „blokuje: tak”.
- **Gotowe** tylko wtedy, gdy wszystkie warunki wstępne są zrobione (albo obecne w inwentarzu) i nie ma
  blokujących niewiadomych.

## Kolejność
1. Fundamenty w kolejności zależności, potem cięcia — nic nie zależy od pozycji późniejszej (porządek topologiczny).
2. **Gwiazda przewodnia** — najmniejszy przepływ end-to-end, który dowodzi tezy produktu — tak wcześnie, jak
   pozwalają zależności. Nie musi być pierwsza.
3. Remisy rozstrzyga **cel sekwencji** zapisany w planie:
   - szybkie wydanie → najpierw ścieżka „must”, reszta do odłożonych;
   - sygnał z rynku → najpierw najbardziej ryzykowne założenie;
   - jakość → fundamenty bezpieczeństwa i obserwowalności nie są odkładane;
   - nauka → najpierw nieznana technologia;
   - prostota → najpierw najmniejsze cięcie.
4. Otwarte pytanie, które wpływa na kolejność, zostawia dotknięte pozycje jako zablokowane — nie przesądzaj odpowiedzi.

## Rozmiar cięć (bez estymat)
Cięcia mają porównywalną wagę. Podziel cięcie, gdy:
- obejmuje więcej niż jedną główną akcję użytkownika;
- łączy konfigurację, główny przepływ i administrację;
- pokrywa większość wymagań „must”, a inne cięcia po jednym drobnym;
- ma więcej niż jedno niezależne ryzyko albo niewiadome różnych właścicieli.
Dziel po węższych wynikach (ścieżki procesu, persony, etapy), nigdy po warstwach. W planie cięć nie ma dni, punktów
ani rozmiarów — kolejność wynika z zależności. Koszt i termin dla sponsora: osobno, jako przedziały
(planowanie projektu; pack-it: proc-project-planning).

## Niewiadome — gdzie je rozstrzygnąć
| Rodzaj niewiadomej | Gdzie |
|---|---|
| lokalna, o kodzie („czy jest już komponent formularza?”) | plan kroku — sprawdza repo i decyduje |
| zewnętrzna, wpływa na decyzję techniczną (biblioteka, API dostawcy, algorytm) | badanie przed planem kroku (core-source-research; pack-it: eng-codebase-mapping) |
| podejrzane założenie, problem może być źle postawiony | przeramowanie przed planem kroku (pack-it: eng-debugging) |
| bez wpływu na bieżące cięcie | „Otwarte pytania” albo „Odłożone” |
Badanie ma sens, gdy blokuje decyzję — nie „na zapas”.

## Samokontrola przed zapisem
Nie zapisuj planu, jeśli któryś punkt nie przechodzi:
- [ ] każde wymaganie „must” i każda historyjka występuje w polu Wymagania co najmniej jednego cięcia;
- [ ] każde cięcie ma co najmniej jedno prawdziwe ID wymagania — nowa potrzeba z rozmowy trafia do „Otwartych
      pytań” albo „Odłożonych”, nie do planu;
- [ ] graf bez cykli, każde ID z warunków wstępnych istnieje, kolejność topologiczna;
- [ ] każdy F-NN ma „Odblokowuje”, nie kończy całej warstwy i nie dubluje warstwy obecnej w inwentarzu;
- [ ] statusy zgodne z niewiadomymi; tabela zgodna z opisem pozycji;
- [ ] co najmniej jedno cięcie „gotowe” — jeśli wszystko jest zablokowane albo jest pięć F i zero gotowych S,
      wymagania są niedomknięte albo inwentarz źle odczytany: wróć do fazy 3;
- [ ] pojęcia „gwiazda przewodnia” i „najbardziej ryzykowne założenie” objaśnione jednym zdaniem przy pierwszym
      użyciu (człowiek nie zna żargonu planu).

## Przekazanie
Na końcu **jedna** rekomendacja następnego kroku, nie lista do wyboru: gwiazda przewodnia, jeśli gotowa; inaczej
fundament, który ją odblokowuje; inaczej najważniejsza niewiadoma do rozstrzygnięcia; inaczej gotowe cięcie
z największą liczbą zależnych pozycji. Przed planem kroku warto przejrzeć plan (przegląd zmian; pack-it: qa-change-review, tryb A).

Źródło: kurs 10xDevs, ed. 3 (2026), moduł 2, lekcje 1–2 (roadmapa, niewiadome) — materiał szkoleniowy
(dostęp 2026-10-09); A. Cockburn — walking skeleton. Opisane własnymi słowami.
