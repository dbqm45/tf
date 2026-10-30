---
name: core-grounding
description: Użyj, gdy twierdzenie lub liczbę (też z raportu agenta, np. ile wywołań lub metod) trzeba sprawdzić, zanim się na niej oprzesz — plik, polecenie, źródło, „nie wiem”.
metadata:
  przeglad: "2027-10-10"
  katalog: "Użyj przy każdej odpowiedzi, raporcie i artefakcie, które zawierają fakty o kodzie, wersjach, API, poleceniach, liczbach lub źródłach — klasy twierdzeń i sposób ich sprawdzenia, miejsca, w których modele najczęściej zmyślają, higiena kontekstu, samosprawdzenie i skrypt sprawdzający odwołania. Nie do procedury badania źródeł zewnętrznych (core-source-research) ani testów kodu (skille testów, pack-it)."
  slowa: "wynik skryptu, liczba z narzędzia, przepisać liczbę z wyniku, halucynacje, zmyślanie, nie zgaduj, czy to prawda, kolega twierdzi, podobno istnieje, czy taka opcja istnieje, sprawdź fakty, źródło, pewność, wymyślona flaga, nieistniejące API, za długi kontekst, model się myli, weryfikacja odpowiedzi, liczby w raporcie, dokładnie N wywołań, tylko w jednym miejscu, ile razy wywoływana, zużyty kontekst, pamięć automatyczna, podsumowanie długiego dokumentu, streszczenie umowy lub regulaminu, notatka z dokumentu, najpierw cytaty, niczego spoza dokumentu, z podanych materiałów, agent powtarza ustalenia, łata wokół czerwonego testu, długa sesja"
---

# Ugruntowanie odpowiedzi — jak nie zmyślać

Model zmyśla najczęściej wtedy, gdy:
- odpowiada z pamięci zamiast ze sprawdzenia;
- czuje presję, żeby odpowiedzieć zawsze;
- pracuje w długim kontekście pełnym nieudanych prób.

Ten skill usuwa te trzy przyczyny. Dwie części działają mechanicznie i nie zależą od modelu:
- hook `context_guard` ostrzega przed zbyt długim kontekstem;
- skrypt `scripts/grounding_check.py` sprawdza, czy odwołania w dokumentach istnieją.

## 1. Każde twierdzenie ma klasę i dowód
| Klasa | Przykład | Dowód przed napisaniem |
|---|---|---|
| **o tym repozytorium** | „funkcja X waliduje Y”, „plik Z istnieje”, „test przechodzi” | przeczytany plik (`plik:linia`), wynik polecenia w tej sesji |
| **aktualny fakt zewnętrzny** | wersja, zgodność wersji, flaga CLI, opcja konfiguracji, nazwa pakietu, cena, termin prawny, CVE | źródło pierwotne z datą (core-source-research), `--help`, `npm view <pakiet> version`, dokumentacja wersji projektu |
| **wiedza stała** | jak działa B-drzewo, czym jest idempotencja | wystarczy wiedza — ale bez konkretnych liczb i nazw, których nie sprawdziłeś |
| **wniosek lub ocena** | „to pewnie przez cache”, „wariant B będzie tańszy” | oznacz: **[założenie]** albo **[ocena]**, z tym, jak to sprawdzić |

Twierdzenia bez dowodu nie podajesz jako faktu. Do wyboru:
- sprawdź je;
- oznacz jako założenie;
- pomiń.

## 2. „Nie wiem” jest poprawną odpowiedzią
- Gdy nie da się sprawdzić (brak dostępu, brak źródła, brak czasu), mówisz to wprost: czego nie wiesz i jak to
  ustalić. Wymyślona, ale wiarygodnie brzmiąca odpowiedź jest gorsza niż „nie wiem”.
- Nie zgadujesz nazw: metod, endpointów, flag, kluczy konfiguracji, pakietów, plików, zmiennych środowiska.
  Nieistniejąca nazwa pakietu to też ryzyko bezpieczeństwa (podszywające się paczki — skill łańcucha dostaw, pack-it: ops-supply-chain-security).
- Pytanie zawiera fałszywe założenie (np. pyta o flagę, która nie istnieje)? Mówisz, że tego nie znalazłeś. Pokazujesz, gdzie szukałeś, i nie dopasowujesz odpowiedzi do pytania.

## 3. Miejsca, w których modele zmyślają najczęściej — sprawdzaj zawsze
Wersje i zgodność wersji · nazwy API, metod i opcji · flagi CLI · nazwy pakietów · ścieżki i nazwy plików
w repozytorium · numery (porty, limity, kody błędów, CVE, RFC, artykuły ustaw) · daty i terminy · cytaty
i przypisanie źródeł · wynik polecenia, którego nie uruchomiłeś · zachowanie kodu, którego nie przeczytałeś ·
liczby w szacunkach (pokaż rachunek). Szczegóły i polecenia sprawdzające: `references/sprawdzanie.md`.

