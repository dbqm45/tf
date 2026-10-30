---
name: ops-datacenter-networking
description: Użyj przy sieci centrum danych — fabryka leaf-spine, BGP, VXLAN i EVPN, automatyzacja i zmiany w sieci.
metadata:
  przeglad: "2027-04-17"
  widocznosc: nazwa
  katalog: "Użyj przy projekcie i zmianach sieci centrum danych lub kampusu — fabryka leaf-spine (Clos) i oversubscription, underlay (eBGP, OSPF, IS-IS), overlay VXLAN z EVPN, BGP dla operatorów (wybór trasy, communities, filtry, limity prefiksów, RPKI), ECMP i domeny awarii, automatyzacja (źródło prawdy, generowanie konfiguracji, CI, okna zmian), zapory na brzegu, telemetria, planowanie pojemności, metoda diagnozy. Wynik to projekt fabryki i plan zmiany. Nie do diagnozy hosta Linux (ops-linux-networking), polityki segmentacji i zaufania (sec-zero-trust-identity) ani sieci w chmurze jako kodu (ops-iac-terraform)."
  slowa: "leaf spine, fabryka sieciowa, centrum danych, datacenter, bgp, vxlan, evpn, underlay, overlay, ecmp, oversubscription, przełączniki, switch, router, netbox, automatyzacja sieci, okno zmian, rpki, prefix list, telemetria sieciowa, pojemność łączy, firewall brzegowy, sieć kampusowa"
---

# Sieć centrum danych: projekt fabryki i plan zmiany

Wynik: **projekt fabryki** (topologia, adresacja, routing, overlay, domeny awarii) i **plan zmiany** (kroki, weryfikacja,
wycofanie). Zmiany na prawdziwych urządzeniach agent tylko proponuje: diff konfiguracji, dry-run i okno zmian,
wdrożenie po zgodzie człowieka. Diagnoza pojedynczego hosta (ss, dig, curl, TLS): ops-linux-networking.
Polityka segmentacji (kto z kim): sec-zero-trust-identity. Sieć chmurowa jako kod: ops-iac-terraform.

## Procedura projektu
1. **Wymagania**: liczba szaf i serwerów, prędkość portów (np. 2x25G), ruch wschód-zachód vs północ-południe,
   docelowa skala za 3 lata, cele dostępności (ops-sre-incidents), wymagania L2 (migracja VM, legacy).
2. **Topologia leaf-spine (Clos)**: każdy leaf łączy się z każdym spine; serwery tylko do leaf. Liczysz
   **oversubscription** = suma pasma portów serwerowych leafa ÷ suma pasma uplinków [przykład: 48x25G w dół,
   6x100G w górę → 1200:600 = 2:1]. Wartość docelową dobierasz do obciążenia (storage i AI: 1:1; ogólne: 2:1–3:1
   [założenie]). Liczba spine'ów = liczba uplinków leafa; skalowanie: dodanie spine'a lub pionu (pod/super-spine).
3. **Underlay**: routed L3 do szafy, bez rozciągania L2 między leafami. Domyślnie **eBGP** z unikalnym ASN
   na leaf (lub na parę) i wspólnym ASN spine'ów, zgodnie z RFC 7938 (Informational, 2016) — ma prostszy model
   niż IGP+iBGP i dobre filtrowanie. Alternatywa: OSPF lub IS-IS (mniejsze skale, zespół zna IGP), wtedy BGP
   tylko dla overlay. Sesje na adresach łączy (point-to-point /31 lub unnumbered), BFD dla szybkiego wykrycia awarii.
4. **Overlay**: VXLAN (RFC 7348, Informational) jako enkapsulacja, **EVPN** (RFC 7432, rozszerzenie dla overlay:
   RFC 8365) jako płaszczyzna kontrolna zamiast flood-and-learn. Decyzje: model L2VNI/L3VNI, anycast gateway,
   symmetric IRB, multihoming (ESI/EVPN-LAG zamiast MLAG, jeśli sprzęt wspiera), obsługa BUM, MTU
   (+50 B nagłówków VXLAN [niezweryfikowane] — jumbo na całej ścieżce). Numerów VNI, RD i RT nie wymyślasz ręcznie:
   schemat z źródła prawdy.
5. **ECMP i domeny awarii**: kilka równorzędnych ścieżek, hashowanie po 5-krotce; nierówny hash i elephant flows to
   typowe przyczyny nierównomiernych uplinków. Domena awarii = co traci ruch przy awarii leafa, spine'a, pary
   leafów, pionu, zasilania, zmiany konfiguracji. Zasada: utrata jednego spine'a nie przekracza budżetu pasma
   (policz N-1). Limit maksymalnej liczby ścieżek i prefiksów sprawdź w specyfikacji sprzętu.
6. **Brzeg i zapory**: łącze do internetu/WAN na osobnych leafach brzegowych (border), zapora stanowa między strefami,
   ruch wschód-zachód w overlay filtrowany politykami zdefiniowanymi w sec-zero-trust-identity; tu tylko mechanika
   (VRF, route leaking z filtrami, service chaining).
