# Znakowanie treści generowanych przez AI (art. 50 ust. 2)

Spis treści: 1. Obowiązek i kodeks praktyk · 2. Warstwy znakowania · 3. Znak wodny w tekście · 4. Ograniczenia ·
5. Co wpisać do dokumentacji zgodności

## 1. Obowiązek i kodeks praktyk
- Art. 50 ust. 2 AI Act: dostawca systemu generującego dźwięk, obraz, wideo albo tekst zapewnia, że wyniki są
  oznaczone w formacie nadającym się do odczytu maszynowego i wykrywalne jako wygenerowane lub zmanipulowane
  sztucznie. Rozwiązania techniczne mają być skuteczne, interoperacyjne, solidne i niezawodne w zakresie technicznie
  wykonalnym, z uwzględnieniem specyfiki i ograniczeń rodzajów treści, kosztów wdrożenia i powszechnie uznanego stanu
  wiedzy (jak może go odzwierciedlać norma). Art. 50 stosuje się od **2026-08-02**. (Streszczenie obowiązku ze
  strony Komisji o kodeksie; dosłowne brzmienie przed cytowaniem sprawdź w eur-lex.)
- **Kodeks praktyk w sprawie przejrzystości treści generowanych przez AI** (*Code of Practice on Transparency of
  AI-generated Content*; wersja końcowa opublikowana 2026-06-10, przygotowana przez niezależnych ekspertów przy
  udziale Urzędu ds. AI). Stan ze strony Komisji (2026-11-01):
  - **dobrowolny**, ale obowiązki z art. 50 są prawne; kodeks nie zastępuje AI Act ani wytycznych Komisji do art. 50;
  - obejmuje art. 50 ust. 2, 4 i 5 w dwóch sekcjach: **1 — dostawcy** (oznaczanie i wykrywanie treści generowanych
    i zmanipulowanych), **2 — podmioty stosujące** (etykietowanie deepfake'ów i tekstów publikowanych w sprawach
    interesu publicznego, chyba że przeszły redakcję człowieka z odpowiedzialnością redakcyjną);
  - Komisja i Rada ds. AI uznały kodeks za **adekwatne dobrowolne narzędzie wykazania zgodności**: sygnatariusz
    może się powołać na jego środki, a kto spełnia obowiązek inaczej, sam wykazuje adekwatność przed organem
    nadzoru rynku;
  - UE udostępnia ikony do etykietowania treści AI dla podmiotów stosujących;
  - ok. 190 sygnatariuszy do końca lipca 2026.
- **Szczegóły sekcji 1 (wg omówień, nie z tekstu kodeksu)** [niezweryfikowane]: co najmniej dwie warstwy
  maszynowego oznaczania (zabezpieczone metadane i znak wodny, odcisk opcjonalnie) i narzędzie do wykrywania
  udostępniane przez dostawcę. Przed wdrożeniem przeczytaj PDF kodeksu (link na stronie Komisji).
- **Wytyczne Komisji do art. 50** (zakres obowiązków): projekt opublikowany 2026-05-08 z konsultacją; czy i kiedy
  przyjęto wersję końcową, sprawdź na stronie Komisji [niezweryfikowane]. Termin 2026-12-02 dla systemów
  wprowadzonych przed 2026-08-02 podają tylko omówienia [niezweryfikowane].

## 2. Warstwy znakowania
| Warstwa | Dla jakiej treści | Co przetrwa | Co ją usuwa |
|---|---|---|---|
| **Metadane z podpisem** (C2PA Content Credentials: manifest z twierdzeniami, podpisany, powiązany ze skrótem pliku) | obraz, wideo, dźwięk, dokumenty | weryfikowalne pochodzenie i historia edycji | zrzut ekranu, ponowne kodowanie, usunięcie metadanych przez platformę |
| **Znak wodny** (w samej treści) | obraz, dźwięk, wideo; tekst statystycznie | kompresja, przycięcie (w granicach odporności algorytmu) | silna edycja, parafraza tekstu |
| **Odcisk** (fingerprint, porównanie z bazą dostawcy) | każda | wykrywanie po stronie dostawcy | treść poza bazą |

