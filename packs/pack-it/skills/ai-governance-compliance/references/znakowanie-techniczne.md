# Znakowanie treści generowanych przez AI (art. 50 ust. 2)

Spis treści: 1. Obowiązek i kodeks praktyk · 2. Warstwy znakowania · 3. Znak wodny w tekście · 4. Ograniczenia ·
5. Co wpisać do dokumentacji zgodności

## 1. Obowiązek i kodeks praktyk
- Art. 50 ust. 2 AI Act: dostawca systemu generującego syntetyczny dźwięk, obraz, wideo albo tekst zapewnia, że
  wyniki są oznaczone w formacie nadającym się do odczytu maszynowego i wykrywalne jako wygenerowane lub
  zmanipulowane przez AI. Rozwiązania mają być skuteczne, interoperacyjne, solidne i niezawodne w granicach
  technicznych możliwości. Treść przepisu przed cytowaniem sprawdź w eur-lex (z sieci tej sesji niedostępna)
  [niezweryfikowane dosłownie].
- **Kodeks praktyk w sprawie oznaczania i etykietowania treści generowanych przez AI** (Komisja Europejska,
  wersja końcowa opublikowana 2026-06-10; dobrowolny). Wg omówień:
  - dla dostawców (art. 50 ust. 2) co najmniej dwie warstwy maszynowego oznaczania: zabezpieczone metadane i znak
    wodny, odcisk (fingerprinting) opcjonalnie;
  - dostawca udostępnia narzędzie do wykrywania znaku w treści ze swojego systemu;
  - dla podmiotów stosujących (art. 50 ust. 4) widoczne etykiety, w tym ikona UE i jej umiejscowienie;
  - podpisanie i wdrożenie kodeksu daje domniemanie zgodności z art. 50.

  [niezweryfikowane w tekście kodeksu — źródła wtórne, kancelarie prawne, 2026-06].
- Terminy: art. 50 stosuje się od 2026-08-02; systemy wprowadzone wcześniej mają czas na znakowanie maszynowe do
  2026-12-02 (wg omówień). Wytyczne Komisji do art. 50 — sprawdź, czy i kiedy przyjęto, bo źródła podają różne daty
  [niezweryfikowane].

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
- wykrywanie bez dostępu do modelu: test z na liczbie zielonych tokenów (oczekiwana wartość γT przy braku znaku);
- skuteczność rośnie z długością tekstu, a spada dla tekstu o niskiej entropii (kod, formułki, tekst zapamiętany),
  bo tam model ma mało swobody wyboru tokenu.

## 4. Ograniczenia
- **Parafraza** (człowiek albo inny model), wstawianie i usuwanie słów obniżają wynik testu poniżej progu.
- **Sztuczki znakowe:** homoglify i znaki zerowej szerokości. Detektor kanonizuje Unicode przed testem.
- **Kradzież i podrabianie znaku:** znając schemat z próbek, napastnik może oznaczyć cudzy tekst jako „z modelu”.
- **„Piggyback”:** treść zmieniona przez człowieka (także szkodliwie) nadal wykrywa się jako wygenerowana.
- **Metadane** giną przy zrzucie ekranu i na platformach, które je usuwają.

## 5. Co wpisać do dokumentacji zgodności
- Znakowanie **wspiera wykrywanie masowe** (platformy, moderacja). Nie jest dowodem, że konkretny tekst wygenerował
  konkretny system, i nie przypisuje autorstwa pojedynczej osobie.
- Opisz warstwy (metadane C2PA + znak wodny, ewentualnie odcisk), zakres treści, narzędzie do wykrywania i znane
  ograniczenia. Wpisz test odporności na typowe przekształcenia (kompresja, przycięcie, parafraza) z wynikiem.
- Czy przyjęte rozwiązanie spełnia art. 50 ust. 2, ocenia prawnik na podstawie aktualnego tekstu kodeksu praktyk
  i wytycznych. Ten plik opisuje technikę, nie interpretację prawa.

Źródła: rozporządzenie (UE) 2024/1689, art. 50 (eur-lex niedostępne z sieci sesji, treść wg omówień); Komisja
Europejska, kodeks praktyk w sprawie oznaczania i etykietowania treści AI (2026-06-10) — omówienia Jones Day, SCL,
Freshfields (dostęp przez wyszukiwarkę 2026-11-01); J. Kirchenbauer i in., arXiv 2301.10226 (ICML 2023);
github.com/c2pa-org/specifications (wersja dokumentacji 2.5, commit 2026-10-28; soft binding, `softbinding-alg-list`).
