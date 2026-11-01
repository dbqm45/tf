# Kontrakt zmiany w istniejącym systemie

Gdy zmiana w legacy **ma** zmienić zachowanie (naprawa błędu, mała funkcja), a reszta ma zostać, zadanie dla agenta
opisujesz kontraktem. Pełna inwentaryzacja systemu na start nie jest potrzebna, wystarczy zasięg zmiany.

## Sześć pól
| Pole | Co wpisujesz |
|---|---|
| **Warunek** | kiedy zmiana działa (dane wejściowe, stan, rola) |
| **Oczekiwany wynik** | obserwowalny wynik, nie „błąd zniknął” |
| **Chronione zachowania** | tabela niżej, z decyzją przy każdej pozycji |
| **Dozwolony zakres plików** | ścieżki, które wolno zmienić; wyjście poza zakres to zgłoszenie do człowieka, nie decyzja agenta |
| **Dowód naprawy** | test czerwony na commicie bazowym i zielony po zmianie |
| **Dowód braku regresji** | testy ochronne nagrane na commicie bazowym **przed** zmianą (osobny etap i commit), zielone przed i po |

## Chronione zachowania — cztery źródła w zasięgu zmiany
1. **Wywołujący i konsumenci** (grep, graf importów, logi wywołań API, eng-codebase-mapping). Brak znalezionych
   to ograniczona wiedza, a nie dowód, że ich nie ma — zapisz to.
2. **Incydenty i zgłoszenia** dotyczące tych plików.
3. **Często zmieniane pliki** w zasięgu (`git_territory.py --hotspots`).
4. **Testy charakteryzujące** istniejące zachowanie (sekcja „Warunek wstępny” w SKILL.md).

| Zachowanie | Źródło | Decyzja | Kto zdecydował |
|---|---|---|---|
| `GET /invoices/{id}` zwraca 404 dla cudzej faktury | konsument: portal klienta | zobowiązanie (chronić) | J. Nowak, właściciel modułu |
| kolejność pozycji w eksporcie CSV | test charakteryzujący | przypadek (wolno zmienić) | J. Nowak |
| zaokrąglenie VAT per pozycja | incydent INC-88 | do decyzji właściciela | — (pytanie otwarte) |

- **Zobowiązanie** dostaje test ochronny przed zmianą. **Przypadek** wolno zmienić, z wpisem w raporcie.
  **Do decyzji** blokuje start, dopóki właściciel (osoba, nie „zespół”) nie rozstrzygnie.
- Zmiana zachowania widocznego dla konsumenta to już nie refaktoryzacja: zgoda człowieka i wpis w `decisions.md`.
- Przy zamknięciu zmiany zatwierdzone gwarancje trafiają do wymagań jako **dodane** (pierwszy zapis wymagania)
  razem ze swoim testem (proc-requirements-shaping, `references/istniejace-specyfikacje.md` §4).

Źródła: J. Wąsowski, „Brownfield Spec and Preservation Contract” (2026-10-22); liczby z artykułu (np. odsetek
agentowych PR z commitem cofającym) [niezweryfikowane]. Przykładowe wiersze tabeli są ilustracją.
