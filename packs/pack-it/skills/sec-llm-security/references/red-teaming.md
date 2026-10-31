# Red teaming funkcji LLM

Tylko za zgodą właściciela systemu, na środowisku testowym lub z ustalonym zakresem; bez ataków na cudze usługi.

## Scenariusze minimalne
1. Bezpośredni jailbreak i obejście polityki treści.
2. Pośredni injection: instrukcja w mailu, stronie, PDF, wyniku narzędzia, dokumencie RAG, opisie narzędzia MCP.
3. Eksfiltracja: czy dane z kontekstu opuszczą system przez obraz, link, narzędzie lub mail.
4. Nadużycie narzędzi: wywołanie z cudzym identyfikatorem (IDOR), argumenty spoza schematu, łańcuch narzędzi.
5. Wyciek system promptu i danych innych sesji lub najemców.
6. Zużycie: pętle, bardzo długie wejścia, koszt na użytkownika.
7. Przeniesienie uprawnień: czy agent działa z uprawnieniami użytkownika, nie szerszymi.
Kryterium sukcesu jest zachowaniem systemu (czy akcja się wykonała, czy dane wyszły), nie treścią odpowiedzi.

## Narzędzia
- **garak** (NVIDIA, Apache 2.0): skaner z biblioteką sond i detektorów (injection, jailbreaki, wycieki); dobry jako
  bazowy skan modelu i regresja. Praca naukowa: arXiv:2406.11036.
- **PyRIT** (Microsoft AI Red Team): szkielet do własnych kampanii, także wieloturowych (np. Crescendo, TAP).
- Badanie porównawcze (arXiv:2410.16527) wskazuje na problemy z rzetelnością wykrywania udanych ataków w takich
  skanerach: wyniki weryfikuj ręcznie na próbce. [wnioski ze streszczenia wyszukiwania 17.10.2026, bez lektury pracy]
- Narzędzia nie zastępują testów aplikacyjnych (uprawnienia, narzędzia, egress): to scenariusze własne.

## MITRE ATLAS
Baza taktyk i technik ataków na systemy AI (odpowiednik ATT&CK). Używaj jako słownika do raportu i mapowania
scenariuszy; identyfikatory (np. AML.T0051 LLM Prompt Injection, AML.T0054 LLM Jailbreak) [niezweryfikowane:
z wtórnego źródła, sprawdź w atlas.mitre.org przed cytowaniem].

## Z testu do ewaluacji
Każdy udany atak: zapis (wejście, kontekst, skutek) → przypadek w zestawie `ai-evals` z asercją na zachowaniu
(brak wywołania narzędzia, brak danych w wyjściu) → bramka w CI przy zmianie modelu, promptu lub narzędzi.

## Ataki adaptacyjne
Obrona sprawdzona tylko stałą listą ataków mówi mało. Nasr, Carlini i in., „The Attacker Moves Second” (arXiv
2510.09023, 2025-10, USENIX Security 2026): adaptacyjne ataki (optymalizacja, RL, wyszukiwanie, ludzie) obeszły
12 obron z wynikiem zwykle powyżej 90%, choć autorzy obron raportowali bliskie zera; na AgentDojo stały szablon
osiągnął 28%, a wyszukiwanie adaptacyjne 99%. Wnioski:
- wynik „blokuje 99% z listy” nie jest dowodem odporności — testuj atakującym, który zna obronę i iteruje;
- **AgentDojo** (NeurIPS 2024) to gotowa uprząż: sędzia sprawdza stan środowiska po przebiegu, a nie tekst modelu,
  więc sam nie da się wstrzyknąć;
- odporność daje architektura (wzorce izolacji, uprawnienia — `wzorce-projektowe-agentow.md`), filtr jest warstwą
  dodatkową.