### Twierdzenia strukturalne o kodzie
„Dokładnie 4 wywołania”, „tylko w module X”, „zawsze przez Y”, „interfejs ma 54 metody” — modele liczą to najsłabiej,
a czytelnik raportu bierze na wiarę. Im pewniej wygląda liczba, tym bardziej ją sprawdź:
1. wypisz wszystkie takie twierdzenia z raportu (mapy, analizy, planu refaktoru);
2. każde sprawdź narzędziem strukturalnym (`ast-grep -p '<wzorzec>' -l <język> --json`, „znajdź odwołania” w LSP,
   kompilator) — werdykt: potwierdzone / doprecyzowane / obalone, z `plik:linia`;
3. każde **zero** z narzędzia strukturalnego potwierdź zwykłym `rg -n '<tekst>'` — zero może znaczyć zły wzorzec;
4. poprawka w miejscu ze śladem („150 (raport: 145)”) i tabela „Weryfikacja twierdzeń”: twierdzenie → werdykt →
   dowód → metoda. Wniosków i rankingu przy tej okazji nie przepisujesz — rozbieżność opisujesz jako „do decyzji”.
5. **Wynik skryptu lub narzędzia to też twierdzenie.** Zanim przepiszesz liczbę do raportu, sprawdź w kodzie
   największą pozycję (największy cykl, hub) i jedną losową — przeczytaj `plik:linia`, który ją tworzy. W pomiarze
   fabryki (2026-10-18) błąd szkicu skryptu („cykl runtime 242 plików”, w rzeczywistości domykany importami typów)
   powtórzyli wszyscy agenci, którzy z niego korzystali; agent bez skryptu policzył poprawnie.

## 4. Długie dokumenty: najpierw cytaty, potem wnioski
Przy analizie długiego materiału (specyfikacja, logi, transkrypcja, regulamin):
1. Wypisz dosłowne cytaty z miejscem (plik:linia, sekcja), które odpowiadają na pytanie.
2. Dopiero na ich podstawie wyciągaj wnioski.
3. Wniosek bez cytatu wycofaj albo oznacz jako założenie.

**Weryfikacja cytatami po napisaniu** (tekst dla innych: raport, notatka prawna, opis zmiany): po szkicu przejdź
twierdzenie po twierdzeniu i do każdego znajdź cytat z materiału. Twierdzenie bez cytatu usuń, a w jego miejscu zostaw
`[]` — czytelnik widzi, że coś wycięto, i może dopytać.

**Tylko z podanych materiałów** — gdy zadanie tego wymaga (przepisy, umowa, wymagania klienta, analiza wywiadów):
wiedza ogólna służy do zrozumienia pytania, nie jako źródło twierdzeń; czego materiały nie obejmują, nazywasz luką.
Fabryka włącza ten tryb konsultantom i rolom z `grounding: sources-only` (`factory/config.yaml`, `sources_only_note`).

Ten sam wzorzec stosuje ddd-discovery-intake z pack-it (bank cytatów z kontrolą `evidence`).

## 5. Higiena kontekstu
Jakość odpowiedzi spada, gdy kontekst się wypełnia, i gdy jest w nim dużo nieudanych prób.
- **Jedno zadanie — jeden kontekst.** Nowe, niezwiązane zadanie zaczynasz od czystej sesji (`/clear`). Wracasz
  od punktu kontrolnego (core-project-record), a nie od długiej historii.
- **Dwie nieudane poprawki tego samego** → zatrzymaj się. Zapisz w punkcie kontrolnym, co nie działa i dlaczego.
  Potem zacznij od nowa z lepszym poleceniem.
- **Eksploracja w subagencie** (`scout`, `Explore`): czytanie wielu plików zostaje w jego kontekście, do ciebie
  wraca wynik.
- **Wczytuj tylko potrzebne skille i sekcje** — TL;DR i Przekazanie zamiast całych artefaktów.
- **Kompaktowanie:** decyzje i ustalenia muszą być w plikach, zanim kontekst zostanie streszczony (CLAUDE.md
  mówi, co zachować).
- **Sygnały zużytego kontekstu** (zachowanie, nie liczba tokenów): powtarzasz ustalenia jako nowe odkrycia; podajesz
  ścieżki lub polecenia, których nie ma; łamiesz przyjęte ograniczenie; łatasz wokół czerwonego testu zamiast wrócić
  do przyczyny; podsumowania rosną, decyzji ubywa. **Dwa sygnały naraz → decyzja, nie kolejna próba:** `/compact`
  (kierunek dobry), cofnięcie ostatniego kroku (`/rewind`), `/clear` (koniec zadania), nowa sesja od punktu kontrolnego.
- **Polecenie kompakcji:** `/compact Zachowaj: decyzje, ścieżki plików, wykonane polecenia i wyniki, status testów,
  ograniczenia, otwarte ryzyka. Usuń: nieudane próby, powtórzone logi, porzucone hipotezy. Następny krok: <jedno>.`
