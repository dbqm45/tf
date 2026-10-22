---
name: sec-zero-trust-identity
description: Użyj przy Zero Trust i tożsamości jako perymetrze — NIST 800-207, ZTNA zamiast VPN, MFA odporne na phishing, PAM, postura urządzeń, mapa dojrzałości CISA.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy planujesz lub oceniasz architekturę Zero Trust — zasady NIST SP 800-207, punkty decyzji i egzekucji polityki (PDP/PEP), tożsamość jako perymetr (IAM pracowników, CIAM klientów, PAM, dostęp just-in-time), MFA odporne na phishing (FIDO2, passkeys), postura urządzeń, mikrosegmentacja, ZTNA kontra VPN, SASE/SSE, model dojrzałości CISA, mapa migracji i metryki. Nie do OAuth/OIDC w kodzie aplikacji (be-auth-security), tożsamości maszynowych i sekretów (ops-secrets-identities), NetworkPolicy (ops-kubernetes), zabezpieczeń chmury (sec-cloud-security) ani modelu zagrożeń funkcji (arch-threat-modeling)."
  slowa: "zero trust, ZTNA, VPN, nigdy nie ufaj, zawsze weryfikuj, perymetr, segmentacja, mikrosegmentacja, SASE, SSE, CASB, SWG, 800-207, PDP, PEP, passkey, FIDO2, WebAuthn, phishing, MFA, PAM, JIT, dostęp na żądanie, IAM, CIAM, stan urządzenia, device posture, dojrzałość zero trust, CISA ZTMM, ruch boczny, lateral movement"
---

# Zero Trust i tożsamość

**Granica.** Skill dotyczy architektury i programu: kto i z jakiego urządzenia dostaje dostęp do czego i na jakich
warunkach. OAuth/OIDC, sesje i tokeny w kodzie: `be-auth-security`. Tożsamości maszynowe, sekrety, OIDC dla CI:
`ops-secrets-identities`. NetworkPolicy i mTLS w klastrze: `ops-kubernetes`. Zabezpieczenia konta chmurowego:
`sec-cloud-security`. Zagrożenia konkretnej funkcji: `arch-threat-modeling`. Algorytmy i certyfikaty:
`sec-cryptography-pki`. Zero Trust to strategia, a nie produkt: żaden zakup go nie „włącza”. Rezygnacja z VPN oznacza
punkt egzekwowania polityki (PEP) przed każdą aplikacją; o dostępie decyduje punkt decyzyjny (PDP) na podstawie
tożsamości, stanu urządzenia i kontekstu (NIST SP 800-207).
Wynik: `docs/project/04-architecture/zero-trust.md` (core-project-record) z mapą stanu, planem i metrykami.

## Fundament: NIST SP 800-207 (sierpień 2020)
Siedem zasad (tenets), w skrócie:
1. Każde źródło danych i usługa to zasób.
2. Cała komunikacja jest zabezpieczona niezależnie od lokalizacji w sieci.
3. Dostęp do zasobu przyznawany jest na sesję.
4. Dostęp wynika z dynamicznej polityki (tożsamość, aplikacja, urządzenie, kontekst).
5. Organizacja monitoruje integralność i postawę wszystkich zasobów.
6. Uwierzytelnienie i autoryzacja są dynamiczne i ścisłe, zanim dostęp zostanie dany.
7. Organizacja zbiera dane o stanie zasobów, sieci i komunikacji i używa ich do poprawy bezpieczeństwa.
Szczegóły i treść zasad [niezweryfikowane] w źródle pierwotnym (strona NIST niedostępna z sandboxu, 2026-10-17).

Model logiczny: **PDP** (policy decision point = policy engine + policy administrator) decyduje, **PEP** (policy
enforcement point) egzekwuje i jest jedyną drogą do zasobu. Dane wejściowe PDP: IdP i MFA, rejestr urządzeń i postura,
inteligencja zagrożeń, logi, polityki dostępu do danych. Wzorce wdrożenia: oparty na tożsamości agent/bramka,
mikrosegmentacja, sieć programowalna (SDP). Zdecyduj, które pasuje do zasobów (`references/architektura-i-sase.md`).

## Procedura
1. **Zasoby i przepływy.** Inwentarz aplikacji, danych, tożsamości (ludzi i maszyn), urządzeń; mapa „kto do czego”.
   Zacznij od **powierzchni ochrony** (najcenniejsze dane i usługi), a nie od całej sieci.
2. **Stan wyjściowy** wg CISA Zero Trust Maturity Model 2.0: pięć filarów (tożsamość, urządzenia, sieci,
   aplikacje i obciążenia, dane), trzy zdolności przekrojowe (widoczność i analityka, automatyzacja i orkiestracja,
   zarządzanie), cztery stopnie (Traditional, Initial, Advanced, Optimal). Oceń każdy filar osobno, filary
   rozwijają się w różnym tempie. Data publikacji wersji 2.0 (kwiecień 2023) i ewentualne nowsze wersje:
   [niezweryfikowane].
3. **Tożsamość jako perymetr** (priorytet nr 1, `references/tozsamosc-i-dostep.md`): jedno IdP z SSO, MFA odporne
   na phishing (FIDO2/WebAuthn, passkeys, klucze sprzętowe), CIAM dla klientów oddzielony od katalogu pracowników,
   PAM i dostęp just-in-time dla uprawnień administracyjnych, przeglądy uprawnień, szybkie odbieranie dostępu.
