# Kryzys na poziomie zarządu, okup, polisa, M&A

Spis treści: 1. Zespół kryzysowy · 2. Playbook (szkic) · 3. Decyzja o okupie · 4. Komunikacja · 5. Tabletop · 6. Ubezpieczenie cyber · 7. M&A i dostawcy · 8. Zgłoszenia i fakty

## 1. Zespół kryzysowy
Dowodzący (zwykle CEO lub COO, nie CISO), CISO/dowodzący technicznie, prawny, komunikacja, HR, finanse, przedstawiciel
biznesu; zastępcy dla każdej roli; sekretarz prowadzący dziennik decyzji. Mandat zapisany z góry: kto ogłasza kryzys,
do jakiej kwoty decyduje zespół, co wymaga zarządu. Kanał awaryjny poza zaatakowaną infrastrukturą (osobne konto czatu,
telefony, wydrukowana lista kontaktów). Szczegóły techniczne reagowania — ops-security-operations.

## 2. Playbook kryzysowy (szkic do `crisis-playbook.md`)
1. **Kryteria ogłoszenia** i poziomy (1 incydent, 2 poważny, 3 kryzys); kto ogłasza.
2. **Pierwsze 4 godziny:** zwołanie zespołu, wstrzymanie komunikacji nieformalnej, polecenie wstrzymania zmian (bez
   „czyszczenia” systemów), powiadomienie prawnika, ubezpieczyciela i doradcy kryzysowego z polisy.
3. **Rytm:** odprawy co 2–4 h, w każdej: fakty (potwierdzone / niepotwierdzone), skutki biznesowe, decyzje, następny krok.
4. **Dziennik decyzji:** czas (UTC i lokalny), decyzja, kto zdecydował, informacje wtedy dostępne, alternatywy, powód.
   Dziennik prowadzi sekretarz; prawnik decyduje, jak go oznaczyć i przechowywać (poufność prawnicza) [niezweryfikowane
   dla jurysdykcji].
5. **Zewnętrzni:** prawnik, firma forensyczna (najlepiej wcześniej umówiona), ubezpieczyciel, organy ścigania, regulator,
   klienci, media, partnerzy, pracownicy.
6. **Decyzje zarządu:** okup, zgłoszenia, wyłączenie usług, komunikat publiczny, wznowienie działania.
7. **Zakończenie:** kryteria wyjścia z kryzysu, przegląd po zdarzeniu (bez szukania winnych) z działaniami i właścicielami,
   raport do zarządu, aktualizacja strategii i ćwiczeń.

## 3. Decyzja o okupie (proces, nie opinia)
Płacenie nie jest zalecane jako domyślna droga, ale decyzja należy do zarządu. Kolejność:
1. Ustal, czy da się odtworzyć z kopii i jak długo trwa (czas odtworzenia wobec tolerowanego przestoju).
2. Opinia prawnika: sankcje (w USA OFAC — odpowiedzialność bez winy, czynnikiem łagodzącym są zgłoszenie do organów
   i współpraca; w UE i Polsce [niezweryfikowane]), obowiązki zgłoszeniowe, zgodność z polisą, ryzyko karne i odpowiedzialność
   członków zarządu.
3. Zgłoszenie do organów ścigania/CSIRT przed jakąkolwiek płatnością, jeśli prawo i polisa tego oczekują.
4. Wiarygodność napastnika: czy deklarowane dane (wyciek) rzeczywiście są u niego, czy deszyfrator działa (próba na
   małym zbiorze przez wyspecjalizowaną firmę), czy płatność usunie wyciek — zwykle nie ma gwarancji.
5. Zapis decyzji w dzienniku (kto, na jakiej podstawie, jakie opinie); decyzję „nie płacimy” zapisujesz tak samo.
Płatności dokonuje wyłącznie wyspecjalizowany pośrednik wskazany z prawnikiem; nie robi tego pracownik IT.

## 4. Komunikacja
Jeden rzecznik, jedno źródło faktów. Kolejność: zarząd i rada → prawny i regulator (wg terminów) → pracownicy →
klienci i partnerzy dotknięci → media (gotowa odpowiedź reaktywna). Treść: co wiemy, czego nie wiemy, co robimy, co ma
zrobić odbiorca (zmiana haseł, czujność); bez spekulacji o sprawcy i przyczynie, bez obietnic „dane są bezpieczne”,
dopóki to niepotwierdzone. Wiadomości sprawdza prawnik. Spółki giełdowe: obowiązki ujawniania (np. formularz 8-K
pozycja 1.05 w USA — zgłoszenie w 4 dni robocze od ustalenia istotności, wg źródeł wtórnych, dostęp 2026-10-17
[niezweryfikowane]); terminy dla NIS2, DORA i RODO — sec-eu-regulations i ops-security-operations.

## 5. Ćwiczenie tabletop
Raz w roku, z udziałem zarządu; 2–3 godziny, scenariusz z biznesu (ransomware na ERP w piątek, wyciek danych klientów,
atak na kluczowego dostawcę), wstrzykiwane „zdarzenia” co kilka minut (dziennikarz dzwoni, klient żąda wyjaśnień, polisa
wymaga zgłoszenia). Ocena: czy role i mandat są jasne, czy dziennik działa, czy kontakty aktualne, czy decyzja o okupie
poszła procesem. Wynik: lista luk z właścicielami i terminem; powtórka zmienionego elementu.

## 6. Ubezpieczenie cyber
Pytania do brokera i prawnika: zakres (koszty własne: forensyka, odtworzenie, przerwa w działalności, powiadomienia,
odpowiedzialność wobec stron trzecich, wymuszenie), wyłączenia (wojna i działania państwowe, niedoinwestowanie
zabezpieczeń, wcześniej znane luki), limity i udziały własne, wymogi kontrolne (MFA, kopie offline, EDR) i skutek
ich niespełnienia, **prawdziwość odpowiedzi we wniosku** (nieprawdziwe mogą unieważnić ochronę), termin powiadomienia,
narzucone firmy doradcze, zgoda ubezpieczyciela na płatność. Polisa nie zastępuje kontroli.

## 7. M&A i dostawcy
- **Przed podpisaniem:** zapytanie do celu o incydenty z 3 lat, certyfikaty, tożsamość i MFA, kopie, dług techniczny,
  dane osobowe i transgraniczne przepływy, własność kodu i licencje; wynik jako ryzyka w modelu wyceny i zapisy w umowie
  (oświadczenia, odszkodowanie).
- **Dzień 1:** połączenie logowania i MFA, widoczność w logach, odcięcie niepotrzebnych połączeń; pełna integracja
  w planie 100 dni, bez „podłączania w ciemno” do sieci właściwej.
- **Dostawcy (program):** tiering wg krytyczności, standard umowy (zgłoszenie incydentu, audyt, plan wyjścia), przegląd
  roczny dla tieru 1, mapa koncentracji (jeden dostawca, wiele usług). Ocena pojedynczego dostawcy: sec-risk-management.

## 8. Zgłoszenia i fakty zewnętrzne
Terminy i adresaci zgłoszeń zależą od jurysdykcji i sektora; skill ich nie ustala. Prawnik potwierdza je w pierwszej
godzinie. Fakty z sekcji 3 i 4 pochodzą ze źródeł wtórnych (wyszukiwanie 2026-10-17) i wymagają sprawdzenia w oryginale.
