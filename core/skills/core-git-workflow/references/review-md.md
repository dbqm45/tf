# Szablon `REVIEW.md`

`REVIEW.md` leży w katalogu głównym repozytorium i dostosowuje przegląd PR wykonywany przez Claude (usługa Code Review
w Claude Code). Zasady wpisujesz wprost do pliku. Poniżej szablon do skopiowania i dopasowania — przebiegi i wagi
według „The AI-Native SDLC Playbook” (Anthropic, 2026).

```markdown
# Zasady przeglądu PR

## Zakres
Przeglądaj zmiany w `src/` i `infra/`. Pomijaj: kod generowany (`**/generated/**`, `*.lock`), zmiany samego
formatowania i wszystko, co sprawdza CI (lint, typy, pokrycie).

## Przebiegi
1. **Błędy i logika** — warunki brzegowe, obsługa błędów, współbieżność, zgodność z testami.
2. **Bezpieczeństwo** — autoryzacja w każdej akcji i endpointcie, walidacja wejścia, sekrety, zależności,
   dane osobowe (minimalizacja, logi).
3. **Zgodność** — z wymaganiami i planem kroku (`docs/project/03-requirements/`, `docs/project/06-delivery/`),
   z ADR (`docs/project/04-architecture/adr/`) i zasadami z `CLAUDE.md`.

## Waga ustaleń
- **Krytyczne** — blokuje scalenie (błąd danych, luka bezpieczeństwa, złamanie kontraktu API).
- **Ważne** — do poprawy w tym PR.
- **Drobne** — najwyżej 3 na PR; resztę pomiń.
Przy każdym ustaleniu: plik i linia, co jest nie tak, dlaczego, propozycja poprawki.
Przy każdym ustaleniu także **trudność decyzji (wpływ)**: niska (oczywista poprawka) / średnia (kompromis — podaj
koszt i czego nie sprawdziłeś) / wysoka (skutki architektoniczne). Najwyżej 10 ustaleń; podobne łącz w jedno.
Nie oceniasz zgodności z tym, czego plan nie obiecał; to, co plan wyłączył („Poza zakresem”), nie jest rozrostem zakresu.

## Czego nie robisz
Nie zatwierdzasz PR i nie oceniasz stylu, który pilnuje formatter. Pytania o wymagania kierujesz do autora.
```

Przegląd w GitHub Actions z werdyktem jako bramką: `przeglad-ai-w-ci.md`. Triaż ustaleń z macierzą waga × wpływ:
qa-change-review.

Po miesiącu: przejrzyj ustalenia (trafne / nietrafne), popraw zakres i przykłady w pliku, a zmianę `REVIEW.md` przejdź
tak jak zmianę kodu — przez PR.
