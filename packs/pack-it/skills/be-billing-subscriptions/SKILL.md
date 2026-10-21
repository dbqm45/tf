---
name: be-billing-subscriptions
description: Użyj przy subskrypcjach i płatnościach cyklicznych — plany, zmiana planu proporcjonalnie, okres próbny, windykacja, webhooki dostawcy, VAT, faktury.
metadata:
  widocznosc: nazwa
  przeglad: 2027-10-20
  katalog: "Użyj, gdy projektujesz lub przeglądasz rozliczenia SaaS — model planów, cen i okresów, subskrypcja i jej stany, zmiana planu w trakcie okresu z rozliczeniem proporcjonalnym, okres próbny, rozliczenie za zużycie, nieudane płatności i windykacja (dunning), idempotentne webhooki dostawcy płatności (Stripe, Adyen, PayU, Przelewy24) i uzgadnianie stanu, pieniądze w kodzie (waluta, zaokrąglenia), VAT dla usług elektronicznych i OSS, faktury i korekty, KSeF, anulowanie i odstąpienie. Nie do ogólnego projektu kolejek (be-messaging-outbox), modelu cennika i księgowania w domenie (ddd-archetypes: Pricing, Accounting), mapy przepisów UE dla produktu z AI (arch-eu-product-law) ani logowania (be-auth-security)."
  slowa: "subskrypcja, abonament, płatność cykliczna, billing, rozliczenia saas, plan taryfowy, zmiana planu, upgrade, downgrade, proration, rozliczenie proporcjonalne, okres próbny, trial, rozliczenie za zużycie, metered billing, nieudana płatność, karta odrzucona, dunning, windykacja, ponowienie płatności, past_due, webhook stripe, webhook przyszedł dwa razy, idempotencja płatności, uzgadnianie płatności, faktura subskrypcji, faktura korygująca, VAT OSS, VAT usług elektronicznych, kwota w groszach, zaokrąglenie kwot, anulowanie subskrypcji"
---

# Subskrypcje i rozliczenia (billing) w SaaS

**Rola agenta:** projektuje model subskrypcji i przepływ pieniędzy tak, żeby klient nigdy nie zapłacił dwa razy,
dostęp zgadzał się ze stanem płatności, a każda kwota dała się odtworzyć z faktury. Źródłem prawdy o płatności jest
dostawca płatności; źródłem prawdy o dostępie — nasza subskrypcja uzgodniona z dostawcą.
Konkretne API, webhooki, klucze i wersje u dostawcy Stripe: tool-stripe.

## 1. Model
- **Produkt → plan (cena) → subskrypcja → pozycje subskrypcji → faktura → płatność.** Cena jest niezmienna i wersjonowana:
  zmiana cennika = nowa cena, istniejący klienci zostają na starej, dopóki decyzja biznesowa nie mówi inaczej.
- Okres rozliczeniowy z kotwicą (dzień rozliczenia), waluta przypisana do klienta, strefa czasowa okresu jawna (eng-i18n).
- Uprawnienia (co klient może) liczysz ze stanu subskrypcji w jednym miejscu, nie z planu rozsianego po kodzie.
- Model domenowy cen, rabatów i sald — archetypy Pricing i Accounting (ddd-archetypes); tu tylko mechanika subskrypcji.

## 2. Stany subskrypcji i dostęp
Typowe stany (nazwy jak u dostawcy, np. Stripe): okres próbny, aktywna, zaległa (pierwsza nieudana płatność),
niezapłacona, anulowana, wstrzymana, niekompletna (pierwsza płatność nie przeszła). Szczegóły: `references/stany-i-webhooki.md`.
- Dla każdego stanu zapisz decyzję: pełny dostęp, dostęp z ostrzeżeniem (okres łaski), tylko odczyt i eksport, brak.
- Odcięcie dostępu nigdy nie kasuje danych — usunięcie wg retencji i prawa do eksportu (arch-multi-tenancy §5).

## 3. Zmiana planu, okres próbny, zużycie
- **Zmiana w trakcie okresu:** podwyższenie — od razu, z kwotą proporcjonalną za resztę okresu (faktura teraz albo
  pozycja na następnej); obniżenie — zwykle od następnego okresu, bez zwrotu. Regułę zapisz w regulaminie i w teście.
- Proporcję liczy dostawca albo jedna funkcja w kodzie (sekundy lub dni okresu, zaokrąglenie na końcu, raz).
- **Okres próbny:** z kartą lub bez; przypomnienie przed końcem; koniec bez metody płatności → jasny stan, nie błąd.
- **Zużycie (metered):** zdarzenia zużycia z identyfikatorem idempotencji, agregacja na koniec okresu, korekta przed
  zamknięciem faktury; licznik per najemca (arch-multi-tenancy).

## 4. Nieudane płatności i windykacja (dunning)
- Ponowienia wg harmonogramu dostawcy (np. Stripe Smart Retries — zalecane 8 prób w 2 tygodnie, konfigurowalne;
  `references/stany-i-webhooki.md`) albo własnego, dobranego do biznesu; e-mail z linkiem do aktualizacji karty,
  okres łaski z dostępem.
