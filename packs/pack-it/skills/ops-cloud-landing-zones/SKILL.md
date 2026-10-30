---
name: ops-cloud-landing-zones
description: Użyj przy projekcie fundamentu chmury dla wielu zespołów — landing zone, konta i subskrypcje, sieć hub-spoke, account vending.
metadata:
  przeglad: "2027-04-17"
  widocznosc: nazwa
  katalog: "Użyj, gdy projektujesz lub porządkujesz fundament chmury dla wielu zespołów (AWS, Azure, GCP) — czym jest landing zone, hierarchia kont, subskrypcji i projektów oraz środowiska, federacja tożsamości i SSO, topologia sieci (hub-and-spoke, transit gateway, Virtual WAN, Shared VPC), konta logów i narzędzi, guardrails zapobiegawcze i wykrywające, tagowanie i alokacja kosztów, account vending i subscription vending w IaC, bazowe konfiguracje per typ obciążenia, wersjonowanie i rozwój landing zone. Wynik to dokument projektowy i lista decyzji. Nie do samych kontroli bezpieczeństwa w chmurze (sec-cloud-security), modułów Terraform (ops-iac-terraform), optymalizacji kosztów (ops-finops), platformy dla deweloperów (ops-platform-engineering) ani przenoszenia obciążeń (ops-cloud-migration)."
  slowa: "wprowadzanie zmian w landing zone, zmiany dotykają wielu istniejących subskrypcji i kont, aktualizacja landing zone, nowa wersja landing zone, wersjonowanie fundamentu chmury, rollout zmian na wszystkie konta, zmiana fundamentu chmury, setki istniejących subskrypcji, setki kont, landing zone, zmiany w landing zone, wersjonowanie landing zone, aktualizacja landing zone, wdrażanie zmian na wiele subskrypcji, dryf kont, fundament chmury, cloud foundation, Control Tower, Landing Zone Accelerator, Azure landing zones, Cloud Adoption Framework, account vending, subscription vending, hierarchia kont, organizacja AWS, grupy zarządzania, foldery GCP, hub and spoke, transit gateway, Virtual WAN, Shared VPC, konto logów, guardrails, SCP, tagowanie, alokacja kosztów, nowe konto dla zespołu, wiele zespołów w chmurze, SSO chmura"
---

# Landing zone: fundament chmury dla wielu zespołów

Landing zone to wstępnie skonfigurowane, zautomatyzowane środowisko wielokontowe: hierarchia, tożsamość, sieć,
logowanie, guardrails i proces zakładania nowych kont. Ten skill opisuje **strukturę i automatykę fundamentu**.
Treść kontroli bezpieczeństwa (szyfrowanie, CSPM, break-glass, benchmarki) to sec-cloud-security; moduły i stan
Terraform to ops-iac-terraform; optymalizacja rachunku to ops-finops. Wynik: `docs/project/04-architecture/landing-zone.md`
(core-project-record) z projektem i listą decyzji (format niżej). Niczego nie wdrażasz: zmiany w chmurze idą jako plan
(`terraform plan`, tryb audytu, okno zmian) i wchodzą po akceptacji człowieka.

## Procedura
1. **Zakres i wybór wzorca.** Ile zespołów, chmur, regionów, wymogów regulacyjnych, kto utrzymuje fundament
   (zespół platformy: ops-platform-engineering). Dobierz punkt wyjścia, nie buduj od zera:
   - AWS: **AWS Control Tower** (landing zone, kontrole, Account Factory); rozszerzenia: Account Factory for Terraform
     i **Landing Zone Accelerator on AWS**; wariant w pełni własny tylko przy wymogach, których to nie pokrywa.
   - Azure: **Azure landing zones** w Cloud Adoption Framework (platform landing zone + application landing zones,
     implementacje referencyjne w Bicep i Terraform).
   - GCP: **Google Cloud enterprise foundations blueprint** (dawniej security foundations blueprint) z Terraform.
   Nazwy produktów i blueprintów zmieniają się; potwierdź w dokumentacji dostawcy (core-source-research).
2. **Hierarchia i środowiska.** Organizacja → grupy (OU, grupy zarządzania, foldery) → konta, subskrypcje, projekty.
   Granica konta jest granicą uprawnień, limitów i rachunku, więc **jedno obciążenie × jedno środowisko = jedno konto**
   (produkcja osobno od nieprodukcji). Grupy wg *polityk*, nie wg organigramu firmy (reorganizacje zmieniają
   organigram, polityki zostają). Typowy układ: `platform` (logi, bezpieczeństwo, sieć, tożsamość, narzędzia),
   `workloads` (prod, nonprod), `sandbox` (budżet, auto-sprzątanie), `suspended`. Konto zarządzające organizacji
   bez obciążeń. Głębokość drzewa minimalna (limity głębokości: sprawdź u dostawcy).
