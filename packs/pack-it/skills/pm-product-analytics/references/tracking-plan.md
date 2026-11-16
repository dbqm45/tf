# Plan śledzenia

## Format jednego zdarzenia
| Pole | Przykład | Uwagi |
|---|---|---|
| nazwa | `invoice_sent` | `obiekt_czynność`, czas przeszły, `snake_case`, angielski; bez nazw ekranów i wersji UI |
| pytanie | „ilu klientów wysyła pierwszą fakturę w ciągu 7 dni” | po co jest zdarzenie |
| źródło | serwer | serwer dla faktów biznesowych, klient dla zachowań w UI |
| właściwości | `invoice_id` (string), `amount_band` (`<1k`, `1k-10k`, `>10k`), `is_first` (bool) | typ i dozwolone wartości; przedziały zamiast dokładnych kwot, gdy wystarczą |
| właściciel | zespół fakturowania | kto odpowiada za poprawność |
| wersja | 2 (od 2026-11-09: dodane `is_first`) | zmiana typu albo znaczenia = nowa nazwa |

## Reguły nazw
- Jeden słownik obiektów (`account`, `invoice`, `project`) i czynności (`created`, `viewed`, `submitted`,
  `completed`, `failed`, `deleted`); nowa czynność tylko, gdy żadna nie pasuje.
- Wynik kroku jako właściwość, nie osobne zdarzenia: `payment_completed` z `status: failed` nie jest dobre —
  osobno `payment_failed` z `reason`, bo lejek liczy sukcesy.
- Właściwości wspólne (`app_version`, `platform`, `plan`) ustawia jedna warstwa, nie każde wywołanie.

## Gdzie trzymać plan
- Plik w repo (YAML lub JSON) obok kodu; z niego typy dla klienta i walidacja w CI albo w narzędziu (schemat
  zdarzeń), żeby literówka w nazwie nie tworzyła nowego zdarzenia.
- Przegląd planu przy każdej zmianie zdarzeń w PR (jak migracji bazy).

## Tożsamość
- Przed zalogowaniem: anonimowe ID z narzędzia lub własne (losowe, bez danych osobowych).
- Przy rejestracji i logowaniu: połączenie anonimowego ID z `user_id` raz, w jednym miejscu kodu.
- Wylogowanie: reset identyfikatora, żeby następny użytkownik na tym urządzeniu nie dostał cudzej historii.
- Konta firmowe (B2B): dodatkowo `account_id` lub grupa, żeby liczyć aktywność firmy, nie tylko osoby.
