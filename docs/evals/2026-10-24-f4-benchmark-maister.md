# F4 (część B): benchmark rekonstrukcji z kodu — eng-project-reconstruction vs maister — 2026-10-24

Decyzja człowieka (2026-10-24): uruchomić część B; repozytoria dobiera Claude. Koszt całej części B: **10,55 USD**
(przebiegi 10,08 USD, odświeżenie 0,47 USD; szacunek przed startem 30–45 USD). Dane: `docs/evals/2026-10-24-f4b/`.

## Warunki
- **Repozytoria** (publiczne, sklonowane `--depth 1`):

  | Repozytorium | Commit | Kod |
  |---|---|---|
  | `spring-projects/spring-petclinic` | 500158f, 2026-09-29 | Java/Spring Boot, 50 plików, 4,3 tys. linii |
  | `dotnet-architecture/eShopOnWeb` | 4da8212, 2025-01-13 | C#/.NET, starszy projekt referencyjny, 315 plików, 10,7 tys. linii |
  | `bxcodec/go-clean-arch` | e06c6d0, 2024-03-08 | Go, 19 plików, 1,8 tys. linii |

- **Narzędzia:**
  - nasz skill `eng-project-reconstruction` (workspace pack-it z rdzeniem);
  - maister 2.2.6 (SkillPanel/maister, MIT, commit a1f05e0): `/maister:init` z odkrywaniem standardów, wtyczka przez
    `--plugin-dir`. Przed użyciem audyt `skill_audit.py`: 0 ustaleń wysokiej wagi, 12 średnich (nazwy z przedrostkiem
    wtyczki), 27 niskich. Hooki przeczytane: blokada destrukcyjnych poleceń i dwa przypomnienia, bez sieci.
- **Jednakowe dla obu narzędzi:**
  - `claude -p` (Claude Code 2.1.310), model główny Sonnet, limit 8 USD na przebieg;
  - tryb `acceptEdits` z listą dozwolonych poleceń: Python, odczytowe polecenia gita, listowanie;
  - bez sieci, bez budowania i uruchamiania kodu projektu, tryb wsadowy bez pytań. maister ma bramki AskUserQuestion,
    więc dostał polecenie wybierania opcji domyślnych: wszystkie dokumenty projektu i standardy.
- **Złoty standard:** 20 faktów na repozytorium (4 stack, 4 moduły, 5 reguł, 5 standardów, 2 inne) z dowodem
  `plik:linia`. Przygotowali je trzej agenci, którzy nie widzieli wyników narzędzi; istnienie dowodów sprawdził skrypt.
- **Ocena ślepa:**
  - trzech agentów (po jednym na repozytorium) dostało dokumenty jako A i B w losowej kolejności, z usuniętymi
    nazwami narzędzi;
  - pokrycie: każdy fakt oceniony jako tak / częściowo / nie / błędnie;
  - poprawność: 10 losowych twierdzeń z każdego zestawu sprawdzonych w kodzie;
  - klucz A/B: `verdicts/klucz-AB.json`.

## Wyniki
| Repozytorium | Koszt: nasz / maister | Czas: nasz / maister | Pokrycie ważone*: nasz / maister | Poprawność: nasz / maister |
|---|---|---|---|---|
| go-clean-arch | 1,10 / 1,93 USD | 5,0 / 8,1 min | 17,5 / 18,5 | 9/9 / 9/10 |
| spring-petclinic | 1,62 / 2,12 USD | 7,1 / 9,2 min | 16,5 / 16 | 10/10 / 9/10 |
| eShopOnWeb | 1,34 / 1,96 USD | 6,2 / 8,8 min | 17 / 13,5 | 8/9 / 8/9 |
| **Razem** | **4,07 / 6,01 USD (68%)** | 18,3 / 26,0 min | **51 / 48 z 60 (85% / 80%)** | **27/28 / 26/29 (96% / 90%)** |

\* tak = 1, częściowo = 0,5. Poprawność liczona bez twierdzeń „nieweryfikowalnych” (nasz: 2, maister: 1).