C2PA wiąże metadane z treścią także przez „soft binding” (znak wodny lub odcisk, który pozwala odnaleźć manifest po
jego usunięciu z pliku); listę algorytmów prowadzi C2PA. Jedna warstwa nie wystarcza, bo każda ma inny sposób
utraty.

## 3. Znak wodny w tekście
Wzorzec z pracy Kirchenbauer i in. („A Watermark for Large Language Models”, ICML 2023):
- przed wygenerowaniem tokenu ziarno z poprzedniego tokenu dzieli słownik na listę „zieloną” i „czerwoną”,
  a próbkowanie lekko faworyzuje zielone tokeny;
- wykrywanie bez dostępu do modelu i bez klucza API, jeśli reguła jest jawna (albo za API, jeśli jest prywatna):
  test z na liczbie zielonych tokenów (oczekiwana wartość γT przy braku znaku);
- wg autorów znak jest wykrywalny już od ok. **25 tokenów**, a fałszywy alarm na tekście człowieka jest
  statystycznie mało prawdopodobny (przy progu z = 4 jednostronne p ≈ 3 × 10⁻⁵);
- znak jest silny tylko w tekście o **wysokiej entropii**. Tekst o niskiej entropii (kod, formułki, tekst
  zapamiętany i odtworzony przez model) prawie nie przenosi znaku i bywa niewykrywalny; autorzy wskazują to jako
  główną przyczynę pominięć.

## 4. Ograniczenia
Ataki skatalogowane przez autorów (sekcja „Attacking the watermark”):
- **Wstawianie, usuwanie i podmiana tokenów**, w tym **parafraza** automatyczna słabszym modelem (osłabia znak
  i jakość tekstu) albo ręczna. W długich tekstach kilka niezmienionych zdań często wystarcza do wykrycia.
- **Drobne zmiany** (spacje, literówki) i **ataki na tokenizację**: detektor normalizuje tekst przed liczeniem
  skrótu.
- **Homoglify i znaki zerowej szerokości**: detektor kanonizuje Unicode, inaczej podmiana znaków usuwa znak wodny.
- **Ataki generatywne** („emoji attack”: model wstawia znaki po każdym tokenie, które potem się usuwa).
- **Odkrycie reguły z próbek**: obserwując pary tokenów, napastnik może poznać listy; zalecane małe okno h i klucz
  trzymany prywatnie.

Spoza tej pracy [niezweryfikowane — literatura wtórna]: **podrabianie znaku** (oznaczenie cudzego tekstu jako
„z modelu”) i **„piggyback”** (treść zmieniona przez człowieka, także szkodliwie, nadal wykrywa się jako
wygenerowana).
- **Metadane** giną przy zrzucie ekranu i na platformach, które je usuwają.

## 5. Co wpisać do dokumentacji zgodności
- Znakowanie **wspiera wykrywanie masowe** (platformy, moderacja). Nie jest dowodem, że konkretny tekst wygenerował
  konkretny system, i nie przypisuje autorstwa pojedynczej osobie.
- Opisz warstwy (metadane C2PA + znak wodny, ewentualnie odcisk), zakres treści, narzędzie do wykrywania i znane
  ograniczenia. Wpisz test odporności na typowe przekształcenia (kompresja, przycięcie, parafraza) z wynikiem.
- Czy przyjęte rozwiązanie spełnia art. 50 ust. 2, ocenia prawnik na podstawie aktualnego tekstu kodeksu praktyk
  i wytycznych. Ten plik opisuje technikę, nie interpretację prawa.

Źródła: Komisja Europejska, „Code of Practice on Transparency of AI-generated Content”,
digital-strategy.ec.europa.eu/policies/code-practice-ai-generated-content (wydruk strony z 2026-11-01, przekazany
przez człowieka); szczegóły sekcji 1 wg omówień Jones Day, SCL, Freshfields (2026-06); rozporządzenie (UE) 2024/1689,
art. 50 (tekst w eur-lex niesprawdzony w tej sesji); J. Kirchenbauer i in., „A Watermark for Large Language Models”,
arXiv 2301.10226v4 (ICML 2023; PDF przekazany przez człowieka, przeczytane: wstęp, sekcje o entropii i atakach);
github.com/c2pa-org/specifications (wersja dokumentacji 2.5, commit 2026-10-28; soft binding, `softbinding-alg-list`).
