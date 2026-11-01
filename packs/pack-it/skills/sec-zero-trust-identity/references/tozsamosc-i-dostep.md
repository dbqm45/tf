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
  - mTLS (RFC 8705, 2020-02): token w postaci JWT niesie odcisk certyfikatu klienta w `cnf` → `x5t#S256`
    (base64url SHA-256 z DER certyfikatu, bez `=`), a serwer zasobu porównuje go z certyfikatem z tego samego
    połączenia TLS; niezgodność → 401 `invalid_token`;
  - DPoP (RFC 9449, 2023-09): agent dołącza do każdego żądania nagłówek `DPoP` z dowodem — JWT podpisanym swoim
    kluczem, z metodą i adresem żądania (`htm`, `htu`) i skrótem tokenu (`ath`); token wiąże się z kluczem przez
    `cnf` → `jkt` (odcisk klucza publicznego). Serwer odrzuca powtórzone dowody (ochrona przed replay);
  - skradziony token bez klucza agenta jest bezużyteczny.
- **Przejście między usługami: wymiana tokenu** (RFC 8693, 2020-01) zamiast przekazywania oryginału. Nowy token
  jest zawężony do odbiorcy i zakresu. RFC rozróżnia **delegację** (token mówi „A działa za B”) od
  **podszycia** (A dostaje token, który identyfikuje tylko B) — dla agenta wybierasz delegację, bo audyt widzi
  wtedy obu. Roszczenie `act` wskazuje bieżącego aktora; zagnieżdżone `act` to historia wcześniejszych aktorów,
  wg RFC **tylko informacyjna** — decyzję o dostępie podejmujesz na podstawie podmiotu tokenu i bieżącego aktora.
  `act` nie zapisuje ograniczeń na każdym kroku; propozycje łańcucha delegacji to szkice IETF [niezweryfikowane].
- **Log audytu:** „instancja X agenta Y w imieniu użytkownika Z, token z wymiany W, zasób R”. Bez tego nie
  odtworzysz incydentu.
- **Usługi bez obsługi wiązania tokenu** wpisujesz jawnie jako słabsze ogniwo (rejestr ryzyka, sec-risk-management):
  krótszy czas życia tokenu, wąski zakres, osobna sieć.
- **Przykład platformy — Google Cloud Agent Identity** (dokumentacja, stan 2026-11-01):
  - tożsamość SPIFFE na agenta (`spiffe://agents.global.org-<ID>.system.id.goog/resources/<usługa>/<ścieżka>`),
    w IAM jako `principal://…`; certyfikat X.509 ważny 24 h, odnawiany automatycznie;
  - w odróżnieniu od kont usługi: niewspółdzielona domyślnie, bez podszywania się i bez długich kluczy;
  - tokeny do Google Cloud związane z certyfikatem; mTLS do API i bramki, DPoP poza bramką („podwójne wiązanie”);
    domyślna polityka Context-Aware Access nie pozwala odtworzyć tokenu poza środowiskiem agenta;
  - trzy tożsamości: użytkownika, agenta i delegowana (agent w imieniu użytkownika przez 3-legged OAuth z magazynu
    poświadczeń „auth manager”); logi pokazują agenta i użytkownika;
  - Principal Access Boundary zawęża zasoby agenta niezależnie od innych uprawnień;
  - **pułapka cyklu życia:** usunięcie agenta nie usuwa powiązań IAM jego tożsamości, a nowy agent (nawet o tej
    samej nazwie) dostaje nową tożsamość — powiązania czyścisz i nadajesz ręcznie;
  - HTTP basic auth do narzędzi zewnętrznych jest dostępny, ale niezalecany.
  Wspierane usługi i status poszczególnych funkcji sprawdzasz w dokumentacji z datą.
- Bezpieczeństwo samego agenta (wstrzyknięcia, nadmierna sprawczość, ASI03 Identity & Privilege Abuse):
  sec-llm-security.

Źródła (sprawdzone 2026-11-01): github.com/spiffe/spiffe — `standards/SPIFFE.md`, `SPIFFE_Workload_API.md`,
README (projekt CNCF, status graduated); RFC 8705, 9449, 8693 — numery, tytuły i pola `cnf`/`x5t#S256` i `act`
sprawdzone w tekstach RFC przekazanych przez człowieka (RFC 8705 §3.1, RFC 8693 §1.1 i §4.1, RFC 9449 — abstrakt,
§4, `jkt`); docs.cloud.google.com/iam/docs/agent-identity-overview (treść przekazana przez człowieka
2026-11-01); G. Blaquiere, „SPIFFE:
Why Google's New Agent Identity…” (2026-06-09).
