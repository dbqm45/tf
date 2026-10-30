---
name: ops-virtualization-storage
description: Użyj przy infrastrukturze własnej i brzegowej — hiperwizor, klaster, SAN/NAS/Ceph, RAID, kopie, cykl życia sprzętu, edge.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj przy projekcie infrastruktury w serwerowni lub na brzegu (edge) — dobór hiperwizora (KVM z libvirt i QEMU, Proxmox VE, VMware vSphere z uwzględnieniem zmian licencyjnych po przejęciu przez Broadcom), wielkość klastra (overcommit CPU i pamięci, N+1, HA, migracja na żywo, kworum), architektura storage (SAN FC i iSCSI, NAS NFS i SMB, Ceph), RAID i erasure coding, IOPS, przepustowość, opóźnienie i głębokość kolejki, migawki a kopie zapasowe, reguła 3-2-1, niezmienialność, cykl życia sprzętu (odświeżanie, części zapasowe, firmware), planowanie pojemności, ograniczenia edge, migracja między hiperwizorami. Wynik to projekt z tabelą wymiarowania. Nie do odtwarzania po awarii regionu i strategii DR (ops-multi-region-resilience), kopii w kontekście incydentów i SLO (ops-sre-incidents), strojenia I/O w systemie operacyjnym (ops-linux-performance) ani orkiestracji kontenerów (ops-kubernetes)."
  slowa: "hiperwizor, wirtualizacja, KVM, libvirt, QEMU, Proxmox, VMware, vSphere, ESXi, Broadcom, licencje VMware, migracja z VMware, klaster, overcommit, nadsubskrypcja, HA, live migration, vMotion, SAN, iSCSI, Fibre Channel, NAS, NFS, SMB, Ceph, storage, macierz, RAID, RAID 6, erasure coding, IOPS, przepustowość, opóźnienie dysku, głębokość kolejki, migawka, snapshot, backup, 3-2-1, niezmienialna kopia, serwerownia, on-premise, odświeżanie sprzętu, części zapasowe, firmware, pojemność, edge, sklep, oddział, zdalne zarządzanie, iDRAC, iLO, wymiarowanie klastra"
  widocznosc: nazwa
---

# Wirtualizacja, storage i sprzęt (serwerownia i edge)

Wynik: **projekt infrastruktury z tabelą wymiarowania** (szablon niżej). Zmiany na działającej infrastrukturze
agent tylko proponuje jako plan (okno zmian, kolejność, wycofanie, dry-run tam, gdzie narzędzie go ma);
wykonuje je człowiek lub agent za jego jawną zgodą. Odtwarzanie po awarii lokalizacji: **ops-multi-region-resilience**;
rola kopii w incydentach i RPO/RTO: **ops-sre-incidents**; I/O w jądrze i systemie plików: **ops-linux-performance**;
kontenery: **ops-kubernetes** (węzły Kubernetes na wirtualnych maszynach liczysz tu jak każde inne obciążenie).

## Procedura
1. **Obciążenia i wymagania.** Inwentarz VM/usług: vCPU, RAM, dysk, profil I/O (losowy czy sekwencyjny, odczyt/zapis,
   rozmiar bloku), RPO/RTO, zależności, licencje zależne od rdzeni (bazy, Windows Server). Bez pomiaru z obecnego
   środowiska (p95 z 30 dni, nie średnia) liczby poniżej są zgadywaniem.
2. **Hiperwizor** — wybór kryteriami, nie marką:
   - **KVM + libvirt/QEMU**: jądro Linuksa, najwięcej swobody, zarządzanie i HA budujesz sam (Pacemaker, Ansible).
   - **Proxmox VE**: KVM i LXC z webowym zarządzaniem, klastrem, HA, Ceph i ZFS w pakiecie; licencja AGPL, płatne
     jest wsparcie (subskrypcja). Wersje: `references/hiperwizory-i-storage.md`.
   - **VMware vSphere**: dojrzały ekosystem (DRS, vSAN, NSX), ale po przejęciu przez Broadcom zmieniły się licencje
     (subskrypcja zamiast wieczystych, rozliczenie za rdzeń, minima zakupowe) — **warunki sprawdź w aktualnej ofercie
     i umowie, nie z pamięci** [niezweryfikowane: szczegóły minimów i renewali, doniesienia resellerów z 2025-04].
   - Decyzja: umiejętności zespołu, wsparcie dostawcy aplikacji (certyfikacja pod hiperwizor), koszt 5 lat (licencje
     + wsparcie + ludzie), ryzyko uzależnienia. Dla małych lokalizacji licz minima zakupowe na lokalizację.
