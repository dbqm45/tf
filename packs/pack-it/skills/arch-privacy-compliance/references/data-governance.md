# Ład danych: właściciel, klasy, inwentarz

Ład danych odpowiada na trzy pytania o każdy zbiór i pole: **kto za nie odpowiada**, **jak bardzo jest wrażliwe**
i **gdzie jeszcze leży**. Bez tego retencja, prawa osób i reakcja na naruszenie są zgadywaniem.

## 1. Właściciel zbioru
- Każdy zbiór (tabela, temat w kolejce, indeks logów, zbiór w hurtowni) ma **właściciela biznesowego**: osobę lub
  zespół, który decyduje o celu, dostępie, retencji i zmianach schematu. Administrator systemu to nie właściciel.
- Właściciel zatwierdza klasę zbioru i każde nowe pole z danymi osobowymi; agent przygotowuje propozycję.
- Kopie (hurtownia, eksporty, środowiska testowe) dziedziczą klasę i właściciela źródła, chyba że dane zostały
  skutecznie zanonimizowane — wtedy zapisz to jako decyzję.

## 2. Klasy danych i wymagania na klasę

| Klasa | Przykłady | Dostęp | Szyfrowanie | Maskowanie w logach i poza produkcją | Retencja |
|---|---|---|---|---|---|
| publiczne | cennik, opis produktu | każdy | w transmisji | nie trzeba | wg potrzeb |
| wewnętrzne | konfiguracja, metryki bez osób | pracownicy wg roli | w transmisji i w spoczynku | nie trzeba | wg potrzeb |
| poufne | umowy, dane finansowe firmy, klucze | imiennie, najmniejsze uprawnienia, rejestr dostępu | w transmisji i w spoczynku | tak | określona, z usuwaniem |
| dane osobowe | e-mail, telefon, PESEL, adres, IP, identyfikator klienta | imiennie wg celu, rejestr dostępu | w transmisji i w spoczynku; pola o wysokim ryzyku (PESEL, IBAN, dokument) także na poziomie pola | tak: pseudonim (HMAC) albo maska | okres na cel, automatyczne usuwanie |
| szczególne kategorie (art. 9) i dane dzieci | zdrowie, biometria do identyfikacji, poglądy | wąsko, z uzasadnieniem | jak dane osobowe, zawsze na poziomie pola | zawsze; bez kopii w testach | najkrótsza możliwa; zwykle DPIA |

- Zbiór ma klasę najwrażliwszego pola, które zawiera.
- Klasa wyznacza wymagania techniczne. Podstawę prawną i cel ustala się osobno (zasada 2 w SKILL.md).

## 3. Inwentarz danych
Plik `docs/project/04-architecture/data-inventory.md`, jeden wiersz na pole z danymi poufnymi lub osobowymi:

| Zbiór | Pole | Klasa | Cel | Retencja | Właściciel | Gdzie jeszcze leży |
|---|---|---|---|---|---|---|
| `customers` | `email` | dane osobowe | konto, powiadomienia | 2 lata po zamknięciu konta | zespół Konta | logi aplikacji (zamaskowane), mailing (procesor), hurtownia |

- „Gdzie jeszcze leży” to kopie: logi, kopie zapasowe, analityka, hurtownia, kolejki, procesorzy i środowiska
  testowe. Od tej kolumny zależy, czy usunięcie danych na żądanie (zasada 5) w ogóle da się wykonać.
- Inwentarz jest wkładem do rejestru czynności przetwarzania (art. 30), który prowadzi administrator.

**Istniejący system bez inwentarza:**
1. Zrób szkic automatycznie: `tf analyze --only data-classification` wypisuje pola o nazwach typowych dla danych
   osobowych w schematach, migracjach i modelach, a także dane osobowe w logach i w wywołaniach analityki.
2. Uzupełnij szkic o pola, których nazwa nic nie mówi. Przejrzyj próbkę danych z kolumn tekstowych i JSON
   (`notes`, `metadata`, `payload`), robiąc to w środowisku produkcyjnym i bez kopiowania danych.
3. Właściciele zatwierdzają klasy, a potem dopisujesz cel i retencję.
4. Najpierw naprawiasz dane osobowe w logach i w analityce, bo mają najszersze grono odbiorców.

## 4. Klasa przy polu w kodzie
Pole z klasą poufną lub osobową oznacz w miejscu definicji, żeby przegląd zmiany i analiza ją widziały:
- SQL: `email varchar(255) NOT NULL, -- pii: dane osobowe` albo `COMMENT ON COLUMN customers.email IS 'pii'`;
- Prisma: komentarz `/// pii` nad polem;
- ORM: adnotacja lub komentarz przy polu (`# pii`, `// pii`, własna adnotacja `@Pii`).

Nowe pole bez klasy i bez wpisu w inwentarzu zgłasza `tf analyze` (reguła `pii-field-unclassified`).

## 5. Pochodzenie i kontrakty
Pochodzenie danych (lineage) i kontrakty danych między zespołami w potokach opisuje `data-engineering`. Kontrakt
zbioru powinien nieść klasę pól, żeby konsument w hurtowni dostał te same wymagania co źródło.
