# Zgodność przeglądarek — polityka, sprawdzanie, testy

> **Spis treści:** 1. Polityka wsparcia · 2. Wykrywanie funkcji i progressive enhancement · 3. Polyfille · 4. Sprawdzanie kodu względem polityki (CI) · 5. Macierz testów · Przykład · Źródła (dostęp 2026-10-18)

Fakty sprawdzone 2026-10-18 w repozytoriach projektów i w npm (źródła na końcu). Wersje pakietów szybko się zmieniają —
przed wpisaniem do projektu sprawdź `npm view <pakiet> version`.

## 1. Polityka wsparcia
**Baseline** (WebDX Community Group, pakiet `web-features`) opisuje, czy funkcja działa w zbiorze głównych przeglądarek:
Chrome (desktop i Android), Edge (desktop), Firefox (desktop i Android), Safari (macOS i iOS).

| Poziom | Znaczenie | Jak używasz |
|---|---|---|
| *Newly available* | działa w aktualnych stabilnych wersjach wszystkich przeglądarek zbioru | z wykrywaniem funkcji i ścieżką zastępczą |
| *Widely available* | minęło 30 miesięcy od dnia, w którym ostatnia przeglądarka zbioru dodała obsługę | bez wahania |
| *Baseline RRRR* | wszystkie funkcje, które były Newly available do końca roku RRRR | cel stały w czasie, np. w umowie z klientem |
| poza Baseline | brak w co najmniej jednej przeglądarce zbioru | tylko jako progressive enhancement |

Polityka jest decyzją produktu, nie programisty. Źródła decyzji to dane analityczne (udział przeglądarek wśród
użytkowników), umowy z klientami (np. wymagany Safari na iPadach w terenie), rynek i koszt testów. Zapisz ją w ADR
(docs-tech-writing) i w repo.

### browserslist — jedno źródło dla narzędzi
Plik `.browserslistrc` (katalog bieżący lub nadrzędny) albo klucz `browserslist` w `package.json`. Z tego samego
zapytania korzystają transpilator, prefiksy CSS i lint JS.

```
# .browserslistrc — przykład polityki opartej na Baseline (browserslist ≥ 4.26)
baseline widely available
```

| Zapytanie | Znaczenie |
|---|---|
| `baseline widely available` | przeglądarki zgodne z Widely available na dziś |
| `baseline newly available` | przeglądarki zgodne z Newly available |
| `baseline 2024` | cel roczny |
| `baseline widely available on 2026-01-01` | stan na dzień (powtarzalne buildy) |
| `... with downstream` | dodaje przeglądarki na silniku z zbioru (np. Opera, Samsung Internet) |
| `defaults` | `> 0.5%, last 2 versions, Firefox ESR, not dead` — oparte na udziałach, nie na Baseline |

- Zapytania oparte na udziałach (`> 0.5%`, `last 2 versions`) zależą od bazy `caniuse-lite` — aktualizuj ją
  (`npx update-browserslist-db@latest`) regularnie, np. w ramach aktualizacji zależności.
- Dane Baseline dostarcza pakiet `baseline-browser-mapping`; ostrzega, gdy dane mają ponad 2 miesiące. Nie wyciszaj
  ostrzeżenia zmienną środowiskową — zaktualizuj zależności.
- Sprawdź, co faktycznie wyszło z zapytania: `npx browserslist` wypisuje listę wersji.

## 2. Wykrywanie funkcji i progressive enhancement
```js
if ('share' in navigator) { /* Web Share */ } else { /* kopiuj link */ }
if (CSS.supports('container-type: inline-size')) { /* ... */ }
```
```css
.karta { display: block; }
@supports (container-type: inline-size) { .lista { container-type: inline-size; } }
```
- Nigdy `navigator.userAgent` do decyzji o funkcjach: kłamie, zmienia się i blokuje przeglądarki, które funkcję mają.
- Podstawowa ścieżka (formularz, link, treść) działa bez JS i bez nowej funkcji; nowość ją ulepsza.
- Mapa obsługi API urządzeń i ścieżki zastępcze: `natywne-api-przegladarki.md`.

## 3. Polyfille
- Najpierw pytanie: czy ścieżka zastępcza wystarczy? Polyfill to kod wysyłany wszystkim lub ładowany warunkowo.
- Ładowanie warunkowe (`if (!('x' in window)) await import('./polyfill-x.js')`), nie globalny pakiet „na wszystko”.
- Rozmiar polyfilli w budżecie paczki (`checklista-wydajnosci.md`); usuwasz je, gdy polityka przestaje obejmować
  przeglądarki, które ich potrzebowały.
- Polyfill z CDN strony trzeciej to ryzyko łańcucha dostaw — tylko z własnego builda.

