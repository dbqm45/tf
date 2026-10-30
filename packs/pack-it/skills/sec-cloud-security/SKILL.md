---
name: sec-cloud-security
description: Użyj przy bezpieczeństwie chmury AWS, Azure, GCP — model współdzielonej odpowiedzialności, guardrails kont, logi, CSPM i CNAPP, CIS, baseline.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj przy projekcie lub przeglądzie bezpieczeństwa chmury publicznej (AWS, Azure, GCP) — współdzielona odpowiedzialność (IaaS, PaaS, SaaS), struktura kont, subskrypcji i projektów z guardrails (SCP, Azure Policy, Organization Policy), tożsamość bez długich kluczy, segmentacja sieci i prywatne punkty końcowe, szyfrowanie z kluczami klienta, klasyfikacja danych, baseline logowania, CSPM, CNAPP i CIEM, benchmarki CIS, kontenery w chmurze, polityki jako kod, gotowość na incydent. Wynik to dokument baseline i mapowanie kontroli. Nie do samego Terraform (ops-iac-terraform), RBAC i NetworkPolicy (ops-kubernetes), OIDC w CI i sekretów (ops-secrets-identities), zero trust i tożsamości ludzi (sec-zero-trust-identity), kosztów (ops-finops) ani obsługi incydentu (ops-security-operations)."
  slowa: "bezpieczeństwo chmury, cloud security, baseline chmury, landing zone, współdzielona odpowiedzialność, shared responsibility, SCP, Azure Policy, Organization Policy, guardrails, publiczny bucket, CloudTrail, Activity Log, Cloud Audit Logs, CSPM, CNAPP, CIEM, CIS Benchmark, prywatny endpoint, private link, VPC, VNet, klucze klienta, CMK, KMS, Checkov, Conftest, break-glass, mapowanie kontroli, multi-cloud, audyt chmury"
---

# Bezpieczeństwo chmury: baseline i mapowanie kontroli

Wynik pracy: plik `docs/project/04-architecture/cloud-security-baseline.md` (core-project-record) z dwiema częściami:
**baseline** (co obowiązuje każde konto, subskrypcję i projekt) oraz **mapowanie kontroli** (kontrola → AWS / Azure / GCP
→ jak wymuszana → jak weryfikowana → właściciel). Tabelę wyjściową i odpowiedniki usług daje
`references/mapowanie-kontroli.md`. Ten skill niczego nie wdraża: zmiany w chmurze przechodzą przez
ops-iac-terraform i akceptację człowieka.

## Procedura
1. **Zakres i typy usług.** Spisz używane chmury i usługi, każdą oznacz IaaS / PaaS / SaaS. Dostawca odpowiada
   za bezpieczeństwo *chmury* (obiekty fizyczne, hipernadzorca; w PaaS także system i środowisko uruchomieniowe),
   klient za bezpieczeństwo *w chmurze*. Zawsze po stronie klienta: dane, tożsamości i uprawnienia, konfiguracja
   usług. Im bliżej IaaS, tym więcej po stronie klienta (system, łatki, sieć hosta). Zapisz granicę per usługa.
2. **Struktura i guardrails.** Hierarchia: organizacja → grupy (OU, grupy zarządzania, foldery) → konta, subskrypcje
   lub projekty osobno dla: produkcji, nieprodukcji, logów (konto tylko do zapisu i odczytu przez bezpieczeństwo),
   narzędzi bezpieczeństwa i sieci współdzielonej. Guardrails zapobiegawcze na górze hierarchii:
   - AWS: **SCP** (Service Control Policies) w Organizations. Ograniczają maksymalne uprawnienia, niczego nie nadają
     i **nie obejmują konta zarządzającego** (management account), więc nie uruchamiaj w nim obciążeń.
   - Azure: **Azure Policy** (efekty Audit, Deny, DeployIfNotExists) przypisana do grupy zarządzania, plus RBAC.
   - GCP: **Organization Policy** (ograniczenia, np. `constraints/iam.disableServiceAccountKeyCreation`,
     `constraints/storage.publicAccessPrevention`).
   Typowe guardrails: zakaz wyłączania logów audytowych, zakaz opuszczenia organizacji, ograniczenie regionów,
   zakaz publicznego dostępu do magazynów, wymóg szyfrowania. Wprowadzaj w trybie audytu, potem blokady.
