---
name: ai-prompt-engineering
description: Użyj przy pisaniu i poprawianiu promptów — struktura, tagi XML, przykłady few-shot, myślenie, długi kontekst, szablony i wersje, układ pod cache, migracja modelu.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy piszesz, poprawiasz lub przenosisz prompt systemowy albo szablon promptu dla modelu — struktura (rola, kontekst, zadanie, ograniczenia, format wyjścia, przykłady), tagi XML, dobór przykładów few-shot, łańcuch myślenia i rozszerzone lub adaptacyjne myślenie oraz kiedy go nie używać, prefill i structured outputs, układ długiego kontekstu (dokumenty na górze, pytanie na końcu), szablony i wersjonowanie promptów (rejestr), układ przyjazny cache (stały prefiks), regresja promptu przez ewaluacje, migracja promptu na nowszy model, typowe błędy (niejednoznaczność, sprzeczne instrukcje, nadmierne ograniczenia). Nie do kontraktu wyjścia, SDK i pętli narzędziowej (eng-llm-features), budowy zbiorów i graderów (ai-evals), reguł cache i doboru modelu (core-cost-control) ani instrukcji dla agenta-programisty (core-agent-instructions)."
  slowa: "prompt, prompt systemowy, prompt engineering, inżynieria promptów, few-shot, przykłady w prompcie, tagi xml, chain of thought, łańcuch myślenia, extended thinking, adaptive thinking, prefill, długi kontekst, szablon promptu, wersjonowanie promptów, rejestr promptów, prompt caching, stały prefiks, migracja promptu, model ignoruje instrukcję, sprzeczne instrukcje, poprawić prompt"
---

# Inżynieria promptów

Prompt to kod z niedeterministycznym wykonawcą: zmienia się go hipotezą i sprawdza pomiarem. Zanim zaczniesz,
miej kryterium sukcesu i sposób jego sprawdzenia (`ai-evals`); bez tego „poprawa” jest wrażeniem. Nie każda porażka
jest problemem promptu — czasem pomaga zmiana modelu, schematu wyjścia lub narzędzia (**eng-llm-features**, kontrakt
wyjścia i SDK). Nazwy modeli i parametrów API sprawdzasz w dokumentacji dostawcy (core-grounding); dla Claude:
wbudowany w Claude Code skill `claude-api` (aktualizuje go Anthropic). Stan z 2026-10-20 i szczegóły: `references/techniki-i-migracja.md`.

## Procedura
1. **Zdiagnozuj, co się psuje**, na 5–10 konkretnych złych wyjściach: zła treść, zły format, pominięta instrukcja,
   nadgorliwość, halucynacja. Każdy objaw ma inną poprawkę (tabela niżej). Bez przykładów porażek nie zaczynaj.
2. **Ułóż strukturę** (kolejność od stałego do zmiennego): rola i cel → kontekst (dlaczego) → zadanie → ograniczenia
   → format wyjścia → przykłady → dane wejściowe. Rola w jednym zdaniu wystarcza. Instrukcja z powodem („nie używaj
   wielokropka, bo tekst czyta syntezator mowy”) działa lepiej niż goły zakaz.
3. **Oddziel części tagami XML**, gdy prompt miesza instrukcje, kontekst, przykłady i dane: `<instructions>`,
   `<context>`, `<example>` w `<examples>`, `<document>`. Spójne nazwy tagów w całym prompcie; dane użytkownika zawsze w tagu,
   żeby model nie wziął ich za polecenia (core-agent-security).
4. **Powiedz, co ma być, a nie czego nie ma.** Zamiast „bez markdownu” → „odpowiedź w zwykłych akapitach”. Konkretny
   format wyjścia z opisem; gdy kod czyta wynik, użyj structured outputs ze schematem, nie prośby w prompcie.
5. **Przykłady (few-shot):** 3–5, **trafne** (jak prawdziwe wejścia), **zróżnicowane** (w tym brzegowe, żeby model nie
   złapał niezamierzonego wzorca), w tagach `<example>`. Przykład ustawia wzorzec bardzo silnie — jeśli wszystkie
   zaczynają się tak samo, odpowiedzi też. Przykłady do promptu bierz z puli rozłącznej ze zbiorem ewaluacji.
6. **Myślenie.** Zadania wieloetapowe, matematyka, analiza: włącz myślenie modelu (adaptacyjne, sterowane parametrem
   `effort`; starsze modele: rozszerzone z budżetem) albo poproś o rozumowanie przed odpowiedzią i wynik w osobnym
   tagu `<answer>`. **Nie używaj** przy prostej ekstrakcji, klasyfikacji i formatowaniu — dodaje koszt i opóźnienie
   bez zysku; sprawdź ewaluacją, czy poprawia wynik.
7. **Długi kontekst (20 tys. tokenów i więcej):** dokumenty na górze, każdy w `<document>` z `<source>`; instrukcje i
   pytanie **na końcu**; przy gęstych dokumentach poproś najpierw o wypisanie cytatów istotnych dla pytania.
8. **Układ pod cache:** część stała (instrukcje, narzędzia, przykłady, dokumenty) na początku, zmienna (data, dane
   użytkownika, pytanie) na końcu. Cache pasuje po dokładnym prefiksie w kolejności narzędzia → system → wiadomości;
   znacznik czasu lub identyfikator użytkownika w prefiksie zeruje trafienia. Zasady, minimalne długości i ceny: core-cost-control i `references/techniki-i-migracja.md`.
