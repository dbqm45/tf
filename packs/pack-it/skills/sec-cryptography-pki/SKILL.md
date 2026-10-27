---
name: sec-cryptography-pki
description: Użyj przy wyborze algorytmów, TLS, zarządzaniu kluczami, PKI, krótkich certyfikatach i migracji postkwantowej — decyzje projektowe kryptografii.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy trzeba zdecydować, jak zaprojektować kryptografię — dobór prymitywów i trybów (AEAD, hashowanie haseł Argon2id, podpisy, wymiana kluczy), konfiguracja TLS 1.3 i HSTS, szyfrowanie w spoczynku z klasami danych (dysk, baza, pole, kopie, bezpieczne usuwanie wg NIST SP 800-88), cykl życia kluczy (KMS/HSM, szyfrowanie kopertowe, rotacja, unieważnianie, zniszczenie), PKI i skracanie ważności certyfikatów (47 dni, ACME), inwentarz kryptografii i zwinność, migracja postkwantowa (FIPS 203/204/205, tryb hybrydowy), typowe błędy (ECB, powtórzony nonce, alg confusion w JWT). Nie do eksploatacji sekretów, rotacji i skanowania (ops-secrets-identities), logowania i tokenów w aplikacji (be-auth-security) ani szerszej architektury zaufania (sec-zero-trust-identity)."
  slowa: "szyfrowanie w spoczynku, encryption at rest, klasyfikacja danych, klasy danych, TDE, SSE-KMS, szyfrowanie dysków, czy szyfrowanie dysku wystarczy, crypto-erase, bezpieczne usuwanie, kryptografia, szyfrowanie, szyfrować dane, szyfrowanie pól, szyfrowanie danych w bazie, jaki algorytm szyfrowania, jak trzymać klucze, rotacja kluczy, AES-GCM, ChaCha20, AEAD, nonce, IV, ECB, hashowanie haseł, Argon2id, bcrypt, scrypt, podpis cyfrowy, wymiana kluczy, TLS 1.3, HSTS, certyfikat, 47 dni, ACME, PKI, CA, root CA, KMS, HSM, szyfrowanie kopertowe, rotacja klucza, postkwantowa, PQC, ML-KEM, ML-DSA, FIPS 203, CNSA 2.0, harvest now decrypt later, zwinność kryptograficzna, CBOM, alg none, JWT alg, własna kryptografia"
---

# Kryptografia stosowana i zarządzanie kluczami

**Granica.** Ten skill odpowiada na pytanie „jaką kryptografię wybrać i jak ją zaprojektować”. Eksploatację
(inwentarz tożsamości maszynowych, skanowanie i rotacja sekretów, operacje PKI) opisuje `ops-secrets-identities`
(`.claude/skills/ops-secrets-identities/references/kryptografia-i-pki.md` to skrót tabelaryczny, tu jest pełniejsza
decyzja). Hasła i tokeny w przepływach logowania: `be-auth-security`. Zagrożenia: `arch-threat-modeling`.
Wynik pracy: sekcja „Kryptografia” w `docs/project/04-architecture/` (core-project-record) albo ADR.

## Procedura
1. **Co chronimy i przed kim.** Dane, ich poufność w czasie (lata → ryzyko „zbierz teraz, odszyfruj później”),
   stan (w spoczynku, w ruchu, w użyciu), wymagania prawne. Bez tego nie ma kryteriów wyboru. Dane w spoczynku:
   klasy danych, warstwy szyfrowania (nośnik, baza, pole, kopie) i cykl życia z usuwaniem —
   `references/dane-w-spoczynku.md`.
2. **Najpierw konstrukcja wysokiego poziomu**, dopiero potem prymitywy: TLS, KMS, biblioteka platformy, libsodium
   lub Tink. Nigdy własny algorytm, protokół ani „sprytne” złożenie prymitywów. Gdy nie ma gotowca, zapisz
   uzasadnienie i poproś o przegląd kryptografa.
