---
name: ux-design-systems
description: Użyj przy systemie projektowym — warstwy tokenów, nazwy, format DTCG, Style Dictionary, komponenty, Storybook, wersje, wycofywanie, motywy, współtworzenie.
metadata:
  przeglad: 2027-10-17
  katalog: "Użyj przy budowie i utrzymaniu systemu projektowego (design system) — warstwy tokenów (prymitywne, semantyczne, komponentowe), konwencja nazw, format Design Tokens (DTCG) i Style Dictionary, komponenty i warianty w Figmie i w kodzie, dokumentacja (Storybook, zasady użycia, rób/nie rób), dostępność wbudowana w komponent, testy regresji wizualnej, wersjonowanie biblioteki, changelog i polityka wycofywania, model współtworzenia, zarządzanie (governance), metryki adopcji, wiele marek i motywów. Nie do audytu dostępności (ux-accessibility), decyzji o wyglądzie, kontraście i ruchu (ux-visual-design), CSS i zmiennych CSS w kodzie (fe-css), reguł numerowania wersji (core-semver) ani struktury aplikacji frontendowej (fe-architecture)."
  slowa: "system projektowy, design system, biblioteka komponentów, tokeny, design tokens, DTCG, Style Dictionary, nazewnictwo tokenów, motyw, ciemny motyw, wiele marek, white label, Storybook, dokumentacja komponentów, wycofanie komponentu, deprecation, breaking change w bibliotece, changelog, adopcja, governance, współtworzenie, zmienne Figma do kodu, regresja wizualna, Chromatic"
---

# System projektowy — tokeny, komponenty, utrzymanie

Cel: wspólny język projektu i kodu, który zespoły chcą używać i który da się rozwijać bez łamania produktów.
System to produkt z odbiorcami (zespoły), wersjami i mapą drogi. Decyzje o wyglądzie (kontrast, skala, ruch):
**ux-visual-design**; wdrożenie zmiennych w CSS: **fe-css**; reguły numerów wersji: **core-semver**; struktura aplikacji:
**fe-architecture**.

## Procedura
1. **Wejście.** Ile zespołów i produktów, jakie platformy (web, iOS, Android), ile marek i trybów, kto utrzymuje, co
   już istnieje (audyt: ile unikalnych kolorów, rozmiarów, wariantów przycisku w kodzie). Mały system z jednym zespołem
   nie potrzebuje tej samej struktury co system dla sześciu — zaczynaj od tego, co się powtarza.
2. **Warstwy tokenów** (szczegóły i nazwy: `references/tokeny.md`):
   - **prymitywne** — surowe wartości bez znaczenia (`color.blue.600`, `space.4`);
   - **semantyczne** — rola, wskazuje na prymityw (`color.text.primary`, `color.action.bg`); to je zmieniają motywy;
   - **komponentowe** — tylko gdy komponent musi odbiegać od roli (`button.primary.bg`), zawsze wskazuje na semantyczny.
   Odwołania idą w jedną stronę (komponent → semantyczny → prymityw). Komponenty nie używają prymitywów.
3. **Nazwy.** Wzór `kategoria.właściwość.rola.stan` (`color.border.input.focus`); nazwa opisuje rolę, nie wartość
   (nie `color.red`, tylko `color.feedback.error`); jedna konwencja wielkości liter; nazwy w kodzie i w Figmie
   identyczne (z dokładnością do separatora).
4. **Format i potok.** Źródło prawdy w formacie DTCG (`$value`, `$type`, aliasy `{color.blue.600}`), plik
   `*.tokens.json`; z niego Style Dictionary generuje CSS, JS/TS, iOS, Android. Co jest źródłem — Figma czy repozytorium
   — ustal raz; druga strona jest generowana albo synchronizowana jednokierunkowo. Status specyfikacji i wersje:
   `references/tokeny.md`.
5. **Komponenty.** Najpierw wzorce z produktów (zasada trzech użyć), potem komponent z API: warianty (rodzaj, rozmiar),
   stany, sloty, zasady użycia. Nazwy wariantów i właściwości zgodne w Figmie i kodzie. Dostępność w komponencie, nie
   „po stronie użytkownika”: rola i nazwa dostępna, klawiatura, fokus widoczny, cele dotyku, kontrast w obu motywach.