3. **Tożsamość.** Ludzie przez SSO z MFA odpornym na phishing (szczegóły: sec-zero-trust-identity). Obciążenia bez
   długotrwałych kluczy: role (AWS IAM roles), managed identity (Azure), konta usług z dołączeniem tożsamości
   (GCP); zewnętrzne systemy i CI przez federację OIDC (ops-secrets-identities). Wyłącz tworzenie kluczy
   kont usług. Uprawnienia na czas (just-in-time), przegląd nieużywanych (IAM Access Analyzer, Entra Permissions
   Management lub odpowiednik, IAM Recommender). **Break-glass**: 2 konta awaryjne poza SSO, hasło w sejfie
   dzielonym na dwie osoby, MFA sprzętowe, alarm przy każdym logowaniu, test co kwartał [przykład].
4. **Sieć.** Osobne sieci (VPC, VNet) per środowisko, podsieci publiczne tylko dla load balancerów i bram; bazy
   i usługi wewnętrzne bez publicznych adresów. Do usług PaaS prywatne punkty końcowe (AWS PrivateLink / VPC
   endpoints, Azure Private Endpoint, GCP Private Service Connect) i wyłączony dostęp publiczny usługi. Egress
   domyślnie zamknięty, z allowlistą (zapora lub proxy) i kontrolą metadanych instancji (AWS: IMDSv2 wymagane,
   ustawienie domyślne konta dla nowych instancji). Zarządzanie bez otwartych SSH i RDP z internetu (SSM,
   Bastion, IAP). Ochrona przed eksfiltracją przez API: GCP VPC Service Controls, polityki punktów końcowych AWS.
5. **Dane.** Klasyfikacja (publiczne, wewnętrzne, poufne, regulowane) w tagu zasobu; klasa decyduje o kluczu,
   lokalizacji i retencji. Szyfrowanie w spoczynku jest dziś domyślne w większości usług; **klucze zarządzane przez
   klienta** (KMS, Key Vault, Cloud KMS) włącz dla klas poufnych i regulowanych, z osobnym właścicielem klucza,
   rotacją i zakazem usunięcia bez karencji. Publiczne magazyny: AWS S3 Block Public Access na koncie i w SCP,
   Azure wyłączony anonimowy dostęp do kontenerów, GCP Public Access Prevention. Kopie zapasowe w osobnym
   koncie z blokadą usuwania (immutability). Dane osobowe: arch-privacy-compliance.
6. **Logowanie i wykrywanie.** Dziennik audytowy płaszczyzny zarządzania zawsze, do osobnego konta logów,
   z retencją i ochroną przed usunięciem:
   - AWS **CloudTrail**: historia zdarzeń to 90 dni zdarzeń zarządzania na region; trail organizacji (wszystkie konta
     i regiony), walidacja integralności plików, zdarzenia danych (S3, Lambda) dla zasobów poufnych.
   - Azure **Activity Log**: 90 dni domyślnie; ustawienie diagnostyczne do Log Analytics i konta magazynu.
   - GCP **Cloud Audit Logs**: Admin Activity zawsze włączone i niewyłączalne; **Data Access** domyślnie wyłączone
     (wyjątek BigQuery: [niezweryfikowane]), więc włącz dla projektów z danymi poufnymi.
   Do tego logi przepływów sieci, DNS, bilansowanie obciążenia i logi usług danych. Reguły wykrywania i obsługa
   alertów: ops-security-operations; telemetria aplikacji: ops-observability.
7. **Postura.** Skrót CSPM: ciągłe sprawdzanie konfiguracji względem benchmarku (AWS Security Hub, Microsoft Defender
   for Cloud, Google Security Command Center, Prowler). **CIEM**: analiza uprawnień i nadmiarowych dostępów.
   **CWPP**: ochrona obciążeń (maszyny, kontenery, funkcje). **CNAPP**: platforma łącząca CSPM, CIEM, CWPP,
   skan IaC i kontekst (ścieżki ataku); to kategoria rynkowa Gartnera, zakres zależy od dostawcy
   [niezweryfikowane: oficjalna definicja]. Od dostawcy CNAPP wymagaj: pokrycia wszystkich kont, ścieżek ataku z kontekstem
   (ekspozycja + uprawnienia + podatność), eksportu wyników, a nie tylko panelu. Benchmarki: CIS Foundations
   (osobne dla AWS, Azure, GCP), AWS Foundational Security Best Practices, Microsoft cloud security benchmark.
   Numer wersji CIS sprawdź przed użyciem. Każde odstępstwo ma właściciela i datę.
