# Przegląd skilla — jak działa i jak zrobić podobny

Na pytanie „jak działa ten skill?”, „dlaczego zachowuje się tak, a nie inaczej?” albo „jak zrobić podobny?”
odpowiadasz raportem w siedmiu punktach. Najpierw czytasz całość: SKILL.md, każdy plik z `references/`, każdy skrypt
(obcy skill — najpierw `python3 factory/skill_audit.py <katalog>`, core-agent-security §4a).

Głębokość: SKILL.md krótszy niż 150 linii → zwięźle, bez tabeli anatomii; dłuższy niż 400 linii → pełna tabela
anatomii z numerami linii.

## Siedem punktów raportu
1. **Problem i cel** — jaką lukę modelu zamyka (wiedza, kroki, format, granice) i po czym poznać, że działa.
2. **Pozycja w łańcuchu** — wejście (plik, pytanie, stan repo) → wyjście (plik, raport, decyzja); który skill jest
   przed nim, który po nim.
3. **Anatomia** — sekcje z zakresem linii i odpowiedzią „co się zepsuje bez tej sekcji”:

   | Sekcja | Linie | Rola | Co się zepsuje bez niej |
   |---|---|---|---|

4. **3–5 mechanizmów napędzających** z oznaczeniem miejsc o dużej dźwigni: opis (reguła wyboru), `allowed-tools`,
   twarde zasady, schemat wyjścia, bramki samosprawdzenia, skrypty.
5. **Decyzje projektowe** — każda z odrzuconą alternatywą („odmowa zamiast domysłu, bo …”).
6. **Zmiany łatwe / średnie / trudne** — trudne to zmiany nazw plików, sekcji i statusów, od których zależą dalsze
   skille, hooki albo skrypty.
7. **Droga od polecenia do skilla** — jak zamienić jednorazowe polecenie na skill: luka zmierzona bez skilla,
   scenariusze ewaluacji, minimalna treść (procedura w SKILL.md głównym).

## Przykład (skrót)
Wejście: „Jak działa skill przeglądu PR, który w CI zostawia komentarze?”
Wynik: (1) zamyka lukę „model komentuje styl zamiast ryzyk”; (2) wejście: diff PR + plan kroku, wyjście: raport
z linią `Werdykt: approve|request-changes`; (4) dźwignia: stały znacznik werdyktu sprawdzany skryptem w CI i zakaz
pytań do człowieka; (5) odrzucono komentarze inline dla każdej uwagi (szum) na rzecz jednego raportu; (6) trudna
zmiana: nazwa pola `Werdykt`, bo czyta ją krok bramki w pipeline.

Kurs 10xDevs, ed. 3 (2026), moduł 1, lekcja 2 — materiał szkoleniowy (dostęp 2026-10-09). Opisane własnymi słowami.

## Odchudzanie
- **Test „no-op” zdanie po zdaniu:** czy zdanie zmienia zachowanie względem domyślnego modelu? Jeśli nie, usuwasz
  całe zdanie (pomiar z 2026-10-30: dwa skille pack-it odchudzone o 5–12% słów bez utraty wyniku).
- **Instrukcje pozytywne zamiast zakazów:** zakaz wnosi zakazane do kontekstu; pisz, co zrobić.
- **Pojęcia po nazwie,** gdy model je zna (np. zapachy kodu Fowlera), zamiast definicji.
- **Skill-router** wywoływany ręcznie, który dopiero ładuje cięższy skill.
- **Koszt opisów wszystkich skilli** widocznych w sesji to stały narzut każdego zapytania: rzadko wywoływane
  automatycznie skille dostają `disable-model-invocation`, gdy człowiek i tak wywołuje je po nazwie (decyzja
  z pomiarem trafień hooka i ewaluacją, nie z intuicji).
- Specyfikacja w skillu bez ścieżek plików i fragmentów kodu projektu — starzeją się, a agent i tak do nich dotrze.
- Każde cięcie przechodzi scenariusze i bramkę; płatny pomiar za zgodą człowieka.
