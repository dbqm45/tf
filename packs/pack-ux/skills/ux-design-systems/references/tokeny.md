# Tokeny — warstwy, nazwy, format, motywy

## Spis treści
Warstwy · Nazwy · DTCG · Style Dictionary · Motywy i marki · Pułapki

## Warstwy
| Warstwa | Przykład | Kto używa | Zmienia się przy |
|---|---|---|---|
| prymitywna (referencyjna) | `color.blue.600` = `#2563EB`, `space.4` = 16 px | tylko warstwa semantyczna | zmianie palety |
| semantyczna (systemowa) | `color.action.bg`, `space.inset.md` | komponenty i produkty | motywie, marce |
| komponentowa | `button.primary.bg` | jeden komponent | odstępstwie komponentu od roli |

- Warstwę komponentową dodajesz dopiero, gdy komponent musi mieć wartość inną niż rola; w małym systemie często
  wystarcza para prymityw + semantyka. Źródła różnią się co do ścisłości (czy semantyczny może wskazywać na
  semantyczny); przyjmij regułę jednego kierunku i trzymaj ją we wszystkich zespołach.
- Skala prymitywów: kolor 10–12 tonów na rodzinę, odstępy wg skali 4 px, typografia wg skali modularnej (wartości
  decyduje ux-visual-design).

## Nazwy
- Wzór: `kategoria.[podkategoria].właściwość.rola.[stan]`, np. `color.text.secondary`, `color.border.input.focus`,
  `space.inset.md`, `radius.control`, `motion.duration.short`.
- Nazwa mówi, **do czego**, nie **jak wygląda**: `color.feedback.error`, nie `color.red`; rozmiary w skali
  `xs–xl` albo cyfrowej, nie `big`/`bigger`.
- Jedna konwencja wielkości liter i separatora (np. kropka w DTCG, kebab-case w CSS: `--color-text-secondary`);
  przekształcenie jest zadaniem Style Dictionary, nie ręcznym.
- Nazwa tokenu jest publicznym API: zmiana nazwy to zmiana niezgodna wstecz (wersjonowanie-i-governance.md).

## DTCG — format
- Specyfikacja *Design Tokens Format Module* ma pierwszą stabilną wersję 2025.10 (Final Community Group Report,
  2025-10-28). Grupa nie jest na ścieżce standaryzacji W3C — to raport grupy społecznej, więc nie nazywaj go
  „standardem W3C”. Zapowiedziane są kolejne, zastępujące wersje.
- Token to obiekt z `$value`; `$type` (np. `color`, `dimension`, `duration`) można ustawić na tokenie lub grupie
  (dziedziczenie); `$description` opcjonalny; `$extensions` na dane narzędzi (klucz z nazwą dostawcy).
- Alias: wartość `{ścieżka.do.tokenu}` [niezweryfikowane w tej sesji, składnia z wcześniejszych wersji specyfikacji].
- Typ medium: preferowany `application/design-tokens+json`, dopuszczalny `application/json`; rozszerzenie pliku
  `.tokens` lub `.tokens.json` [niezweryfikowane w tekście specyfikacji, wtórne źródła].
- Wycofanie tokenu: pole `$deprecated` [niezweryfikowane w tej sesji]; do czasu pewności zapisz wycofanie także
  w `$description` i w changelogu.
- Pola ze znakiem `$` są zarezerwowane; nazwy tokenów nie zaczynają się od `$` i nie zawierają `{`, `}`, `.`.
  [niezweryfikowane]

## Style Dictionary
- Transformuje tokeny na artefakty platform: CSS custom properties, JS/TS, XML dla Androida, Swift dla iOS.
  Konfiguracja: źródła (`source`), platformy, transformacje (kolor, jednostki, nazwy), formaty, pliki wyjściowe.
- Wersja 5 przyjmuje DTCG 2025.10 jako format bazowy (wtórne źródło) [niezweryfikowane]; sprawdź numer i obsługę typów
  złożonych w dokumentacji i `package.json` repozytorium, zanim zaplanujesz migrację z wersji 3/4.
- Potok: Figma (zmienne) → eksport/wtyczka → `*.tokens.json` w repozytorium → Style Dictionary w CI → pakiet
  wersjonowany. Kierunek jeden; edycje ręczne w plikach wygenerowanych są zakazane.

## Motywy i marki
- Motyw (jasny/ciemny) i marka (A/B) to **osie** wartości warstwy semantycznej. Dwie osie = macierz (marka × tryb);
  generuj ją, nie utrzymuj ręcznie. W Figmie: kolekcja semantyczna z trybami; w CSS: zestaw custom properties pod
  atrybutem (`[data-theme]`, `[data-brand]`) — implementacja w fe-css.
- Zakres marki: kolory, krój, promienie, ewentualnie ikony; układ i zachowanie wspólne. Marka, która zmienia
  zachowanie komponentu, to osobny komponent.
- Każda kombinacja przechodzi kontrast (ux-visual-design): test automatyczny liczący pary tekst/tło z tokenów.

## Pułapki
- Wartość surowa w komponencie omija motywy. Zakazuj w lintingu (np. reguła stylelint na kolory i odstępy).
- Zbyt wiele tokenów komponentowych: setki nazw bez użytkownika. Dodawaj na żądanie użycia.
- Token semantyczny nazwany od jednego zastosowania (`color.header.bg`) — nie przenosi się; nazwij rolę.
