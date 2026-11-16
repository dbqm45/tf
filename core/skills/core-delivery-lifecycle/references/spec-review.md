# Przegląd specyfikacji przez panel recenzentów

## Kiedy
Po fazie 3 (wymagania) i przed planem cięć — gdy wymagania mają być realizowane przez agentów (pętla `/tf`, wykonawcy),
zmiana jest duża albo dotyka obszarów z triażu wysokiego ryzyka (`tf risk`: uprawnienia, pieniądze, dane, schemat).
Mała zmiana z kilkoma kryteriami: wystarczy zwykły przegląd planu.

## Panel
2–3 recenzentów, każdy jako osobny podagent w **świeżym kontekście**, bez wglądu w odpowiedzi pozostałych i bez
rozmowy, w której specyfikacja powstała. Każdy dostaje tylko specyfikację (i ADR, jeśli są) oraz swoje zadanie:
- **przeciwnik** — dziury i sprzeczności: wymagania niesprawdzalne, dwuznaczne, sprzeczne ze sobą, brakujące
  przypadki brzegowe, nieograniczony zakres, otwarte pytania udające odpowiedzi;
- **operator** — co się dzieje przy awariach: częściowe zapisy, współbieżność, ponowienia i duplikaty, zależności
  niedostępne, limity, obserwowalność błędów, odzyskiwanie;
- **wykonawca** — czy da się to zbudować i sprawdzić testem w ustalonym stacku: kryteria akceptacji jako testy,
  dane testowe, zależności między wymaganiami, kolejność.
Każde ustalenie: identyfikator (F1…), waga (blokujące / poważne / drobne), wymaganie lub fragment, scenariusz
pokazujący problem, propozycja.

## Przebieg
1. Uruchom recenzentów równolegle (Agent, osobne konteksty); brief zawiera ścieżkę specyfikacji i zadanie, bez
   wniosków autora specyfikacji.
2. Zbierz ustalenia do raportu `03-requirements/spec-review.md` (szablon `spec-review` w core-project-record).
3. Dla każdego ustalenia decyzja: zmiana wymagania (nowy REQ lub poprawka), zapisana decyzja (DEC/ADR) albo
   odrzucenie z powodem. Decyzje biznesowe i rozbieżności rozstrzyga człowiek.

## Odczyt wyników
- **Zbieżne** (wskazało je kilku recenzentów niezależnie) — traktuj jak defekt.
- **Pojedyncze** — do zważenia jedno po drugim; często najcenniejsze (np. pominięty scenariusz awarii).
- **Rozbieżne** (jeden uważa za problem, drugi wprost za poprawne) — decyzja człowieka, zapisana z uzasadnieniem.
- **Niezależność ograniczona:** recenzenci to ten sam dostawca modeli; zgodność to słabszy dowód niż przegląd
  przez ludzi albo różne modele — napisz to w raporcie.

## Bramka
Do planu cięć przechodzisz, gdy wszystkie ustalenia **blokujące i poważne** są zamknięte śladem (identyfikator
wymagania lub decyzji przy ustaleniu). Drobne mogą zostać otwarte z adnotacją. Wykonawca i recenzent zadania mogą
później cytować ustalenie po identyfikatorze (np. odrzucić pracę, która łamie wymaganie dopisane po F5).

## Granice
Panel nie zastępuje rozmowy z ekspertem domeny ani testów — znajduje dziury w tekście, nie w rzeczywistości.
Koszt: kilka przebiegów modelu na specyfikację; przy małych zmianach nie warto.
