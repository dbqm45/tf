# Audyt monorepo Nx z Angularem — inwentarz i analiza

Spis treści: 1. Obszary i pytania · 2. Workspace · 3. Inwentarz bibliotek · 4. Zależności · 5. Angular ·
6. Pozostałe obszary · 7. Pierwsze kroki

Zasady narzędzi i frameworka bierzesz z tool-nx (graf, tagi, granice, generatory), fw-angular (konwencje według
wersji) i fe-architecture (stan, komponenty, granice frontu) — ten plik mówi, **co zebrać do teczki**.

## 1. Obszary i pytania (checklista etapu 1)
| Obszar | Główne pytanie |
|---|---|
| Nx workspace | czy struktura monorepo jest czytelna i konsekwentna? |
| Granice bibliotek | czy biblioteki mają jasne odpowiedzialności? |
| Graf zależności | czy zależności płyną we właściwym kierunku? |
| Architektura Angulara | czy komponenty, serwisy, moduły mają odpowiedzialności adekwatne do roli? |
| Routing | czy podział tras i lazy loading są uzasadnione? |
| Stan | gdzie jest stan i kto jest jego właścicielem? |
| Dostęp do danych | jak wygląda komunikacja z API, modele, obsługa błędów? |
| Kod współdzielony | co współdzielimy i czy powinno być współdzielone? |
| Testy | czy testy odpowiadają strukturze i odpowiedzialnościom? |
| Build i narzędzia | czy konfiguracja Nx i Angulara wspiera przyjętą architekturę? |

Biblioteki współdzielonej nie oceniasz w izolacji: w zakresie są też jej konsumenci i to, od czego zależy.

## 2. Workspace
Polecenia (składnia zależy od wersji Nx — sprawdź `nx --version` i tool-nx; wynik zapisz w `evidence/`):
```bash
npx nx show projects                      # lista projektów
npx nx graph --file=evidence/graph.json    # graf zależności do pliku (dowód dla ustaleń)
npx nx report                             # wersje Nx, wtyczek, Node
```
Do zapisu: liczba aplikacji i bibliotek, typy bibliotek, grupowanie, tagi (`project.json`), reguły zależności
(`@nx/enforce-module-boundaries` w konfiguracji ESLint: włączona? `depConstraints` odpowiadają faktycznym
granicom?), `nx.json` (cache, domyślne opcje), generatory, wersje Nx i Angulara. Sama liczba bibliotek nie
świadczy o jakości.

## 3. Inwentarz bibliotek
Karta modułu = biblioteka lub aplikacja. W nagłówku karty dopisz `Typ:` (feature / ui / data-access / util /
shared / app — tylko jeśli taki podział faktycznie występuje) i tagi. Reguły biznesowe: zwykle w feature i
data-access; biblioteka czysto techniczna ma pustą tabelę z jednym zdaniem „brak — biblioteka techniczna”.

| Biblioteka | Typ | Odpowiedzialność | Używana przez | Zależności | Uwagi |
|---|---|---|---|---|---|
| `orders-feature` | feature | widok zamówień | `shop-app` | `orders-data-access`, `orders-ui` | — |

Pytania: czy nazwa odpowiada odpowiedzialności; podział według domen, funkcji, warstw czy przypadkowy; biblioteki
o niejasnej odpowiedzialności; właściciel kodu współdzielonego; jeden konsument czy wielu.

## 4. Zależności
Z grafu (nie z czytania) sprawdź: feature zależny od innego feature bez uzasadnienia; biblioteka współdzielona
importująca kod jednej aplikacji; cykle; biblioteki techniczne z logiką biznesową; importy omijające public API
(`@org/lib/src/...` zamiast `@org/lib`); zależności nieprzewidywalne ze struktury. Układ
`app → feature → data-access / ui → shared-ui` bywa uzasadniony, ale nie zakładaj, że każda aplikacja go ma.

## 5. Angular
- **Komponenty:** odpowiedzialność; mieszanie prezentacji, wywołań API i stanu; przepływ danych i zdarzeń
  (inputy/outputy, sygnały); czy „współdzielone” komponenty są faktycznie wielokrotnego użytku.
- **Serwisy i logika biznesowa:** gdzie jest logika; zakres serwisów; DI; czy logikę da się testować bez widoku.
- **Routing:** podział tras, lazy loading, trasy feature'ów, guardy i resolvery, błędy nawigacji, związek tras ze
  strukturą bibliotek.
- **Stan:** mechanizmy (sygnały, serwisy ze stanem, NgRx lub inne); stan globalny / domenowy / lokalny; dane z API;
  duplikacja stanu. Nie zakładaj jednego mechanizmu dla całej aplikacji — oceniaj w kontekście użycia.
- **API:** klienci i adaptery, modele, mapowanie odpowiedzi na modele aplikacji, obsługa błędów, współdzielenie.

## 6. Pozostałe obszary (według zakresu)
Testy jednostkowe i integracyjne, e2e, aliasy i standardy importów, współdzielone typy i modele, konfiguracja
środowisk, build i cache, uruchamianie testów i lintu (`nx affected`), generatory, dokumentacja techniczna.

## 7. Pierwsze kroki
1. Workspace: `nx show projects`, `nx graph --file=evidence/graph.json`, `nx.json`, konfiguracje projektów, ESLint,
   wersje Nx i Angulara.
2. Lista bibliotek pogrupowana według domen i odpowiedzialności; oznacz niejasne.
3. Zależności: używane przez aplikację, kierunki pod prąd, cykle, public API, działanie reguł Nx.
4. 3–5 reprezentatywnych funkcji biznesowych prześledzonych `trasa → feature → stan/serwis → API → UI` (do sekcji
   Przepływy indeksu; nie każda funkcja musi mieć ten układ).
5. Ustalenia na bieżąco do `assessment.md`; rekomendacje dopiero po analizie.
