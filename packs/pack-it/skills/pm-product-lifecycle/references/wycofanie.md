# Wycofanie produktu lub modułu

## Kryteria go/no-go
| Kryterium | Pytanie | Dane |
|---|---|---|
| Użycie | ilu klientów i jak często używa; czy to kluczowi klienci | analityka, lista klientów z MRR |
| Przychód | ile przychodu zależy od produktu, także pośrednio (powód zakupu pakietu) | rozliczenia, rozmowy sprzedaży |
| Koszt | ludzie, infrastruktura, licencje, wsparcie, ryzyko bezpieczeństwa | budżet, zgłoszenia, skany zależności |
| Umowy | czy umowy, SLA, oferty przetargowe gwarantują funkcję i do kiedy | umowy, regulamin |
| Zastępstwo | czy jest zamiennik albo obejście i ile kosztuje migracja klienta | test z klientami |
| Wpływ | co tracą najwięksi klienci; ryzyko odejścia | rozmowy, NRR kohorty |
„Go”, gdy koszt i ryzyko utrzymania przewyższają przychód zagrożony odejściem, a umowy pozwalają na zmianę.

## Harmonogram (typowe etapy)
1. **Decyzja** wewnętrzna i plan.
2. **Zapowiedź** — data wyłączenia i powód; okres zależy od umów i kosztu migracji klienta (zwykle 3–12 mies.).
3. **Koniec sprzedaży** — produkt znika z oferty i cennika dla nowych klientów.
4. **Koniec wsparcia** — tylko poprawki bezpieczeństwa albo nic (napisz wprost).
5. **Wyłączenie** — dostęp zamknięty; eksport danych jeszcze przez ustalony okres.
6. **Usunięcie danych** — zgodnie z umową i polityką retencji; potwierdzenie dla klientów, którzy o nie proszą.

## Kolejność interesariuszy
Zarząd i właściciele budżetu → wsparcie, sprzedaż, opiekunowie klientów (zanim klient zapyta) → kluczowi klienci
osobiście → wszyscy klienci (w produkcie, e-mail, dokumentacja) → partnerzy i integratorzy → publicznie (strona,
notatka o zmianach). Nikt z zespołu nie dowiaduje się z ogłoszenia publicznego.

## Komunikat dla klientów
Co się zmienia · dlaczego (uczciwie, z korzyścią dla klienta, jeśli jest) · od kiedy (daty etapów) · co klient ma
zrobić (zamiennik, migracja, eksport — z instrukcją) · kto pomoże (kontakt) · co z danymi i opłatami (zwrot,
zmiana planu). Bez żargonu i bez obietnic, których nie ma w planie.

## Checklista z właścicielami
- [ ] decyzja i kryteria zapisane (właściciel produktu)
- [ ] przegląd umów, SLA i regulaminu (prawnik)
- [ ] zamiennik albo instrukcja migracji gotowa i przetestowana z klientem (zespół produktu)
- [ ] eksport danych w otwartym formacie, czas trwania eksportu (inżynieria)
- [ ] rozliczenia: koniec opłat, zwroty, zmiany planów (finanse, be-billing-subscriptions)
- [ ] wsparcie: odpowiedzi na typowe pytania, skrypty (wsparcie)
- [ ] dokumentacja, cennik, strona, materiały sprzedaży zaktualizowane (marketing)
- [ ] w produkcie: ostrzeżenie dla użytkowników modułu z datą (inżynieria)
- [ ] monitoring użycia po zapowiedzi — kto jeszcze używa tydzień przed wyłączeniem (analityka)
- [ ] usunięcie kodu, danych, infrastruktury i kosztów po wyłączeniu (inżynieria)
- [ ] podsumowanie: migracja, odejścia, oszczędność (właściciel produktu)
