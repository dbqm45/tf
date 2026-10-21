# Nowa aplikacja Angular i praca z CLI

Spis treści: 1. Utworzenie aplikacji · 2. Generowanie kodu i paczki · 3. Nazwy plików · 4. Konfiguracja środowisk
· 5. Serwer MCP Angular CLI · Źródła

## 1. Utworzenie aplikacji
1. **Wersja.** Bez prośby człowieka nie podajesz wersji: bierzesz najnowszą stabilną. Gdy człowiek prosi o konkretną,
   używasz `npx @angular/cli@<wersja> new …` z pominięciem lokalnej instalacji.
2. **CLI.** Sprawdź, czy `ng` jest dostępne (`ng version`). Jest → `ng new`; nie ma → `npx @angular/cli@latest new`.
   Instalację globalną (`npm install -g @angular/cli`) proponujesz człowiekowi, nie wykonujesz jej sam.
3. **Polecenie bez pytań:** `ng new <nazwa> --interactive=false` i flagi dobrane do opisu aplikacji:
   - `--style=scss|css|less`, `--routing`, `--ssr` (renderowanie na serwerze, `renderowanie-i-ssr.md`),
     `--prefix=<prefiks>` (prefiks selektorów);
   - `--ai-config=<narzędzie>` zapisuje w projekcie reguły dla agenta (np. `claude`, `agents`); po utworzeniu przeczytaj
     wygenerowany plik i stosuj go razem z tym skillem;
   - `--skip-tests` tylko na wyraźną prośbę.
4. **Nazwa aplikacji:** zaproponuj z opisu albo zapytaj.
5. **Domyślne decyzje w nowym projekcie:** formularze w Signal Forms (stabilne od v22), zoneless i `OnPush` (domyślne
   w nowych wersjach), Vitest, standalone, nowy control flow.
6. **Nie uruchamiaj serwera deweloperskiego od razu.** Najpierw zbuduj pierwsze funkcje, potem zapytaj człowieka, czy
   uruchomić `ng serve`.
7. **Weryfikacja po każdej zmianie kodu:** `ng build`. Błędy kompilacji czytasz i poprawiasz przed oddaniem pracy.

## 2. Generowanie kodu i paczki
- Kod generujesz przez CLI, potem go uzupełniasz: `ng g c <ścieżka>` (komponent), `ng g s` (serwis), `ng g d`
  (dyrektywa), `ng g p` (pipe), `ng g g` (guard funkcyjny), `ng g interceptor`, `ng g resolver`, `ng g interface`,
  `ng g enum`, `ng g class`. Zapisz ścieżkę zwróconą przez generator, żeby edytować właściwy plik.
- Trasy nie mają generatora: wygeneruj komponent i dopisz go do tablicy `Routes` (zwykle `app.routes.ts`).
- Biblioteki Angulara dodajesz przez `ng add <paczka>` zamiast `npm install`: polecenie instaluje paczkę i uruchamia jej
  schematy konfiguracji (np. `ng add @angular/material`, `ng add tailwindcss`).
- **Tailwind CSS v4:** po `ng add tailwindcss` w globalnym arkuszu jest `@import 'tailwindcss';`. Nie twórz
  `tailwind.config.js` ani dyrektyw `@tailwind base/components/utilities` z wersji 3. Przy ręcznej konfiguracji
  wystarcza plik `.postcssrc.json` z wtyczką `@tailwindcss/postcss`.
- Proxy do lokalnego API w trakcie pracy: plik `proxy.conf.json` i opcja `proxyConfig` celu `serve` w `angular.json`.
- Testy e2e: `ng add` wybranego narzędzia (np. Playwright, Cypress), potem `ng e2e`.

## 3. Nazwy plików (przewodnik stylu od v20)
- W projektach utworzonych w nowym stylu pliki nie mają sufiksu roli: `product-list.ts` z klasą `ProductList` zamiast
  `product-list.component.ts`; szablon i style mają tę samą nazwę bazową, test `.spec.ts`.
- Nazwa mówi o celu, nie o roli: serwisy `auth-data.ts`, `orders-store.ts`, `user-data-client.ts`; kontekst daje katalog
  (`core/`, `features/<funkcja>/`, `shared/`). Typy danych zostają z sufiksem `.model.ts`.
- Kolizje nazw: komponent `UserProfile` w `user-profile.ts` obok interfejsu `User` w `user.model.ts`.
- **Najpierw sprawdź projekt:** sąsiednie pliki, ustawienia schematów w `angular.json`, reguły ESLint. Projekt
  z sufiksami zostaje przy sufiksach. Nie mieszaj obu stylów w jednym katalogu funkcji; w razie wątpliwości użyj
  sufiksów.

## 4. Konfiguracja środowisk
- **W czasie budowania:** `ng g environments` tworzy `src/environments/` i podmianę plików w `angular.json`. Sprawdzenie
  trybu deweloperskiego: `isDevMode()` zamiast ręcznej flagi `production`.
- **W czasie uruchomienia:** ten sam artefakt na wiele środowisk; konfiguracja z pliku JSON wczytywana przed startem
  aplikacji (`provideAppInitializer`) i udostępniana tokenem. Sekretów nie umieszczasz w żadnym z tych plików: trafiają
  do przeglądarki.

## 5. Serwer MCP Angular CLI
- Angular CLI ma wbudowany serwer MCP: `npx @angular/cli mcp` (w konfiguracji klienta MCP jako `command: npx`,
  `args: ["-y", "@angular/cli", "mcp"]`). Opcje: `--read-only` (tylko narzędzia bez zmian w projekcie), `--local-only`
  (bez sieci).
- Narzędzia m.in.: `get_best_practices` (przewodnik dobrych praktyk dla wersji projektu), `search_documentation`
  (angular.dev), `list_projects`, `onpush_zoneless_migration` (plan przejścia na `OnPush` i zoneless), `run_target`,
  `devserver_start`, `devserver_stop`, `devserver_wait_for_build`.
- Dodanie serwera MCP do konfiguracji agenta to zmiana uprawnień: tylko za zgodą człowieka (core-agent-security).
  Wybieraj `--read-only`, gdy agent ma tylko czytać.

## Źródła
- angular/skills, skille `angular-new-app` i `angular-developer` (pliki angular-developer/references: cli, naming-conventions,
  environment-configuration, tailwind-css, mcp, e2e-testing), commit
  43ec6adc2b35049734d0d114e3948e022f1cd1e7 z 2026-10-21 (generowane z angular/angular), licencja MIT, autor Google LLC.
  Opisane własnymi słowami; odczyt 2026-10-21.
