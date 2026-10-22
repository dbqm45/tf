---
name: ops-platform-engineering
description: Użyj przy wewnętrznej platformie deweloperskiej (IDP) — platforma jako produkt, złote ścieżki, portal, samoobsługa, metryki.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj przy budowie i prowadzeniu wewnętrznej platformy deweloperskiej dla wielu zespołów — platforma jako produkt (użytkownicy to deweloperzy, odkrywanie bólów, roadmapa, metryki adopcji), najcieńsza użyteczna platforma, złote ścieżki i szablony, samoobsługa z barierami, portal (np. Backstage), abstrakcje infrastruktury (kompozycje Crossplane, moduły Terraform, operatory Kubernetes), GitOps (Argo CD, Flux), policy as code, topologia zespołu platformowego i tryby interakcji, miary sukcesu (DORA, SPACE, ankiety doświadczenia deweloperów), CNCF Platforms White Paper i Platform Engineering Maturity Model. Wynik to karta platformy i roadmapa. Nie do podziału organizacji na typy zespołów (proc-team-topologies), budowy pipeline'ów (ops-ci-cd), manifestów Kubernetes (ops-kubernetes), pisania modułów Terraform (ops-iac-terraform), definicji metryk DORA (eng-continuous-delivery) ani fundamentu kont i sieci chmury (ops-cloud-landing-zones)."
  slowa: "platforma wewnętrzna, platforma dla wielu zespołów, zespoły wdrażają po swojemu, od czego zacząć platformę, platforma której nikt nie użyje, czy platforma się opłaciła, metryki platformy, zwrot z platformy, wskaźniki sukcesu platformy, internal developer platform, IDP, platform engineering, zespół platformowy, złota ścieżka, golden path, paved road, portal deweloperski, Backstage, samoobsługa, self-service, Crossplane, GitOps, Argo CD, Flux, policy as code, developer experience, DevEx, adopcja platformy, roadmapa platformy, karta platformy, ticket do ops, szablony serwisów, dojrzałość platformy, SPACE, ankieta deweloperów"
  widocznosc: nazwa
---

# Platform engineering — wewnętrzna platforma deweloperska

**Granica.** Typy zespołów i tryby interakcji (platform team, X-as-a-Service) — **proc-team-topologies**; tutaj tylko ich
zastosowanie do zespołu platformowego. Pipeline'y — **ops-ci-cd**; manifesty — **ops-kubernetes**; moduły Terraform —
**ops-iac-terraform**; definicje DORA — **eng-continuous-delivery**; fundament kont i sieci — **ops-cloud-landing-zones**;
wydania i GitOps od strony wdrożenia — **ops-release-engineering**. Zmiany na realnych klastrach i kontach platformy
proponujesz jako plan (diff, dry-run, okno zmian) i stosujesz po zatwierdzeniu przez człowieka.

## Procedura
1. **Czy platforma jest potrzebna.** Sygnały: wiele zespołów odtwarza to samo (CI, wdrożenie, baza, monitoring), długie
   kolejki do ops, duże zróżnicowanie narzędzi, onboarding liczony w tygodniach. Przy 2–3 zespołach wystarczy wspólny
   szablon i dobra dokumentacja, nie osobny zespół.
2. **Użytkownicy i bóle.** Użytkownikiem są zespoły deweloperskie. Przeprowadź 8–12 wywiadów (kilka zespołów, różne
   doświadczenie), zmapuj ścieżkę „pomysł → produkcja” z czasami oczekiwania, zbierz zgłoszenia do ops. Zapisz bóle
   z liczbą zespołów i kosztem (czas, ryzyko). Bez tego roadmapa jest zgadywaniem.
3. **Platforma jako produkt.** Właściciel produktu, wizja, roadmapa wg wpływu na bóle (proc-product-discovery, RICE/WSJF
   z proc-lean), publiczny backlog, cykl opinii. Platforma jest **dobrowolna**: zespół wybiera ją, bo jest łatwiejsza
   (CNCF Platforms White Paper: platforma nie powinna być obowiązkowa ani blokować narzędzi spoza niej). Obowiązkowe są
   tylko wymagania (bezpieczeństwo, koszt), nie sposób ich spełnienia.
