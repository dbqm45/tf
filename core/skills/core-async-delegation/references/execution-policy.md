# Polityka wykonania planu bez nadzoru — formaty

## Polecenie `/goal` do skopiowania
Warunek celu jest testem zatrzymania sesji; polityka z `SKILL.md` §4 jest sposobem jego spełnienia. Oceniający
widzi tylko rozmowę, więc warunek odwołuje się do tego, co agent wypisuje.
```text
/goal Wykonaj wszystkie fazy planu docs/project/<krok>/plan.md wg polityki core-async-delegation §4.
Gotowe, gdy: każdy automatyczny punkt w sekcji postępu planu jest odhaczony, każda faza ma własny commit
(Conventional Commits) z SHA wypisanym w rozmowie, a na końcu jest lista punktów do weryfikacji ręcznej.
Ograniczenia: nie zmieniaj ani nie osłabiaj istniejących testów, chyba że plan tak mówi; nie dotykaj plików
spoza zakresu planu. Zatrzymaj się po <N> turach, jeśli nie skończysz.
```
Uruchomienie bez okna (lista narzędzi bez sieci i bez `git push`, jeśli zadanie ich nie wymaga):
```bash
claude -p "<polecenie>" --allowedTools "<lista>" --permission-mode acceptEdits --max-budget-usd <kwota>
```

## Linie werdyktu (po każdej bramce)
```text
BRAMKA testy-z-planu: PASS
BRAMKA celowe-zepsucie: PASS (test czerwony na zepsutym kodzie, plik przywrócony)
BRAMKA lint: FAIL (2 błędy w src/limits.ts, próba 1/2)
BRAMKA lint: PASS
DIRTY (nie dodane): .env.local, notes.md
ADAPT: plan wskazuje src/limits.ts, plik jest w src/limits/index.ts
COMMIT faza 2: a1b2c3d
```

## Celowe zepsucie (tylko fazy, które dodają lub zmieniają testy)
1. Pliki fazy są już w indeksie (`git add <pliki>`), więc przywrócenie będzie dokładne.
2. W kodzie produkcyjnym odwróć lub osłab chronione zachowanie — zmiana tylko w drzewie roboczym.
3. Uruchom wyłącznie ten test. Czerwony = PASS bramki.
4. Zawsze przywróć `git checkout -- <plik>`, także po porażce; zepsucie nigdy nie trafia do commita.
5. Test zielony na zepsutym kodzie → asercja nic nie chroni → wzmocnij asercję (nie osłabiaj kodu, nie pomijaj kroku).

## Blok STOP (potem koniec: bez dalszych zmian i bez commita)
```text
STOP — <ROZJAZD STRUKTURALNY | PORAŻKA BRAMKI> w fazie <N>
Oczekiwane: <co mówi plan / czego wymaga bramka>
Znalezione: <stan faktyczny / skrót błędu>
Dlaczego blokuje: <czemu nie da się kontynuować bez decyzji człowieka>
Wznowienie: <co poprawić>, potem ponownie od fazy <N>
```
Przed zatrzymaniem: odhaczone punkty zostają, praca w toku zostaje niezacommitowana w drzewie roboczym,
celowe zepsucie przywrócone.

## Raport końcowy (zawsze — po sukcesie i po STOP)
```text
RAPORT — <krok>
Fazy: <zrobione>/<wszystkie>
- Faza 1: <tytuł> — <SHA> (bramki: testy, celowe-zepsucie, lint, typy: PASS)
- Faza 2: <tytuł> — STOP (<powód>)
Adaptacje: <po jednej linii albo „brak”>
Niepewności: <punkty, gdzie plan i kod się nie zgadzały, bez niezależnego źródła — albo „brak”>
Do weryfikacji ręcznej (dla człowieka): <punkty z planu, dosłownie>
Następny krok: przegląd w świeżym kontekście (core-git-workflow; testy od specyfikacji, pack-it: qa-spec-first-testing)
```

## Odwołania w commitach
Identyfikatory zgłoszeń (`ABC-123`, `#123`) dopisujesz w stopce commita tylko wtedy, gdy padły w rozmowie lub
planie — nigdy nie wymyślasz ich z nazwy gałęzi.