3. **Wymiarowanie klastra** (tabela i wzory w `references/wymiarowanie.md`):
   - **Pojemność po awarii**: projektuj na **N+1** (utrata jednego węzła, przy HA bez przekroczenia limitów);
     przy dużych klastrach N+2. Nie licz węzłów „na styk” — HA uruchomi VM tylko tam, gdzie jest wolna pamięć.
   - **CPU**: stosunek vCPU do rdzeni fizycznych zależy od obciążenia; punktem wyjścia są wartości [przykład]
     2:1–4:1 dla ogólnych usług, 1:1 dla opóźnieniowo wrażliwych i baz, i **weryfikujesz go pomiarem czasu gotowości
     CPU (CPU ready/steal)**, nie regułą kciuka.
   - **Pamięć**: bez overcommitu dla baz i obciążeń krytycznych; balloon i swap hosta to wyjątek, nie plan.
   - **Migracja na żywo** wymaga wspólnego storage lub kopiowania dysków, spójnej rodziny CPU (wspólny model CPU
     w klastrze) i sieci migracyjnej osobnej od ruchu VM.
   - **Kworum**: klaster potrzebuje większości głosów; 2 węzły wymagają trzeciego głosu (QDevice, świadek), w innym
     razie awaria jednego węzła zatrzymuje klaster. Zalecany start to 3 węzły.
   - Sieć: osobne VLAN-y lub interfejsy dla zarządzania, migracji, storage i ruchu VM; 25 GbE dla storage
     rozproszonego [przykład], ścieżki redundantne (LACP/MLAG, MPIO dla iSCSI/FC).
4. **Storage** — wybór architektury:

   | Wymaganie | Wybór | Uwaga |
   |---|---|---|
   | bloki o niskim opóźnieniu, współdzielone | SAN (FC lub iSCSI) | FC: dedykowana sieć, drogie, przewidywalne; iSCSI na Ethernecie: taniej, wymaga izolacji i MPIO |
   | pliki dla wielu klientów | NAS (NFS dla Linuksa/VM, SMB dla Windows) | uważaj na blokady, uprawnienia i pojedynczą głowicę |
   | skalowanie poziome bez macierzy | storage definiowany programowo (Ceph, vSAN) | minimum 3 węzły, sieć i dyski z konsekwentnym wymiarowaniem |
   | pojedynczy host lub edge | lokalny ZFS/LVM, replikacja asynchroniczna | prostota ponad HA |

   Ceph: domyślnie replikacja ×3 z `min_size` 2; pula erasure coding k+m oszczędza miejsce kosztem opóźnienia i
   narzutu przy odbudowie, wymaga co najmniej k+m domen awarii [niezweryfikowane: wymagania wersji — sprawdź
   dokumentację używanego wydania].
5. **RAID i erasure coding** — dla dużych dysków (≥ 10 TB) odbudowa trwa godzinami do dni, a w tym czasie klaster jest
   podatny na drugą awarię i błąd odczytu (URE):
   - RAID 5 na dużych dyskach: unikaj dla danych, których utrata boli; **RAID 6 lub RAID 10** (10: szybszy zapis i
     odbudowa, 50% pojemności); RAID 0 tylko dla danych tymczasowych.
   - Zapis w RAID 5/6 ma karę (read-modify-write: ok. 4 i 6 operacji na zapis [przykład, kontroler z cache zmniejsza]).
   - Erasure coding: mniejszy narzut pojemności (np. k=4, m=2 → 1,5× zamiast 3×), ale droższe odczyty/zapisy małych
     bloków i odbudowa — dla obciążeń archiwalnych i obiektowych, rzadziej dla baz.
   - RAID nie jest kopią zapasową: chroni przed awarią dysku, nie przed usunięciem, błędem aplikacji ani ransomware.
6. **Wydajność.** Wymiaruj na trzech osiach: **IOPS**, **przepustowość** (IOPS × rozmiar bloku) i **opóźnienie**
   (p95/p99). Głębokość kolejki wiąże je prawem Little'a (współbieżność = przepustowość × opóźnienie): bez
   równoległości SSD NVMe nie osiągnie specyfikacji. Mierz pod realistycznym obciążeniem (fio z profilem aplikacji),
   zostaw zapas ~30% na odbudowy i szczyty. Strojenie po stronie OS: **ops-linux-performance**.
7. **Ochrona danych.** **Migawka nie jest kopią zapasową** — leży na tym samym storage i znika razem z nim. Kopia:
   zasada **3-2-1** (3 kopie, 2 różne nośniki, 1 poza lokalizacją; rozszerzenie 3-2-1-1-0 to konwencja
   dostawców: +1 niezmienialna/offline, 0 błędów po teście odtworzenia). Co najmniej jedna kopia **niezmienialna**
   (Object Lock/WORM, taśma, offline) z osobnymi poświadczeniami niż produkcja. Kopia liczy się po **teście odtworzenia**
   z pomiarem czasu. RPO/RTO i incydenty: **ops-sre-incidents**.
8. **Cykl życia sprzętu i pojemność.** Rejestr zasobów: model, data zakupu, koniec gwarancji i wsparcia, wersja
   firmware, wymagane wymiany. Cykl odświeżania typowo 4–6 lat [przykład — zależy od wsparcia producenta i
   amortyzacji]; część zapasowa na miejscu (dyski, zasilacze, wentylatory, optyki) i umowa SLA na wymianę. Firmware
   aktualizujesz w oknach zmian, węzeł po węźle, najpierw w środowisku testowym; zgodność BIOS/HBA/dysków z hiperwizorem
   sprawdzasz w macierzy zgodności dostawcy. Prognoza pojemności z trendu zużycia: alert przy ~70–80% zajętości puli
   (czas zamówienia sprzętu bywa dłuższy niż czas do zapełnienia).