3. **Tożsamość.** Jedno źródło prawdy (IdP firmowy) → federacja SSO (AWS IAM Identity Center, Microsoft Entra ID,
   Cloud Identity / Workforce Identity Federation) → grupy mapowane na role per konto. Role standardowe: admin
   platformy, deweloper, tylko odczyt, audyt. Użytkownicy lokalni w kontach zabronieni guardrailem. MFA, PAM
   i break-glass: sec-zero-trust-identity i sec-cloud-security; tożsamości maszyn i OIDC w CI: ops-secrets-identities.
4. **Sieć.** Plan adresacji (CIDR) z rejestrem **zanim** powstanie pierwsza sieć: zachodzące zakresy blokują
   późniejsze łączenie, a zmiana to migracja. Topologie:
   - **hub-and-spoke**: centralny hub z zaporą, DNS i łączem do on-premises; sieci obciążeń jako spoke. Realizacja:
     AWS Transit Gateway, Azure Virtual WAN lub hub VNet, GCP hub project z peeringiem lub NCC [niezweryfikowane: aktualne limity];
   - **Shared VPC** (GCP; w AWS odpowiednik to VPC sharing przez RAM): jedna sieć udostępniana projektom/kontom
     obciążeń, zarządzana centralnie;
   - **sieć per obciążenie** bez huba: prostsza, gdy obciążeń jest mało i niewiele łączą.
   Zapisz: kto jest właścicielem huba, centralny czy rozproszony egress, rozwiązywanie nazw (DNS prywatny),
   koszt transferu między strefami i regionami (ops-finops). Segmentacja i prywatne punkty końcowe: sec-cloud-security.
5. **Logi i narzędzia centralne.** Osobne konta/projekty: **log archive** (tylko zapis, retencja, ochrona przed
   usunięciem) i **security tooling** (CSPM, wykrywanie; delegowany administrator). Trail/ustawienia diagnostyczne
   włączone *przez fundament*, nie przez zespoły. Co dokładnie logować i jak wykrywać: sec-cloud-security,
   ops-security-operations; telemetria aplikacji: ops-observability.
6. **Guardrails jako polityki.** Dwa rodzaje, oba w projekcie:
   - **zapobiegawcze** (preventive): SCP, Azure Policy z efektem Deny, Organization Policy — blokują akcję;
   - **wykrywające** (detective): reguły Config, Azure Policy z Audit, CSPM — zgłaszają niezgodność.
   Zasada: blokada tylko tam, gdzie nie ma uprawnionego wyjątku (np. wyłączenie logów audytowych); reszta wykrywanie
   z właścicielem i terminem. Każdy guardrail wchodzi w **trybie audytu** (zwykle 2–4 tygodnie [przykład]), potem
   blokada. Wyjątki: rejestr z właścicielem i datą wygaśnięcia. Zawartość listy guardrails: sec-cloud-security.
7. **Tagowanie i koszty.** Minimalny zestaw tagów wymuszany polityką: `team`, `env`, `project`, `cost-center`,
   `data-class`, `expires` (dla tymczasowych). Tag kosztowy aktywowany w narzędziu rozliczeń; konto/subskrypcja
   jest *pierwszym* wymiarem alokacji, tagi drugim. Model: showback najpierw, chargeback gdy dane są wiarygodne.
   Budżety i anomalie, sprzątanie: ops-finops.
8. **Vending kont.** Nowe konto/subskrypcja powstaje z żądania (PR do pliku YAML/HCL lub formularz → PR), nie
   z konsoli. Wejście: nazwa, właściciel, środowisko, typ obciążenia, centrum kosztów, CIDR z rejestru. Wyjście:
   konto we właściwej grupie, role SSO, budżet i alerty, tagi, połączenie z hubem, baseline, osobne pole
   tożsamości dla pipeline'u (OIDC). Realizacja: Account Factory for Terraform / customizations, Azure subscription
   vending (moduł referencyjny), projekt factory w GCP. Moduły i stan: ops-iac-terraform. Czas od żądania do
   użyteczności konta jest metryką fundamentu (cel [przykład]: < 1 dzień roboczy).
