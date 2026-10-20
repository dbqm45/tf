# Tożsamość i dostęp w Zero Trust

Spis treści: IAM i CIAM · MFA odporne na phishing · PAM i JIT · cykl życia · urządzenia · sygnały

## IAM pracowników i CIAM klientów
- Jedno źródło prawdy o pracownikach (HR → IdP, automatyczne wprowadzanie, zmiana roli i wyprowadzanie).
  SSO przez OIDC/SAML; lokalne hasła w aplikacjach wygaszaj.
- CIAM (klienci) to osobny system i inny model zagrożeń: rejestracja, odzyskiwanie konta, zgody, boty.
  Nie mieszaj katalogu klientów z pracownikami. Kod logowania i OAuth: `be-auth-security`.
- Federacja z partnerami zamiast kont gościnnych bez właściciela; konta gości z datą wygaśnięcia.

## MFA odporne na phishing
- Odporne: FIDO2/WebAuthn (klucze sprzętowe, passkeys), certyfikat na urządzeniu z kluczem chronionym sprzętowo.
  Powiązanie z domeną (origin) uniemożliwia podanie poświadczenia fałszywej stronie.
- Nieodporne: SMS, kod głosowy, TOTP, push „zatwierdź” (zmęczenie MFA, phishing w czasie rzeczywistym).
  Jeśli musisz je zostawić, push z dopasowaniem numeru, ograniczenie prób i monitorowanie anomalii.
- Kolejność: administratorzy i konta uprzywilejowane → dostęp do kodu i chmury → reszta pracowników.
  Procedury odzyskiwania (utrata klucza) są częstym obejściem: dwa klucze na osobę, weryfikacja tożsamości.
- Sesja po zalogowaniu: skradzione ciasteczka omijają MFA — krótkie sesje, wiązanie z urządzeniem
  (`be-auth-security`, `.claude/skills/be-auth-security/references/tokeny-sesje-oauth.md`).
- Wymogi NIST dla poziomów uwierzytelniania (SP 800-63B, wersja 4) i mapowanie na ryzyko: [niezweryfikowane].

## PAM i dostęp just-in-time
- Brak stałych uprawnień administracyjnych: podniesienie na zadanie, z uzasadnieniem, zatwierdzeniem i limitem czasu
  (minuty–godziny), nagrywaniem sesji dla krytycznych systemów.
- Osobne konta administracyjne (nie to samo konto do poczty i do administracji); stacje uprzywilejowane.
- Konta awaryjne („break glass”): 2, offline, hasło w sejfie, alarm przy użyciu, przegląd po każdym użyciu.
- Poświadczenia maszynowe i dostęp usług: `ops-secrets-identities`.

## Cykl życia (joiner–mover–leaver)
Automatyczne odebranie dostępu w ciągu godzin od odejścia, przegląd uprawnień kwartalnie (właściciel zasobu
potwierdza), wykrywanie kont bez użycia przez 90 dni [przykład], segregacja obowiązków dla działań wysokiego ryzyka.

## Urządzenia
Rejestr (własność, właściciel), MDM, szyfrowanie, aktualizacje, EDR. Sygnały postury: zgodność, wersja, ryzyko z EDR.
Polityka: pełny dostęp, ograniczony (np. tylko odczyt), brak. Urządzenia bez agenta (IoT, OT): segmentacja i monitoring
zamiast postury.

## Sygnały ciągłej oceny
Anomalie logowania (niemożliwa podróż, nowe urządzenie), ryzyko z IdP, alerty EDR, zmiana uprawnień. Reakcja:
wymuszenie ponownego uwierzytelnienia, ograniczenie sesji, odcięcie. Obsługa incydentu: `ops-security-operations`.
