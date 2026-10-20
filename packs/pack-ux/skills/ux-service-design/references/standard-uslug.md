# Standard usług i prototypowanie usługi

## Spis treści
1. GOV.UK Service Standard
2. Prototypowanie usługi
3. Granice

## 1. GOV.UK Service Standard
Standard brytyjskiego rządu dla usług publicznych, 14 punktów. Tytuły (stan wg wyników wyszukiwania i wiedzy
modelu, dostęp 2026-10-17; pełną listę sprawdź na gov.uk/service-manual/service-standard [niezweryfikowane
dla punktów 5–9 i 11–13]):
1. Understand users and their needs
2. Solve a whole problem for users
3. Provide a joined up experience across channels
4. Make the service simple to use
5. Make sure everyone can use the service
6. Have a multidisciplinary team
7. Use agile ways of working
8. Iterate and improve frequently
9. Create a secure service which protects users’ privacy
10. Define what success looks like and publish performance data
11. Choose the right tools and technology
12. Make new source code open
13. Use and contribute to open standards, common components and patterns
14. Operate a reliable service

Do czego użyć poza sektorem publicznym: punkty 2 i 3 jako pytania kontrolne blueprintu („czy rozwiązujemy cały
problem klienta, także tam, gdzie kończy się nasz dział?”, „czy zmiana kanału nie gubi stanu?”), punkt 10 jako
wzór metryk. Formalne oceny usług (assessment) dotyczą administracji brytyjskiej; w innym kraju standard to
wzorzec, nie wymóg.

## 2. Prototypowanie usługi
| Metoda | Co testuje | Koszt | Uwaga |
|---|---|---|---|
| Odgrywanie ról / bodystorming | rozmowy, układ miejsca, przekazania | niski | pracownicy grają klienta i odwrotnie |
| Concierge | czy klient chce wynik usługi | niski, wolny przy skali | klient wie, że robi to człowiek |
| Wizard of Oz | czy interakcja z „systemem” działa | średni | klient nie wie; powiedz po sesji |
| Makieta fizyczna / papierowy formularz | układ, czytelność | niski | |
| Pilotaż w jednym oddziale | cała usługa na realnym ruchu | wysoki | najpierw plan wycofania |
Dobór: najtańsza metoda, która rozstrzyga najryzykowniejsze założenie (proc-product-discovery: testy założeń).

## 3. Granice
Pytanie o ekran lub stan formularza — ux-feature-design. Rozmowa z ekspertami o zdarzeniach domeny — ddd-event-storming.
Wydajność procesu i kolejki — proc-lean. Etyka zgód i manipulacji — ux-feature-design (`tresci-i-etyka.md`).