4. **Urządzenie:** rejestr, szyfrowanie dysku, aktualność systemu, EDR; sygnał postury trafia do PDP, a niezgodne
   urządzenie dostaje mniej, nie „wszystko albo nic”. Urządzenia prywatne (BYOD) — dostęp przez przeglądarkę/VDI.
5. **Dostęp do aplikacji:** ZTNA per aplikacja zamiast VPN do całej sieci; stare aplikacje za proxy świadomym
   tożsamości. VPN zostaje tylko tam, gdzie ZTNA nie sięga, z ograniczeniem do segmentu i planem wycofania.
6. **Segmentacja:** mikrosegmentacja wokół powierzchni ochrony, zasada domyślnej odmowy dla ruchu wschód–zachód;
   w Kubernetesie `ops-kubernetes`. Najpierw tryb obserwacji, potem blokada.
7. **Dane i ciągła weryfikacja:** klasyfikacja, DLP, telemetria do SIEM, reakcje automatyczne (odebranie sesji,
   kwarantanna urządzenia) — `ops-security-operations`.
8. **Plan migracji** (poniżej) i **metryki**. Plan i akceptację ryzyka zatwierdza człowiek; agent proponuje.

## Mapa migracji (etapy, każdy z kryterium ukończenia)
| Etap | Zakres | Gotowe, gdy |
|---|---|---|
| 0 | inwentarz, powierzchnia ochrony, ocena CISA per filar | mapa zatwierdzona |
| 1 | IdP z SSO dla wszystkich aplikacji, MFA odporne na phishing dla administratorów | 100% kont uprzywilejowanych na FIDO2 |
| 2 | rejestr urządzeń i postura w polityce; PAM i JIT | brak stałych uprawnień administratora |
| 3 | ZTNA dla pierwszych 3–5 aplikacji; pilotaż wycofania VPN | pilotaż bez wzrostu zgłoszeń |
| 4 | mikrosegmentacja powierzchni ochrony, telemetria do SIEM | blokada ruchu bocznego w trybie wymuszenia |
| 5 | automatyzacja reakcji, ciągła ocena, przegląd co kwartał | metryki w progach |
Kolejność może się różnić, ale tożsamość i MFA zawsze przed segmentacją.

## Metryki
Odsetek kont z MFA odpornym na phishing (cel dla uprzywilejowanych: 100%); stałe konta uprzywilejowane vs JIT;
odsetek aplikacji za ZTNA/SSO; odsetek urządzeń zgodnych z polityką; mediana czasu odebrania dostępu po odejściu;
odsetek ruchu wschód–zachód objętego polityką; czas wykrycia i odcięcia sesji; liczba wyjątków od polityki i ich wiek.
Każda metryka ma właściciela, źródło danych i próg; progi poniżej to [przykład] do uzgodnienia.

## Przykład
**Wejście:** „Firma 400 osób, VPN dla wszystkich, ataki phishingowe na administratorów, ERP i repozytorium kodu
w chmurze. Chcemy Zero Trust.”
**Wynik** (fragment `zero-trust.md`):
- Powierzchnia ochrony: ERP, repozytorium, konsola chmury, baza klientów.
- Ocena CISA: tożsamość Initial, urządzenia Traditional, sieci Traditional, dane Traditional.
- Kwartał 1: klucze FIDO2 dla 12 administratorów; SMS wyłączony dla kont uprzywilejowanych [przykład]; JIT na konsolę chmury.
- Kwartał 2: rejestr urządzeń i polityka postury; ERP i repozytorium za ZTNA.
- Kwartał 3: wygaszenie VPN poza dwoma systemami przemysłowymi; mikrosegmentacja bazy klientów.
- Metryka sukcesu: 0 stałych kont administratora, 100% dostępu do ERP przez ZTNA, czas odebrania dostępu < 1 h [przykład].
- Ryzyka: zależność od jednego IdP (konta awaryjne offline z przeglądem), zgłoszenia od pracowników BYOD.

## Checklista
- [ ] powierzchnia ochrony i inwentarz tożsamości, urządzeń i aplikacji
- [ ] ocena per filar CISA, nie jedna ocena ogólna
- [ ] MFA odporne na phishing dla uprzywilejowanych, potem dla wszystkich; SMS i push bez dopasowania numeru odpada
- [ ] PAM i JIT, brak stałych uprawnień administratora; konta awaryjne
- [ ] postura urządzenia w decyzji o dostępie; ZTNA per aplikacja; plan wycofania VPN
- [ ] mikrosegmentacja najpierw w trybie obserwacji; telemetria do SIEM
- [ ] mapa etapów z kryteriami ukończenia i metryki z właścicielami

## Źródła
- NIST SP 800-207, *Zero Trust Architecture* (sierpień 2020) — siedem zasad przez źródła wtórne, 2026-10-17 [niezweryfikowane w pierwotnym]
- CISA, *Zero Trust Maturity Model* v2.0 — filary i stopnie przez źródła wtórne, 2026-10-17 [niezweryfikowane w pierwotnym]
- FIDO Alliance (FIDO2, passkeys), definicje SASE/SSE (Gartner) — [niezweryfikowane]
Opisane własnymi słowami.
