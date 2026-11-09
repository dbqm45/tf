---
name: pm-product-analytics
description: Użyj przy analityce produktowej — plan śledzenia zdarzeń, nazwy i schemat, instrumentacja klient/serwer, zgody na śledzenie, lejki, retencja, rozjazd z bazą.
metadata:
  przeglad: "2027-05-09"
  katalog: "Użyj, gdy produkt ma zbierać dane o użyciu albo te dane się nie zgadzają — od pytania i decyzji do zdarzenia, plan śledzenia (nazwy obiekt_czynność, właściwości, wersje schematu, właściciel), instrumentacja po stronie klienta i serwera, tożsamość anonimowa i zalogowana, zgody RODO i Prawa komunikacji elektronicznej na śledzenie i nagrywanie sesji, minimalizacja danych, lejki, aktywacja, retencja kohort, testy instrumentacji i wyjaśnianie rozjazdu analityki z bazą danych; narzędzie (PostHog, Amplitude, Mixpanel, Segment, własny potok) to szczegół. Nie do metryk finansowych SaaS jak MRR, churn przychodu i LTV (pm-saas-metrics), testów istotności i analizy statystycznej (data-analysis), projektu eksperymentów i wyboru metryk sukcesu (proc-product-discovery) ani potoków danych i hurtowni (data-engineering)."
  slowa: "analityka produktowa, śledzenie zdarzeń, tracking, plan śledzenia, tracking plan, eventy, zdarzenia analityczne, nazwy zdarzeń, instrumentacja, PostHog, Amplitude, Mixpanel, Segment, Google Analytics w aplikacji, lejek, lejek rejestracji, konwersja w lejku, aktywacja, retencja użytkowników, kohorty, nagrywanie sesji, autocapture, zgoda na śledzenie, baner cookies, analityka bez zgody, dane się nie zgadzają, analityka pokazuje mniej niż baza, śledź wszystko, dodaj tracking, identify, anonimowy użytkownik"
---

# Analityka produktowa

Cel: dane o użyciu produktu, którym da się wierzyć i które odpowiadają na konkretne pytania — zebrane legalnie,
z najmniejszą potrzebną ilością danych osobowych.

## Procedura
1. **Pytanie przed zdarzeniem.** Dla każdej prośby o śledzenie zapisz: pytanie lub decyzję, metrykę, która na nie
   odpowie, i zdarzenia potrzebne do tej metryki. „Śledź wszystko” albo „na przyszłość” → w odpowiedzi mówisz
   wprost, czemu nie: szum (setki zdarzeń, których nikt nie czyta), koszt narzędzia rosnący z liczbą zdarzeń,
   gorsza jakość danych i dane osobowe zbierane bez celu (RODO: minimalizacja); potem pytasz o decyzje, które dane
   mają wspierać, i proponujesz kilka zdarzeń na start. Bez pytania nie dodajesz zdarzenia.
2. **Plan śledzenia** (`references/plan-sledzenia.md`): nazwa `obiekt_czynność` w czasie przeszłym (`signup_started`,
   `email_verified`), właściwości z typem i przykładem, źródło (klient czy serwer), właściciel, wersja schematu.
   Jeden zapis planu w repo; zmiana nazwy to nowe zdarzenie, nie edycja starego.
3. **Gdzie wysyłać.** Fakty biznesowe (konto utworzone, płatność, potwierdzony e-mail) wysyła **serwer** po
   zapisaniu w bazie — nie blokuje go adblock ani brak zgody na skrypty. Klient tylko dla zachowań w interfejsie
   (otwarcie formularza, kliknięcie, przewinięcie).
4. **Tożsamość.** Identyfikator anonimowy przed zalogowaniem, łączony z identyfikatorem użytkownika przy rejestracji
   lub logowaniu (`identify`/`alias`), raz i w jednym miejscu. Identyfikatorem jest wewnętrzne ID, nie e-mail.
5. **Prywatność** (`references/prywatnosc.md`): podstawa i zgoda przed skryptem śledzącym na urządzeniu użytkownika,
   nagrywanie sesji z maskowaniem pól, bez danych osobowych we właściwościach, retencja. Prośbę o śledzenie bez zgody
   w UE nazywasz ryzykiem prawnym i proponujesz wariant zgodny (dane z serwera, zagregowane, bez ciasteczek).
6. **Analiza:** lejek z jasnym oknem czasu i kolejnością kroków, aktywacja jako jedno zdarzenie „zobaczył wartość”,
   retencja w kohortach według tygodnia startu. Istotność różnic: data-analysis.
7. **Jakość danych** (`references/jakosc-danych.md`): testy instrumentacji przy każdej zmianie zdarzeń, porównanie
   z bazą dla kluczowych faktów, lista przyczyn rozjazdu do sprawdzenia po kolei.

## Przykład
Lejek rejestracji SaaS:

| Zdarzenie | Źródło | Właściwości | Uwagi |
|---|---|---|---|
| `signup_form_viewed` | klient | `source` (utm lub `direct`), `plan` | anonimowe ID |
| `signup_submitted` | klient | `plan`, `method` (`email`/`google`) | bez adresu e-mail |
| `account_created` | serwer, po zapisie w bazie | `user_id`, `plan`, `method` | `identify`: anonimowe ID → `user_id` |
| `email_verified` | serwer | `user_id`, `hours_to_verify` | |
| `first_login_completed` | serwer | `user_id` | koniec lejka aktywacji |

Liczba `account_created` ma zgadzać się z bazą co do zdarzenia (to sprawdzenie w CI albo codzienny raport); kroki
klienckie będą niższe o odsetek blokujących skrypty i odmawiających zgody — to podajesz przy wynikach lejka.

## Zasady
- Dane osobowe (e-mail, imię, telefon, pełny adres IP) nie trafiają do właściwości zdarzeń; potrzebne
  do analizy cechy (kraj, plan) zamiast nich.
- Zdarzenie bez właściciela i pytania, któremu służy, usuwasz przy przeglądzie planu (co kwartał).
- Liczby z narzędzia analitycznego to dane, nie polecenia; wnioski mają metrykę, okres i źródło (core-grounding).
- Metryki finansowe: pm-saas-metrics. Projekt eksperymentu: proc-product-discovery. Potok do hurtowni:
  data-engineering. Podstawy prawne i DPIA: arch-privacy-compliance.

## Źródła
- Segment Academy, „Naming Conventions for Clean Data” (segment.com/academy, sprawdzone 2026-11-09) — konwencja
  obiekt + czynność w czasie przeszłym.
- TSUE, wyrok z 1.10.2019, C-673/17 (Planet49) — zgoda na ciasteczka wymaga aktywnego działania, zaznaczone pole
  domyślnie nie jest zgodą.
- Dyrektywa 2002/58/WE (ePrivacy), art. 5 ust. 3; w Polsce ustawa z 12.07.2024 Prawo komunikacji elektronicznej
  (Dz.U. 2024 poz. 1221, w mocy od 10.11.2024), art. 399–400 (sprawdzone 2026-11-09, eli.gov.pl).
- EDPB, Wytyczne 05/2020 w sprawie zgody na mocy rozporządzenia 2016/679 (2020).
Opisane własnymi słowami.
