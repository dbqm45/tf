# Hiperwizory i storage — fakty do sprawdzenia przed decyzją

Spis treści: Wersje i licencje · Kiedy co · Pytania do dostawców

## Wersje i licencje (stan wg wyszukiwania 2026-10-17)
- Proxmox VE 9.1: Debian 13 „Trixie”, jądro 6.17, QEMU 10.1, Ceph Squid 19.2.3, ZFS 2.3.4. Czy istnieje nowsze wydanie: [niezweryfikowane].
  Aktualizacja z 8.x wymaga najpierw Ceph Reef → Squid.
- Ceph: Tentacle (20.x) najnowsza seria, Squid (19.x) w końcowej fazie wsparcia; w Tentacle 20.2.0 zgłoszono błąd
  przy włączeniu `allow_ec_optimizations` na puli EC — przed włączeniem sprawdź zgłoszenie (Tracker 74813)
  [niezweryfikowane].
- VMware (Broadcom): subskrypcja zamiast licencji wieczystych, rozliczenie za rdzeń, minimum 16 rdzeni na procesor;
  doniesienia o minimum 72 rdzeni na zakup od 2025-04 (nie dotyczy wszystkich renewali — źródła rozbieżne)
  [niezweryfikowane]. Zawsze weryfikuj w ofercie partnera i umowie; nazwy pakietów (VCF, VVF) się zmieniają.

## Kiedy co
- Mała firma, 2–10 węzłów, umiejętności Linuksa: Proxmox VE lub KVM.
- Duże środowisko z narzędziami VMware i certyfikacjami aplikacji: licz koszt subskrypcji i koszt migracji obok siebie.
- Obciążenia kontenerowe: węzły Kubernetes mogą działać też na gołym metalu — decyzja w ops-kubernetes.

## Pytania do dostawców
Minima zakupowe na lokalizację, polityka renewali, okres wsparcia sprzętu, macierz zgodności firmware, czas wymiany
części w lokalizacji brzegowej, eksport VM do formatów otwartych.
