# F4 (część B, v2): ponowny pomiar po tabeli stacku i liście modułów — 2026-10-24

Decyzja człowieka (2026-10-24): ponowić pomiar po zmianie z PR #64, która wymusza w `recon_check.py --final` tabelę
stacku i wpis każdego modułu z kart. Pierwszy pomiar: `2026-10-24-f4-benchmark-maister.md`. Dane:
`docs/evals/2026-10-24-f4b/v2/`.

## Warunki
- Nasz skill uruchomiony ponownie: te same repozytoria i commity, ten sam skrypt, model, limit i lista poleceń co
  w v1. Workspace pack-it złożony z main po PR #64.
- Dokumenty maistera są te same co w v1, bo narzędzie się nie zmieniło. Oceniający ocenili je ponownie, więc różnica
  między dwiema ocenami tych samych dokumentów mierzy rozrzut oceniających.
- Ocena ślepa jak w v1: ten sam prompt, nowe losowanie A/B (klucz w `v2/verdicts/klucz-AB.json`), nazwy narzędzi
  usunięte. Oceniający dostali pliki `.md` bez kart modułów `modules/*.json`, tak jak w v1.

## Wyniki
| | Nasz v1 | Nasz v2 | maister (ocena v1) | maister (ocena v2) |
|---|---|---|---|---|
| Koszt | 4,07 USD | 4,34 USD | 6,01 USD | — |
| Czas | 18,3 min | 18,8 min | 26,0 min | — |
| Pokrycie ważone (z 60) | 51 (85%) | **51,5 (86%)** | 48 (80%) | 47 (78%) |
| Stack (z 12) | 9 | **11** | 12 | 12 |
| Moduły (z 12) | 9,5 | **10** | 12 | 12 |
| Reguły (z 15) | 14 | 13 | 5,5 | 5 |
| Standardy (z 15) | 13 | 12 | 14 | 13,5 |
| Inne (z 6) | 5,5 | 5,5 | 4,5 | 4,5 |
| Poprawność (prawda / ocenione) | 27/28 (96%) | **29/30 (97%)** | 26/29 (90%) | 24/29 (83%) |

- **Według repozytoriów** (nasz v2, w nawiasie v1):
  - go-clean-arch 16 (17,5);
  - spring-petclinic 16,5 (16,5);
  - eShopOnWeb 19 (17).
- **Koszt według repozytoriów:**
  - go-clean-arch 0,97 USD;
  - spring-petclinic 1,40 USD;
  - eShopOnWeb 1,97 USD (v1: 1,34; najdłuższy przebieg, 9 min).
- **`recon_check --final`:** wszystkie trzy raporty przechodzą. Dowody: 55, 71 i 87; złych dowodów 0; twierdzeń bez
  dowodu 0.
- **Rozrzut oceniających:** te same dokumenty maistera dostały 48 i 47 punktów, a poprawność 26/29 i 24/29. Różnice
  rzędu 1–1,5 punktu mieszczą się w szumie.

## Co dała zmiana
1. **Stack: z 9 do 11 na 12.** Wszystkie raporty mają tabelę z wersjami, profilami, CI i testami. Rozjazd Go w CI
   kontra go.mod jest podany. Jedyny utracony punkt to **błąd**: raport petclinic twierdzi „brak CI w repo”, a w
   `.github/workflows/` są 3 pliki. Wiersz miał oznaczenie [niezweryfikowane], więc `--final` go przepuścił. W dwóch
   pozostałych repozytoriach CI jest opisane poprawnie, więc to pomyłka modelu, a nie spisu plików.
2. **Moduły: z 9,5 do 10 na 12.** Lista jest pełna, ale opisy są ogólne. Oceniający obniżają ocenę za brak nazw klas,
   tras i relacji (np. ArticleHandler i `/articles`, `isNew()`, `@ManyToMany`). Te szczegóły **są** w kartach
   `modules/*.json`, czego oceniający nie widzą. Raport w Markdownie nie przenosi więc wiedzy z kart.
3. **Reguły i standardy:** −1 punkt każde, w granicach rozrzutu oceniających. Przewaga w regułach zostaje (13 wobec 5).

## Kryterium sukcesu z planu (po v2)
| Kryterium | Wynik | Spełnione? |
|---|---|---|
| Pokrycie ≥ maister | 86% wobec 78–80% | tak |
| Koszt ≤ 50% maistera | 72% (4,34 / 6,01) | **nie** |
| Precyzja dowodów ≥ 95% | 97% twierdzeń prawdziwych w próbie | tak |

## Dalsze kroki
1. **Moduły:** w sekcji Moduły raportu przy każdym module podawać 2–4 kluczowe elementy z karty (klasa wejściowa,
   trasy, encje i relacje). Można też generować `modules/<moduł>.md` z kart skryptem, bez modelu.
2. **CI:** `recon_check --final` powinien ostrzegać, gdy wiersz CI mówi o braku CI, a w repo istnieją pliki pipeline'u
   (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`). To sprawdzenie deterministyczne,
   bez kosztu.
3. **Koszt:** bez zmian, nadal 68–72% maistera. Kandydaci jak w v1.
4. **Ograniczenia pomiaru:** jak w v1. Do tego jeden przebieg na repozytorium, a koszt eShopOnWeb wahał się między
   przebiegami o 47% (1,34 i 1,97 USD).
