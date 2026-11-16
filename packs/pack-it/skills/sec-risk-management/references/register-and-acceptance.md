# Rejestr ryzyk i akceptacja ryzyka

Spis treści: 1. Pola rejestru · 2. Szablon wiersza · 3. Zapis akceptacji · 4. Uprawnienia · 5. Wygaśnięcie i przegląd

## 1. Pola rejestru
ID · tytuł · opis (przyczyna → zdarzenie → skutek) · aktywo/proces · kategoria (dane, dostępność, dostawca, ludzie,
zgodność) · źródło (model zagrożeń, audyt, incydent, dostawca) · właściciel ryzyka · prawdopodobieństwo i wpływ
(inherentne) · ocena inherentna · istniejące kontrole · opcja postępowania · plan (zadania, właściciele, terminy) ·
prawdopodobieństwo i wpływ rezydualne · ocena rezydualna · status (otwarte, w postępowaniu, utrzymane, zamknięte) ·
data ostatniego przeglądu i następnego · powiązania (ID kontroli w macierzy, ADR, zgłoszenie).

## 2. Szablon wiersza [przykład]
| ID | Opis | Właściciel | Inh. | Opcja | Plan | Rez. | Status | Następny przegląd |
|---|---|---|---|---|---|---|---|---|
| R-017 | Przejęcie konta partnera w panelu bez MFA → wyciek zamówień | dyr. sprzedaży | 16 | modyfikacja + utrzymanie przejściowe | MFA do 2027-03-31 (Z-212) | 9 | w postępowaniu | 2027-01-15 |

Zasady: jeden właściciel (osoba, nie zespół); ryzyko bez planu i terminu nie jest „w postępowaniu”; zamknięcie ryzyka
wymaga dowodu (test, skan, umowa), nie deklaracji.

## 3. Zapis akceptacji ryzyka (risk acceptance record)
Nagłówek: `Akceptacja ryzyka R-017` · wersja · data.
- Ryzyko (opis i ocena inherentna/rezydualna, FAIR: przedział straty rocznej, jeśli policzono).
- Dlaczego nie postępujemy w pełni teraz (koszt, termin, zależność) i **alternatywy rozważone**.
- Kontrole kompensujące i ich dowód.
- Warunki unieważnienia (incydent, zmiana zakresu, nowa podatność, zmiana apetytu).
- Właściciel ryzyka akceptujący (imię, rola, uprawnienie), data decyzji, **ważne do** (data), osoba przeglądu.
- Konsultowani i informowani (CISO, prawnik, IOD, finanse).
- Podpis akceptującego. Zapis i identyfikacja podpisu wg procedur firmy; agent przygotowuje projekt, nie podpisuje.

## 4. Uprawnienia do akceptacji [przykład, ustala zarząd w kryteriach]
| Ocena rezydualna | Kto akceptuje | Maks. okres |
|---|---|---|
| niska | kierownik zespołu | 24 mies. |
| średnia | dyrektor obszaru | 12 mies. |
| wysoka | członek zarządu + CISO informowany | 6 mies. |
| krytyczna | nie akceptujemy; postępowanie albo unikanie, wyjątkowo zarząd | — |
Zasada rozdziału: osoba, która zarządza kontrolą lub wnioskuje o wyjątek, nie jest jedynym akceptującym.

## 5. Wygaśnięcie i przegląd
Kalendarz wygasających akceptacji (alert 30 dni przed). Po wygaśnięciu ryzyko wraca do postępowania; przedłużenie
to nowa decyzja z aktualnymi danymi, a nie automatyczny zapis. KRI „akceptacje po terminie” raportowane kwartalnie.
Akceptacja wyjątku od polityki bezpieczeństwa jest tym samym zapisem (sec-governance-compliance: wyjątki w macierzy).
