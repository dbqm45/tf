**Ładowarki łamią specyfikację**
- Wejście od ładowarki i partnera roamingowego parsujesz tolerancyjnie, wyjście generujesz ściśle wg specyfikacji.
- Brakujące lub nadmiarowe pola, złe typy, zła kolejność komunikatów, zdublowane transakcje i rozjechany zegar to scenariusze testowe, nie wyjątki.
- Odchylenie konkretnego modelu lub firmware zapisujesz (producent, model, wersja firmware, zachowanie, obejście) w dokumentacji projektu.
- Obejście dla jednego producenta trzymasz za jawną flagą, nie w głównej ścieżce dla wszystkich.
