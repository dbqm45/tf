# Izolacja fabryki: trzy poziomy

Zapisane 2026-11-20. Plan wdrożenia: `docs/plans/2026-11-20-poziomy-izolacji.md`.

Tak, trzy poziomy mają sens, z kontenerem jako najmocniejszym. Postawiłbym jednak jeden warunek: każdy poziom musi
uczciwie mówić, co gwarantuje. Najsłabszy w praktyce nie izoluje, więc nie powinien nazywać się izolacją.

## Jak bym je ułożył

| Poziom | Co działa | Co gwarantuje | Czego nie |
|---|---|---|---|
| **1. Podstawowy** | reguły uprawnień fabryki: zakazy, pytania, `deny` na sekrety | chroni przed typowymi pomyłkami i oczywistymi poleceniami | to filtr na wzorcach poleceń, więc da się go obejść; narzędzia Claude, hooki i MCP mają dostęp do całego dysku |
| **2. Sandbox** | poziom 1 + sandbox Bash (bubblewrap albo Seatbelt) z szablonem fabryki | polecenia w terminalu zapisują tylko w projekcie, nie czytają kluczy, a sieć ma tylko listę dozwolonych domen | własne narzędzia Claude do plików, hooki i MCP działają poza sandboxem |
| **3. Kontener** | poziom 2 wewnątrz kontenera, do którego podpięty jest tylko folder projektu i osobny `~/.claude` | nic z fabryki ani Claude nie widzi niczego poza projektem; zapora sieciowa obejmuje cały ruch | wymaga Dockera albo Podmana; trzeba rozwiązać push i klucze |

## Co sądzę

- **Domyślnie poziom 2.** Kosztuje prawie nic: fabryka zmierzyła niewielki narzut. Usuwa najczęstsze realne
  zagrożenie, czyli polecenie wklejone ze strony czy zgłoszenia, które czyta `~/.ssh` albo wysyła dane na zewnątrz.
  Poziom 1 zostawiłbym jako świadome wyjście z sandboxa, np. gdy sandbox nie działa na danym systemie.
- **Poziom 3 dla projektów z wrażliwymi danymi, dostępem do produkcji albo cudzym kodem,** a także dla pracy agenta
  bez nadzoru, na przykład w nocy. Tylko ten poziom spełnia wymaganie „nic poza projektem”.
- **Poziom zapisany i widoczny.** Wybór przy `tf install`, zapisany w konfiguracji projektu i pokazywany przy starcie
  sesji oraz w `tf doctor`, żeby nikt nie myślał, że ma kontener, kiedy go nie ma.
- **Poziomu nie da się obniżyć z wnętrza sesji.** Agent ani skill nie może sam przejść z 3 na 1. Zmiana tylko
  poleceniem człowieka.
- **Firma może narzucić minimum.** Przez ustawienia zarządzane (managed settings) da się wymusić np. „co najmniej 2”
  dla wszystkich.

## Ryzyka, o których trzeba pamiętać

- **Systemy:** sandbox nie działa na samym Windowsie, tylko pod WSL. Na macOS fabryka nie ma jeszcze własnego
  pomiaru, skrypt `scripts/sandbox_check.py` czeka na uruchomienie u właściciela.
- **Pułapki konfiguracji:** sesja uruchomiona w podkatalogu nie wczytuje ustawień projektu, a projektowe
  `"enabled": false` po cichu wyłącza sandbox wszystkim. To już jest opisane w skillu `core-agent-security`, ale przy
  poziomach musiałby tego pilnować kod, a nie tylko tekst w skillu.
- **Wygoda w kontenerze:** pliki na macOS są wolniejsze, sesje logowania są osobne, a narzędzia spoza obrazu, np.
  lokalna baza danych, trzeba albo dodać do obrazu, albo udostępnić przez sieć.
