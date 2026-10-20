# Incydent w sieci ładowania — runbook

Ujęcie defensywne. Niniejszy runbook to wzór do dostosowania; czasy to ilustracje **[do weryfikacji]**. Diagnoza awarii
bez podejrzenia ataku: `dom-ev-diagnostics`.

## 1. Role i przygotowanie
| Rola | Zadanie |
|---|---|
| dowodzący incydentem | decyzje, zapis czasów, dostęp do zarządu |
| operacje sieci (NOC) | izolacja stacji, przywracanie, stan floty |
| bezpieczeństwo | analiza, zabezpieczenie dowodów, rotacja sekretów |
| łączność | OSD, partnerzy roamingowi, klienci, media |
| prawnik / inspektor ochrony danych | zgłoszenia (NIS2, RODO), ocena wycieku danych |
| producent / dostawca CSMS | wsparcie techniczne wg umowy (czas reakcji!) |
Przygotuj wcześniej: listę kontaktów 24/7 (CSIRT, organ, OSD, partnerzy OCPI/OICP, producenci), szablony komunikatów,
przełącznik zamrożenia komend masowych, kopie konfiguracji stacji, ćwiczenie co najmniej raz w roku (ilustracja).

## 2. Pierwsze 60 minut
1. Zapisz **czas uzyskania wiedzy** (start zegara 24 h NIS2 i CRA).
2. Zamroź komendy masowe i podejrzane konta; zabezpiecz logi CSMS, bramy, konsoli (kopia, nie edycja).
3. Ustal zasięg: które stacje, które konta, które tokeny; zakres skutku: dostępność, moc, dane, pieniądze.
4. Oceń skutek dla sieci energetycznej (zmiany mocy lub masowe wyłączenie/włączenie).
5. Powołaj dowodzącego; zaplanuj komunikację i decyzję o zgłoszeniu.

## 3. Izolacja i odcięcie komend masowych
| Cel | Środek |
|---|---|
| zatrzymać nadużycie komend | tryb zamrożenia w CSMS; unieważnienie sesji i tokenów kont; zmiana haseł kont usług |
| odciąć podejrzane stacje | blokada połączenia na bramie / kwarantanna sieciowa (VLAN, APN), nie kasowanie stacji ani logów |
| zachować ciągłość | stacje z poprawną konfiguracją zostają online; domyślne zachowanie offline (profil domyślny, lokalna lista) |
| podejrzany firmware | wstrzymaj aktualizacje, zachowaj próbkę obrazu i hasz, skontaktuj się z producentem |
| wyciek tokenu OCPI | unieważnij i wydaj nowy token, powiadom partnera, przejrzyj żądania z tego tokenu |
| podejrzany terminal płatniczy | wyłącz płatność na stacji, powiadom dostawcę płatności (`dom-ev-payments`) |
Nie przywracaj ani nie restartuj stacji, zanim nie zapiszesz jej stanu i logów (`GetLog` z `logType` `SecurityLog` w 2.x).

## 4. Komunikacja
- **OSD:** gdy zmieniono moc lub wyłączono znaczną część floty — krótki komunikat: skala, region, czas, plan przywracania,
  kontakt. Przywracanie falami uzgodnij tak, by nie powstał skok obciążenia (`dom-ev-energy-management`).
- **Partnerzy roamingowi i huby:** niedostępność lokalizacji (status w OCPI/OICP), możliwy wyciek tokenu lub CDR,
  zalecenia (rotacja tokenu, blokada tokenów). Użyj kanału z umowy, nie publicznego.
- **Klienci i kierowcy:** informacja o niedostępności, bezpieczeństwie płatności i danych; NIS2 Art. 23(1)-(2) wymaga
  powiadomienia odbiorców usług o poważnym incydencie i środkach zaradczych.
- **Zarząd:** bieżący stan; decyzje o zgłoszeniu i komunikacji publicznej.
- Wyciek danych osobowych: osobna ścieżka RODO (zgłoszenie do organu w ustawowym terminie — [do weryfikacji] w skillu
  prywatności i prawie krajowym).

## 5. Zgłoszenie
| Akt | Kto | Terminy (od uzyskania wiedzy) |
|---|---|---|
| NIS2 Art. 23(4) | podmiot kluczowy lub ważny | ostrzeżenie wczesne **24 h**; zgłoszenie **72 h**; raport pośredni na żądanie; raport końcowy **do miesiąca** po zgłoszeniu |
| CRA Art. 14 | producent (od 11.09.2026) | podatność aktywnie wykorzystywana: **24 h**, **72 h**, raport końcowy **14 dni** po środku zaradczym; poważny incydent wpływający na bezpieczeństwo produktu: analogicznie, raport do miesiąca |
Adresaci: CSIRT krajowy lub organ (NIS2); jedna platforma zgłoszeniowa CRA (Art. 16). Ostrzeżenie wczesne wskazuje, czy
podejrzewa się czyn bezprawny i czy możliwy skutek transgraniczny; nie czekaj na pełną analizę. Samo zgłoszenie nie
zwiększa odpowiedzialności (Art. 23(1)). Dowody wg `references/regulacje-cyber.md`.

## 6. Przywracanie
1. Usuń przyczynę (konto, token, firmware, błąd procesu) i zweryfikuj, że nie wraca.
2. Rotacja sekretów w zasięgu: hasła i certyfikaty stacji, tokeny OCPI, klucze API, konta konsoli.
3. Weryfikacja konfiguracji i wersji firmware stacji względem wzorca (`BootNotification`, raport konfiguracji).
4. Wznowienie falami z kohortą pilotażową; opóźnienia losowe; obserwacja obciążenia z OSD.
5. Uzgodnienie danych: sesje w trakcie incydentu, CDR, odczyty (`dom-ev-session-lifecycle`, `dom-ev-cdr-settlement`).
6. Zamknięcie dopiero po raporcie końcowym i potwierdzeniu partnerów.

## 7. Po incydencie
Przegląd bez szukania winnych: oś czasu, przyczyna, skuteczność detekcji (po jakim czasie wykryto), co zadziałało,
poprawki (uprawnienia, reguły, procesy), właściciele i terminy. Zaktualizuj model zagrożeń i runbook.

## Źródła
- `eu-nis2` Art. 23, `.claude/knowledge/eu-nis2/doc.txt:L3219-3360`, eur-lex.europa.eu/eli/dir/2022/2555/oj, pobrane 2026-10-20.
- `eu-cra` Art. 14, `.claude/knowledge/eu-cra/doc.txt:L2637-2700`, eur-lex.europa.eu/eli/reg/2024/2847/oj, pobrane 2026-10-20.
- `dom-ev-asset-operations` (`GetLog`, kwarantanna komend), `dom-ev-energy-management`, stan repozytorium 2026-10-20.
- Wiedza ogólna branży (role, kolejność działań) — [do weryfikacji] w organizacji.
