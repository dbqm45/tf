# Mapowanie kontroli: odpowiedniki usług i szablon tabeli

Spis treści: 1. Szablon · 2. Odpowiedniki usług · 3. Pułapki konfiguracji

## 1. Szablon tabeli w `cloud-security-baseline.md`
Kolumny: ID · kontrola (cel) · AWS · Azure · GCP · wymuszenie (zapobiegawcze) · wykrywanie · weryfikacja · właściciel ·
odstępstwa (do kiedy). Kontrola zapisana jako cel („brak publicznych magazynów”), nie jako nazwa usługi.

## 2. Odpowiedniki usług
| Cel | AWS | Azure | GCP |
|---|---|---|---|
| Hierarchia | Organizations, OU, konta | grupy zarządzania, subskrypcje | organizacja, foldery, projekty |
| Guardrail zapobiegawczy | SCP (RCP dla zasobów) | Azure Policy (Deny) | Organization Policy |
| Dziennik audytowy | CloudTrail | Activity Log | Cloud Audit Logs |
| Tożsamość obciążenia | role IAM, IRSA, Pod Identity | managed identity, Workload Identity | konto usługi z dołączeniem, Workload Identity |
| Federacja z CI | OIDC provider w IAM | federacja poświadczeń Entra | Workload Identity Federation |
| Prywatny dostęp do PaaS | PrivateLink, endpointy VPC | Private Endpoint | Private Service Connect |
| Klucze klienta | KMS | Key Vault | Cloud KMS |
| Postura | Security Hub | Defender for Cloud | Security Command Center |
| Analiza dostępu | IAM Access Analyzer | Entra Permissions Management [niezweryfikowane: status produktu] | IAM Recommender |

## 3. Pułapki konfiguracji
- SCP bez wyjątku dla roli awaryjnej blokuje także naprawę; testuj w OU próbnym.
- Azure Policy z efektem Deny nie poprawia istniejących zasobów (potrzebne zadanie naprawcze).
- Trail tylko w jednym regionie pomija aktywność w pozostałych; użyj trailu wielu regionów.
- Logi w tym samym koncie co obciążenia: napastnik z uprawnieniami je kasuje; konto logów osobno.
- „Szyfrowane” nie znaczy „klucz klienta”: sprawdź, kto jest właścicielem klucza i polityki.
