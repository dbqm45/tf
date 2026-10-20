---
name: ux-design-leadership
description: Użyj przy strategii i prowadzeniu designu w organizacji — dojrzałość UX, metryki (HEART, SUS), struktura zespołu, DesignOps, ścieżki kariery, ROI.
metadata:
  przeglad: 2027-10-17
  katalog: "Użyj, gdy prowadzisz lub budujesz funkcję designu/UX w organizacji (Head of Design, UX Strategist, DesignOps) — ocena dojrzałości UX (model NN/g, sześć etapów), wizja i strategia designu powiązane z wynikami biznesowymi, metryki UX (HEART, Goals-Signals-Metrics, SUS, skuteczność zadań), struktura zespołu designu (scentralizowana, wbudowana, hybrydowa) i kompromisy, budowa DesignOps i ResearchOps (narzędzia, procesy, standardy, rytuały jak krytyka projektu), ścieżki kariery i rekrutacja projektantów, zarządzanie jakością i dostępnością, budżet i argumenty ROI dla zarządu, rytm pracy z produktem i inżynierią; artefakty ux-maturity.md i design-strategy.md. Nie do struktury zespołów inżynierskich ogólnie (proc-team-topologies), metryk produktowych i wyboru, co budować (proc-product-discovery), poziomów inżynierów frontendu (fe-engineering-levels), praktyki architekta (arch-architect-practice), planowania i metod badań (ux-research-methods), budowy biblioteki komponentów (ux-design-systems) ani techniki dostępności (ux-accessibility)."
  slowa: "head of design, szef designu, dyrektor UX, UX strategist, strategia designu, wizja designu, dojrzałość UX, UX maturity, jak przekonać zarząd do UX, ROI designu, budżet na design, metryki UX, HEART, SUS, NPS to za mało, mierzenie UX, zespół designerów, ilu projektantów, scentralizowany zespół designu, designerzy w zespołach, hybryda, DesignOps, ResearchOps, krytyka projektu, rytuały designu, ścieżka kariery projektanta, rekrutacja projektanta, ocena projektantów, jakość designu, governance, współpraca z produktem i inżynierią, design bez wpływu"
---

# Przywództwo w designie — od oceny dojrzałości do rytmu pracy

Cel: funkcja designu, która ma wpływ na wyniki biznesowe i da się ją **zmierzyć, zorganizować i obronić budżetowo**.
Zaczynasz od stanu faktycznego, nie od ideału: ocena dojrzałości dyktuje, co robić najpierw. Skill daje
procedurę dla osoby prowadzącej design; techniki pracy zespołu (badania, system komponentów, dostępność) mają swoje
skille.

## Procedura
1. **Diagnoza dojrzałości.** Oceń organizację modelem NN/g (`references/dojrzalosc-i-metryki.md`): sześć etapów
   (od „nieobecny” do „kierowany użytkownikiem”) wg czterech czynników — strategia, kultura, proces, wyniki.
   Model nie jest listą do odhaczenia po kolei: wskaż etap **na czynnik** i dowód (kto decyduje o priorytetach,
   czy jest budżet, czy badania poprzedzają decyzje). Wynik: `docs/project/01-discovery/ux-maturity.md`.
2. **Cel i ograniczenia.** Zapytaj sponsora o 1–3 wyniki biznesowe, na które design ma wpłynąć (np. spadek
   rezygnacji w onboardingu, mniej kontaktów do wsparcia). Bez tego strategia jest listą życzeń.
3. **Wizja i strategia.** Jedna strona: wizja (jak wygląda doświadczenie za 2–3 lata), 3–5 filarów, dla każdego
   wynik biznesowy, inicjatywa, metryka i właściciel; czego **nie** robimy. Zapis: `design-strategy.md`.
   Wybór, co budować, i drzewo szans — proc-product-discovery; tu tylko powiązanie designu z wynikami.
4. **Metryki.** Dla każdego filaru ramka HEART (Happiness, Engagement, Adoption, Retention, Task success) w
   procesie Goals → Signals → Metrics; wybierz tylko kategorie istotne (zwykle 2–3 na produkt). Do ankiet SUS,
   do zachowań skuteczność i czas zadania. Metryka bez progu i właściciela nie jest metryką
   (`references/dojrzalosc-i-metryki.md`). Samo NPS nie wskazuje, co poprawić.
5. **Struktura zespołu.** Dobierz model do dojrzałości i liczby zespołów produktowych (tabela w
   `references/organizacja-i-dojrzalosc-zespolu.md`): scentralizowany, wbudowany albo hybrydowy. Decyzja zapisana
   jako ADR (kontekst, opcje, kompromisy, kiedy wrócimy). Zespoły inżynierskie i prawo Conwaya — proc-team-topologies.
