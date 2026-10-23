# Mapa historyjek i dzielenie historyjek

## Mapa historyjek
1. **Kręgosłup** — aktywności użytkownika od lewej do prawej w kolejności, w jakiej je wykonuje („znajdź salę” →
   „zarezerwuj” → „zmień lub odwołaj” → „rozlicz”), pod każdą kroki (np. „filtruj po terminie”, „sprawdź
   wyposażenie”). Opowiadasz historię jednego użytkownika, nie spisujesz modułów systemu.
2. **Historyjki pod krokami** — od góry najważniejsze, niżej warianty, wyjątki i udogodnienia. Istniejący backlog
   rozkładasz pod kroki; historyjka, której nie da się przypiąć do kroku, to sygnał (brak kroku albo zbędna praca).
3. **Linie wydań** — poziome cięcia przez całą mapę. Pierwsze wydanie: najcieńszy plaster przez wszystkie kroki,
   który daje użytkownikowi wynik od początku do końca (chodzący szkielet), nawet jeśli każdy krok jest ubogi.
   Każde wydanie ma nazwany wynik i miarę (proc-product-discovery), nie listę funkcji.
4. **Luki i ryzyka** — kroki bez historyjek, kroki z samymi wariantami bez wersji podstawowej, zależności
   zewnętrzne; oznacz je na mapie i dopisz pytania.
5. **Aktualizacja** — mapa żyje: po każdym wydaniu przesuwasz linie według tego, czego się nauczyliście.

## Wzorce dzielenia za dużej historyjki
Każdy kawałek po podziale nadal daje użytkownikowi coś działającego (pionowo), nie warstwę.
| Wzorzec | Kiedy | Przykład (import wyciągów) |
|---|---|---|
| Kroki przepływu | historyjka obejmuje kilka kroków procesu | wgraj plik → podgląd → zatwierdź → uzgodnij |
| Warianty reguł | reguły biznesowe mają przypadki | najpierw bez dopasowania automatycznego, potem dopasowanie po kwocie, potem po tytule |
| Dane | różne formaty lub źródła danych | najpierw jeden bank i jeden format, kolejne banki osobno |
| Interfejsy | kilka kanałów wejścia | najpierw ręczne wgranie pliku, potem import przez API banku |
| Ścieżki | ścieżka główna i alternatywne | najpierw poprawny plik, potem błędy i duplikaty |
| Proste przed złożonym | jest wersja „wystarczająca” | najpierw ręczne przypisanie, potem podpowiedzi |
| Wydajność później | wymagania wydajności są osobną pracą | najpierw 500 wierszy, potem 50 000 |
| Rozpoznanie (spike) | za dużo niewiadomych, żeby ocenić | ograniczone czasowo rozpoznanie formatu, wynik: decyzja i nowe historyjki |

Kolejność kawałków: najpierw ten, który daje najwięcej wiedzy albo wartości przy najmniejszym ryzyku.
Podział na „backend” i „frontend” albo „baza, API, UI” to zadania, nie historyjki.

## Źródła
- J. Patton, *User Story Mapping* (2014).
- R. Lawrence, „Patterns for Splitting User Stories” (2009); M. Cohn, SPIDR (Spikes, Paths, Interfaces, Data,
  Rules), mountaingoatsoftware.com (2017).
Opisane własnymi słowami.