7. **Pojemność i telemetria**: wykorzystanie uplinków (p95 i szczyt), drop i błędy portów, liczba tras/MAC w tablicach
   vs limit ASIC, tempo wzrostu → termin rozbudowy (alert przy 60–70% [przykład]). Streaming telemetry
   (gNMI/OpenConfig, push co sekundy-dziesiątki sekund) zamiast SNMP polling tam, gdzie sprzęt pozwala;
   flow logs (IPFIX/sFlow) do analizy ruchu; stos metryk: ops-observability.

## BGP dla operatorów — minimum
- **Wybór trasy** (RFC 4271, w skrócie): najwyższy weight/local-pref → najkrótszy AS-path → origin → najniższe MED →
   eBGP przed iBGP → najniższy koszt IGP → router-id. Kolejność dokładną sprawdź w dokumentacji dostawcy.
- **Communities** oznaczają pochodzenie i intencję (np. „z DC”, „nie eksportuj”); ich znaczenie jest w źródle prawdy.
- **Filtry zawsze**: import i eksport przez prefix-list/policy; bez polityki sesja eBGP nic nie wymienia (RFC 8212
  [niezweryfikowane]). **Limit prefiksów** (`maximum-prefix`) na każdej sesji z ostrzeżeniem i odcięciem.
- **RPKI route origin validation** (RFC 6811): stany Valid / Invalid / NotFound; odrzucaj Invalid na sesjach
  tranzytowych, ROA dla własnych prefiksów utrzymuj aktualne. Dotyczy brzegu internetowego, nie fabryki.
- Zmiana polityki BGP na brzegu = wysokie ryzyko: najpierw porównanie tras przed/po (`show` + diff), potem okno zmian.

## Automatyzacja i zmiany
- **Źródło prawdy** (np. NetBox, wg dokumentacji NetBox Labs system do modelowania urządzeń, połączeń i IP):
  intencja w danych, konfiguracja **generowana** z szablonów (Jinja, Ansible, Nornir), nie pisana ręcznie na urządzeniu.
- **CI dla zmian sieciowych**: PR do repo → lint danych i szablonów → wygenerowana konfiguracja i diff → test
  w emulacji/labie (Containerlab, Batfish do analizy konfiguracji [niezweryfikowane]) → przegląd → wdrożenie
  falami (jeden leaf → para → szafa → reszta) z automatyczną weryfikacją stanu (sesje BGP, trasy, ping między VTEP).
- **Okno zmian**: cel, zakres, kroki z czasem, kryteria „stop”, **wycofanie** przetestowane (rollback do ostatniej
  konfiguracji lub `commit confirmed`), kontakt dyżurny, zamrożenie innych zmian. Zmiana awaryjna: ops-release-engineering.
- Dryf: konfiguracja z urządzeń porównywana cyklicznie ze źródłem prawdy; ręczne zmiany to incydent procesowy.

## Metoda diagnozy
Od objawu do warstwy: fizyka (optyka, błędy CRC) → łącze/LAG → sesje underlay → trasy → overlay (VTEP, EVPN route
type 2/3/5) → polityki/zapora → aplikacja. Porównaj z drugą, zdrową ścieżką; jedna zmiana naraz; oś czasu.
Host na końcu ścieżki: ops-linux-networking.

## Przykład
**Wejście:** 40 szaf, 2x25G na serwer, 20 serwerów w szafie, ruch głównie wschód-zachód, cel 3:1.
**Wynik** [przykład]: leaf na szafę (2 leafy w parze), w dół 20x2x25G = 1000G na szafę → po 500G na leaf; uplinki
4x100G = 400G → oversubscription 1,25:1 — lepiej niż cel, więc 4 spine'y wystarczą; N-1 (3 spine'y) → 300G = 1,67:1,
nadal ≤ 3:1. Underlay eBGP (RFC 7938), overlay EVPN-VXLAN, jumbo MTU 9216 [założenie]. Plan zmiany: wdrożenie
falami, wycofanie przez `commit confirmed`, weryfikacja sesji BGP i tras po każdej fali.

## Checklista
- [ ] oversubscription policzona i zestawiona z celem, także w stanie N-1
- [ ] underlay uzasadniony (eBGP wg RFC 7938 lub IGP), BFD, brak L2 między leafami
- [ ] overlay: EVPN jako control plane, MTU, multihoming, numeracja ze źródła prawdy
- [ ] BGP: filtry import/eksport, limity prefiksów, RPKI na brzegu
- [ ] konfiguracja generowana ze źródła prawdy, diff i test w CI przed oknem zmian
- [ ] plan zmiany z falami, kryteriami stop i przetestowanym wycofaniem; wdrożenie za zgodą człowieka
- [ ] telemetria i alerty pojemności; granice z sąsiednimi skillami zachowane

## Źródła
- IETF RFC 7938, „Use of BGP for Routing in Large-Scale Data Centers”, Informational, sierpień 2016 (datatracker.ietf.org, dostęp 2026-10-17)
- IETF RFC 7348 (VXLAN, Informational, 2014; trwają prace nad następcą draft-ietf-nvo3-rfc7348bis, stan 2025-12), RFC 7432 i RFC 8365 (EVPN), RFC 4271 (BGP-4), RFC 6811 (RPKI origin validation), RFC 8212 — numery i daty bez ponownego sprawdzenia treści [niezweryfikowane]
- NetBox Labs — dokumentacja NetBox jako network source of truth (netboxlabs.com/docs, dostęp 2026-10-17)
Opisane własnymi słowami.
