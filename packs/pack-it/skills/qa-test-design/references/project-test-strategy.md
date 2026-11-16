# Strategia testów projektu — żywy dokument

Plik: `docs/project/05-plan/test-strategy.md` (szablon: `.claude/skills/qa-test-design/templates/test-strategy.md`).
Plan testów zmiany (`test-plan.md`) korzysta ze strategii i po zakończeniu ją uzupełnia.

## Kiedy
Projekt bez testów albo z testami „tam, gdzie łatwo” — zanim agent napisze pierwszy test. Bez strategii agent pokrywa
helpery i formatery, procent pokrycia rośnie, a krytyczny przepływ (płatność, dostęp do treści) zostaje bez ochrony.
Testy wychodzą od ryzyka, nie od pliku.

## Wejścia — czytasz, nie wymyślasz; każdy fakt ze ścieżką źródła
- wymagania (użytkownicy, przepływy, reguły, wyłączenia), roadmapa (co będzie zmieniane → prawdopodobieństwo),
  zamknięte zmiany, stack i istniejąca konfiguracja testów, `CLAUDE.md`;
- **profil bazy testów** jednym słowem: `brak` (bez konfiguracji, < 3 pliki testów), `rzadki` (konfiguracja, ale
  kilkanaście plików lub wszystkie w jednym miejscu), `znaczący` (testy w wielu obszarach);