- **Oceny surowe:**
  - nasz: tak 42, częściowo 18, nie 0, błędnie 0;
  - maister: tak 45, częściowo 6, nie 9, błędnie 0.

  maister częściej podaje fakt w pełni, ale 9 faktów pomija całkiem. Wszystkie 9 to reguły biznesowe lub inne
  w petclinic i eShopOnWeb.
- **Pokrycie według kategorii** (punkty ważone):

  | Kategoria | Nasz | maister |
  |---|---|---|
  | Reguły | 14/15 | 5,5/15 |
  | Stack | 9/12 | 12/12 |
  | Moduły | 9,5/12 | 12/12 |
  | Standardy | 13/15 | 14/15 |
  | Inne | 5,5/6 | 4,5/6 |

- **Dowody:**
  - nasz: 484 odwołania `plik:linia`, wszystkie istnieją; 419 z 507 wypunktowań ma dowód; `recon_check` na raporcie
    głównym: 0 złych dowodów w każdym repozytorium;
  - maister: 6 odwołań z numerem linii (2 trafne), żadne wypunktowanie nie ma dowodu z linią; w dokumentach pojawiają
    się same nazwy plików (np. 44 wzmianki w go-clean-arch).
- **Błędy znalezione przez oceniających:**
  - nasz: 1 fałsz (liczba logerów w eShopOnWeb), 1 przesunięty numer linii (petclinic, o 1);
  - maister: 3 fałsze — liczba plików testów (go), nagłówek licencji we „wszystkich” plikach (petclinic),
    „wszystkie endpointy na `EndpointBaseAsync`” (eShopOnWeb).
- **Odświeżenie** (eShopOnWeb, 12 z 254 plików z kodem, 4,7%):
  - nasz: 0,25 USD, 62 s; manifest wskazał wszystkie 12 plików;
  - maister: 0,22 USD, 31 s; zauważył zmiany i nie zmienił dokumentów.

  Zmiana dotyczyła tylko komentarzy, więc test nie rozróżnia narzędzi — trzeba go powtórzyć ze zmianą w logice.

## Kryterium sukcesu z planu
| Kryterium | Wynik | Spełnione? |
|---|---|---|
| Pokrycie ≥ maister | ważone 85% wobec 80% (pełnych trafień 42 wobec 45) | tak, z zastrzeżeniem |
| Koszt ≤ 50% maistera | 68% | **nie** |
| Precyzja dowodów ≥ 95% | 96% twierdzeń prawdziwych w próbie; 100% odwołań `plik:linia` istnieje | tak |

## Wnioski i dalsze kroki
1. **Stack i moduły to nasza luka** (9/12 i 9,5/12 wobec 12/12). W raporcie brakowało:
   - wersji narzędzi i ich rozjazdów (Go w CI kontra go.mod);
   - profili i ustawień (`ddl-auto`, profile Springa);
   - CI i pokrycia testami (JaCoCo);
   - pełnej listy projektów lub pakietów z odpowiedzialnością.

   Poprawka: w `references/raport.md` obowiązkowa tabela stacku (język i wersja, framework i wersja, dane, build, CI,
   testy, z dowodem) i lista modułów z odpowiedzialnością. Do tego scenariusz ewaluacji, który to sprawdza.
2. **Reguły biznesowe to nasza przewaga** (14/15 wobec 5,5/15) — utrzymać.
3. **Koszt:** 68% maistera, cel 50% niespełniony. Kandydaci do sprawdzenia:
   - karty modułów na Haiku już są;
   - mniej tur głównego modelu (76–88 tur);
   - limit liczby kart dla małych repozytoriów.
4. **Odświeżenie:** powtórzyć ze zmianą w logice (nowa reguła walidacji, nowy endpoint), żeby sprawdzić, czy narzędzie
   aktualizuje treść.
5. **Ograniczenia pomiaru:**
   - jedno uruchomienie na parę;
   - małe repozytoria (do 10,7 tys. linii);
   - oceniający to jeden model (Sonnet), a format dowodów zdradzał narzędzie mimo zanonimizowania nazw;
   - maister w trybie wsadowym nie zadał pytań, które w normalnej pracy dają mu kontekst od człowieka.
