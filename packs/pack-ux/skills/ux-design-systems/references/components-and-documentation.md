# Komponenty, dokumentacja, dostępność, testy

## Komponent — kiedy i jak
- **Kiedy:** wzorzec użyty w ≥ 3 miejscach lub produktach, o stabilnym zachowaniu. Pierwsze użycie zostaje w produkcie.
- **API** (Figma = kod): warianty tylko dla różnic wykluczających się (rodzaj, rozmiar), reszta jako właściwości
  (ikona tak/nie, treść, zamiana ikony) i sloty. Nazwy identyczne: `variant=primary`, `size=md`, `disabled`.
  Mapowanie właściwości Figma → propsy utrzymuj w Code Connect lub w tabeli w dokumentacji.
- **Stany:** domyślny, najechanie, fokus, wciśnięty, wyłączony, błąd, ładowanie; komponent bez któregoś stanu
  nie jest gotowy.
- **Złożoność:** komponent, który ma ponad ok. 10 właściwości, dzielisz (np. `Button` + `IconButton`), zamiast
  dodawać kolejną flagę.

## Dostępność w komponencie
- Semantyczny element natywny przed `div` z rolą; nazwa dostępna wymuszona w API (brak `aria-label` na przycisku
  z ikoną → błąd typu lub ostrzeżenie w trybie deweloperskim).
- Klawiatura: kolejność, Enter/Spacja/Esc/strzałki zgodnie z wzorcem; fokus widoczny i niezasłonięty; pułapka fokusu
  w oknie modalnym z powrotem fokusu po zamknięciu.
- Cele dotyku ≥ 24×24 px (WCAG 2.2 SC 2.5.8), zalecane 44×44 px; kontrast w obu motywach i markach.
- Automatyka (axe w Storybooku) wykrywa tylko część problemów — Storybook podaje do 57% — więc każdy komponent ma
  też ręczny przegląd klawiaturą i czytnikiem ekranu (qa-exploratory-manual).

## Dokumentacja komponentu
Stała struktura strony, żeby dało się ją sprawdzić:
1. Po co i kiedy użyć; kiedy **nie** (z odesłaniem do właściwego komponentu).
2. Anatomia (nazwane części), warianty, stany — obrazy z żywych historyjek, nie zrzuty ręczne.
3. Rób / nie rób — para obrazków z jednym zdaniem uzasadnienia każdy.
4. Treść: etykiety, długość, ton (ux-content-design, jeśli dostępny).
5. Dostępność: rola, klawisze, odczyt, wymagania treściowe.
6. API: propsy z typami i wartościami domyślnymi, tokeny komponentu, przykład kodu.
7. Zmiany: link do changelogu, status (eksperymentalny, stabilny, przestarzały).
- Storybook: historyjka na wariant i stan, `args` dla właściwości, panel dostępności, testy interakcji dla złożonych
  komponentów. Historyjki są też danymi dla testów zrzutowych.

## Testy zrzutowe (regresja wizualna)
- Zrzut każdej historyjki w CI (np. Chromatic lub Playwright) w obu motywach i markach; próg różnicy ustawiony
  (np. 0,1% pikseli) i stałe środowisko (czcionki, przeglądarka, brak animacji).
- Różnica = przegląd człowieka: zatwierdzenie zmiany zamierzonej (wpisuje się w changelog) albo poprawka błędu.
  Nigdy automatyczne zatwierdzanie.
- Wykluczaj z zrzutów dane zmienne (daty, losowe obrazy); animacje wyłączone lub zatrzymane w stanie końcowym.
- Zrzuty nie zastępują testów zachowania ani dostępności (tool-playwright, qa-regression).