6. **Dokumentacja.** Storybook (historyjki dla każdego wariantu i stanu, panel dostępności), strona zasad: kiedy użyć
   i kiedy nie, rób/nie rób z obrazkami, treść przycisków, kod do skopiowania, dostępność, zmiany. Format:
   `references/komponenty-i-dokumentacja.md`.
7. **Testy.** Test dostępności automatyczny (axe) na każdej historyjce — wyłapuje tylko część problemów, resztę ręcznie
   (qa-exploratory-manual); zrzuty wizualne historyjek w CI z progiem różnicy i zatwierdzaniem zmian przez człowieka.
8. **Wersje i zmiany.** SemVer biblioteki (core-semver): publiczne API to komponenty, ich propsy, nazwy tokenów
   i klasy. Zmiana wartości tokenu wizualna = minor lub patch wg ustalonej reguły; usunięcie lub zmiana nazwy
   = major. Polityka wycofywania i changelog: `references/wersjonowanie-i-governance.md`.
9. **Współtworzenie i zarządzanie.** Kryteria przyjęcia (przydatne wielu zespołom, unikalne), droga zgłoszenia,
   dyżur przeglądu, kto decyduje. Metryki adopcji: `references/wersjonowanie-i-governance.md`.
10. **Wiele marek i motywów.** Motyw = wymiana wartości warstwy semantycznej; komponenty bez zmian. Zakres, nazwy
    i pułapki: `references/tokeny.md` § Motywy i marki.

## Przykład
Wejście: „Trzy produkty, dwie marki, ciemny motyw; przycisk ma dziś 11 odcieni niebieskiego w kodzie.”
Wynik (fragment `tokens/semantic.tokens.json`):

```json
{
  "color": {
    "action": {
      "bg": {
        "$type": "color",
        "$value": "{color.blue.600}",
        "$description": "Tło głównego przycisku"
      }
    }
  }
}
```

Motyw ciemny nadpisuje `color.action.bg` na `{color.blue.400}`; marka B na `{color.teal.600}`. Komponent
`Button` czyta wyłącznie `color.action.bg`. Plan: audyt 11 odcieni → 1 token semantyczny; wydanie 1.0.0 z
oznaczeniem starych zmiennych jako przestarzałe (do 2.0.0, okres przejściowy 2 wydania minor); test zrzutowy
historyjek `Button` w obu motywach i obu markach (6 zrzutów).

## Checklista
- [ ] trzy warstwy tokenów, odwołania w jedną stronę, komponenty bez prymitywów
- [ ] nazwy opisują rolę, jedna konwencja, te same w Figmie i w kodzie
- [ ] źródło prawdy tokenów ustalone, potok generuje platformy (DTCG + Style Dictionary lub odpowiednik)
- [ ] każdy komponent: warianty, stany, dostępność, zasady użycia, historyjki
- [ ] testy dostępności i zrzutowe w CI; zmiany zrzutów zatwierdza człowiek
- [ ] SemVer, changelog, polityka wycofywania z okresem przejściowym i migracją
- [ ] model współtworzenia i metryki adopcji opisane

## Materiały dodatkowe
- `references/tokeny.md` — warstwy, nazwy, DTCG i Style Dictionary (status), motywy i marki.
- `references/komponenty-i-dokumentacja.md` — komponenty w Figmie i kodzie, Storybook, dostępność, testy zrzutowe.
- `references/wersjonowanie-i-governance.md` — SemVer biblioteki, wycofywanie, współtworzenie, metryki.

## Źródła
- Design Tokens Community Group, *Design Tokens Format Module 2025.10* — Final Community Group Report, 2025-10-28:
  w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/ (dostęp 2026-10-17).
- Design Tokens CG, „Design Tokens specification reaches first stable version” (2025-10-28) i FAQ designtokens.org
  (dostęp 2026-10-17).
- Style Dictionary — v5 przyjmuje DTCG 2025.10 jako format bazowy [niezweryfikowane, wtórne źródło: zeroheight Help
  Center, dostęp 2026-10-17; numer najnowszej wersji [niezweryfikowane]].
- GOV.UK Design System: Contribution criteria, Propose a component or pattern (dostęp 2026-10-17).
- Figma Help Center: Guide to variables, Explore component properties (dostęp 2026-10-17).
- Storybook: „Automate accessibility tests with Storybook” (axe-core wykrywa do 57% problemów WCAG, wg Storybook;
  dostęp 2026-10-17); dokumentacja Chromatic (dostęp 2026-10-17).
Opisane własnymi słowami.