- Po ostatniej próbie: stan „niezapłacona” lub anulowanie wg decyzji; dostęp wg tabeli z §2.
- Uwierzytelnienie płatności (SCA, 3-D Secure) przy odnowieniu: stan „wymaga działania” i link dla klienta.

## 5. Webhooki dostawcy — idempotentnie
- Weryfikujesz podpis na surowym ciele żądania i tolerancję czasu; sekret z menedżera sekretów (ops-secrets-identities).
- Zapisujesz zdarzenie (id zdarzenia jako klucz unikalny) i odpowiadasz 2xx od razu; obsługa asynchronicznie
  z deduplikacją w tej samej transakcji co efekt (inbox — be-messaging-outbox).
- Kolejność nie jest gwarantowana i zdarzenia się powtarzają: obsługa nie ufa kolejności, przy wątpliwości pobiera
  aktualny obiekt z API dostawcy.
- Wywołania do dostawcy (utworzenie subskrypcji, zwrot) z kluczem idempotencji — ponowienie po błędzie sieci nie
  tworzy drugiej płatności.
- **Uzgadnianie:** okresowe zadanie porównuje stany subskrypcji i faktur u nas i u dostawcy; rozbieżność = alert.

## 6. Pieniądze, podatki, faktury
- Kwoty jako liczba całkowita w najmniejszej jednostce waluty albo typ dziesiętny — nigdy liczba zmiennoprzecinkowa;
  liczba miejsc po przecinku zależy od waluty (ISO 4217). Zaokrąglenie w jednym miejscu, z jawną regułą.
- **VAT:** usługa elektroniczna B2C w UE — stawka kraju konsumenta, rozliczenie przez OSS; B2B z ważnym numerem VAT UE —
  odwrotne obciążenie. Dowody miejsca konsumenta (adres, karta, IP) zapisujesz z fakturą. Fakty i progi:
  `references/stany-i-webhooki.md` [do sprawdzenia przez księgowość].
- **Faktury:** numeracja ciągła, niezmienne po wystawieniu; zmiana = faktura korygująca. W Polsce KSeF
  (terminy: księgowość; notatki `.claude/skills/arch-eu-product-law/references/poza-zakresem-fabryki.md`). Kwoty faktury = kwoty pobrane, z odtwarzalnym wyliczeniem pozycji.
- **Anulowanie i odstąpienie B2C:** anulowanie tak proste jak zakup, odstąpienie i zwrot wg praw konsumenta
  (prawnik; notatki `.claude/skills/arch-eu-product-law/references/poza-zakresem-fabryki.md`).

## Zasady
- Jedno źródło prawdy o stanie płatności (dostawca) i jedno o dostępie (subskrypcja), uzgadniane zadaniem.
- Każdy webhook i każde wywołanie dostawcy idempotentne; test „to samo zdarzenie dwa razy” w zestawie.
- Danych kart nie przechowujesz — tokeny dostawcy (zakres PCI DSS: sec-governance-compliance).
- Testy na zegarze kontrolowanym (koniec okresu, koniec próby, zmiana czasu) i w trybie testowym dostawcy.
- Fakty podatkowe i prawne idą do księgowości lub prawnika; w kodzie trzymasz je jako konfigurację z datą obowiązywania.

## Przykład
**Sytuacja:** „Odnowienie się nie udało, webhook `invoice.payment_failed` przyszedł dwa razy, klient stracił dostęp
od razu i dostał dwa e-maile.”
**Wynik (skrót):**
- Webhook: tabela zdarzeń z unikalnym `event_id`; drugie doręczenie → 2xx bez efektu. E-mail wysyłany z outboxa raz.
- Stan: „zaległa” zamiast natychmiastowej blokady; okres łaski 7 dni [decyzja biznesu], baner z linkiem do karty.
- Ponowienia: harmonogram dostawcy; po ostatniej nieudanej → tylko odczyt i eksport.
- Testy: podwójne zdarzenie; zdarzenia w odwrotnej kolejności (najpierw `paid`, potem `failed` starszej próby);
  koniec okresu łaski na zegarze testowym.

## Checklista
- [ ] model produkt → cena → subskrypcja → faktura; ceny wersjonowane
- [ ] tabela stanów subskrypcji z decyzją o dostępie dla każdego
- [ ] reguła zmiany planu i okresu próbnego zapisana i przetestowana
- [ ] windykacja: ponowienia, komunikacja, okres łaski, stan końcowy
- [ ] webhooki: podpis, zapis z id, 2xx od razu, deduplikacja, brak zaufania do kolejności; klucze idempotencji w API
- [ ] kwoty bez liczb zmiennoprzecinkowych; VAT/OSS i faktury potwierdzone przez księgowość; uzgadnianie z alertem

## Źródła
Opisane własnymi słowami; fakty z datą dostępu w `references/stany-i-webhooki.md`.
