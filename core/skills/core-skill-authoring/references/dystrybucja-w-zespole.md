# Dystrybucja własnych skilli i reguł w zespole


Skille, reguły, polecenia i szablony konfiguracji agentów to kod wykonywany przy każdej zmianie: potrzebują wersji,
przeglądu zmian i kontrolowanej dystrybucji. Kopiowanie między repozytoriami rozjeżdża wersje po kilku tygodniach.
Instalator tej fabryki (`factory/install.py`, `factory/update.py`) realizuje opisane niżej własności — to działający
wzorzec do porównania.

## 1. Wymagania — miara każdego rozwiązania
- jedno źródło prawdy (repozytorium z artefaktami);
- wersja wg SemVer (core-semver), zmiana łamiąca = nowa wersja główna;
- kontrola, kto czyta i kto publikuje;
- instalacja, aktualizacja i **czysta deinstalacja**;
- dostarczenie do każdego narzędzia AI w zespole — różnią się tylko katalogi docelowe (np. `.claude/skills/`,
  katalog reguł innego narzędzia).

## 2. Wybór kanału — decyduje odbiorca
| Odbiorca | Kanał | Koszt startu | Koszt utrzymania |
|---|---|---|---|
| zespół na jednej platformie git | repo z tagami albo paczka w rejestrze tej platformy | mały | token odczytu dla odbiorców spoza organizacji |
| organizacja z własną chmurą i zarządzaniem rejestrem | rejestr artefaktów w chmurze, konfiguracja jako kod, logowanie przez OIDC | konto + kod infrastruktury | uprawnienia, rotacja |
| odbiorcy na różnych stackach, dostęp dawkowany w czasie | własne API + CLI | pełny produkt | API, uwierzytelnianie, klient |
| jedno narzędzie AI w całym zespole | marketplace wtyczek tego narzędzia | zerowy | zależność od kanału dostawcy |
Antywzorzec: kanał „imponujący” zamiast dopasowanego do odbiorcy.

## 3. Instalator — obowiązkowe własności
- **Idempotentny:** drugie uruchomienie daje ten sam wynik.
- **Bloki ze znacznikami** w plikach edytowanych przez ludzi (`CLAUDE.md`, `AGENTS.md`): podmieniasz wyłącznie środek
  bloku begin/end. Jeden znacznik bez drugiego = blok uszkodzony → przerwij z komunikatem. Treść, która sama zawiera
  znaczniki, odrzuć — inaczej następna instalacja skasuje cudzy tekst.
- **Manifest** w repo odbiorcy: paczka, wersja, narzędzie, lista plików ze skrótami. Deinstalacja usuwa dokładnie pliki
  z manifestu, nie zależy od `node_modules` ani skryptów menedżera pakietów; uszkodzony manifest → nie usuwa nic.
- **Plik zmieniony lokalnie** nie jest nadpisywany — nowa wersja obok (np. `<plik>.factory-new`) do ręcznego scalenia.
- **Kopiowanie** działa wszędzie (także przy jednorazowym uruchomieniu z cache, który znika); dowiązania tylko przy
  trwałej zależności.
- **Zależności między skillami** deklarowane w nagłówku; wybór podzbioru przechodzi przez rozwiązywanie zależności.
- Błąd kroku poinstalacyjnego nie wywraca instalacji zależności projektu — ostrzeżenie zamiast awarii.
- Nowa wersja obcego skilla przechodzi audyt przed zapisaniem (`factory/skill_audit.py`, core-agent-security §4a).

## 4. Paczka prywatna — uwierzytelnianie i wydania
- Repo odbiorcy commituje tylko mapowanie zakresu paczek na rejestr, **nigdy** tokena.
- Publikacja z CI z uprawnieniem zapisu do rejestru i krótkotrwałym tokenem zadania (ops-ci-cd).
- Odczyt: w tej samej organizacji często wystarcza token zadania CI; poza nią (inne repo, obce CI, platformy budowania)
  potrzebny token z prawem odczytu ze zmiennej środowiskowej, lokalnie logowanie do rejestru. Szczegóły zależą od
  rejestru i typu tokena — sprawdź w jego dokumentacji [niezweryfikowane w tej sesji].
- Rejestry zwykle odrzucają ponowną publikację tej samej wersji → wersję liczy automat (`semver.py`).
- Wydanie tylko, gdy od ostatniego tagu **zmieniły się pliki wchodzące do paczki** (diff), niezależnie od typu commita.

## 5. Własne API + CLI jako granica bezpieczeństwa
- Podpis paczki (np. Ed25519, klucz publiczny wbudowany w klienta): najpierw zgodność skrótu treści, potem podpis.
- Lista dozwolonych hostów API wbudowana w klienta — adresu nie da się przestawić zmienną środowiskową.
- Krótkotrwały token z ponownym sprawdzeniem uprawnień przy odświeżeniu.
- Kontrakt API–klient generowany ze specyfikacji OpenAPI: zmiana łamiąca klienta wychodzi przy kompilacji.

## 6. Zanim zbudujesz
Pierwsza wersja: jedno repo źródłowe, jedna paczka testowa, ręczna instalacja w jednym projekcie. Automatyzację wydań
i kolejne kanały dodajesz dopiero, gdy ktoś realnie pobiera nowe wersje.

## 7. Przykład
Zespół 8 osób, wszystkie repo w jednej organizacji na platformie git, dwa narzędzia AI. Wybór: repo `ai-toolkit`
z tagami SemVer i paczką w rejestrze platformy; instalator kopiuje skille do `.claude/skills/` i reguły do katalogu
drugiego narzędzia, w `CLAUDE.md` i `AGENTS.md` dopisuje blok między znacznikami, zapisuje manifest. CI publikuje
tylko przy zmianie plików paczki. Odrzucone: własne API + CLI (jeden odbiorca, brak potrzeby dawkowania dostępu).

Kurs 10xDevs, ed. 3 (2026), moduł 5, lekcja 4 — materiał szkoleniowy (dostęp 2026-10-09). Opisane własnymi słowami.