4. **Najcieńsza użyteczna platforma (TVP).** Zacznij od jednego, najboleśniejszego przepływu dla 1–2 zespołów pilotażowych
   (np. „nowy serwis na produkcji w 1 dzień”), nie od portalu. Dostarczaj cienką warstwę nad tym, co już istnieje,
   i rozbudowuj po dowodzie użycia. Test: czy pilot wróciłby do starego sposobu?
5. **Złote ścieżki i szablony.** Szablon serwisu zawiera repozytorium, pipeline, obserwowalność, tagi kosztowe, sekrety,
   skanowanie; ma właściciela, wersję i ścieżkę aktualizacji istniejących serwisów (inaczej szablony się rozjeżdżają).
   Ścieżka obejmuje 80% przypadków; wyjście poza nią jest dozwolone, ale z własnym utrzymaniem.
6. **Samoobsługa z barierami.** Deweloper prosi o zasób deklaratywnie (PR, formularz w portalu, plik CRD), bez ticketu.
   Bezpieczeństwo jest wbudowane w abstrakcję (domyślnie szyfrowanie, sieć prywatna, tagi) i egzekwowane
   **policy as code** (np. OPA/Gatekeeper, Kyverno, politykami w pipeline) w trybie audytu, potem wymuszenia; odmowa
   zwraca czytelny komunikat z naprawą.
7. **Abstrakcje infrastruktury** — dobór wg wymaganego kontraktu, nie mody:

| Potrzeba | Narzędzie | Uwaga |
|---|---|---|
| spójne zasoby chmury z własną polityką | moduły Terraform/OpenTofu (ops-iac-terraform) | prosty start; samoobsługa wymaga potoku i stanu |
| własne API typu „Database” nad wieloma zasobami | Crossplane: XRD i Composition | reconcile w klastrze; koszt: model CRD i debugowanie |
| logika dla jednego rodzaju zasobu w klastrze | operator Kubernetes | utrzymujesz kod; używaj gotowych, gdy są |
| wdrożenie stanu z gita | GitOps: Argo CD lub Flux | reconcile i drift; wydania — ops-release-engineering |
   Jedna abstrakcja = jedna umowa wersjonowana jak API (zmiany niezgodne wstecz przez wersje).
8. **Portal (opcjonalny).** Katalog usług, szablony (software templates), dokumentacja, status. Backstage to otwarty
   framework portalu (projekt CNCF) — wymaga zespołu do utrzymania wtyczek i uprawnień; alternatywą jest gotowy produkt
   lub samo repozytorium szablonów i CLI. Portal buduj po tym, jak ścieżki działają; katalog zacznij od właścicieli
   i zależności, bo to najczęściej brakuje.
9. **Zespół i interakcje.** Zespół platformowy (typ platform, ok. 5–9 osób na start [przykład]), tryb domyślny
   X-as-a-Service, na starcie Collaboration z zespołami pilotażowymi, Facilitating przy wdrażaniu szablonów
   (proc-team-topologies). Pilnuj obciążenia poznawczego samego zespołu platformowego: liczba produktów, rotacja dyżurów, wsparcie.
10. **Miary sukcesu.** Cztery warstwy, żadna jako cel nagrody (prawo Goodharta):
   - **adopcja:** odsetek zespołów/serwisów na złotej ścieżce, aktywni użytkownicy, czas onboardingu, liczba ticketów do ops;
   - **DORA** (eng-continuous-delivery) na poziomie usług, porównywane w czasie dla tego samego systemu, nie między zespołami;
   - **doświadczenie:** ankieta (np. kwartalna) o satysfakcji, obciążeniu poznawczym, pętlach zwrotnych i przepływie (DevEx), wymiary SPACE (satysfakcja, wydajność, aktywność, komunikacja, efektywność);
   - **biznes i koszt:** czas „pomysł → produkcja”, koszt platformy na zespół, incydenty z przyczyn platformy.
   Raport dla zarządu: trend 3–4 miar, wniosek i decyzja, nie ściana metryk; do tego samoocena wg CNCF Platform
   Engineering Maturity Model (pkt 11) jako mapa luk, bez rankingu zespołów.
