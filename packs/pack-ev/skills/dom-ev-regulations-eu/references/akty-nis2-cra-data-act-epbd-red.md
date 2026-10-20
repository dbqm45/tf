# NIS2, CRA, Data Act, EPBD, RED III — co czytać i jak stosować

> **Spis treści:** 1. NIS2 — dyrektywa (UE) 2022/2555, EN · 2. CRA — rozporządzenie (UE) 2024/2847, PL · 3. Data Act — rozporządzenie (UE) 2023/2854, EN · 4. EPBD — dyrektywa (UE) 2024/1275, wersja skonsolidowana… · 5. RED III — dyrektywa (UE) 2023/2413, EN (zmienia… · 6. Jak te akty łączą się ze sobą

Wszystkie teksty wczytane 2026-10-20 z plików od człowieka; linie dotyczą `.claude/knowledge/<id>/doc.txt`.
To nie porada prawna. Dyrektywy (NIS2, EPBD, RED III) wiążą firmę dopiero przez prawo krajowe: Polska — dom-ev-regulations-pl.

## Spis treści
1. NIS2 (`eu-nis2`)
2. CRA (`eu-cra`)
3. Data Act (`eu-data-act`)
4. EPBD (`eu-epbd`)
5. RED III (`eu-red-iii`)
6. Jak te akty łączą się ze sobą

## 1. NIS2 — dyrektywa (UE) 2022/2555, EN
| Temat | Wg tekstu | Linie |
|---|---|---|
| Zakres | podmioty typu z Aneksu I lub II, które są średnimi przedsiębiorstwami lub większymi (Zalecenie 2003/361/WE); mniejsze tylko w wyjątkach Art. 2(2) (np. jedyny dostawca w państwie, istotny dla kraju lub regionu) | Art. 2: 1892 |
| CPO | Aneks I, sektor 1 Energia, (a) Elektryczność: „operatorzy punktu ładowania odpowiedzialni za zarządzanie i działanie punktu, który świadczy usługę ładowania użytkownikom końcowym, także w imieniu i na rzecz eMSP” | 4199 |
| eMSP bez własnych punktów | nie jest wymieniony jako typ podmiotu w Aneksie I sektor 1; ocena przez inne typy (np. usługi chmurowe, zarządzane w Aneksie I pkt 8-9) | **[do weryfikacji]** |
| Producent ładowarki | Aneks II pkt 5(c): produkcja sprzętu elektrycznego (NACE sekcja C dział 27); czy ładowarka tam wpada — **[założenie]**, zależy od kodu działalności | 4376, 4416 |
| Rodzaj podmiotu | kluczowy: Aneks I i powyżej progów średniego przedsiębiorstwa; ważny: pozostałe z Aneksu I lub II | Art. 3: 2003 |
| Środki | polityka analizy ryzyka, obsługa incydentów, ciągłość działania, bezpieczeństwo łańcucha dostaw, bezpieczeństwo w nabywaniu i rozwoju systemów z obsługą podatności, kryptografia, kontrola dostępu, MFA | Art. 21(2): 3119 |
| Zgłoszenia | poważny incydent: ostrzeżenie wczesne do 24 h, zgłoszenie do 72 h, raport pośredni na żądanie, raport końcowy do miesiąca; powiadomienie odbiorców usług przy zagrożeniu | Art. 23: 3219 |
| Poważny incydent | powoduje lub może powodować poważne zakłócenie usług albo stratę finansową, albo znaczną szkodę innych osób | Art. 23(3) |
| Kary | podmioty kluczowe do co najmniej 10 mln EUR lub 2 % obrotu; ważne do co najmniej 7 mln EUR lub 1,4 % | Art. 34: 3920, 3936 |
| Transpozycja | do 17.10.2024, stosowanie od 18.10.2024; listy podmiotów do 17.04.2025 | Art. 41: 4109; Art. 3(3) |

Dla CPMS: rejestr incydentów z czasem „uzyskania wiedzy” (start zegara 24 h), kanał do CSIRT, klauzule dla dostawców
CPMS i producentów ładowarek (łańcuch dostaw, Art. 21(2)(d) i 21(3)), MFA i kontrola dostępu do konsoli CPO. Przykładowy
próg: 120 pracowników to zwykle średnie przedsiębiorstwo, czyli podmiot ważny, jeśli obrót nie przekracza pułapu
(progi z Zalecenia 2003/361/WE nie są w bazie, **[do weryfikacji]**; partnerzy i powiązania zmieniają liczenie).

## 2. CRA — rozporządzenie (UE) 2024/2847, PL
| Temat | Wg tekstu | Linie |
|---|---|---|
| Zakres | produkty z elementami cyfrowymi udostępniane na rynku, których przeznaczenie obejmuje bezpośrednie lub pośrednie połączenie danych z urządzeniem lub siecią | Art. 2(1): 1948 |
| Wyłączenia | pojazdy wg rozp. (UE) 2019/2144, wyroby medyczne, lotnictwo; części zamienne identyczne | Art. 2(2)-(6) |
| Produkt | oprogramowanie lub sprzęt plus powiązane **zdalne przetwarzanie danych** (oprogramowanie projektowane przez producenta lub na jego odpowiedzialność, bez którego produkt nie spełni funkcji) | Art. 3 pkt 1-2: 2002 |
| Chmura/SaaS | funkcje chmurowe producenta, bez których urządzenie nie działa, wchodzą; chmura poza odpowiedzialnością producenta oraz SaaS, PaaS, IaaS podlegają NIS2 | motyw (12), ok. 182 |
| Producent | ocena ryzyka (Art. 13(2)-(3)), staranność przy komponentach obcych i open source (13(5)), dokumentacja podatności (13(7)), obsługa podatności w okresie wsparcia (13(8)); okres wsparcia co najmniej 5 lat, krócej tylko gdy produkt ma być używany krócej | Art. 13: 2425 |
| Wymagania | Aneks I część I: brak znanych podatności, bezpieczna konfiguracja domyślna z resetem, aktualizacje (opt-out), kontrola dostępu, szyfrowanie, integralność, minimalizacja danych, odporność na DoS, ograniczona powierzchnia ataku, logowanie, bezpieczne usunięcie danych; część II: SBOM (zestawienie komponentów, co najmniej najwyższy poziom zależności), polityka skoordynowanego ujawniania, adres do zgłoszeń, bezpłatne aktualizacje, regularne testy | Aneks I: 4550 |
| Zgłaszanie | aktywnie wykorzystywana podatność: ostrzeżenie do 24 h, zgłoszenie do 72 h, raport końcowy do 14 dni po środku zaradczym; poważny incydent wpływający na bezpieczeństwo produktu: 24 h, 72 h, raport do miesiąca; przez jedną platformę (Art. 16) do CSIRT koordynatora i ENISA | Art. 14: 2637, Art. 16: 2802 |
| Ocena zgodności | domyślnie kontrola wewnętrzna (moduł A); badanie typu lub pełne zapewnienie jakości dla produktów ważnych z Aneksu III (klasy I i II); Aneks III nie wymienia wprost ładowarki ani CPMS — klasyfikacja **[do weryfikacji]** | Art. 32: 3377; Aneks III: 4691 |
| Deklaracja i CE | Art. 28 deklaracja zgodności UE, Art. 29-30 oznakowanie CE, Art. 31 dokumentacja techniczna (Aneks VII) | 3260-3377 |
| Terminy | stosowanie od 11.12.2027; **Art. 14 od 11.09.2026**; rozdział IV (jednostki notyfikowane) od 11.06.2026 | Art. 71: 4521 |
| Produkty starsze | wprowadzone przed 11.12.2027 podlegają CRA tylko po istotnej modyfikacji, ale Art. 14 stosuje się do wszystkich takich produktów | Art. 69(2)-(3): 4497 |

Dla firmware i aplikacji: proces PSIRT i polityka ujawniania podatności już dziś (Art. 14 działa), SBOM w repozytorium,
podpisane aktualizacje OTA, okres wsparcia podany w dokumentacji i na stronie, zgłoszenie aktywnie wykorzystywanej luki
w ciągu 24 h od wiedzy. Parametry techniczne OCPP security: dom-ev-ocpp-2x.

## 3. Data Act — rozporządzenie (UE) 2023/2854, EN
| Temat | Wg tekstu | Linie |
|---|---|---|
| Zakres | producenci produktów skomunikowanych i dostawcy usług powiązanych, posiadacze danych, użytkownicy w UE, dostawcy usług przetwarzania danych | Art. 1: 2020 |
| Produkt skomunikowany | przedmiot, który uzyskuje, generuje lub zbiera dane o użyciu lub otoczeniu i może przekazywać dane produktu; ładowarka i pojazd spełniają to opisowo | Art. 2 pkt 5: 2172 |
| Usługa powiązana | usługa cyfrowa połączona z produktem tak, że jej brak uniemożliwiłby funkcję produktu, lub dodana później; aplikacja lub CPMS producenta — **[założenie]**, ocena per przypadek | Art. 2 pkt 6 |
| Dostęp domyślny | produkt zaprojektowany tak, by dane były łatwo, bezpiecznie, bezpłatnie, w czytelnej maszynowo formie dostępne dla użytkownika; dotyczy produktów wprowadzonych **po 12.09.2026** | Art. 3(1): 2379; Art. 50: 4690 |
| Informacja przed umową | rodzaj, format i szacowana ilość danych, czy ciągłe, gdzie przechowywane, jak uzyskać dostęp; dla usług: kto jest posiadaczem danych, jak udostępnić stronie trzeciej, prawo skargi | Art. 3(2)-(3) |
| Żądanie użytkownika | gdy użytkownik nie ma bezpośredniego dostępu, posiadacz danych udostępnia dane bez zbędnej zwłoki, bezpłatnie, ciągle i w czasie rzeczywistym tam, gdzie wykonalne | Art. 4(1): 2447 |
| Strona trzecia | na żądanie użytkownika dane trafiają do wskazanej strony trzeciej (nie do gatekeeperów DMA) | Art. 5: 2569 |
| Dane osobowe | tylko przy podstawie z art. 6 RODO; dane nieosobowe używane przez posiadacza wyłącznie na podstawie umowy z użytkownikiem | Art. 4(12)-(14) |
| Wyłączenie | mikro i małe przedsiębiorstwa (bez powiązań z większymi) w rozdziale II | Art. 7: 2727 |
| Zmiana dostawcy chmury | umowa z prawem zmiany: wypowiedzenie do 2 miesięcy, okres przejściowy do 30 dni, odzyskanie danych co najmniej 30 dni; od 12.01.2027 bez opłat za zmianę | Art. 25: 3572; Art. 29: 3709 |
| Stosowanie | od 12.09.2025; rozdział IV (nieuczciwe warunki B2B) dla umów po 12.09.2025 | Art. 50 |

Dla CPMS: katalog danych ładowarki i sesji (kWh, moc, czas, błędy), wniosek użytkownika przez konto, eksport w JSON/CSV,
rozróżnienie danych osobowych (RODO), umowa z chmurą z klauzulami wyjścia i eksportem. Jeśli CPMS oferujesz jako SaaS,
możesz być dostawcą „usługi przetwarzania danych” wobec klientów (rozdział VI) — **[do weryfikacji]**.

## 4. EPBD — dyrektywa (UE) 2024/1275, wersja skonsolidowana EN 24.05.2026
| Temat | Wg tekstu | Linie |
|---|---|---|
| Definicje | punkt ładowania wg AFIR Art. 2 pkt 48; pre-okablowanie = środki niezbędne do późniejszego montażu punktów, w tym transmisja danych, kable, trasy kablowe i liczniki | Art. 2 pkt 33-34: 315 |
| Budynki niemieszkalne nowe lub po gruntownej renowacji, > 5 miejsc | jeden punkt na 5 miejsc; pre-okablowanie dla co najmniej 50 % miejsc i kanały dla reszty; biura: jeden punkt na 2 miejsca | Art. 14(1): 1639 |
| Wszystkie niemieszkalne > 20 miejsc | do 01.01.2027 jeden punkt na 10 miejsc albo kanały dla co najmniej 50 %; budynki organów publicznych: pre-okablowanie 50 % do 01.01.2033 | Art. 14(2) |
| Mieszkalne > 3 miejsca | pre-okablowanie 50 % i kanały dla reszty; nowe: co najmniej jeden punkt; wymiarowanie dla jednoczesnego użycia na wszystkich miejscach | Art. 14(4) |
| Smart i protokoły | punkty z ust. 1, 2, 4 zdolne do smart charging i, gdzie stosowne, dwukierunkowego; sterowane niezastrzeżonymi i niedyskryminującymi protokołami w sposób interoperacyjny, zgodnie z normami i aktami z AFIR Art. 21(2)-(3) | Art. 14(6) |
| Punkty niepubliczne | państwa zachęcają do zasad cenowych z AFIR Art. 5(4) | Art. 14(7) |
| Dane budynku | dostęp właścicieli, najemców i zarządców do danych systemów budynku, w tym punktów ładowania, za zgodą dla stron trzecich | Art. 16(1): 1928 |
| Transpozycja | do 29.05.2026 (Art. 14 objęty) | Art. 35: 3195 |

Dla CPMS: budynek z pre-okablowaniem to potencjalny klient; projektuj zarządzanie obciążeniem (load management) dla wielu
punktów za jednym przyłączem; protokoły otwarte (OCPP, ISO 15118) spełniają ducha Art. 14(6) — dosłowna zgodność **[do weryfikacji]**.
Przepisy krajowe: dom-ev-regulations-pl.

## 5. RED III — dyrektywa (UE) 2023/2413, EN (zmienia dyrektywę 2018/2001)
| Temat | Wg tekstu | Linie |
|---|---|---|
| Definicje | smart recharging (dynamiczna regulacja na podstawie informacji z komunikacji), bi-directional recharging (wg AFIR), power set point | pkt 14m-14o: 1658 |
| Dane z sieci | OSP i OSD udostępniają udział OZE i emisyjność energii w strefie, w odstępach do godziny, w formacie czytelnym m.in. dla punktów ładowania | Art. 20a(1)-(2): 2924 |
| Dane baterii i pojazdu | państwa wymagają od producentów pojazdów udostępniania w czasie rzeczywistym danych o SoH, SoC, power set point, pojemności i, gdzie stosowne, lokalizacji, właścicielom oraz osobom trzecim działającym w ich imieniu, w tym **eMSP** i uczestnikom rynku energii, bez dyskryminacji i bez opłat | Art. 20a(3) |
| Punkty niepubliczne | nowe i wymieniane normalne punkty niepubliczne mają obsługiwać smart charging, interfejs z licznikiem inteligentnym i, gdzie stosowne, dwukierunkowe ładowanie; dyrektywa odsyła do AFIR Art. 15(3)-(4) | Art. 20a(4) |
| Rynek energii | pojazdy i małe zasoby mają uczestniczyć w rynkach (zarządzanie ograniczeniami, bilansowanie, agregacja) | Art. 20a(5) |
| Kredyty OZE | operatorzy publicznych punktów ładowania otrzymują kredyty za dostarczanie odnawialnej energii pojazdom i mogą je sprzedać dostawcom paliw | Art. 25(4) 2018/2001: 3532 |
| Transpozycja | do 21.05.2025 | Art. 5: 4618 |

Uwaga: odesłanie w Art. 20a(4) RED III do AFIR „Art. 15(3) i (4)” nie pasuje do tekstu AFIR z 08.01.2026, w którym Art. 15(3) to ocena
państw dotycząca elastyczności pojazdów (linia 1610); nie wyprowadzaj z niego dodatkowych obowiązków **[do weryfikacji]**.
Dla CPMS: dostęp do SoC i SoH przez eMSP w smart charging, sygnały cenowe i emisyjności sieci jako wejście planisty, dane
OZE do kredytów. Obowiązek producentów pojazdów realizują przepisy krajowe, nie bezpośrednio dyrektywa.

## 6. Jak te akty łączą się ze sobą
| Zdarzenie | Akty |
|---|---|
| Incydent cyber w CPMS, który dotyka ładowarek | NIS2 Art. 23 (CPO), CRA Art. 14 (producent, jeśli luka w produkcie), RODO (naruszenie danych) |
| Nowy model ładowarki z aplikacją | CRA, Data Act Art. 3, RED DA / EN 18031 (radio, dla wprowadzonych do 10.12.2027; potem CRA — rozp. 2026/339), MID (licznik), AFIR Aneks II |
| Dane sesji dla klienta flotowego | Data Act Art. 4-5, RODO, AFIR Art. 20 dla danych publicznych punktu |
| Garaż biurowy z load management | EPBD Art. 14, AFIR Art. 5(4) (cena niepubliczna), RED III Art. 20a(4) |
