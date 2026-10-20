# Architektura Zero Trust: PDP/PEP, ZTNA, VPN, SASE/SSE

Spis treści: komponenty · wzorce · ZTNA a VPN · SASE i SSE · pułapki

## Komponenty (NIST SP 800-207)
- **Policy engine** (ocena żądania wg polityki i sygnałów) + **policy administrator** (wydaje token/ustanawia sesję)
  = PDP. **PEP** stoi na ścieżce do zasobu (agent, bramka, proxy) i zamyka sesję na polecenie PDP.
- Źródła sygnałów: IdP, zarządzanie urządzeniami (MDM/EDR), SIEM, inteligencja zagrożeń, polityki zgodności,
  klasyfikacja danych, logi dostępu.
- Wymóg: PEP jest jedyną drogą; PDP jest wysoko dostępny (awaria → plan „fail closed” dla zasobów krytycznych
  i kontrolowany tryb awaryjny dla reszty, zapisany w ADR).

## Wzorce wdrożenia
1. Oparty na ulepszonym zarządzaniu tożsamością (polityka z tożsamości i grup).
2. Mikrosegmentacja (bramki lub agenty hosta wokół zasobów).
3. Sieć programowalna (SDP), czyli sieć „niewidoczna”, dopóki PDP nie zezwoli.
Zwykle łączysz wzorce; wybór zależy od tego, czy dominują aplikacje webowe, stare protokoły, czy serwery.

## ZTNA a VPN
| | VPN | ZTNA |
|---|---|---|
| zakres po zalogowaniu | segment lub cała sieć | pojedyncza aplikacja |
| decyzja | raz przy połączeniu | na sesję, z postury i kontekstu |
| ruch boczny | ułatwiony | ograniczony |
| widoczność | adresy IP | użytkownik, aplikacja, urządzenie |
| ryzyko | skradzione poświadczenia dają szeroki dostęp; bramka VPN to cel ataków | zależność od brokera i IdP |
ZTNA bez agenta (przeglądarka) pasuje do BYOD i partnerów, z agentem do protokołów nie-HTTP. Migracja: po jednej
aplikacji, z równoległym VPN do czasu potwierdzenia.

## SASE i SSE (definicje wg Gartnera, [niezweryfikowane] w źródle)
- **SASE** — chmurowa usługa łącząca sieć (SD-WAN) z funkcjami bezpieczeństwa.
- **SSE** — część bezpieczeństwa SASE bez sieci: zwykle SWG (bezpieczna bramka webowa), CASB (kontrola SaaS)
  i ZTNA, często z DLP. Używaj nazw jako opisu funkcji; sprawdzaj, co dostawca naprawdę oferuje.

## Pułapki
„Zero Trust” jako nazwa produktu; ZTNA przed porządkiem w tożsamości; polityki zbyt szczegółowe, więc obchodzone
wyjątkami; brak planu awarii PDP; zaufanie do postury zgłaszanej przez samo urządzenie bez atestacji.
Zagrożenia i odporność: `arch-threat-modeling`, `ops-security-operations`.
