---
name: arch-ai-solutions
description: Użyj przy architekturze systemu z komponentem AI — wzorzec (LLM, RAG, workflow, agent), źródło modelu i lock-in dostawcy, koszt, opóźnienie, granice zaufania.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj, gdy projektujesz architekturę systemu z komponentem AI na poziomie decyzji — dobór wzorca (zwykłe wywołanie modelu, RAG, workflow z narzędziami, agent, fine-tuning, klasyczne ML) wg tabeli wymagań, źródło modelu (API, open-weights na własnej infrastrukturze, usługa zarządzana w chmurze), rezydencja danych i lock-in, komponenty architektury referencyjnej (bramka, serwis promptów, warstwa wyszukiwania i narzędzi, ewaluacje, guardrails, kolejka przeglądu), budżet opóźnienia, cache, fallback i routing modeli, granice bezpieczeństwa, szablon kosztu i pojemności, izolacja najemców, ADR dla decyzji AI. Nie do ogólnego projektu systemu (arch-system-design), metody doboru stacku (arch-tech-selection), atrybutów jakości (arch-quality-attributes), modelu zagrożeń (arch-threat-modeling), szczegółów RAG (ai-rag), projektu agenta (ai-agents), kodu z SDK (eng-llm-features) ani hostowania modeli (ops-ai-inference)."
  slowa: "wymiana modelu na tańszy, zostawić harness, uzależnienie od dostawcy, wymiana harnessu, architektura ai, architekt rozwiązań ai, rag czy agent, jaki wzorzec ai, wybór modelu, api czy własny model, open-weights, rezydencja danych, lock-in dostawcy, brama llm, llm gateway, routing modeli, fallback modelu, budżet opóźnienia, koszt na żądanie, szacunek kosztu llm, prompt caching w architekturze, izolacja klientów, multi-tenant ai, human review queue, adr dla ai, referencyjna architektura ai, system AI odpowiada liczbami, pewnie złe liczby, kiedy odpowiedzi można ufać, model pisze SQL, text-to-SQL architektura"
---

# Architektura rozwiązań z AI — decyzje przed kodem

Skill prowadzi od wymagań do udokumentowanych decyzji: jaki wzorzec, jaki model, jakie komponenty, jakie granice
i ile to kosztuje. Ogólny projekt systemu (szacunki, API, dane, dostępność) daje **arch-system-design**; wybór
technologii metodą kandydatów i macierzy — **arch-tech-selection**. Tu dodajesz to, co specyficzne dla AI.
Wynik: `docs/project/04-architecture/ai-architecture.md` i ADR-y (szablon: `references/szablony.md`).

## Procedura
1. **Wymagania, które rozstrzygają.** Zapisz sześć osi: świeżość wiedzy, wymagana trafność (cena błędu), opóźnienie,
   koszt na żądanie, wrażliwość danych, wyjaśnialność. Bez liczb (np. p95 ≤ 2 s, ≤ 0,02 USD na żądanie [przykład])
   nie wybierzesz wzorca. Brak osi → pytanie do człowieka, nie założenie.
2. **Wzorzec: najprostszy, który spełnia osie.** Zaczynasz od góry tabeli i schodzisz niżej tylko z dowodem
   (ewaluacja, **ai-evals**), że wyższy nie wystarcza. Anthropic radzi to samo: najprostsze rozwiązanie, złożoność
   dopiero, gdy mierzalnie pomaga.

   | Wzorzec | Wybierz, gdy | Cena (opóźnienie, koszt, ryzyko) |
   |---|---|---|
   | klasyczne ML lub reguły | zadanie wąskie, dane etykietowane, potrzebna wyjaśnialność i niski koszt | najtańsze; wymaga danych i MLOps (**ai-mlops**) |
   | jedno wywołanie LLM | wiedza ogólna lub podana w prompcie, zadanie jednokrokowe | 1 wywołanie; brak aktualnych faktów |
   | RAG | wiedza prywatna, zmienna, z uprawnieniami lub cytatami | + wyszukiwanie; szczegóły **ai-rag** |
   | workflow z narzędziami | kroki znane z góry, dane na żywo, akcje w systemach | przewidywalne; koszt i czas rosną liniowo z krokami |
   | agent | liczba kroków nieznana z góry, potrzebna elastyczność | najdroższy, najwolniejszy, błędy się kumulują; **ai-agents** |
   | fine-tuning | stały styl, format lub zachowanie, duży wolumen, tańszy mały model | nie dostarcza aktualnych faktów [założenie]; **ai-fine-tuning** |

   Wzorce łączy się (RAG w kroku workflow). Decyzję „agent” uzasadnij tym, czego workflow nie umie.