9. **Szablony i wersje.** Prompt w pliku lub rejestrze, nie sklejany stringami po kodzie: szablon z nazwanymi
   zmiennymi, wersja (SemVer lub data), opis zmiany, przypięty model. Zmianę wersji zawsze przepuszczasz przez zestaw
   regresyjny (`ai-evals`); cykl życia w produkcji: ai-mlops.
10. **Jedna zmiana na raz.** Zmień jedną rzecz, uruchom ewaluację na tych samych przypadkach, porównaj z poprzednią
    wersją; zapisz wynik w opisie zmiany. Zmiana prompt + model naraz nie mówi, co zadziałało.
11. **Migracja na nowszy model:** przeczytaj przewodnik migracji dostawcy, uruchom stary prompt na nowym modelu **bez
    zmian** i zmierz; usuń obejścia (prefill, agresywne CRITICAL/MUST, ręczny budżet myślenia, prośby o „więcej starań”),
    bo nowsze modele silniej słuchają promptu i bywają nadgorliwe; potem dopiero tuning.

## Objaw → poprawka
| Objaw | Zwykła przyczyna | Poprawka |
|---|---|---|
| ignoruje instrukcję | ginie w długim prompcie, sprzeczność | przenieś na początek lub koniec, usuń konflikt, podaj powód |
| zmienny format | opis zamiast schematu | structured outputs lub przykład |
| zbyt dosłowny / zbyt gorliwy | zakazy, wielkie litery, „zawsze” | normalny ton, powód zamiast nacisku |
| odpowiedzi jak przykłady | jeden wzorzec w przykładach | zróżnicuj, zmniejsz liczbę |
| gubi szczegóły w dokumentach | pytanie na górze, brak tagów | dokumenty na górze, pytanie na końcu, cytaty |
| wolno i drogo | myślenie przy prostym zadaniu | najpierw tańszy model i niższy effort, potem prompt |
| pewna odpowiedź bez podstaw | presja, by odpowiedzieć zawsze | pozwól na „nie wiem”, cytaty przed wnioskami (core-grounding) |
| wynik minimalny, „generyczny” | ogólna prośba; nowe modele robią dokładnie to, o co proszono | napisz zakres i ambicję wprost („pełna wersja, wykraczająca poza podstawy”) |
| dwie instrukcje się wykluczają | prompt rósł latami | priorytety wprost lub usuń jedną |

## Przykład
**Wejście:** prompt klasyfikujący zgłoszenia, 1 800 tokenów, data i imię klienta w pierwszej linii, „MUSISZ ZAWSZE
zwrócić JSON”, 30 błędnych etykiet na 200 przypadków, cache nie trafia.
**Wynik:**
- stały prefiks (instrukcje, 4 zróżnicowane `<example>`, definicje kategorii) na początku; data i `<ticket>` z treścią zgłoszenia na końcu → cache działa;
- `MUSISZ ZAWSZE JSON` → structured outputs ze schematem (enum kategorii); w prompcie jedno zdanie o kategoriach brzegowych z powodem;
- brak myślenia (klasyfikacja), tańszy model; wersja `zgloszenia-klasyfikator@1.3.0`, opis zmiany;
- ewaluacja 200 przypadków przed i po: 170/200 → 186/200 (85% → 93%); regresyjny zestaw bez nowych porażek.

## Checklista
- [ ] kryterium sukcesu i zestaw przypadków przed zmianą; objawy opisane na przykładach
- [ ] struktura: rola, kontekst z powodem, zadanie, ograniczenia pozytywnie, format, przykłady 3–5 zróżnicowanych
- [ ] dane i dokumenty w tagach XML; długi kontekst: dokumenty na górze, pytanie na końcu
- [ ] myślenie tylko tam, gdzie ewaluacja pokazuje zysk; format wyjścia przez schemat, nie prefill
- [ ] stały prefiks na początku, zmienne na końcu; brak czasu i identyfikatorów w prefiksie
- [ ] szablon z wersją, przypięty model, zmiana przepuszczona przez ewaluacje, jedna zmiana naraz
- [ ] migracja: stary prompt bez zmian na nowym modelu, usunięte obejścia, dopiero potem tuning

## Źródła
- Anthropic, „Prompting best practices” (platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices, odczyt 2026-10-17):
  przykłady 3–5, trafne i zróżnicowane w `<example>`; tagi XML; dokumenty na górze, pytanie na końcu (do ok. 30% poprawy w testach); adaptive thinking i `effort`; prefill na ostatniej turze nieobsługiwany od modeli 4.6; łagodzenie agresywnego języka.
- Anthropic, „Prompt engineering overview” (ta sama domena, odczyt 2026-10-17): kryteria sukcesu i ewaluacje przed promptowaniem.
- Anthropic, „Prompting Claude Opus 5.5”, „… Sonnet 5.5”, „… Haiku 5.5”, „Reduce hallucinations”, „Increase output
  consistency” (platform.claude.com, odczyt 2026-10-20): effort i `max_tokens` w modelach 5.5, wczesne kończenie pracy
  agenta, prawo do „nie wiem”, structured outputs zamiast prośby o format.
- Anthropic, „Prompt caching” (platform.claude.com/docs/en/build-with-claude/prompt-caching, odczyt 2026-10-17): kolejność prefiksu, TTL 5 min i 1 godz., unieważnianie.
- OpenAI, przewodnik promptowania (developers.openai.com/api/docs/guides/prompting) — wyniki wyszukiwania z 2026-10-17: rola w wiadomości systemowej, przykłady w blokach, cache po prefiksie; strona nie została otwarta bezpośrednio [niezweryfikowane]. Przypinanie wersji modelu — zalecenie znane z drugiego źródła [niezweryfikowane].

Opisane własnymi słowami.
