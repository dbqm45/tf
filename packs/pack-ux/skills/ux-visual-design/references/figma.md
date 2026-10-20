# Praktyka w Figmie

Dokumentacja: Figma Help Center, „Guide to variables in Figma”, „Explore component properties”. Biblioteka
komponentów jako produkt (nazwy, wersje, wydania): ux-design-systems.

## Komponenty
- Najpierw wzorzec w ekranach, potem komponent, gdy użyty ≥ 2 razy. Komponent bazowy + instancje; nie odłączaj
  instancji (detach) dla jednej różnicy — dodaj właściwość.
- **Wariant** dla zmian dużych i wykluczających się (rodzaj, rozmiar, stan); **właściwości** dla drobnych:
  logiczna (pokaż ikonę), tekst, zamiana instancji (ikona z listy). Slot — elastyczny obszar na treść (nowsza funkcja,
  sprawdź dostępność w swoim planie [niezweryfikowane]).
- Nazwy właściwości jak w kodzie (`size=md`, `state=hover`, `hasIcon`), żeby przekazanie nie wymagało tłumaczenia.
- Stany: domyślny, najechanie, fokus, wciśnięty, wyłączony, błąd, ładowanie — każdy jako wariant.

## Auto layout
- Każdy komponent z auto layout: kierunek, odstęp i wypełnienie z zmiennych; zachowanie rozmiaru „hug” (zawartość)
  lub „fill” (kontener) wybierane świadomie. Test: skróć i wydłuż tekst (1 słowo, 3 linie) — układ ma wytrzymać.
- Ograniczenia min/max szerokości odzwierciedlają CSS; ramki ekranów w szerokościach 375, 768, 1280 px.

## Zmienne
- Kolekcja zawiera zmienne i tryby (np. jasny/ciemny, marka A/B); zmienna może wskazywać inną (alias) tego samego
  typu. Warstwy: kolekcja prymitywów, kolekcja semantyczna z trybami, ewentualnie komponentowa (ux-design-systems).
- Typy: kolor, liczba (odstępy, promienie), tekst, wartość logiczna. Zmiennych używasz zamiast stylów lokalnych
  tam, gdzie potrzebny tryb. Surowa wartość w komponencie to błąd przeglądu.

## Porządek i przekazanie
- Strony: Okładka, Podstawy, Komponenty, Wzorce, Ekrany (stan „gotowe do wdrożenia” oznaczony).
- Nazwy warstw znaczące; brak ukrytych pozostałości; adnotacje fokusu, nazw dostępnych i regionów żywych.
- Dev Mode i Code Connect łączą komponenty Figmy z kodem; mapowanie właściwości na propsy utrzymuj z zespołem kodu.
