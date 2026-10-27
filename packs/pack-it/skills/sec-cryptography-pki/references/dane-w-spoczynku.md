# Dane w spoczynku: klasy danych, warstwy szyfrowania, cykl życia

Odpowiada na „czy szyfrujemy dane w spoczynku” w sposób, który da się obronić przed audytorem i napastnikiem.
Dobór algorytmów, KMS i szyfrowanie kopertowe: SKILL.md i `references/cykl-zycia-kluczy-i-pki.md`. Retencja
i usuwanie danych osobowych (RODO): `arch-privacy-compliance`. Kopie i odtwarzanie: `ops-sre-incidents`.

## 1. Klasy danych
Najpierw klasyfikacja, potem zabezpieczenia — inaczej wszystko jest „poufne” albo nic.

| Klasa | Przykłady | Minimum w spoczynku |
|---|---|---|
| publiczne | treści marketingowe, dokumentacja publiczna | integralność (kto może zmienić) |
| wewnętrzne | konfiguracja, dane operacyjne bez osób | szyfrowanie nośnika (dostawca), kontrola dostępu |
| poufne | dane klientów, umowy, logi z identyfikatorami | szyfrowanie bazy/obiektów kluczem w KMS organizacji, logi użycia klucza, kopie zaszyfrowane |
| ściśle poufne | dane szczególnych kategorii, numery dokumentów, dane płatnicze, sekrety | dodatkowo szyfrowanie na poziomie pola/aplikacji, osobny klucz, dostęp do odszyfrowania tylko wybranej usługi |

Klasa jest atrybutem zbioru danych (tabela, bucket, kolumna), zapisanym obok niego (tag, katalog danych). Dane
pochodne (eksport, kopia, środowisko testowe, logi) dziedziczą klasę, chyba że zostały zanonimizowane.

## 2. Warstwy szyfrowania i przed czym chronią

| Warstwa | Przykład | Chroni przed | Nie chroni przed |
|---|---|---|---|
| nośnik / wolumen | szyfrowanie dysków u dostawcy, LUKS, BitLocker | kradzieżą lub wyniesieniem nośnika, złym wycofaniem dysku | każdym, kto ma dostęp do działającego systemu, bazy, API |
| baza / magazyn obiektów | TDE, szyfrowanie po stronie serwera kluczem z KMS (np. SSE-KMS) | dostępem do plików bazy i snapshotów bez uprawnień do klucza; daje log użycia klucza | użytkownikowi lub aplikacji z dostępem do bazy |
| pole / aplikacja | szyfrowanie wartości przed zapisem (AEAD, klucz z KMS) | administratorowi bazy, wyciekowi kopii lub zrzutu, SQL injection odczytującemu tabelę | przejęciu samej aplikacji, która ma prawo odszyfrować |

Odpowiedź „dyski są szyfrowane przez dostawcę” zamyka tylko pierwszy wiersz. Dla danych poufnych dodaj klucz
zarządzany przez organizację (polityka klucza, rozdział ról, log użycia, możliwość odcięcia), a dla ściśle poufnych
szyfrowanie na poziomie pola.

## 3. Klucze
- KMS/HSM, szyfrowanie kopertowe (DEK przy danych, KEK w KMS), osobne klucze per środowisko i klasa danych.
- Rozdzielone role: kto administruje kluczem, kto szyfruje, kto odszyfrowuje. Uprawnienie do odszyfrowania jest
  rzadsze niż dostęp do danych zaszyfrowanych.
- Rotacja KEK zgodnie z polityką; logi użycia kluczy w SIEM (nietypowe odszyfrowania to sygnał wycieku).
- Długość życia i stany klucza: NIST SP 800-57 część 1 (rev. 5; rev. 6 to projekt z 12.2025).

## 4. Kopie zapasowe
- Kopie mają klasę źródła: szyfrowane, kluczem innym niż produkcyjny, w innym koncie lub regionie, co najmniej jedna
  niezmienialna (`ops-sre-incidents`).
- Test odtworzenia sprawdza też dostęp do kluczy — kopia bez klucza nie istnieje.

## 5. Cykl życia danych
Tworzenie (klasa nadana) → przechowywanie (zabezpieczenia klasy) → użycie (minimalny dostęp, maskowanie w
środowiskach nieprodukcyjnych) → archiwum (retencja z uzasadnieniem; dane osobowe: `arch-privacy-compliance`) →
usunięcie.
- **Bezpieczne usuwanie** wg NIST SP 800-88 rev. 2: dla nośników w chmurze i danych szyfrowanych praktyczną metodą
  jest kryptograficzne wymazanie (zniszczenie klucza, którym zaszyfrowano dane) — dlatego osobne klucze per zbiór
  albo per klient ułatwiają usuwanie. Dla własnego sprzętu: wymazanie lub fizyczne zniszczenie nośnika z zapisem.
- Usunięcie obejmuje kopie, repliki, eksporty i środowiska testowe; zapisz, po jakim czasie dane znikają z kopii.

## Przykład
**Wejście:** „Audytor pyta o szyfrowanie w spoczynku. Postgres w chmurze, S3 z plikami klientów, nocne kopie; dyski
szyfruje dostawca.”
**Wynik:** klasy — pliki klientów i tabela `customers` poufne, kolumna z numerem dokumentu ściśle poufna. Postgres:
szyfrowanie magazynu kluczem organizacji w KMS (nie domyślnym kluczem dostawcy), log użycia klucza do SIEM. S3:
SSE-KMS z kluczem per środowisko, polityka bucketu wymaga szyfrowania i TLS. Kolumna z numerem dokumentu:
AES-256-GCM w aplikacji (przykład w SKILL.md). Kopie: osobny klucz, osobne konto, kopia niezmienialna, kwartalny
test odtworzenia z kluczem. Usuwanie klienta: dane w bazie i S3 + upływ retencji kopii; dla eksportów klucz per
eksport i crypto-erase.

## Źródła
- NIST SP 800-111 *Guide to Storage Encryption Technologies for End User Devices* (final, 11.2007):
  https://csrc.nist.gov/pubs/sp/800/111/final
- NIST SP 800-88 rev. 2 *Guidelines for Media Sanitization* (final, 09.2025; zastępuje rev. 1):
  https://csrc.nist.gov/pubs/sp/800/88/r2/final
- NIST SP 800-57 część 1 rev. 5 (final, 05.2020); rev. 6 — projekt (12.2025)
- OWASP Cryptographic Storage Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
Statusy wg wyszukiwania w domenach nist.gov i owasp.org 2026-10-27; strony csrc.nist.gov i owasp.org niedostępne
z sandboxu — treść stron [niezweryfikowane]. Opisane własnymi słowami.