9. **Edge.** Założenia: łącze bywa niedostępne, nikt nie jest na miejscu, miejsca i zasilania mało.
   - Praca **autonomiczna** bez łączności (lokalne DNS, uwierzytelnianie, kolejkowanie danych), synchronizacja po powrocie.
   - **Zdalne zarządzanie poza pasmem** (BMC: iDRAC, iLO, Redfish), zero-touch provisioning, obrazy zatwierdzone centralnie.
   - Małe klastry: 1 węzeł + szybka wymiana, 2 węzły + świadek, 3 węzły dla HA. Zapasowy węzeł wysłany kurierem bywa
     tańszy niż trzeci węzeł w każdej lokalizacji.
   - Flotą zarządzasz jak kodem (**ops-iac-terraform**), aktualizacje falami (kanarki), telemetria przez bufor lokalny
     (**ops-observability**). Kontenery na brzegu: **ops-kubernetes**.
10. **Migracja między hiperwizorami.** Inwentarz VM i zależności, pilotaż na VM niekrytycznej, konwersja dysków
    (qcow2, VMDK, VHDX), sterowniki wirtualne (virtio), zmiana kart sieciowych i adresów MAC, licencje powiązane ze
    sprzętem, agenty backupu i monitoringu, okno przełączenia, **plan wycofania** (stare środowisko działa równolegle
    do akceptacji). Fale od najmniej do najbardziej krytycznych.
11. **Wynik** — szablon:
    ```
    # Projekt infrastruktury: <nazwa>
    Założenia: obciążenia, RPO/RTO, budżet, horyzont
    Tabela wymiarowania: | zasób | wymaganie | wyliczenie | z zapasem N+1 | uwagi |
    Decyzje: hiperwizor, storage, RAID/EC, sieć, kopie (z uzasadnieniem i odrzuconymi opcjami)
    Ryzyka i pułapki | Plan wdrożenia i wycofania | Do potwierdzenia przez człowieka
    ```

## Przykład
Wejście: 3 węzły po 2×16 rdzeni i 512 GB RAM; 60 VM (łącznie 180 vCPU, 700 GB RAM) [przykład].
Wynik: po utracie węzła zostaje 64 rdzenie i 1024 GB. Pamięć: 700 GB < 1024 GB, ale z zapasem 15% (805 GB) mieści
się; CPU: 180/64 = 2,8:1 — akceptowalne dla usług ogólnych, nie dla baz. Decyzja: 3 węzły, Ceph ×3 na NVMe, sieć
25 GbE, bazy przypięte do 1:1; kopie na osobny serwer z niezmienialną kopią poza lokalizacją i testem odtworzenia
co kwartał.

## Checklista
- [ ] obciążenia zmierzone (p95), nie oszacowane
- [ ] pojemność policzona po awarii węzła (N+1), kworum zapewnione
- [ ] CPU i pamięć: overcommit zweryfikowany metryką, nie regułą kciuka
- [ ] warunki licencji sprawdzone w aktualnej ofercie (VMware) i koszt 5 lat
- [ ] RAID/EC dobrany do rozmiaru dysków i czasu odbudowy
- [ ] IOPS, przepustowość i opóźnienie p99 policzone, zapas na odbudowę
- [ ] 3-2-1, kopia niezmienialna, test odtworzenia z czasem
- [ ] rejestr sprzętu, firmware, części zapasowe, prognoza pojemności
- [ ] edge: praca offline, zdalne zarządzanie, zapasowy sprzęt
- [ ] migracja z planem wycofania; zmiany tylko za zgodą człowieka

## Źródła
- Proxmox VE: [Release notes i roadmap](https://pve.proxmox.com/wiki/Roadmap) — w wyszukiwaniu z 2026-10 znaleziono wydanie 9.1 (Debian 13, Ceph Squid 19.2.3); [niezweryfikowane] czy jest nowsze.
- Ceph: [docs.ceph.com — releases](https://docs.ceph.com/en/latest/releases/) — Tentacle 20.2.x aktywne, Squid 19.2.x z szacowanym końcem wsparcia 2026-09 lub 2026-10 (źródła rozbieżne) [niezweryfikowane].
- VMware/Broadcom: doniesienia o minimum 72 rdzeni na zakup i 16 rdzeni na procesor (od 2025-04, [Techzine](https://techzine.eu/news/infrastructure/130027/broadcom-raises-minimum-requirement-for-vmware-licenses-from-16-to-72-cores)) — źródła wtórne, [niezweryfikowane] względem warunków Broadcom.
- Zasada 3-2-1: CISA, [Data Backup Options](https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf) [niezweryfikowane: stan na dziś].
