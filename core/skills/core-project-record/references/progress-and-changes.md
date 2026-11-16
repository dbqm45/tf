# Postęp kroku, eksploracja i tracker

> Szczegóły do SKILL.md core-project-record: sekcja „Postęp” w raporcie kroku, kroki badawcze, decyzje człowieka
> vs propozycje AI, przeniesienie planu cięć do trackera.

## Postęp kroku realizacji (sekcja „Postęp” w `06-delivery/NNN-*.md`)
Plan kroku (szablon `delivery`) kończy się podsekcją „Postęp” — jedynym miejscem stanu realizacji kroku:
- pola wyboru `- [ ]` / `- [x]` są tylko w „Postępie”; w pozostałej części planu ich nie ma;
- numeracja `<faza>.<n>` nadana przy planowaniu nigdy nie jest przenumerowana — usunięty punkt zostawia lukę,
  zmieniona intencja to notatka w bloku fazy, tytuł bez zmian;
- następny krok = pierwsze `- [ ]`; faza bieżąca = faza pierwszego `- [ ]`; ukończenie = `[x] / ([ ] + [x])`;
- pole odhaczasz po każdym kroku; SHA dopisujesz raz, po commicie fazy (` — <sha>`, core-git-workflow).
  W środku fazy `[x]` bez SHA to stan poprawny; faza bez zmian w kodzie zostaje bez SHA;
- kryteria ręczne odhacza się dopiero po potwierdzeniu człowieka; przy ostatniej fazie przypomnij wszystkie
  niezaliczone kryteria ręczne z wcześniejszych faz.
Punkt kontrolny w `wip/` mówi, które zadanie trwa; „Postęp” mówi, gdzie w planie kroku jesteś.

## Zmiany, fazy i eksploracja
- **Eksploracja, której produktem jest raport** (badanie, mapa kodu, ranking opcji), to osobny wpis — osobny raport
  kroku z intencją na górze: co badamy, czego na tym etapie NIE robimy (żadnych zmian w kodzie, żadnej decyzji),
  kto i kiedy decyduje. Następny krok czyta ten raport jako punkt wyjścia; badania nie dopisujesz do poprzedniej,
  zamkniętej zmiany.
- Raport kroku i raport przeglądu mają sekcję **„Decyzje człowieka vs propozycje AI”**: co zaproponował agent,
  co rozstrzygnął człowiek i dlaczego. To ślad, kto za co odpowiada.

## Plan cięć w trackerze (Jira, Linear, GitHub Issues)
- **Plan cięć do trackera:** zgłoszenie z pozycji planu — tytuł = Wynik, opis = Wymagania + Warunki wstępne + Ryzyko
  + kryteria akceptacji; etykiety `cięcie` / `fundament` / `gwiazda`; zależności jako powiązania zgłoszeń;
  identyfikator zmiany w treści.
- **Dostęp agenta do trackera:** token o najmniejszym zakresie (czytanie i tworzenie w jednym projekcie, bez
  administracji); kasowanie, zmiana ról i masowe zmiany statusów robi człowiek w interfejsie narzędzia. Po pierwszej
  sesji przejrzyj dziennik aktywności i ustal z zespołem, czy agent może zmieniać i komentować cudze zgłoszenia.

## Przykład sekcji „Postęp” w trakcie fazy 2
```
### Postęp
#### Faza 1: Model i zapis
- [x] 1.1 npm test -- cards.repo.spec.ts przechodzi — 3f9c2a1
- [x] 1.2 migracja działa na kopii bazy (ręczne) — 3f9c2a1
#### Faza 2: Endpoint
- [x] 2.1 npm test -- cards.api.spec.ts przechodzi
- [ ] 2.3 401 dla niezalogowanego (2.2 usunięty — luka zostaje)
- [ ] 2.4 człowiek sprawdził odpowiedź w przeglądarce (ręczne)
```
Następny krok: 2.3; faza bieżąca: 2; ukończenie: 3/5. Punkt 2.1 bez SHA, bo faza 2 nie ma jeszcze commita.

Źródło: kurs 10xDevs, ed. 3 (2026), moduł 2 (format postępu planu, przeniesienie roadmapy do trackera) i moduł 4,
lekcja 4 (kroki badawcze) — materiał szkoleniowy (dostęp 2026-10-09). Opisane własnymi słowami.
