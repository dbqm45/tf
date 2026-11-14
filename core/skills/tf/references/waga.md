# Waga zadania w pętli /tf

Czytasz, gdy `run_report.py start` albo etap `plan` drukuje linię o wadze innej niż zwykła, gdy skrypt odmawia etapu
z powodu wagi albo gdy człowiek chce ją zmienić. Wagę dobiera skrypt, nie Ty i nie człowiek: z treści zgłoszenia
przy starcie i ze ścieżek planu przy etapie `plan`. Człowiekowi mówisz jednym zdaniem, co wybrano i dlaczego
(„Zmiana dotyczy haseł, więc przed kodem pokażę Ci plan”).

| Waga | Kiedy | Co się zmienia w przebiegu |
|---|---|---|
| lekka | literówka, nazwa, komentarz, dokumentacja; bez kryteriów akceptacji; jeden kawałek, najwyżej 2 pliki | bez `spec.md` (więc bez flagi i śladu kryteriów); jeden kawałek; test, dowód `verify`, skan i przegląd zakresu zostają |
| zwykła | wszystko inne | pełny przebieg ze SKILL.md |
| pełna | logowanie, hasła, uprawnienia, płatności, migracje bazy, dane osobowe, sekrety, wdrożenie — w treści zgłoszenia albo w ścieżkach planu | jak zwykła, a do tego dwa punkty niżej |

## Waga pełna
1. **Plan zatwierdza człowiek przed kodem.** Po zapisaniu planu: `run_state.py stage <katalog> needs --needs plan`,
   pokazujesz plan i czekasz. Po zgodzie człowieka zapisujesz ją: `python3 .tf/factory/tf.py task approve <KEY>
   plan.md --by human:<id>` (identyfikator człowieka, który się zgodził) — dopiero wtedy `step` wpuści pętlę kawałka.
   **Z `--auto` nie ma kogo zapytać:** kończysz blokiem STOP („zadanie o wadze pełnej — plan czeka na Twoją zgodę”),
   z planem w raporcie. Zgody nie zapisujesz sam.
2. **Przegląd `security-reviewer` jest obowiązkowy** przed PR (faza warunkowa bez warunku), a `architect` — gdy plan
   zawiera decyzję trudną do odwrócenia (migracja danych, zmiana kontraktu).

## Zmiana wagi
- Podgląd z powodem: `run_state.py weight <katalog>`.
- **Podnieść** może każdy, także Ty, gdy widzisz ryzyko, którego skrypt nie złapał:
  `run_state.py weight <katalog> --set pelna`.
- **Obniżyć** może tylko człowiek, z powodem: `python3 .tf/factory/tf.py task weight <KEY> --set zwykla --by human:<id>
  --reason "<dlaczego>"`. Gdy uważasz, że waga jest za wysoka, mówisz to człowiekowi i podajesz mu to polecenie —
  sam go nie uruchamiasz. Po decyzji człowieka skrypt wagi już nie zmienia.
- Waga lekka, a plan wyszedł na więcej niż jeden kawałek → podnosisz ją do zwykłej i zakładasz specyfikację.
- Przebieg cięcia pdi nie ma wagi.