3. **Źródło modelu.** Trzy opcje, kryteria jak w arch-tech-selection (filtry, potem macierz):
   - **API dostawcy modeli** — najszybszy start i najlepsze modele; ryzyko: rezydencja danych, zmiany i wycofywanie wersji;
   - **usługa zarządzana w chmurze** (modele przez konto chmurowe) — wspólne IAM, sieć prywatna, wybór regionu;
     ryzyko: lock-in w narzędziach wokół modelu, opóźnienie wdrożenia nowych modeli [niezweryfikowane];
   - **open-weights na własnej infrastrukturze** — pełna kontrola danych i koszt stały; ryzyko: obsługa GPU
     i słabszy model (**ops-ai-inference**, **ai-model-optimization**); sprawdź licencję wag.
   Filtry obowiązkowe: region przetwarzania (także logów i cache u dostawcy), umowa powierzenia i zero-retention,
   dostępność modelu w regionie. Lock-in ograniczasz cienką warstwą własnego interfejsu (bramka) i zestawem
   ewaluacji, który pozwala zmienić model w dni, nie miesiące.
   Drugie piętro lock-inu to wagi przyzwyczajone do formatu narzędzi harnessu — widać je w wynikach, nie w konfiguracji;
   przed wymianą samego modelu albo samego harnessu zrób **test wymiany w obu kierunkach** na własnych ewaluacjach
   (stary model w nowym harnessie i nowy model w starym); wymiana samego modelu nie zdejmuje lock-inu
   (hipoteza z jednego preprintu, źródło niżej).
4. **Komponenty (architektura referencyjna).** Dobierz z listy tylko to, co uzasadniają wymagania:
   - **bramka** przed modelem: uwierzytelnienie, limity (żądania i tokeny na klienta), liczenie kosztu per najemca,
     routing i fallback, logowanie z maskowaniem PII;
   - **serwis promptów**: wersjonowane szablony, wdrażane jak kod, z ewaluacją w CI (**ai-prompt-engineering**);
   - **warstwa wyszukiwania** (**ai-rag**) i **warstwa narzędzi** (kontrakty, uprawnienia, idempotencja);
   - **ewaluacje i obserwowalność**: zbiór złoty, ewaluacje online, tracing kroków, koszt i tokeny na żądanie
     (**ai-evals**, **ops-observability**);
   - **guardrails**: walidacja wejścia i wyjścia, filtry treści, schemat wyniku;
   - **kolejka przeglądu przez człowieka** dla akcji nieodwracalnych lub o niskiej pewności; człowiek widzi propozycję
     i dowody, a nie tylko „zatwierdź”.
5. **Budżet opóźnienia.** Rozpisz cel p95 na kroki: bramka, wyszukiwanie, model (czas do pierwszego tokenu i generowanie),
   narzędzia, walidacja. Dźwignie: streaming (użytkownik widzi początek, więc liczy się czas do pierwszego tokenu),
   równoległe niezależne kroki, mniejszy model w prostych krokach, krótsze wyjście, cache. Dla każdego kroku: **timeout**
   i zachowanie po jego przekroczeniu.