- **Pamięć to twierdzenie z dnia zapisu.** Wpis automatycznej pamięci (`~/.claude/projects/<projekt>/memory/`) albo
  wcześniejszy artefakt (mapa, research) to punkt wyjścia, nie prawda: przed użyciem sprawdź w kodzie, a nieaktualne
  twierdzenie koryguj jawnie w raporcie. Reguły wiążące zespół trzymasz w repo (core-agent-instructions), nie w pamięci.
- Hook `context_guard` ostrzega, gdy kontekst przekroczy próg (domyślnie 100 tys. i 150 tys. tokenów). Na
  ostrzeżenie odpowiadasz zapisem punktu kontrolnego i propozycją nowej sesji albo `/compact` z instrukcją.

## 6. Samosprawdzenie przed oddaniem
Przed odpowiedzią z faktami, raportem kroku albo artefaktem:
1. Wypisz w myślach twierdzenia faktograficzne. Każde musi mieć dowód z sekcji 1. Bez dowodu: sprawdź, oznacz
   albo usuń.
2. Twierdzenia o stanie („testy przechodzą”, „plik istnieje”, „wersja X obsługuje Y”) podaj z dowodem: polecenie
   i wynik, `plik:linia`, źródło z datą.
3. Dla dokumentów: `python3 .claude/skills/core-grounding/scripts/grounding_check.py <plik.md>`. Skrypt
   sprawdza, czy ścieżki, odwołania `plik:linia` i lokalne linki istnieją. Z `--jev` (opcjonalnie, klucz
   TYPESAFE_API_KEY) sprawdza też, czy wskazane linie **potwierdzają** zdanie, przy którym stoi odwołanie.
   - Sprzeczne i niepotwierdzające odwołania popraw.
   - Niepewne przejrzyj sam.
4. W diffie szukasz trzech typowych klas błędów modelu: kod poprawny składniowo, ale zły semantycznie (zgubiona
   transakcja, ponowienie, przypadek brzegowy); test utrwalający implementację zamiast zachowania; decyzja ze środka
   długiej rozmowy pominięta na rzecz nowszego kontekstu.
5. Przy ważnych decyzjach (architektura, bezpieczeństwo, prawo) niech wynik oceni ktoś bez twojego kontekstu:
   security-reviewer, `/code-review` albo drugi wykonawca. Autor nie ocenia własnej pracy.
6. **Decyzja trudna do odwrócenia, odpowiedź bez źródła do sprawdzenia:** zadaj to samo pytanie 2–3 razy
   niezależnie (osobni wykonawcy, ten sam brief — best-of-N). Rozbieżne odpowiedzi to sygnał zmyślenia: zostaje
   tylko to, co się powtarza i ma dowód; reszta wraca jako pytanie. Kosztuje N przebiegów — tylko przy takich
   decyzjach. Tańszy wariant: oddaj odpowiedź do sprawdzenia twierdzenie po twierdzeniu (iteracyjne doprecyzowanie).

## Checklista
- [ ] fakty o repo poparte przeczytanym plikiem lub poleceniem z tej sesji
- [ ] wersje, flagi, API, pakiety, liczby i daty sprawdzone u źródła albo oznaczone jako niezweryfikowane
- [ ] wnioski oznaczone **[założenie]** / **[ocena]**; „nie wiem” tam, gdzie nie da się sprawdzić
- [ ] długi materiał: cytaty przed wnioskami; tekst dla innych zweryfikowany cytatami (wycięte twierdzenia jako `[]`)
- [ ] kontekst: zadanie w czystej sesji, eksploracja w subagencie, ostrzeżenie `context_guard` obsłużone
- [ ] liczby i wyłączności o kodzie („dokładnie N”, „tylko tu”) sprawdzone narzędziem strukturalnym, zera potwierdzone `rg`
- [ ] `grounding_check.py` bez błędów dla oddawanych dokumentów

## Źródła
- Anthropic — „Reduce hallucinations” (prawo do „nie wiem”, cytaty jako podstawa, weryfikacja przez cytaty,
  weryfikacja wieloprzebiegowa, ograniczenie do podanych materiałów), platform.claude.com, sprawdzone 2026-10-20
- Anthropic — „Best practices for Claude Code” (wypełniony kontekst obniża jakość, `/clear` między zadaniami,
  subagenci do eksploracji, weryfikacja zamiast deklaracji)
- Claude Code — „How Claude remembers your project” (code.claude.com/docs/en/memory, dostęp 2026-10-10): pamięć
  automatyczna w `~/.claude/projects/<projekt>/memory/`, `MEMORY.md` ładowany do 200 linii lub 25 KB.
- ast-grep 0.50.0 — `ast-grep run --help` (flagi `-p`, `-l`, `--json`), sprawdzone 2026-10-10.
- Kurs 10xDevs, ed. 3 (2026), lekcje 3.1 i 3.3 (klasy błędów, sygnały zużytego kontekstu), moduł 4, lekcje 3–4
  (weryfikacja twierdzeń strukturalnych) — materiał szkoleniowy (dostęp 2026-10-09).
Opisane własnymi słowami.
