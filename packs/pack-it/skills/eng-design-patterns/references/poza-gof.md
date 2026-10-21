# Wzorce spoza GoF: obiekt roli i obiekt rozszerzenia

Dwa wzorce strukturalne z późniejszych katalogów PLoP, przydatne w modelach domenowych, gdy ten sam byt pełni wiele
ról albo dostaje dodatkowe zdolności. Oba zastępują pola-flagi i rosnące pole „status” (ddd-deep-modeling,
`.claude/skills/ddd-deep-modeling/references/rozplatywanie.md`).

## Obiekt roli (Role Object)
- **Problem:** ta sama osoba albo firma jest jednocześnie klientem, dostawcą i pracownikiem. Każda rola ma własne
  dane, reguły i cykl życia, a role pojawiają się i znikają w czasie. Jedna klasa z polami `isCustomer`,
  `isSupplier` i ich danymi rośnie bez końca. Podklasy (`KlientDostawca`) wybuchają kombinatorycznie i nie pozwalają
  zmienić roli w trakcie życia obiektu.
- **Rozwiązanie i uczestnicy:**
  - **rdzeń** (core): tożsamość i dane wspólne, np. osoba z imieniem i adresem;
  - **obiekty ról:** osobne obiekty z danymi i zachowaniem roli (`Klient` z limitem kredytowym, `Dostawca`
    z warunkami dostaw), które wskazują rdzeń;
  - rdzeń pozwala zapytać o rolę, dodać ją i usunąć (`hasRole`, `getRole`, `addRole`, `removeRole`).
- **Kiedy używać:** role są niezależne, dochodzą i znikają w czasie albo każda ma własne reguły i właściciela.
- **Koszty:** tożsamość jest rozbita na kilka obiektów; trzeba pilnować, by rola nie istniała bez rdzenia, i ustalić,
  gdzie żyją dane wspólne.
- **W modelu domenowym:** rola to często osobny agregat w innym kontekście, wskazujący stronę identyfikatorem.
  Archetyp Party i PartyRole (`.claude/skills/ddd-archetypes/references/party.md`) to ten wzorzec na poziomie
  modelu biznesowego.
- **Kiedy NIE:** rola nie ma własnych danych ani reguł, tylko zmienia uprawnienia; wtedy wystarczy atrybut albo
  mechanizm autoryzacji.

## Obiekt rozszerzenia (Extension Object)
- **Problem:** do istniejącej klasy trzeba dokładać interfejsy, których potrzebują tylko niektórzy klienci, np.
  dokument z rozszerzeniem „podpisywalny” albo „do druku”. Dopisanie metod do klasy bazowej rozdyma ją i zmusza
  wszystkie podklasy do implementacji.
- **Rozwiązanie i uczestnicy:**
  - **podmiot** z jedną metodą dostępu do rozszerzenia po nazwie albo typie, np. `getExtension("podpis")`;
  - **rozszerzenia:** osobne obiekty z dodatkowym interfejsem, dołączane do podmiotu;
  - klient pyta o rozszerzenie i obsługuje jego brak.
- **Kiedy używać:** zestaw dodatkowych interfejsów jest otwarty, a o tym, które obiekty je mają, decyduje się
  w czasie działania, np. we wtyczkach albo w rozszerzeniach dodawanych przez inne moduły.
- **Koszty:** klient musi sprawdzać, czy rozszerzenie istnieje; interfejs podmiotu przestaje mówić, co obiekt potrafi.
- **Różnica:** obiekt roli dotyczy ról w modelu biznesowym z cyklem życia, a obiekt rozszerzenia dotyczy dodatkowych
  interfejsów technicznych. Dekorator zachowuje interfejs i dokłada zachowanie wokół wywołań, a obiekt rozszerzenia
  dodaje nowy interfejs obok.
- **Kiedy NIE:** rozszerzeń jest kilka i są znane z góry; wtedy wystarczy zwykły interfejs albo unia typów.
  W TS często wystarczy mapa rozszerzeń po kluczu typu.

## Źródła
- D. Bäumer, D. Riehle, W. Siberski, M. Wulf, „Role Object”, PLoP '97; przedruk w *Pattern Languages of Program
  Design 4* (red. N. Harrison, B. Foote, H. Rohnert), Addison-Wesley, 2000, s. 15–32 [niezweryfikowane: dane
  bibliograficzne z katalogów i źródeł wtórnych, bez lektury tekstu w tej sesji].
- E. Gamma, „Extension Object”, w: *Pattern Languages of Program Design 3* (red. R. Martin, D. Riehle, F. Buschmann),
  Addison-Wesley, 1998, ISBN 0201310112 [niezweryfikowane: jak wyżej].
- Opisane własnymi słowami; zakres na podstawie programu szkolenia „DDD — zaawansowane techniki modelowania
  i archetypy” (Bottega IT Minds, materiał od człowieka, 2026-10-21).