6. **Cache, fallback, routing.**
   - **Prompt caching** (u dostawcy): stały prefiks na początku (narzędzia, instrukcje, dokumenty), zmienne na końcu;
     zmiana definicji narzędzi lub prefiksu unieważnia cache, więc szablony wersjonuj świadomie. Ceny i TTL: tabela
     w **core-cost-control**; wartości sprawdzaj w cenniku dostawcy w dniu decyzji.
   - **Cache wyników** (dokładny lub semantyczny) tylko dla odpowiedzi niezależnych od użytkownika i uprawnień;
     klucz zawiera wersję promptu i modelu oraz najemcę.
   - **Fallback**: drugi model lub dostawca z tym samym kontraktem wyjścia, degradacja (odpowiedź z cache, tryb
     bez AI, kolejka do człowieka). Przełączenie musi przejść ewaluację, nie tylko zwracać HTTP 200.
   - **Routing modeli**: prosty klasyfikator lub reguła kieruje łatwe żądania do taniego modelu, trudne do mocnego;
     próg ustawiasz na zbiorze złotym.
   - **Idempotencja akcji**: narzędzie zmieniające stan przyjmuje klucz idempotencji, bo ponowienie po timeoucie
     nie może wystawić dwóch zwrotów (**be-api-design**, **be-messaging-outbox**).
7. **Granice bezpieczeństwa** (pełny model zagrożeń: **arch-threat-modeling**). Rysujesz je na diagramie:
   - treść z dokumentów, maili i stron to **dane, nie polecenia** (prompt injection); model nie dostaje narzędzi
     zapisu ani wysyłki sterowanych taką treścią bez zatwierdzenia;
   - narzędzia działają z **uprawnieniami wywołującego użytkownika**, nie konta serwisowego z pełnym dostępem;
     autoryzacja po stronie narzędzia, nie w prompcie;
   - **egress danych**: lista dozwolonych adresów wyjściowych, brak renderowania obrazków i linków z adresami
     z modelu bez kontroli, maskowanie PII przed wysłaniem do dostawcy (**arch-privacy-compliance**).
8. **Koszt i pojemność** (wzór: `references/szablony.md`). Koszt żądania = Σ po wywołaniach (tokeny wejścia ×
   cena wejścia + tokeny wyjścia × cena wyjścia), osobno **bez cache** i **z cache** (odczyt z cache kosztuje ułamek
   ceny wejścia, zapis więcej). Pomnóż przez wolumen, dodaj wyszukiwanie, narzędzia i ewaluacje. Pojemność: żądania
   równoległe w szczycie × czas trwania, limity tokenów dostawcy; własny model — **ops-ai-inference**.
   Ceny podstawiasz z cennika z datą, nie z pamięci.
9. **Izolacja najemców.** Domyślnie wspólna infrastruktura i **logiczna izolacja**: identyfikator najemcy w każdym
   zapytaniu do indeksu, narzędzia i cache (filtr w bazie, nie w prompcie), osobne klucze szyfrowania i limity
   kosztu per najemca. Osobny indeks, instancja lub model tylko tam, gdzie wymaga tego umowa lub ryzyko
   (np. dane regulowane). Test: zapytanie najemcy A o dane B zwraca „brak”.
   **Wynik liczbowy z modelu (np. text-to-SQL):** dwie niezależne drogi — model pisze SQL, a drugi model wypełnia
   strukturę z katalogu metryk, którą kod kompiluje do SQL regułami. Zgodne wyniki = wysoka pewność, rozbieżność →
   krytyk albo odmowa, jedna droga → niższa pewność. Model pisze zapytanie, baza liczy (arytmetyka modelu zawodzi).
   Przed dołożeniem komponentu (wyszukiwanie wartości, wybór tabel) mierz, czy pomaga — gdy cały schemat mieści się
   w promptcie, dodatkowy etap potrafi pogorszyć wynik (F. Khan, 2026-10 [niezweryfikowane]).
   **Obsługa dużego wolumenu spraw** (zwroty, reklamacje, zmiany danych): progi autonomii per intencja, macierz
   pomyłek z kosztem i „model proponuje, orkiestrator wykonuje” — `references/obsluga-spraw.md`.
