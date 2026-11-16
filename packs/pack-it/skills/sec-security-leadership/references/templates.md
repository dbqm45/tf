# Szablony: strategia, raport dla zarządu, RACI

Spis treści: 1. Jednostronicowa strategia · 2. Raport dla zarządu · 3. KPI i KRI · 4. RACI · 5. Uświadamianie

## 1. Jednostronicowa strategia
```markdown
Security leadership: <firma> — profil docelowy <rok>, decyzje do podjęcia: <n>
1. Cele biznesu (3–5) i „klejnoty”: <co musi działać, jakie dane>
2. Stan obecny: profil bieżący CSF 2.0 wg funkcji (Govern … Recover), 3 największe luki z dowodem
3. Stan docelowy: profil docelowy za 3 lata i dlaczego taki poziom (klient, regulacja, apetyt)
4. Filary (3–5): wynik biznesowy · inicjatywa · miernik z progiem · właściciel
5. Mapa drogowa: 0–6 / 6–18 / 18–36 miesięcy; zależności; punkty decyzji
6. Budżet: koszt całkowity (przedział) · redukcja ryzyka · alternatywa „bez zmian” i „ubezpieczenie”
7. Czego nie robimy i dlaczego · główne ryzyka strategii
8. Decyzje do podjęcia przez zarząd (z terminem)
```
Zasady: strona A4, bez żargonu technicznego, każda liczba z przedziałem i źródłem. Przegląd co rok lub po dużym incydencie
albo przejęciu.

## 2. Raport dla zarządu (kwartalny, 1 strona + załączniki)
1. **Werdykt jednym zdaniem** (np. „ryzyko w granicach apetytu, jedno wyjątkowe do decyzji”).
2. **Ryzyka względem apetytu:** 3–5 największych w języku skutków (zł, dni przestoju, kontrakty); trend (↑ → ↓).
3. **KRI** z progami (patrz niżej) — tylko te, które przekroczyły próg lub zbliżają się do niego.
4. **KPI programu:** postęp inicjatyw z mapy drogowej, budżet wykonany, kluczowe terminy.
5. **Zdarzenia i wnioski:** incydenty istotne dla zarządu, bliskie trafienia, co zmieniono.
6. **Decyzje do podjęcia** i prośby (budżet, akceptacja ryzyka, mandat) — z rekomendacją i konsekwencją odmowy.
7. **Zmiany otoczenia:** klienci, regulatorzy, przejęcia, nowe technologie (w tym AI).

Apetyt na ryzyko to **oświadczenie zatwierdzone przez zarząd**, nie CISO, np. „nie akceptujemy ryzyka krytycznego
dłużej niż 90 dni bez planu; przestój systemu przychodowego ponad 4 h jest poza tolerancją”. Sformułowanie i procedura
akceptacji — sec-risk-management.

Pułapki: liczba zablokowanych ataków jako sukces (rośnie z szumem); kolorowa mapa cieplna bez skutków; 40 slajdów
metryk SOC-a; zaskakiwanie zarządu złą wiadomością na sali — wstępnie omów z przewodniczącym.

## 3. KPI i KRI
| | KPI | KRI |
|---|---|---|
| pytanie | czy program robi to, co zaplanowano | czy ryzyko rośnie |
| przykłady [przykład] | % systemów krytycznych w EDR; inicjatywy w terminie; pokrycie ćwiczeniami | konta uprzywilejowane bez MFA; krytyczne podatności >7 dni na zasobach z internetu; średni czas wykrycia; wygasłe akceptacje ryzyka |
| próg i właściciel | cel + właściciel | próg alarmowy + właściciel + działanie po przekroczeniu |
Metryka bez progu i właściciela nie trafia do raportu. Mało liczb, stała definicja, ten sam miernik co kwartał.

## 4. RACI (R wykonuje, A odpowiada, C konsultowany, I informowany) [przykład]
| Decyzja | Zarząd | CISO | IT/produkt | Prawny | Audyt wew. |
|---|---|---|---|---|---|
| apetyt na ryzyko | A | R | C | C | I |
| akceptacja ryzyka powyżej progu | A | C | R (właściciel) | C | I |
| ogłoszenie kryzysu | I | R | C | C | I |
| decyzja o okupie | A | C | C | R (opinia) | I |
| kontakt z regulatorem | A | C | I | R | I |
| niezależna ocena programu | I | I | I | I | A/R |
Jedna osoba **A** na wiersz. Audyt wewnętrzny nie należy do CISO (niezależność wg modelu trzech linii).

## 5. Uświadamianie — mierniki zachowań
Odsetek pracowników zgłaszających phishing (nie tylko klikających), czas od otrzymania do zgłoszenia, powtarzalni
klikający (wsparcie, nie kara), użycie menedżera haseł i MFA, liczba zgłoszeń błędów bez obaw o winę. Szkolenie krótkie
i kontekstowe (rola: finanse, programiści, zarząd), bo wymaga innych scenariuszy. Symulacje: zatwierdzone przez zarząd
i HR, zgodne z prawem pracy i ochroną danych (konsultacja z prawnikiem i IOD [niezweryfikowane] dla danej jurysdykcji),
zbiorcze wyniki zamiast nazwisk.