11. **Dojrzałość.** Samoocena wg CNCF Platform Engineering Maturity Model: pięć aspektów (inwestycja, adopcja, interfejsy,
    operacje, pomiary) oceniane osobno na czterech poziomach. Używaj do rozmowy i luk, nie do rankingu zespołów.
12. **Wynik:** karta platformy (cel, użytkownicy, bóle, zakres „jest/nie jest”, miary, właściciel, tryb współpracy)
    i roadmapa (Teraz/Następne/Później z hipotezą i miarą dla każdej pozycji) w `docs/project/`.

## Przykład
Wejście: „30 zespołów, każdy ma inny pipeline i ręczne zamawianie baz; ops ma 60 ticketów miesięcznie.”

Wynik (fragment) [przykład, liczby ilustracyjne]:
- Ból nr 1 (11 z 12 wywiadów): „nowa usługa na produkcji = 3 tygodnie”; nr 2: baza przez ticket, 5 dni.
- Karta: cel „nowy serwis z pipeline, obserwowalnością i bazą w ≤ 1 dzień bez ticketu”. Poza zakresem na rok 1: portal, FinOps, ML.
- Roadmapa: Teraz — szablon serwisu + pipeline (2 zespoły pilotażowe), baza przez Composition w Crossplane lub moduł Terraform z PR;
  Następne — policy as code w trybie audytu, katalog właścicieli; Później — portal.
- Miary: czas pierwszego wdrożenia (cel 1 dzień), odsetek zespołów na ścieżce (pilot 2 → 10 w 2 kwartały), tickety do ops (−50%),
  ankieta DevEx co kwartał. Nie nagradzamy zespołów za liczby; wynik DORA śledzimy w czasie per usługa.
- Interakcja: Collaboration z pilotami przez 6 tygodni, potem X-as-a-Service.

## Checklista
- [ ] wywiady z użytkownikami i bóle z liczbą zespołów; potrzeba platformy uzasadniona
- [ ] właściciel produktu, roadmapa wg bólów, platforma dobrowolna
- [ ] najcieńsza użyteczna platforma z zespołami pilotażowymi
- [ ] złota ścieżka z wersją i ścieżką aktualizacji szablonów
- [ ] samoobsługa z barierami (policy as code: audyt, potem wymuszenie)
- [ ] abstrakcje wersjonowane jak API; wybór narzędzia uzasadniony
- [ ] miary: adopcja, DORA w czasie, ankieta DevEx/SPACE, koszt; nie jako cele
- [ ] samoocena wg Platform Engineering Maturity Model; karta i roadmapa zapisane

## Źródła
- CNCF TAG App Delivery, „CNCF Platforms White Paper” (v1, 2023) — atrybuty platformy: produkt, doświadczenie użytkownika, dobrowolność, złote ścieżki; tag-app-delivery.cncf.io, wyszukiwanie 2026-10-17 (strona niedostępna do pobrania w sesji).
- CNCF TAG App Delivery, „Platform Engineering Maturity Model” (2023; wg źródła wtórnego bex.co wersja 2 z 2026-03-23, rdzeń niezmieniony) — pięć aspektów, cztery poziomy; nazwy poziomów w źródłach różnią się [niezweryfikowane].
- CNCF: Crossplane — awans do poziomu graduated ogłoszony 2025-11-06; Argo — graduated od 2022-12-06 (cncf.io/projects/argo); Flux — graduated [wg źródła wtórnego, niezweryfikowane]; Backstage — poziom dojrzałości CNCF [niezweryfikowane, źródła rozbieżne], sprawdź na cncf.io/projects.
- Forsgren i in., „The SPACE of Developer Productivity” (2021); Noda i in., „DevEx” (ACM Queue, 2023) — przez źródła wtórne, 2026-10-17 [niezweryfikowane u źródła].
- DORA, „2025 State of AI-assisted Software Development” i DORA AI Capabilities Model — jedną z siedmiu zdolności są wysokiej jakości platformy wewnętrzne (źródła wtórne, 2026-10-17).