8. **Kontenery i Kubernetes.** Zarządzany klaster ze sterowaniem prywatnym lub ograniczonym zakresem adresów,
   tożsamość podów (IRSA / EKS Pod Identity, Azure Workload Identity, GKE Workload Identity), rejestr prywatny ze
   skanem i podpisami, węzły z minimalnym systemem i auto-aktualizacją. RBAC, NetworkPolicy i Pod Security: ops-kubernetes; obrazy:
   ops-docker.
9. **Polityki jako kod.** Kolejność: skaner IaC (**Checkov**) → polityki własne w **OPA / Conftest** (Rego na planie
   Terraform w JSON) → guardrails w chmurze jako ostatnia linia. Ta sama reguła ma jedno źródło; bramki w PR:
   ops-iac-terraform. Dryf i ręczne zmiany w konsoli zgłasza CSPM.
10. **Gotowość na incydent.** Przed incydentem: konto forensyczne (odizolowane), migawki dowodowe, uprawnienia
    zespołu reagowania z góry nadane na czas, scenariusze: wyciek klucza, zainfekowana instancja, publiczny bucket,
    przejęte konto root / globalnego administratora. Procedury: ops-security-operations. Koszt logów: ops-finops.
11. **Zapis i weryfikacja.** Wypełnij tabelę mapowania. Każda kontrola ma sposób sprawdzenia (zapytanie CSPM, test
    polityki, przegląd). Wynik `proposed` → akceptacja człowieka; wyjątki od baseline tylko decyzją człowieka.

## Przykład
**Sytuacja:** „15 kont AWS i 2 subskrypcje Azure, deweloperzy mają klucze dostępowe, bucket z fakturami był publiczny.”
**Wynik** (fragment mapowania, liczby [przykład]):

| Kontrola | AWS | Azure | Wymuszenie | Weryfikacja | Właściciel |
|---|---|---|---|---|---|
| K-03 brak publicznych magazynów | S3 Block Public Access | zakaz anonimowego dostępu do kontenerów | SCP + Azure Policy (Deny) | CSPM, 0 wyników krytycznych | platforma |
| K-07 brak długich kluczy | role + federacja SSO | managed identity | SCP zakazuje `iam:CreateAccessKey` | raport poświadczeń, 0 kluczy > 90 dni | tożsamość |
| K-11 logi audytowe | trail organizacji do konta logów | Activity Log → Log Analytics | SCP zakazuje `cloudtrail:StopLogging` | alarm przy zatrzymaniu | bezpieczeństwo |

Plan: audyt 2 tygodnie → blokada; wyjątki z datą wygaśnięcia.

## Checklista
- [ ] każda usługa oznaczona IaaS / PaaS / SaaS, granica odpowiedzialności zapisana
- [ ] struktura kont z kontem logów; guardrails na górze hierarchii, najpierw tryb audytu
- [ ] brak długotrwałych kluczy; break-glass przetestowany; uprawnienia na czas
- [ ] prywatne punkty końcowe, egress z allowlistą, zero SSH i RDP z internetu
- [ ] klasyfikacja danych, klucze klienta dla klas poufnych, publiczny dostęp zablokowany
- [ ] logi audytowe do osobnego konta; Data Access w GCP włączone tam, gdzie trzeba
- [ ] CSPM i benchmark z wersją; odstępstwa z właścicielem i datą
- [ ] polityki jako kod w PR; mapowanie kontroli z metodą weryfikacji

## Źródła
- AWS: Organizations SCP, CloudTrail, S3 (aktualizacja domyślnych ustawień bucketów: 2023-04-05), IMDSv2 jako domyślne (2024-03); sprawdzone wyszukiwaniem 2026-10-17, strony dokumentacji niedostępne bezpośrednio
- Google Cloud: Audit Logs, Organization Policy (security foundations blueprint), CIS GCP Foundation v5.0.0 (CIS, czerwiec 2026)
- Microsoft: Azure Policy, Activity Log (90 dni), Private Link, Microsoft cloud security benchmark (MCSB v1)
- Checkov, Conftest i OPA — dokumentacje projektów; definicje CNAPP, CSPM, CIEM, CWPP: Gartner (pośrednio) [niezweryfikowane]
