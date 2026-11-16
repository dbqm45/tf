# Playbook zgłoszeń: jeden incydent, wiele zegarów

Spis treści: zasady · oś czasu · szablon · pułapki. Technika reagowania — `.claude/skills/ops-security-operations/SKILL.md`.
RODO (kiedy zgłosić, treść zawiadomienia) — `.claude/skills/arch-privacy-compliance/SKILL.md`. Nie jest poradą prawną.

## Zasady
1. **Jedna osoba odpowiada za zegary** (koordynator zgłoszeń), z zastępcą; prawnik i IOD w pierwszej godzinie.
2. **Godzina 0** to moment uzyskania wiedzy; zapisz, kto, kiedy i na jakiej podstawie ją ustalił. Klasyfikacja (poważny? dane
   osobowe? produkt?) nie może opóźniać pierwszego sygnału — zgłoś z zastrzeżeniem i koryguj.
3. **Jedna oś czasu, jedno źródło faktów**, z której kopiuje się treść do każdego zgłoszenia, żeby zgłoszenia nie
   przeczyły sobie. Różni adresaci chcą różnych pól, fakty są te same.
4. **Wysyłasz tyle, ile masz.** Brakujące elementy uzupełniasz w kolejnym etapie, nie czekasz do pełnej wiedzy.
5. **Adresaci i kanały przygotowane przed incydentem** (formularze, konta, certyfikaty do platform), także poza godzinami pracy.

## Oś czasu [przykład]
| Czas | Działanie | Właściciel |
|---|---|---|
| T0 | stwierdzenie, zapis godziny, klasyfikacja wstępna wg tabeli decyzyjnej | koordynator |
| T0+4 h | DORA: wstępne zgłoszenie, jeśli sklasyfikowano jako poważny (cap 24 h) | podmiot finansowy |
| T0+24 h | NIS2 wczesne ostrzeżenie; CRA wczesne ostrzeżenie (produkt) | koordynator |
| T0+72 h | NIS2 zgłoszenie; RODO art. 33 do UODO; CRA zgłoszenie; DORA raport pośredni (72 h od wstępnego) | koordynator, IOD |
| po poprawce | CRA raport końcowy podatności w 14 dni | PSIRT |
| ~1 miesiąc | NIS2, CRA incydent, DORA raporty końcowe | koordynator |

## Szablon zgłoszenia (wspólny rdzeń)
Kto zgłasza i kontakt · godzina wykrycia i uzyskania wiedzy · co zaszło (fakty, bez spekulacji) · dotknięte systemy, usługi,
produkty i wersje · dane osobowe (kategorie, liczba — szacunek) · skutek transgraniczny · podejrzenie czynu zabronionego ·
podjęte środki · wskaźniki (IOC, o ile bezpieczne do przekazania) · status i następny raport · kto już powiadomiony.

## Pułapki
- Zegar RODO administratora a procesora: procesor zawiadamia administratora; 72 h liczy administrator od swojej wiedzy.
- Dostawca ICT musi dać klientowi czas na jego zegar — ustal w umowie godziny powiadomienia znacznie krótsze niż 24 h.
- Zgłoszenie do organu nie zwalnia z powiadomienia klientów, ubezpieczyciela i stron umów (kary umowne).
- Uzupełnianie zgłoszeń sprzecznymi liczbami; wersjonuj treść i notuj zmiany ustaleń.
- Ćwicz tabletopem raz w roku; mierz czas od T0 do każdego zgłoszenia.