3. **Dobór prymitywu** wg tabeli niżej; odchylenie od niej to ADR z powodem.
4. **Klucze:** wygenerowane CSPRNG, zapisane w KMS/HSM, z właścicielem, rolą i planem cyklu życia
   (`references/cykl-zycia-kluczy-i-pki.md`).
5. **Transport:** TLS 1.3, ścisła walidacja certyfikatów, HSTS (sekcja TLS).
6. **Inwentarz i zwinność:** każdy algorytm jest wymienialny konfiguracją, a nie przepisaniem kodu; wersja
   algorytmu zapisana przy danych (nagłówek szyfrogramu, `kid`).
7. **Przegląd** wg checklisty i listy błędów (`references/typowe-bledy.md`).

## Dobór prymitywów
| Potrzeba | Wybór | Uwagi |
|---|---|---|
| poufność + integralność danych | AEAD: AES-256-GCM albo ChaCha20-Poly1305 (XChaCha20-Poly1305 przy losowych nonce) | nonce unikalny dla klucza; GCM: nie powtarzaj, limit wiadomości na klucz |
| wiadomość między stronami z kluczem współdzielonym | HMAC-SHA-256 lub AEAD | porównanie w stałym czasie |
| hasło użytkownika | Argon2id; scrypt; bcrypt dla systemów zastanych; PBKDF2 tylko gdy wymagany FIPS | parametry niżej |
| skrót danych | SHA-256 / SHA-3 | MD5 i SHA-1 do niczego, co ma odpierać napastnika |
| podpis | Ed25519 lub ECDSA P-256; RSA-PSS ≥ 3072 bit | RSA 2048 tylko ze względu na zgodność |
| wymiana klucza | X25519 / ECDHE; w TLS hybryda z ML-KEM | statyczny DH bez forward secrecy odpada |
| klucz z hasła lub z innego klucza | KDF: Argon2id/scrypt (z hasła), HKDF (z klucza) | nie używaj hasha jako KDF |
| losowość | CSPRNG systemu (`/dev/urandom`, `crypto.randomBytes`, `SecureRandom`, `secrets`) | `Math.random` i `rand()` wykluczone |

**Hasła — parametry z OWASP Password Storage Cheat Sheet** (stan wg wyszukiwania 2026-10-17, strony źródłowej nie
udało się pobrać bezpośrednio, więc przed wdrożeniem porównaj z aktualną: [niezweryfikowane]):
- Argon2id: minimum 19 MiB pamięci, 2 iteracje, równoległość 1 (równoważne warianty z większą pamięcią i mniejszą
  liczbą iteracji są dopuszczalne);
- scrypt: N = 2^17, r = 8, p = 1; bcrypt: współczynnik ≥ 10 (w projekcie przyjmij ≥ 12 jak w `be-auth-security`)
  i limit hasła 72 bajtów; PBKDF2-HMAC-SHA-256: ≥ 600 000 iteracji.
- Parametry zmierz na produkcyjnym sprzęcie (cel rzędu setek ms na hash) i zapisuj w haszu, by móc je podnosić
  przy następnym logowaniu. Papryka (pepper) w KMS to dodatek, nie zamiennik.

## TLS
- Nowe usługi: TLS 1.3. TLS 1.2 tylko dla klientów, którzy go potrzebują, z szyframi AEAD i ECDHE.
  Wyłączone: SSL, TLS 1.0 i 1.1, RC4, 3DES, szyfry eksportowe. Profile „modern” i „intermediate” bierz z generatora
  konfiguracji Mozilli, bo wersje i listy szyfrów się zmieniają ([niezweryfikowane] szczegóły aktualnych profili).
- Klient waliduje łańcuch, nazwę hosta, ważność i przeznaczenie; nigdy `verify=false`, `InsecureSkipVerify` ani
  „akceptuj wszystko” poza testem jednostkowym. Pinning kluczy tylko tam, gdzie kontrolujesz klienta i ścieżkę
  wymiany (aplikacje mobilne: z kluczem zapasowym).
