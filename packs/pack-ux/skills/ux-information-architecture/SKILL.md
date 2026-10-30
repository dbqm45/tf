---
name: ux-information-architecture
description: Użyj przy architekturze informacji serwisu lub aplikacji — inwentarz treści, sortowanie kart, test drzewa, taksonomia, etykiety, nawigacja, wyszukiwarka.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj, gdy trzeba uporządkować strukturę informacji w serwisie, intranecie, sklepie lub dużej aplikacji — inwentarz i audyt treści, sortowanie kart otwarte, zamknięte i hybrydowe, test drzewa (odsetek sukcesu, bezpośredniość), taksonomia i etykiety, wzorce nawigacji, metadane, mapa serwisu, projekt wyszukiwarki, test odnajdywalności i dokumentacja architektury informacji (ia-documentation.md). Nie do podstawowej struktury informacji w przepływie jednej funkcji, makiet i heurystyk (ux-feature-design), planowania badania, rekrutacji i zgód uczestników (ux-research-methods), wyglądu interfejsu (ux-visual-design), decyzji co budować (proc-product-discovery) ani modelu domeny w kodzie (ddd-strategic-analysis)."
  slowa: "architektura informacji, IA, struktura serwisu, mapa serwisu, sitemap, nawigacja, menu, kategorie, taksonomia, etykiety, nazewnictwo, sortowanie kart, card sorting, test drzewa, tree testing, inwentarz treści, audyt treści, metadane, wyszukiwarka w serwisie, nie mogą znaleźć, odnajdywalność, findability, głębokość menu, intranet, sklep z produktami"
---

# Architektura informacji — struktura, którą ludzie odnajdują

Cel: użytkownik **znajduje** to, czego szuka, i **rozumie**, gdzie jest. IA to nie wygląd menu, tylko grupy, nazwy,
hierarchia, powiązania i wyszukiwanie. Podstawy IA w przepływie jednej funkcji (słownik domeny, nawigacja, hierarchia)
są w **ux-feature-design** — ten skill wchodzi, gdy struktura jest duża albo sporna i trzeba ją **zmierzyć**. Planowanie badań,
rekrutacja i zgody uczestników: **ux-research-methods**; dla sortowania kart i testu drzewa obowiązują te same reguły.

## Procedura
1. **Cel i zakres.** Kto szuka czego (5–10 najważniejszych zadań użytkowników, z badań lub analityki wyszukiwarki
   i ścieżek), które treści są w zakresie, jaki wskaźnik się poprawi (np. odsetek zadań ukończonych w teście drzewa).
2. **Inwentarz i audyt treści** (`references/inwentarz-i-metadane.md`): lista wszystkich stron z adresem, tytułem,
   typem, właścicielem, datą aktualizacji, ruchem. Inwentarz to **liczenie**, audyt to **ocena** (aktualne,
   dokładne, potrzebne, zrozumiałe). Decyzja dla każdej: zostaw / popraw / połącz / usuń / dopisz. Skrypt lub eksport
   z CMS, nie ręczne przepisywanie.
3. **Sortowanie kart** — wybór wariantu:
   - **otwarte** — uczestnicy grupują i **sami nazywają** grupy; gdy struktury jeszcze nie ma lub jest wątpliwa;
   - **zamknięte** — przydzielają karty do **gotowych** kategorii; gdy chcesz sprawdzić lub rozbudować istniejące;
   - **hybrydowe** — gotowe kategorie plus możliwość dodania własnych.
   Karty: 30–60 pozycji, nazwy w języku użytkowników, bez słów z docelowych etykiet (nie sugeruj). Liczba uczestników
   i analiza (macierz podobieństw, dendrogram, standaryzacja nazw): `references/sortowanie-kart-i-test-drzewa.md`.
4. **Projekt struktury.** Z wyników: hierarchia (szeroka i płytka zwykle lepsza niż wąska i głęboka — sprawdź testem,
   nie regułą), nazwy kategorii z języka uczestników, **jedna** zasada grupowania na poziom (temat, zadanie,
   odbiorca, czas — nie mieszaj), obsługa treści w dwóch miejscach (odsyłacz, nie kopia). Wzorce nawigacji
   i etykiety: `references/nawigacja-i-etykiety.md`. Zapisz mapę serwisu (Mermaid lub lista wcięta).
