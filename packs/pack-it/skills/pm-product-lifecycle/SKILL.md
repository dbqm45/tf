---
name: pm-product-lifecycle
description: Użyj przy etapie życia produktu lub modułu — wzrost, dojrzałość, schyłek; decyzja przedłużyć, zastąpić, utrzymać lub wycofać; plan wycofania z klientami.
metadata:
  przeglad: 2027-10-23
  katalog: "Użyj, gdy produkt, plan cenowy albo moduł przestaje rosnąć lub kosztuje więcej, niż daje — rozpoznanie etapu cyklu życia (wprowadzenie, wzrost, dojrzałość, schyłek) z danych, wybór ruchu (inwestować, przedłużyć życie, zastąpić, utrzymać bez rozwoju, wycofać) z kryteriami decyzji go/no-go, plan wycofania: kolejność interesariuszy, komunikat dla klientów, harmonogram (zapowiedź, koniec sprzedaży, koniec wsparcia, wyłączenie), migracja i eksport danych, umowy i prawo, checklista z właścicielami. Nie do technicznego wycofania wersji API (be-api-design), wydań i flag funkcji (ops-release-engineering), metryk SaaS (pm-saas-metrics) ani wyboru nowych funkcji (proc-product-discovery)."
  slowa: "cykl życia produktu, produkt przestał rosnąć, rynek nasycony, schyłek produktu, wycofać produkt, wyłączyć moduł, wygaszenie produktu, sunset, end of life, koniec wsparcia, koniec sprzedaży, mało kto używa, utrzymanie kosztuje, zastąpić produkt, przedłużyć życie produktu, migracja klientów, ogłoszenie wycofania"
---

# Cykl życia produktu i wycofanie

Cel: decyzja o produkcie lub module oparta na danych, a gdy zapada „wycofać” — wyłączenie bez zaskoczenia
klientów, bez utraty ich danych i bez złamania umów. Decyduje człowiek; ty dajesz dane, opcje i plan.

## Procedura
1. **Etap z danych**, nie z wrażenia: trend przychodu i liczby aktywnych klientów (12–24 mies.), retencja kohort,
   udział w przychodzie, koszt utrzymania (ludzie, infrastruktura, wsparcie), presja cenowa konkurencji.
   Etapy: wprowadzenie → wzrost → dojrzałość (wzrost spowalnia, rynek nasycony, konkurencja ceną) → schyłek
   (spadek klientów i przychodu).
2. **Ruchy do wyboru** — porównaj co najmniej trzy z kosztem, ryzykiem i wpływem na klientów:
   - **inwestować dalej** — gdy wzrost ma przyczynę, którą umiemy wzmocnić;
   - **przedłużyć życie** — nowi użytkownicy (segment, kraj), nowe zastosowania, częstsze użycie u obecnych;
   - **zastąpić** — nowy produkt lub moduł przejmuje klientów (migracja jako projekt);
   - **utrzymać bez rozwoju** — tylko poprawki i bezpieczeństwo, koszt minimalny, przychód zbierany do końca;
   - **wycofać** — gdy koszt i ryzyko (bezpieczeństwo, zależności bez wsparcia) przewyższają wartość.
3. **Go/no-go dla wycofania** — kryteria w `references/wycofanie.md` (użycie, przychód, koszt, umowy, zastępstwo,
   wpływ na kluczowych klientów); wynik zapisany jako decyzja z datą (core-project-record).
4. **Plan wycofania** — harmonogram, kolejność interesariuszy, komunikat, migracja, checklista z właścicielami:
   `references/wycofanie.md`. Kolejność ludzi i plan komunikacji wg pm-stakeholders.
5. **Prawo i umowy** — umowy z klientami i SLA, regulamin, eksport i usunięcie danych (RODO), przy usługach
   chmurowych prawo klienta do zmiany dostawcy i przeniesienia danych (Data Act) — z arch-eu-product-law.
6. **Po wyłączeniu** — zmierz: ilu klientów przeszło na zamiennik, ilu odeszło, zgłoszenia do wsparcia,
   oszczędność kosztów; wnioski do dziennika projektu.

## Przykład
Moduł raportów: 4% klientów aktywnych miesięcznie, 1 etat utrzymania, biblioteka wykresów bez wsparcia od roku.
Opcje: utrzymać (koszt 1 etatu, ryzyko bezpieczeństwa), zastąpić eksportem do arkusza + szablonem w narzędziu BI,
wycofać bez zamiennika. Rekomendacja: zastąpić. Kryteria go: 3 z 5 największych klientów modułu akceptują
zamiennik w rozmowach, umowy nie gwarantują modułu. Harmonogram: dzień 0 — zespół wsparcia i opiekunowie
klientów; dzień 7 — rozmowy z kluczowymi klientami; dzień 14 — ogłoszenie w produkcie i e-mail; dzień 14 —
koniec udostępniania nowym klientom; dzień 104 — wyłączenie (90 dni od ogłoszenia), eksport danych dostępny
do dnia 134, potem usunięcie.

## Źródła
- T. Levitt, „Exploit the Product Life Cycle”, *Harvard Business Review* (1965) — etapy i sposoby przedłużania
  życia produktu.
- Rozporządzenie (UE) 2023/2854 (Data Act), rozdział VI — zmiana dostawcy usług przetwarzania danych.
Opisane własnymi słowami.
