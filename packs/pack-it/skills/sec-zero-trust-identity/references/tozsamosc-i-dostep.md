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

## Tożsamość agentów AI i delegacja
Agent to obciążenie (workload), które działa także w imieniu człowieka. Jedno wspólne konto usługi z długim tokenem
zaciera, kto co zrobił, a skradziony token działa wszędzie.
- **Każdy agent i każda jego instancja ma własną tożsamość obciążenia**, osobną od loginu człowieka, z nazwanym
  właścicielem. Standard: **SPIFFE** — identyfikator `spiffe://<domena-zaufania>/<ścieżka>`, krótko żyjące SVID
  (X.509 albo JWT) pobierane przez Workload API (lokalne gniazdo, bez sekretu w kodzie), implementacja referencyjna
  SPIRE. Rotacja certyfikatu jest automatyczna, więc nie ma długiego klucza do wycieku.
- **Działanie w imieniu użytkownika = token użytkownika związany z kluczem agenta** (sender-constrained):
  - mTLS: token niesie odcisk certyfikatu klienta (`cnf` → `x5t#S256`, RFC 8705), a serwer zasobu porównuje go
    z certyfikatem z tego samego połączenia TLS;
  - DPoP (RFC 9449): agent dołącza do każdego żądania dowód podpisany swoim kluczem;
  - skradziony token bez klucza agenta jest bezużyteczny.
- **Przejście między usługami: wymiana tokenu** (RFC 8693) zamiast przekazywania oryginału. Nowy token jest
  zawężony do odbiorcy i zakresu, a roszczenie `act` zapisuje, kto działa w czyim imieniu (zagnieżdżone `act`
  dla łańcucha). `act` mówi tylko kto, nie z jakimi ograniczeniami na każdym kroku; propozycje łańcucha delegacji to
  na razie szkice IETF.
- **Log audytu:** „instancja X agenta Y w imieniu użytkownika Z, token z wymiany W, zasób R”. Bez tego nie
  odtworzysz incydentu.
- **Usługi bez obsługi wiązania tokenu** wpisujesz jawnie jako słabsze ogniwo (rejestr ryzyka, sec-risk-management):
  krótszy czas życia tokenu, wąski zakres, osobna sieć.
- Platformy chmurowe dają to gotowe (np. Google Cloud Agent Identity: tożsamość SPIFFE i certyfikat X.509 na
  24 h dla każdego agenta, tokeny związane z certyfikatem, mTLS do bramki i DPoP dalej). Zakres usług i status
  funkcji (część w Preview) sprawdzasz w dokumentacji dostawcy z datą.
- Bezpieczeństwo samego agenta (wstrzyknięcia, nadmierna sprawczość, ASI03 Identity & Privilege Abuse):
  sec-llm-security.

Źródła (sprawdzone 2026-11-01): github.com/spiffe/spiffe — `standards/SPIFFE.md`, `SPIFFE_Workload_API.md`,
README (projekt CNCF, status graduated); RFC 8705, 9449, 8693 — numery, tytuły i pola `cnf`/`x5t#S256` i `act`
potwierdzone w wyszukiwarce i dokumentacji implementacji (rfc-editor.org i ietf.org niedostępne z sieci sesji);
docs.cloud.google.com/iam/docs/agent-identity-overview (przez wyszukiwarkę, 2026-11-01); G. Blaquiere, „SPIFFE:
Why Google's New Agent Identity…” (2026-06-09).
