# Skille podejrzane o dublowanie wiedzy modelu — 2026-11-16

Pliki: `2026-11-16-podejrzane-skille.{md,jsonl}`. 24 skille z `pack-it` wybrane z treści: wiedza podręcznikowa, bez
odwołań do fabryki i projektu, bez skryptów (`ux-feature-design` nie ma pliku scenariuszy, pominięty). Scenariusze
strojenia `trigger` (71), tylko Sonnet, ze skillami i bez (`--baseline`), `--isolated`, jeden przebieg, sędzia
modelowy przy braku trafienia wyrażenia. 142 przebiegi, 0 błędów, koszt 9,91 USD.

## Zastrzeżenie
Scenariusze strojenia napisano na podstawie treści skilli, więc sprzyjają skillom (terminy z treści, np.
„SAFe-washing”, „drabina minimalizmu”). Dlatego wynik działa w jedną stronę: **brak przewagi mimo takich sprawdzeń
to mocny sygnał dublowania**, a przewaga o jeden scenariusz to słaby sygnał wartości. Jeden przebieg na scenariusz.

## Wynik (treść poprawna ze skillem / bez skilli)

### Bez przewagi — kandydaci do wyłączenia
| Skill | Ze skillem | Bez | Uwagi |
|---|---|---|---|
| eng-algorithms-data-structures | 2/2 | 2/2 | |
| fe-technical-seo | 3/3 | 3/3 | |
| ops-iac-terraform | 2/2 | 2/2 | |
| pm-saas-metrics | 4/4 | 4/4 | |
| proc-lean | 2/2 | 2/2 | |
| tool-nx | 3/3 | 3/3 | |
| eng-design-principles | 2/3 | 2/3 | jeden lepiej, jeden gorzej |
| eng-design-patterns | 2/3 | 3/3 | gorzej ze skillem w `dekorator-vs-proxy` |

### Przewaga o jeden scenariusz, głównie w terminach skilla — niepewne
| Skill | Ze skillem | Bez | Czego brakowało bez skilla |
|---|---|---|---|
| pm-product-strategy | 4/4 | 3/4 | sformułowanie „wartość dla / korzyść” |
| pm-product-lifecycle | 2/2 | 1/2 | „kryteria decyzji / go-no-go” |
| pm-stakeholders | 2/2 | 1/2 | siatka wpływ × zainteresowanie, poziomy zaangażowania |
| proc-team-topologies | 2/2 | 1/2 | typy zespołów (stream-aligned) |
| qa-exploratory-manual | 2/2 | 1/2 | wpływ × częstość w zgłoszeniu defektu |
| eng-clean-code | 3/3 | 2/3 | „logowanie to nie obsługa błędu”, OWASP A10:2025 |
| ops-docker | 2/2 | 1/2 | blokada metadanych chmury (169.254.169.254) |
| data-analysis | 2/4 | 1/4 | testy obalające przy wnioskowaniu przyczynowym; skill wczytany 2/4 |

### Wyraźna przewaga — zostają
| Skill | Ze skillem | Bez | Czego brakowało bez skilla |
|---|---|---|---|
| eng-continuous-delivery | 4/4 | 1/4 | DORA do uczenia, nie jako cel; wskaźniki wyprzedzające i opóźnione |
| eng-debugging | 3/4 | 1/4 | rozdzielenie obserwacji od hipotez, zmiana jednej rzeczy naraz i dzielenie na połowy |
| tool-jest | 3/3 | 1/3 | nowe API Jest (`arrayOf`, `unstable_mockModule`), ID wymagania w nazwie testu |
| be-business-app-patterns | 5/5 | 3/5 | dziennik audytu i indeks częściowy przy soft delete, uprawnienia per rekord w operacji masowej |
| proc-agile | 6/6 | 4/6 | wzorce cięcia historyjek, średnia w prognozie ukrywa ryzyko |
| proc-safe | 2/2 | 0/2 | „SAFe-washing”, najpierw zmniejsz zależności — w obu przypadkach terminy skilla |
| fe-css | 2/2 | 0/2 | tokeny (`var(--…)`) zamiast wartości wpisanych na sztywno — konwencja skilla |
| ops-finops | 2/2 | 0/2 | reguły skilla (`expires`, 7 dni na sprzeciw) |

## Wnioski
- **8 skilli nie wnosi nic nawet na sprzyjających im scenariuszach.** To kandydaci do wyłączenia
  (`metadata.widocznosc: nazwa` albo osobna nakładka opcjonalna), po przeglądzie, czy nie mają reguł fabryki,
  których scenariusze nie sprawdzają.
- **`be-business-app-patterns` nie jest zbędny:** 2026-11-10 4/5 scenariuszy zaliczanych bez skilla, teraz 3/5.
  Różnica mieści się w rozrzucie jednego przebiegu. Wcześniejsza rekomendacja „wyłącz od razu” była przedwczesna.
- **Prawdziwa wartość jest w trzech rodzajach treści:** świeża wiedza (nowe API Jest, OWASP 2025), procedura
  diagnozy (`eng-debugging`) i reguły domu (tokeny CSS, `expires`, DORA jako narzędzie uczenia). Wiedza ogólna
  (algorytmy, Terraform, Nx, metryki SaaS, Lean) nie wnosi nic. Scenariusz `regresja-200-commitow`
  (`eng-debugging`) nie przechodzi ani ze skillem, ani bez.
- **Przewagi w `proc-safe`, `pm-stakeholders`, `qa-exploratory-manual` mogą być dopasowaniem do słów skilla.**
  Rozstrzygnąłby to holdout napisany przez agenta bez dostępu do treści skilli.
- Tylko Sonnet: Haiku bez skilla może wypaść gorzej, więc wyłączenie dotyczy pracy na Sonnecie i mocniejszych.
