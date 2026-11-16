# Kontrakt delegacji — szablon, przykłady, dry run

## 1. Szablon do wypełnienia
Skopiuj do polecenia (część pól przenieś do konfiguracji środowiska — tabela w §2). Pole puste = decyzja jeszcze
niepodjęta, nie „domyślnie”.
```text
Cel i warunek „gotowe”: <co ma istnieć / które polecenie ma przejść z kodem 0>
Zakres – edytuj:        <ścieżki>
Zakres – tylko czytaj:  <ścieżki>
Nie rób:                <merge, push na main, zmiany w kodzie produkcyjnym, migracje, zmiany zależności>
Setup:                  <polecenia skryptu startowego; narzędzia, które zakładasz w obrazie>
Sieć:                   <wyłączona po setupie | allowlista: host1, host2>
MCP / konfiguracja:     <tylko .mcp.json z repo | brak>
Sekrety:                <brak | nazwa, zakres tylko do odczytu, czas życia>
Stop:                   <warunek + limit tur + budżet + czas>
Niejednoznaczność:      wybierz wariant zachowawczy i zapisz go w raporcie; nie pytaj
Raport:                 <co zrobiono, założenia, niepewności, lista do sprawdzenia przez człowieka>
Kryteria przeglądu:     <diff tylko w zakresie; testy/bramki z wynikiem; brak próśb o szersze uprawnienia>
```

## 2. Gdzie co ustawić
| Decyzja | Konfiguracja środowiska | Polecenie dla agenta |
|---|---|---|
| setup, narzędzia | skrypt startowy sandboxa | — (agent nie instaluje w trakcie) |
| sieć | polityka sieci / allowlista | wzmianka, żeby agent nie próbował pobierać |
| MCP | plik w repo (np. `.mcp.json`) | które narzędzia wolno wołać |
| sekrety | magazyn sekretów środowiska | zakaz proszenia o kolejne |
| uprawnienia narzędzi | `--allowedTools`, `--permission-mode`, ustawienia projektu | — |
| budżet | `--max-budget-usd` (w `claude -p`), limit platformy | warunek stopu słownie |
| cel, zakres, raport, kryteria | — | tak |

Zasada: to, czego agent **nie może** zrobić, wymusza środowisko; polecenie mówi, czego **nie powinien** próbować.
Zmiana skryptu startowego, sieci lub sekretów zwykle unieważnia cache środowiska — setup krótki i powtarzalny.

## 3. Przykład: sandbox, plan testów
Zob. sekcja „Przykład” w `SKILL.md` (moduł płatności, sieć wyłączona po setupie, brak sekretów, limit 20 tur).

## 4. Przykład: rutyna dzienna
**Sytuacja:** codziennie rano przegląd zgłoszeń z etykietą `ai-candidate`.
```text
Cel: plik docs/triage/<data>.md z listą zgłoszeń ai-candidate: dla każdego – czy ma kroki odtworzenia,
prawdopodobny moduł, ryzyko (niskie/średnie/wysokie), rekomendacja (do agenta / do człowieka / zamknąć).
Zakres: tylko odczyt zgłoszeń i repo; zapis wyłącznie docs/triage/. Bez komentarzy w zgłoszeniach.
Idempotencja: jeśli plik z dzisiejszą datą istnieje, zaktualizuj go; nie twórz drugiego.
Stop: po zapisaniu pliku albo po 15 turach; budżet na przebieg ustalony w konfiguracji rutyny.
Porażka mimo zielonego statusu: brak nowych pozycji przy nowych zgłoszeniach; rekomendacje skopiowane z wczoraj;
zgłoszenie bez rekomendacji.
```
Przegląd co tydzień: ile rekomendacji „do agenta” okazało się trafnych; koszt na przebieg; czy rutyna nadal
ma sens.

## 5. Przykład: zdalna kontrola lokalnej sesji
**Sytuacja:** w trakcie diagnozy musisz wyjść; agent ma dokończyć zbieranie logów i hipotez.
- Tryb: zdalna kontrola (Remote Control albo SSH + `tmux`) — wykonanie zostaje na Twojej maszynie.
- Ryzyko: agent ma dostęp do Twojego katalogu domowego i sieci → bez trybu omijania uprawnień, zakres
  słownie ograniczony do diagnozy (bez poprawek), sesja zatrzymana, jeśli nie wrócisz w ustalonym czasie.
- Z telefonu tylko decyzje: kontynuuj / doprecyzuj / zatrzymaj.

## 6. Dry run, gdy funkcja jest niedostępna
Plan konta, polityka firmy albo wersja narzędzia blokuje uruchomienie? Rozpisz kontrakt tak, jakby zadanie miało
trafić do zespołu jutro, i oznacz każdy krok:
```text
[wykonane]                      kontrakt wypełniony, skrypt startowy przetestowany lokalnie w kontenerze
[zablokowane przez dostęp]      sandbox w chmurze niedostępny na planie zespołu – wymaga decyzji administratora
[do sprawdzenia przed wdrożeniem] czy allowlista sieci obejmuje rejestr paczek firmy
```
Wynik dry runu to lista decyzji dla człowieka, nie esej.
