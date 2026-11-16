# Cykl życia kluczy, certyfikaty i PKI

Spis treści: cykl życia klucza · szyfrowanie kopertowe · certyfikaty publiczne · wewnętrzna PKI · decyzje

## Cykl życia klucza
| Faza | Wymaganie |
|---|---|
| generowanie | CSPRNG, w KMS/HSM albo tam, gdzie klucz będzie używany; klucz prywatny nie podróżuje mailem ani repozytorium |
| przechowywanie | klucze główne w KMS/HSM i nieeksportowalne; dostęp przez rolę, nie przez plik |
| użycie | jeden klucz = jedno przeznaczenie (szyfrowanie, podpis, MAC osobno); limity użycia (liczba wiadomości, wiek) |
| rotacja | zaplanowana (cyklicznie) i awaryjna (po podejrzeniu); stara wersja zostaje tylko do odszyfrowania |
| unieważnienie | kompromitacja → natychmiastowe wycofanie, powiadomienie zależnych, ocena, co zostało podpisane lub odszyfrowane |
| zniszczenie | po okresie oczekiwania i zgodzie człowieka; usunięcie klucza = kryptograficzne usunięcie danych |
Operacje na sekretach (inwentarz, wyciek, rotacja w CI): `ops-secrets-identities`.

## Szyfrowanie kopertowe
KEK w KMS/HSM nie opuszcza modułu; DEK per obiekt lub partia, zaszyfrowany KEK-iem i przechowywany obok danych.
Rotacja KEK nie wymaga przeszyfrowania danych, tylko ponownego owinięcia DEK (rewrap). Rozdziel trzy role:
szyfrowanie, odszyfrowanie i administracja kluczem. Kontekst szyfrowania (encryption context) wiąże DEK z tenantem
lub zasobem. Każde użycie klucza w logu audytowym (ops-observability).

## Certyfikaty publiczne
- Harmonogram CA/Browser Forum (SC-081v3): maksymalna ważność 200 dni od 2026-03-15, 100 dni od 2027-03-15,
  47 dni od 2029-03-15; skraca się też okres ponownego użycia walidacji domeny (do 10 dni w ostatniej fazie)
  [niezweryfikowane w pierwotnym rejestrze Forum; źródła wtórne 2026-10-17]. Dziś jest 2026-10-17, więc obowiązuje faza 200 dni.
- Wniosek: ręczne wgrywanie certyfikatów przestaje być wykonalne. Automatyzacja ACME (certbot, cert-manager,
  wbudowane w serwer/CDN), jeden kanał wyzwań (HTTP-01 lub DNS-01 z kontem o minimalnych uprawnieniach), alarm na
  certyfikaty bliskie wygaśnięcia niezależny od automatu, i inwentarz urządzeń, które nie obsługują ACME
  (stare appliance, VPN, IoT) — te wymagają planu wymiany albo terminacji TLS na bramie.
- Unieważnianie: coraz mniej polegaj na OCSP (Let's Encrypt zakończył OCSP w 2025 według
  `ops-secrets-identities`); krótka ważność zastępuje unieważnianie. Zweryfikuj klientów wymagających OCSP stapling.
- Zawsze CAA w DNS, monitoring Certificate Transparency własnych domen.

## Wewnętrzna PKI
- Root CA offline w HSM (ceremonia z dwiema osobami), pośrednie CA online per środowisko lub zastosowanie,
  certyfikaty końcowe krótkotrwałe (godziny–dni dla usług), wystawiane po uwierzytelnieniu tożsamości
  obciążenia (SPIFFE, tożsamość chmurowa, atestacja).
- Ograniczenia nazw (name constraints) i polityki certyfikatów, osobne hierarchie dla ludzi, usług i podpisywania kodu.
- Odporność: ≥ 2 pośrednie CA w różnych strefach, dystrybucja CRL o wysokiej dostępności, plan kompromitacji CA
  (unieważnienie pośredniego, wymiana trust bundle) przećwiczony na sucho.
- Zamiast CA od zera: zarządzane CA dostawcy chmury, step-ca, Vault PKI, mesh usług. Wdrożenie i eksploatacja:
  `ops-secrets-identities`, mTLS w klastrze: `ops-kubernetes`.

## Decyzje do zapisania w ADR
Długość życia certyfikatów per klasa, kto jest właścicielem CA, gdzie żyje root, jak odnawiamy, co robimy z
urządzeniami bez ACME, kiedy rotujemy KEK, jak szybko potrafimy wymienić algorytm.