## 4. Sprawdzanie kodu względem polityki (CI)
| Obszar | Narzędzie | Źródło polityki | Status |
|---|---|---|---|
| JS (API przeglądarki) | `eslint-plugin-compat` | `browserslist` z `package.json` | społeczność |
| CSS w ESLint | `@eslint/css`, reguła `css/use-baseline` (domyślnie `available: "widely"`; opcje `"newly"` albo rok) | własna opcja reguły | oficjalny pakiet ESLint |
| CSS w stylelint | `stylelint-plugin-use-baseline`, reguła `plugin/use-baseline` | własna opcja | społeczność |

- Próg w regułach CSS ustaw zgodnie z `browserslist` — dwa źródła polityki to ryzyko rozjazdu; zapisz to w ADR.
- `css/use-baseline` nie zgłasza funkcji użytych wewnątrz `@supports` — to zachęca do poprawnego wzorca.
- Wyjątki (`allowProperties` itd.) z komentarzem, dlaczego funkcja jest bezpieczna (np. ma ścieżkę zastępczą).
- Lint nie zastępuje testów: nie widzi błędów implementacji ani różnic w zachowaniu silników.

## 5. Macierz testów
| Warstwa | Przeglądarki | Kiedy |
|---|---|---|
| PR | Playwright `chromium` | każdy PR |
| noc | `chromium`, `firefox`, `webkit` + urządzenia mobilne (`devices['iPhone 13']`, `devices['Pixel 7']`) | raz na dobę (qa-regression) |
| przed wydaniem | wybrane ścieżki na prawdziwym Safari i iOS | gdy polityka lub zgłoszenia tego wymagają |
| markowe Chrome/Edge | `channel: 'chrome'` lub `'msedge'` | gdy funkcja zależy od markowej przeglądarki (np. kodeki, DRM) |

```ts
// playwright.config.ts — fragment
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
],
```
Uruchomienie tylko jednego projektu w PR: `npx playwright test --project=chromium`. Szczegóły narzędzia: tool-playwright.

**WebKit z Playwright to nie Safari.** Playwright buduje WebKit z najnowszych źródeł (często przed wydaniem w Safari),
z własnymi poprawkami, i nie działa z markowym Safari. Funkcje zależne od systemu (np. kodeki) różnią się między
platformami; najbliżej Safari jest WebKit uruchomiony na macOS. Emulacja `iPhone 13` zmienia ekran, dotyk i user-agent,
nie silnik ani system. Dlatego:
- błędy zgłaszane z iPhone'ów odtwarzasz najpierw w `webkit` z emulacją urządzenia; gdy się nie odtwarzają — na
  prawdziwym urządzeniu (Safari Web Inspector na macOS) albo w chmurze urządzeń;
- chmura prawdziwych urządzeń jest płatna — tylko przy wymaganiu biznesowym, dla kilku krytycznych ścieżek, z budżetem
  (core-cost-control).

**iOS:** poza UE wszystkie przeglądarki na iOS używają WebKit, więc „Chrome na iPhonie” to w praktyce silnik Safari.
W UE od iOS 17.4 (iPadOS 18) Apple dopuszcza inne silniki dla przeglądarek z uprawnieniem Web Browser Engine
(developer.apple.com/support/alternative-browser-engines, dostęp 2026-10-20). Wydanej przeglądarki z Gecko lub Blink
na iOS w UE nie znaleziono (stan 2026-10-20, wyszukiwanie) — testuj na WebKit także w UE.

## Przykład
**Sytuacja:** B2B SaaS, klienci w UE; analityka: 61% Chrome, 22% Safari (z czego połowa iOS), 9% Edge, 6% Firefox.
Zgłoszenia „nie działa na iPadzie” po wdrożeniu CSS nesting i `:has()`.
**Wynik (skrót):**
- Polityka: `baseline widely available` w `.browserslistrc`, ADR z danymi z analityki; Newly available tylko z `@supports`.
- CI: `eslint-plugin-compat` dla JS, `css/use-baseline` z `available: "widely"` dla CSS; istniejące naruszenia na
  liście wyjątków z terminem naprawy.
- Testy: PR — `chromium`; noc — trzy silniki i `iPad (gen 7)`; przed wydaniem — logowanie i płatność na prawdziwym iPadzie.

## Źródła (dostęp 2026-10-18)
- web-platform-dx/web-features, `docs/baseline.md` — definicje, zbiór przeglądarek, 30 miesięcy.
- browserslist README i CHANGELOG — zapytania Baseline (od 4.26.0), pliki konfiguracji, `defaults`.
- browserslist/update-db README; web-platform-dx/baseline-browser-mapping README.
- eslint/css, `docs/rules/use-baseline.md`; amilajack/eslint-plugin-compat README; ryo-manba/stylelint-plugin-use-baseline.
- microsoft/playwright, `docs/src/browsers.md` (projekty, kanały, WebKit a Safari), `docs/src/emulation.md`.
- developer.apple.com/support/alternative-browser-engines/ — silniki inne niż WebKit w UE.
Strony web.dev i MDN były niedostępne z sesji — definicje Baseline wzięte z repozytorium specyfikacji.
Opisane własnymi słowami.