- **gorące miejsca z historii git** — liczba commitów na katalog z ostatnich ~30 dni, tylko kod pisany ręcznie (bez
  lockfile'i, snapshotów, kodu generowanego, `dist`). Zakres skanu pokazujesz człowiekowi. Mniej niż ~5 commitów
  w oknie → pomiń skan i zapisz, że prawdopodobieństwo opiera się na roadmapie i wywiadzie.

## Wywiad (po jednym pytaniu, z 2–3 przykładowymi odpowiedziami, echo odpowiedzi w jednej linii)
- W1. Czego najbardziej boisz się zepsuć — niezależnie od dokumentów?
- W2. Gdzie już się sparzyłeś (w tym kodzie lub podobnym)?
- W3. Co zmieniasz najczęściej i bez pewności?
- W4. Co jest dziś niedotestowane? (profil `rzadki`: „która dziura niepokoi najbardziej?”; profil `brak`: pomiń)
- W5. Na co NIE chcesz wydawać budżetu testów? → sekcja „Czego nie testujemy”.

Trzy pominięte pytania → kończysz wywiad i zaznaczasz, że strategia opiera się wyłącznie na dokumentach.

## Mapa ryzyk (5–7 wierszy)
Ryzyko to scenariusz awarii odczuwalny przez użytkownika lub biznes — nie nazwa modułu ani testu.
Dobrze: „zalogowany, płacący użytkownik dostaje 403 na własnej treści”. Źle: „przetestować formularz logowania”.

| Ocena | Wpływ | Prawdopodobieństwo |
|---|---|---|
| wysoki | utrata dostępu, danych lub pieniędzy; awaria widoczna publicznie | obszar zmienia się co tydzień albo był tu incydent |
| średni | funkcja działa gorzej, jest obejście, dotyczy części użytkowników | zmieniany od czasu do czasu, bywał źródłem błędów |
| niski | kosmetyka, łatwe cofnięcie, bez skutku dla danych | stabilny, rzadko dotykany |

- Kolejność: wysoki × wysoki najpierw. Wysoki wpływ × niskie prawdopodobieństwo (awaria dostawcy chmury) to zwykle
  monitoring i alert, nie test (ops-observability) — zapisz to zamiast wiersza.
- Kolumna **Źródło**: dowód, który podniósł ryzyko — wiersz wymagań, punkt roadmapy, zamknięta zmiana, odpowiedź W1–W5,
  katalog z liczbą commitów, ograniczenie stacku. **Nie** plik, `plik:linia`, funkcja ani moduł — to ustala dopiero
  analiza kodu w fazie (eng-codebase-mapping). Wiersz, który bez kotwicy w kodzie traci źródło, usuń albo podeprzyj
  wywiadem.
- **Soczewka nadużyć** — obowiązkowa przy logowaniu, płatnościach albo jakimkolwiek wejściu od użytkownika: co
  najmniej jeden wiersz z klas: cudzy zasób (sprawdzenie własności, nie tylko zalogowania), niezaufane wejście
  (wstrzyknięcia, walidacja po stronie serwera), wyciek sekretów lub danych osobowych (logi, treść błędu, bundle
  frontu), nadużycie zasobów (obejście limitu, kosztowna operacja w pętli). Brak takich wierszy przy tych
  powierzchniach to luka, nie dowód bezpieczeństwa (arch-threat-modeling).
- Numery ryzyk są stałe; nowe dopisujesz na końcu.

## Odpowiedź na ryzyko (jeden wiersz na ryzyko)
| Ryzyko | Co udowodni ochronę (zachowanie obserwowalne) | Założenie do podważenia | Kontekst do ustalenia w kodzie | Najtańsza warstwa (hipoteza) | Antywzorzec do uniknięcia |

Założenia do podważenia, np.: „udane logowanie = dostęp do opłaconej treści”, „200 = zapis się udał”, „pusta
odpowiedź = brak danych”. Odrzucasz odpowiedzi typu „testy jednostkowe modułu X”, „pokryć ścieżkę główną”, „asercja
na obecny wynik”. Ryzyko, dla którego nie da się wypełnić wiersza, przeformułuj albo usuń.

## Kontrola przed zapisem (każde ryzyko)
1. Defekt czy opis implementacji? Ryzyko wymagające zabezpieczenia, którego nie ma („brak retry”), to spekulacja —
   przeformułuj na to, co istnieje („awaria dostawcy kończy się czystym 5xx, nie udaje sukcesu, nic nie zapisuje”).
2. Czy w źródle nie ma kotwicy w kodzie?
3. Czy odpowiedź złapie realną regresję, czy tylko podniesie pokrycie?

Usunięte lub przeformułowane ryzyka wypisz w jednej linii „Wyniki kontroli”.

## Fazy wdrażania (3–5)
| # | Faza | Jaką ochronę udowadnia | Ryzyka | Rodzaje testów | Stan | Folder zmiany |

Stany (stałe słowa): `nie rozpoczęta` → `otwarta` → `zbadana` → `zaplanowana` → `w realizacji` → `zakończona`.
Stan wyprowadzasz z plików na dysku (jest analiza → `zbadana`, jest plan → `zaplanowana`, postęp odhaczony →
`zakończona`), nie z pamięci rozmowy. Profil `brak`: faza 1 = postawienie runnera i pierwszy test integracyjny dla
ryzyka #1. Każda faza kończy się uzupełnieniem przepisów.

## Bramki jakości
| Bramka | Warstwa (edycja / commit / push / CI) | Wymagana od | Co łapie |

Każdy wiersz jest już podpięty albo wskazuje fazę, która go podepnie („od fazy 2”). Bramka bez fazy to życzenie.
Warstwy lokalne: eng-local-quality-gates; CI: ops-ci-cd.

## Przepisy (rosną z fazami)
Na start: `TBD — faza N (ochrona przed <zachowanie>)`. Po fazie, dla każdego rodzaju testu: lokalizacja, nazewnictwo,
polityka dublerów, test wzorcowy (ścieżka), polecenie uruchomienia. 3–6 przepisów; rzadki przypadek = link do testu.
Po wpisaniu przepisu zaktualizuj sekcję testów w `CLAUDE.md` projektu — inaczej każdy agent zgaduje polecenia.

## Czego świadomie nie testujemy
Odpowiedzi na W5 z powodem i warunkiem ponownej oceny. Więcej niż 5–6 punktów = strategia za szeroka.

## Świeżość
Data przeglądu, wersje narzędzi i data sprawdzenia odniesień do narzędzi AI. Przegląd, gdy: nowe ryzyko w top 3,
data narzędzia starsza niż 3 miesiące, zmiana stacku, wykluczenie przestało być prawdą. Zmiana ryzyk lub faz idzie
jako osobna zmiana; wyjątek — poprawka sformułowania ryzyka po analizie kodu, za zgodą człowieka.

## Czego nie ma w dokumencie
Kodu testów, YAML CI, skryptów hooków, kotwic w kodzie w mapie ryzyk, nowych słów stanów.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja 1 (plan testów projektu) — materiał szkoleniowy (dostęp 2026-10-09).
- ISTQB CTFL v4.0 — testowanie oparte na ryzyku (wpływ × prawdopodobieństwo).
Opisane własnymi słowami.