6. **DesignOps i ResearchOps.** Zacznij od największego tarcia (np. brak jednego narzędzia, chaos w plikach, brak
   rekrutacji uczestników), nie od pełnej struktury: narzędzia i licencje, onboarding projektantów, standardy
   plików i przekazania, rytuały (krytyka projektu co tydzień, przegląd jakości przed wydaniem, demo), budżet.
   Metody badań — ux-research-methods; biblioteka komponentów — ux-design-systems.
7. **Kariera i rekrutacja.** Ścieżka z poziomami i kryteriami zachowań (rzemiosło, wpływ, przywództwo), dwie
   ścieżki: ekspercka i menedżerska; rekrutacja z zadaniem opartym na realnym problemie i jedną rubryką dla
   wszystkich kandydatów. Analogia dla inżynierii: fe-engineering-levels.
8. **Jakość i dostępność.** Bramki jakości w procesie (przegląd projektu przed przekazaniem, kontrola dostępności,
   zgodność wdrożenia z projektem) z jednym właścicielem. Technika dostępności — ux-accessibility.
9. **Budżet i argument ROI.** Zarządowi pokazujesz: koszt braku (kontakty do wsparcia, rezygnacje, poprawki po
   wdrożeniu), koszt zespołu i oczekiwany efekt z **zakresem** niepewności, nie jedną liczbą. Dane własne firmy
   przed benchmarkami zewnętrznymi; liczby cudze oznacz źródłem i datą.
10. **Rytm z produktem i inżynierią.** Wspólny cykl: planowanie kwartalne z wynikami (nie z listą ekranów),
    odkrywanie wyprzedzające budowę o 1–2 iteracje, przegląd projektu z inżynierią przed końcem projektowania,
    wspólny przegląd metryk po wydaniu. Rytuały zapisane w jednym miejscu.

Wynik: `ux-maturity.md` (diagnoza), `design-strategy.md` (strategia, metryki, struktura, plan 90 dni). TL;DR i
Przekazanie wg core-project-record; pierwsza linia: `Design leadership: <organizacja> — etap <czynnik:etap,…>`.

## Przykład
Wejście: „Fintech, 180 osób w produkcie; 12 projektantów w 6 zespołach, każdy robi po swojemu; zarząd pyta o sens
inwestycji.”
Wynik (fragment `design-strategy.md`):

```markdown
Design leadership: fintech — strategia: proces:3 kultura:2 strategia:2 wyniki:2 (etapy NN/g)
Filary: (1) onboarding bez tarcia → wynik: aktywacja z 41% do 55% w 2 kwartały
Metryki (HEART): Adoption = aktywacja konta w 7 dni; Task success = ukończenie weryfikacji bez wsparcia
(cel ≥ 85%); Happiness = SUS ≥ 75 (średnia SUS w badanych produktach to 68, czyli ok. 50. percentyl).
Struktura: hybryda — projektanci w zespołach produktowych, szef designu jako linia zarządzania; 1 osoba DesignOps.
Pierwsze 90 dni: wspólny plik biblioteki, krytyka co czwartek, rubryka rekrutacji; budżet: 1 etat DesignOps.
```

## Checklista
- [ ] ocena dojrzałości na czterech czynnikach z dowodami; nie traktowana jak lista do odhaczenia
- [ ] strategia powiązana z 1–3 wynikami biznesowymi, z listą rzeczy, których nie robimy
- [ ] metryki HEART w układzie Goals-Signals-Metrics z progiem i właścicielem
- [ ] decyzja o strukturze zespołu zapisana jako ADR z kompromisami
- [ ] DesignOps zaczyna od największego tarcia; rytuały i bramki jakości mają właściciela
- [ ] argument ROI z przedziałem niepewności i źródłami; [niezweryfikowane] oznaczone

## Materiały dodatkowe
- `references/dojrzalosc-i-metryki.md` — etapy NN/g, HEART, SUS, szablon ramki metryk; czytaj przy diagnozie i metrykach.
- `references/organizacja-i-dojrzalosc-zespolu.md` — struktury zespołu, DesignOps, kariera, ROI; czytaj przy projekcie organizacji.

## Źródła
- NN/g, *UX Maturity Model* (nngroup.com/consulting/ux-maturity-assessment/ i artykuły o etapach 1–5), dostęp
  2026-10-17: sześć etapów (absent, limited, emergent, structured, integrated, user-driven), cztery czynniki
  (strategy, culture, process, outcomes). Opis etapu 6 według źródeł wtórnych [niezweryfikowane].
- Rodden, Hutchinson, Fu, *Measuring the User Experience on a Large Scale* (Google, CHI 2010) — HEART i
  Goals-Signals-Metrics; potwierdzone przez źródła wtórne, oryginału nie otwarto (dostęp 2026-10-17).
- MeasuringU (Sauro, Lewis), SUS: średnia 68 ≈ 50. percentyl (dostęp 2026-10-17).
- Futurice, *DesignOps — small team starter guide* — opis modeli i ryzyka hybrydy (dostęp 2026-10-17).
Opisane własnymi słowami.
