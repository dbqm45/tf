# Usuwanie: soft delete, kosz i usunięcie danych

## Kiedy soft delete
- Tak: potrzebne przywracanie (kosz), rekord jest celem relacji (faktury wskazują klienta), audyt lub rozliczenia
  wymagają historii.
- Nie: dane osobowe na żądanie usunięcia, dane bez wartości historycznej (sesje, tokeny, logi techniczne), tabele,
  w których filtr `deleted_at IS NULL` byłby wszędzie i łatwo go zapomnieć.

## Pułapki implementacji
- Filtr domyślny (zakres w ORM, widok, polityka RLS) — inaczej usunięte rekordy wracają w raportach, wyszukiwarce,
  eksporcie i licznikach.
- Unikalność: indeks unikalny częściowy `WHERE deleted_at IS NULL`, żeby po usunięciu można było użyć tej samej
  nazwy lub e-maila.
- Kaskady: co dzieje się z dziećmi (oznaczyć razem, zostawić, zablokować usunięcie) — decyzja jawna.
- Pliki w magazynie obiektów i dane w wyszukiwarce lub cache usuwasz albo ukrywasz razem z rekordem.

## Kosz i nieodwracalne usuwanie
- Usunięcie z dużym skutkiem: uprawnienie (właściciel), potwierdzenie przez wpisanie nazwy z liczbą elementów,
  które znikną; dla krytycznych ponowne uwierzytelnienie lub drugi czynnik.
- Okres karencji (np. 30 dni) z przywracaniem, potem trwałe usunięcie zadaniem w tle; powiadomienie osób, których
  dotyczy.

## Żądanie usunięcia danych osobowych (RODO art. 17)
- `deleted_at` nie wystarcza: dane nadal są w bazie. Usunięcie trwałe albo anonimizacja (nieodwracalna, bez
  klucza do przywrócenia; pseudonimizacja to nadal dane osobowe).
- Obejmuje: tabele aplikacji, pliki, wyszukiwarkę, analitykę, systemy zewnętrzne i podwykonawców, logi i audyt
  (pseudonimizacja), kopie zapasowe (zwykle wygasają z rotacją; dokumentujesz termin i nie przywracasz usuniętych
  danych przy odtwarzaniu).
- Wyjątki (obowiązek prawny, np. dokumenty księgowe) — dane zostają tylko w zakresie wymaganym; decyzja i podstawa
  zapisane. Ocena prawna: arch-privacy-compliance.