10. **Zapis.** `ai-architecture.md` (TL;DR, osie, wzorzec, komponenty, budżety, granice, koszt, ryzyka) i **ADR** dla
    każdej decyzji kluczowej: wzorzec, źródło modelu, rezydencja, fallback (**arch-architect-practice**,
    **docs-tech-writing**). Kryterium rewizji decyzji (np. jakość na zbiorze złotym poniżej progu) wpisz do ADR.

## Przykład
**Wejście:** „Asystent wsparcia: regulamin zmieniany co tydzień, zwroty w systemie płatności, dane tylko w UE, 200 tys.
żądań dziennie [przykład].”
**Wynik:**
- osie: świeżość wysoka, cena błędu wysoka (pieniądze), p95 ≤ 3 s, dane osobowe w UE;
- wzorzec: **workflow** (RAG po regulaminie, narzędzie `refund` z kluczem idempotencji, zatwierdzenie człowieka powyżej
  progu kwoty); agent odrzucony — kroki znane, ADR-002;
- model: usługa zarządzana w regionie UE albo API z umową powierzenia; bramka z własnym interfejsem, fallback na drugi model;
- budżet p95: bramka 0,1 s + wyszukiwanie 0,4 s + model do pierwszego tokenu 1,2 s (streaming) + narzędzia 0,8 s [przykład];
- koszt: wzór z `references/szablony.md` z cache i bez; stały prefiks (instrukcje, narzędzia) na początku promptu;
- granice: regulamin to dane; `refund` z uprawnieniami agenta wsparcia, nie konta serwisowego.

## Checklista
- [ ] sześć osi wymagań z liczbami; wzorzec najprostszy z dowodem, że niższy nie wystarcza
- [ ] źródło modelu: filtry (region, retencja, licencja), ocena lock-inu, ADR
- [ ] komponenty dobrane do wymagań; bramka z kosztem per najemca
- [ ] budżet opóźnienia per krok, timeouty, streaming, fallback po ewaluacji
- [ ] akcje zmieniające stan idempotentne; człowiek zatwierdza nieodwracalne
- [ ] granice zaufania na diagramie: dane to nie polecenia, uprawnienia wywołującego, egress
- [ ] koszt z i bez cache, ceny z datą; pojemność w szczycie
- [ ] izolacja najemców przetestowana; ADR-y z kryterium rewizji

## Źródła
- Anthropic, „Building effective agents” (anthropic.com/engineering, dostęp 2026-10-17): najprostsze rozwiązanie
  najpierw, workflow dla zadań przewidywalnych, agent przy potrzebie elastyczności, punkty kontrolne człowieka i limity iteracji.
- Anthropic, „Prompt caching” (platform.claude.com/docs, dostęp 2026-10-17): zapis 1,25× (5 min) lub 2× (1 h),
  odczyt zwykle 0,1× ceny wejścia (mnożnik zależy od modelu), TTL domyślnie 5 min, minimalna długość zależna od modelu,
  zmiana definicji narzędzi lub prefiksu unieważnia cache.
- Microsoft, „AI gateway in Azure API Management” (dostęp 2026-10-17, przez wyniki wyszukiwania): limity tokenów
  na konsumenta, cache semantyczny, równoważenie backendów — potwierdzono tylko pośrednio [niezweryfikowane w pełnym tekście].
- AWS, „Well-Architected Framework — Generative AI Lens” (docs.aws.amazon.com, dostęp 2026-10-17): sześć filarów
  w fazach cyklu życia, kontrolowana autonomia, odpowiedzialne AI; treść zasad szczegółowych [niezweryfikowane].
- [niezweryfikowane] opóźnienie wdrażania nowych modeli w usługach zarządzanych oraz dostępność regionów — sprawdź
  u wybranego dostawcy w dniu decyzji.
- Yu i in. (Salesforce AI), arXiv:2609.09134, preprint v1 z 8.09.2026, omówiony przez J. Wasowskiego („Model–Harness
  Fit: Why A Better Teacher Makes A Worse Agent”, Medium, ok. 12.10.2026); preprintu nie otwarto, liczby z artykułu
  [niezweryfikowane] — lock-in w wagach, test wymiany w obu kierunkach.

Opisane własnymi słowami.
