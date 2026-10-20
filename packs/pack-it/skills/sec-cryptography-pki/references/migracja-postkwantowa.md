# Migracja postkwantowa (PQC)

Spis treści: standardy · zagrożenie · plan krok po kroku · terminy · pułapki

## Standardy
- NIST FIPS 203 (ML-KEM, enkapsulacja klucza), FIPS 204 (ML-DSA, podpis), FIPS 205 (SLH-DSA, podpis oparty na
  haszach) — opublikowane w sierpniu 2024. FIPS 206 (FN-DSA) i algorytm HQC: status [niezweryfikowane].
- Stateful hash-based (LMS, XMSS) do podpisywania oprogramowania/firmware'u: NIST SP 800-208; wymagają bezpiecznego
  zarządzania stanem klucza.

## Zagrożenie
Napastnik zapisuje dziś ruch i odszyfruje go, gdy powstanie odpowiedni komputer kwantowy („harvest now, decrypt
later”). Dotyczy poufności o długim horyzoncie (dane medyczne, państwowe, własność intelektualna) i wymiany kluczy.
Podpisy są mniej pilne w przypadku krótkotrwałych poświadczeń, ale pilne dla zaufania o długim życiu
(firmware, root CA, dokumenty prawne). Szyfry symetryczne i hashe: AES-256 i SHA-384+ zostają, rozmiar klucza
decyduje.

## Plan
1. **Inwentarz** (CBOM, CycloneDX): algorytmy, biblioteki, protokoły, certyfikaty, urządzenia, zależności od
   dostawców; priorytet = czas poufności + ekspozycja (ruch publiczny, kopie zapasowe, archiwa).
2. **Zwinność:** algorytm w konfiguracji, wersjonowane formaty, większe pola na klucze i podpisy (PQ podpisy
   i klucze są wielokrotnie większe — sprawdź limity protokołów, nagłówków, HSM i certyfikatów).
3. **Wymiana kluczy najpierw:** tryb hybrydowy X25519 + ML-KEM w TLS tam, gdzie wspierają go biblioteka, CDN
   i klienci; zmierz narzut i zgodność middleboxów.
4. **Podpisy i PKI:** plan dla root CA, podpisywania kodu i firmware'u; dostawcy HSM i KMS z PQC.
5. **Dostawcy:** zapytaj SaaS i producentów o plan i terminy; wpisz do umów.
6. **Test i wycofanie** starych algorytmów po ocenie zgodności.

## Terminy (wszystkie [niezweryfikowane] w źródłach pierwotnych; wtórne z 2026-10-17)
- NIST IR 8547 (projekt, listopad 2024): algorytmy o sile 112 bitów (np. RSA-2048, ECC 256) wycofane po 2030,
  RSA/ECC niedozwolone po 2035.
- NSA CNSA 2.0: nowe zakupy systemów bezpieczeństwa narodowego zgodne od 2027-01-01; podpisywanie oprogramowania
  i sprzęt sieciowy docelowo do 2030, przeglądarki, serwery i usługi chmurowe do 2033, całość do 2035.
- Terminy unijne i krajowe (w tym polskie) oraz plan UE: sprawdź w ENISA i dokumentach krajowych —
  [niezweryfikowane], nie podawaj liczb bez źródła.

## Pułapki
Samo „PQC” bez hybrydy tam, gdzie nowy algorytm jest młody; zapominanie o kopiach zapasowych i archiwach już
przechwyconego ruchu; limity rozmiaru w protokołach; migracja bez inwentarza.