9. **Bazy per typ obciążenia (golden baselines).** Mała liczba profili, np. `web-app`, `data-platform`, `batch`,
   `regulated`; każdy to zestaw: sieć, role, polityki, logi, backup, budżet. Wybór profilu przy vendingu. Nie
   mnóż profili: nowy powstaje dopiero po trzecim powtórzonym wyjątku.
10. **Rozwój i wersje.** Landing zone jest produktem: backlog, właściciel, wersje (SemVer: core-semver; zmiana
    guardrailu blokującego = major dla konsumentów). Zmiany wdrażane falami (konta testowe → sandbox → nonprod →
    prod), z notą zmian i planem wycofania. Pomiar dryfu (konta poza bazą) i migracja kont do nowej wersji
    to stały proces. Konta zastane: ops-cloud-migration (relokacja do hierarchii).
11. **Zapis.** Dokument projektowy + lista decyzji; każda decyzja: pytanie, wybór, odrzucone opcje, właściciel,
    data przeglądu. Wynik `proposed` do akceptacji człowieka.

## Format listy decyzji
| ID | Decyzja | Wybór | Odrzucone | Właściciel | Przegląd |
|---|---|---|---|---|---|

## Przykład
**Sytuacja:** „Mamy 20 zespołów, AWS jako główna chmura, mały Azure dla jednej aplikacji. Konta zakłada się mailem do admina.”
**Wynik** (fragment, liczby [przykład]):

| ID | Decyzja | Wybór | Odrzucone | Właściciel | Przegląd |
|---|---|---|---|---|---|
| D-01 | Punkt wyjścia AWS | Control Tower + Account Factory for Terraform | własny skrypt Organizations (koszt utrzymania) | platforma | 2027-04 |
| D-04 | Sieć | Transit Gateway, hub z zaporą, CIDR z rejestru /16 per środowisko | peering każdy z każdym (rośnie kwadratowo) | sieci | 2027-04 |
| D-07 | Guardrail wyłączenia logów | preventive (SCP), bez wyjątków | detective (za późno) | bezpieczeństwo | rocznie |
| D-09 | Tagi | `team`, `env`, `cost-center`; brak = odmowa w vendingu | wymóg ręczny w wiki | finanse | 2027-01 |

Azure: osobny przypadek, bez pełnej platformy do 3 aplikacji; wchodzi pod ten sam IdP i rejestr CIDR.

## Pułapki
- Fundament budowany „w pełni” przed pierwszym obciążeniem: zacznij od minimalnego rdzenia i pierwszego klienta.
- Guardrails od razu w trybie blokady: zespoły omijają je lub tracą zaufanie do platformy.
- Konta ręczne obok vendingu: nie obejmie ich baseline ani rozliczenie.
- Rozjazd wersji: 40 kont na 5 wersjach baseline'u; mierz i migruj.

## Checklista
- [ ] punkt wyjścia wybrany i nazwa produktu sprawdzona w dokumentacji
- [ ] hierarchia wg polityk, granica konta = obciążenie × środowisko, konto zarządzające puste
- [ ] SSO z jednego IdP, brak użytkowników lokalnych
- [ ] rejestr CIDR przed pierwszą siecią; topologia i właściciel huba zapisani
- [ ] konta log archive i security tooling, logi włączone przez fundament
- [ ] guardrails: rodzaj (zapobiegawczy/wykrywający), tryb audytu, rejestr wyjątków
- [ ] tagi wymuszane, alokacja kosztów po koncie i tagach
- [ ] vending z IaC, metryka czasu do konta, profile bazowe
- [ ] wersjonowanie i fale wdrażania zmian fundamentu

## Źródła
- AWS Control Tower, Account Factory, Landing Zone Accelerator on AWS — dokumentacja AWS; kontrole preventive (SCP), detective
  (Config), proactive (CloudFormation hooks) potwierdzone wyszukiwaniem 2026-10-17, strony dokumentacji niedostępne bezpośrednio
- Microsoft Learn: Cloud Adoption Framework, Azure landing zones (platform i application landing zones, subscription
  vending); wyszukiwanie 2026-10-17
- Google Cloud: enterprise foundations blueprint, organizacja folderów, Shared VPC, topologia hub-and-spoke
  (docs.cloud.google.com/architecture); wyszukiwanie 2026-10-17
- Limity (głębokość grup, liczba spoke'ów, peering) [niezweryfikowane]; sprawdź przed projektem.