5. **Test drzewa** na samej hierarchii (tekst, bez wyglądu): 8–10 zadań o prawdziwych celach, każde z jedną (lub
   kilkoma) poprawną ścieżką. Miary: **odsetek sukcesu** (dotarł do poprawnego węzła), **bezpośredniość**
   (dotarł bez cofania), czas, **węzeł pierwszego kliknięcia** i miejsca, w których ludzie się mylą. Czytaj razem:
   wysoki sukces przy niskiej bezpośredniości = etykiety wprowadzają w błąd, ale ludzie dochodzą metodą prób;
   niski sukces z wysoką bezpośredniością = pewny wybór złego węzła (konkurencyjne etykiety). Poprawki → ponowny test.
6. **Wyszukiwarka** (`references/nawigacja-i-etykiety.md` § Wyszukiwanie): analiza zapytań bez wyników, synonimy,
   podpowiedzi, filtry z metadanych, strona wyników z komunikatem przy braku.
7. **Test odnajdywalności** na prototypie lub działającym serwisie: zadania „znajdź…” w moderowanym lub niemoderowanym
   teście; porównanie ze wskaźnikiem bazowym. Wynik zgłoś zespołowi wg ux-research-methods.
8. **Dokumentacja** `docs/project/03-requirements/ia-documentation.md`: cel i zakres, użytkownicy i zadania, mapa
   serwisu, taksonomia i słownik etykiet (nazwa, definicja, synonimy, zakaz), schemat metadanych, reguły dodawania
   treści i właściciele, wyniki testów z datami, otwarte decyzje.

## Przykład
Wejście: „Intranet ‘Biuro24’ ma 1 200 stron, ludzie nie znajdują formularza urlopowego. Zaproponuj plan IA.”
Wynik (fragment `ia-documentation.md`):

```markdown
## Zadania i wskaźnik
Z1 „Złóż wniosek urlopowy”, Z2 „Sprawdź zasady pracy zdalnej”… Wskaźnik: ≥80% sukcesu, ≥60% bezpośrednio.
## Plan
1. Inwentarz CMS: 1 200 → po audycie ok. 700 do zachowania (decyzje w arkuszu, właściciele treści).
2. Sortowanie otwarte: 40 kart, 20 pracowników z 4 działów. 3. Hierarchia v1: 7 działów, maks. 3 poziomy.
4. Test drzewa v1: 10 zadań, 30 osób; Z1 wyszło 72% sukcesu, 38% bezpośrednio → etykieta „Absencje” myli,
   zmiana na „Urlopy i nieobecności”; test v2 → 88% / 71%.
```

## Checklista
- [ ] zadania użytkowników i wskaźnik przed projektem struktury
- [ ] inwentarz z właścicielami i decyzją dla każdej strony; audyt oparty na kryteriach
- [ ] wariant sortowania kart dobrany do sytuacji; karty bez słów sugerujących
- [ ] test drzewa z sukcesem i bezpośredniością; poprawki sprawdzone ponownie
- [ ] słownik etykiet (definicja, synonimy); jedna zasada grupowania na poziom
- [ ] wyszukiwarka i metadane zaplanowane; zapytania bez wyników monitorowane
- [ ] ia-documentation.md z wynikami testów i datami

## Materiały dodatkowe
- `references/inwentarz-i-metadane.md` — inwentarz, audyt, metadane, taksonomia; czytaj przy porządkowaniu treści.
- `references/sortowanie-kart-i-test-drzewa.md` — uczestnicy, analiza, progi i pułapki obu metod.
- `references/nawigacja-i-etykiety.md` — wzorce nawigacji, etykiety, wyszukiwanie, mapa serwisu.

## Źródła
- Tullis i Wood (2004), próba w sortowaniu kart — 20–30 osób wg wtórnych streszczeń; korelacja z „prawdziwym” wynikiem
  ok. 0,90 przy 15 i 0,95 przy 30 osobach, przypisywana NN/g (wyszukiwanie 2026-10-17, oryginałów nie otwarto
  [niezweryfikowane]).
- Definicje sukcesu i bezpośredniości w teście drzewa, progi interpretacji (różne u różnych dostawców narzędzi:
  wyszukiwanie 2026-10-17; dokumentacji Optimal Workshop nie otwarto [niezweryfikowane]).
- Pozostałe zasady (głębokość, jedna zasada grupowania, odsyłacze) to praktyka branżowa bez pojedynczego źródła [niezweryfikowane].
Opisane własnymi słowami.