- Wewnątrz organizacji mTLS z krótkotrwałymi certyfikatami (`references/cykl-zycia-kluczy-i-pki.md`).
- HSTS: `Strict-Transport-Security: max-age=…; includeSubDomains`; `preload` dopiero po przetestowaniu wszystkich
  subdomen, bo cofnięcie trwa miesiącami. Nagłówki ogólne: `be-auth-security`.

## Postkwantowo i zwinność
- NIST opublikował FIPS 203 (ML-KEM), 204 (ML-DSA) i 205 (SLH-DSA) w sierpniu 2024. Szczegóły, terminy
  krajowe i plan: `references/migracja-postkwantowa.md`.
- Kolejność: inwentarz (CBOM) → priorytet dla danych o długiej poufności i wymiany kluczy → tryb hybrydowy
  (X25519 + ML-KEM) → podpisy i PKI. Terminy NIST IR 8547 i CNSA 2.0 to [niezweryfikowane] w źródłach pierwotnych.

## Przykład
**Wejście:** „Szyfrujemy numery dokumentów w polu bazy. Pomysł: AES-CBC, klucz w pliku konfiguracyjnym, IV stały.”
**Wynik** (fragment ADR):
1. AES-256-GCM, 96-bitowy losowy nonce na rekord, nagłówek `v1|kid|nonce|szyfrogram|tag`; AAD = id rekordu.
2. Szyfrowanie kopertowe: DEK na tabelę lub partię, KEK w KMS; DEK zaszyfrowany obok danych. Rotacja KEK co rok [przykład] bez przeszyfrowania, rotacja DEK przy kompromitacji.
3. Role KMS rozdzielone: szyfruje aplikacja, odszyfrowuje tylko usługa X, administruje zespół platformy.
4. Wyszukiwanie po numerze: osobna kolumna HMAC-SHA-256 z kluczem z KMS (blind index), nie szyfrogram deterministyczny.
5. Odrzucone: CBC bez MAC (podatność na oracle), stały IV (ujawnia równość), klucz w konfiguracji.

## Checklista
- [ ] cel, czas poufności i model napastnika zapisane; nie ma własnej kryptografii
- [ ] klasy danych nadane; warstwa szyfrowania w spoczynku dobrana do klasy, kopie i usuwanie objęte
- [ ] AEAD z unikalnym nonce, wersja algorytmu i `kid` przy danych
- [ ] hasła: Argon2id/scrypt/bcrypt z zapisanymi parametrami; brak szybkich hashy
- [ ] klucze w KMS/HSM, szyfrowanie kopertowe, rozdzielone role, rotacja i zniszczenie opisane
- [ ] TLS 1.3, pełna walidacja certyfikatów, HSTS; brak wyłączonej weryfikacji
- [ ] certyfikaty automatyczne (ACME) i monitoring wygasania, zgodnie z kalendarzem skracania ważności
- [ ] inwentarz kryptografii i plan migracji postkwantowej dla danych długowiecznych
- [ ] przegląd listy typowych błędów (`references/typowe-bledy.md`)

## Źródła
- OWASP Password Storage Cheat Sheet (parametry przez wyszukiwanie, 2026-10-17; strona nieosiągalna z sandboxu)
- CA/Browser Forum, głosowanie SC-081v3: ważność 398 → 200 dni (2026-03-15) → 100 (2027-03-15) → 47 (2029-03-15),
  skrócone ponowne użycie walidacji domeny; źródła wtórne, 2026-10-17 [niezweryfikowane w pierwotnym rejestrze]
- NIST FIPS 203, 204, 205 (sierpień 2024); NIST IR 8547 (projekt z listopada 2024: wycofanie RSA/ECC po 2030,
  zakaz po 2035; status końcowy [niezweryfikowane]); NSA CNSA 2.0 (źródła wtórne, 2026-10-17)
- Mozilla Server Side TLS (generator konfiguracji) — wersje profili [niezweryfikowane]
Opisane własnymi słowami.
