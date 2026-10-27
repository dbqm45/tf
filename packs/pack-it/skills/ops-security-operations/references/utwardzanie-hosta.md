# Utwardzanie hosta (system serwera)

Dotyczy maszyny wirtualnej albo fizycznej z pełnym systemem (Linux, krótko Windows Server). Kontener i obraz:
`ops-docker`; konto i usługi chmury, CSPM: `sec-cloud-security`; sekrety i klucze maszyn: `ops-secrets-identities`.
Cel: mniejsza powierzchnia ataku i konfiguracja, która nie dryfuje.

## Procedura
1. **Linia bazowa zamiast listy z głowy.** Wybierz CIS Benchmark dla dystrybucji i wersji (poziom 1 na start;
   poziom 2 dla systemów o wysokiej klasie danych) albo profil SCAP/STIG, jeśli wymaga go regulacja. Odchylenia
   zapisz z powodem i właścicielem (ADR albo plik wyjątków obok IaC). Ogólne zasady: NIST SP 800-123.
2. **Minimalny system.** Obraz minimalny dystrybucji; usuń albo wyłącz usługi i pakiety, których rola maszyny nie
   potrzebuje (`systemctl list-unit-files --state=enabled`, `ss -tulpn` — każdy nasłuchujący port ma właściciela).
   Bez kompilatorów i narzędzi diagnostycznych na produkcji, jeśli nie są potrzebne.
3. **SSH.** Tylko klucze (`PasswordAuthentication no`, `KbdInteractiveAuthentication no`), bez logowania roota
   (`PermitRootLogin no`), ograniczeni użytkownicy lub grupy (`AllowGroups`), dostęp tylko z bastionu, VPN albo
   dostępu warunkowego (sec-zero-trust-identity) — port 22 nie jest otwarty na internet. Lepiej: dostęp przez
   zarządcę sesji dostawcy chmury lub krótkotrwałe certyfikaty SSH zamiast stałych kluczy.
4. **Konta i uprawnienia.** Konta imienne, bez współdzielonych; `sudo` z listą poleceń dla ról, nie `ALL`;
   konta serwisowe bez powłoki; wygaszanie nieużywanych kont. Najmniejsze uprawnienia także dla procesów: usługa
   jako osobny użytkownik, ograniczenia systemd (`NoNewPrivileges`, `ProtectSystem`, `PrivateTmp`).
5. **Zapora hosta** domyślnie odrzuca ruch przychodzący (nftables, ufw, firewalld; w chmurze dodatkowo grupy
   zabezpieczeń). Ruch wychodzący ograniczony tam, gdzie to możliwe — utrudnia wyciek i pobranie narzędzi przez
   napastnika.
6. **Jądro i system plików.** Parametry `sysctl` z linii bazowej (np. wyłączone przekazywanie pakietów, gdy maszyna
   nie jest routerem; ochrona przed fałszowaniem adresów); `/tmp` i partycje danych z `noexec`, `nosuid`, `nodev`,
   gdzie rola na to pozwala; Secure Boot; SELinux albo AppArmor w trybie wymuszania, nie wyłączony.
7. **Audyt i logi.** `auditd` (zmiany kont, sudo, pliki konfiguracyjne, ładowanie modułów) i logi systemowe
   wysyłane poza host (sekcja 1 skilla: telemetria). Synchronizacja czasu (NTP/chrony) — bez niej korelacja nie działa.
8. **Łatki.** Automatyczne łatki bezpieczeństwa (`unattended-upgrades`, `dnf-automatic`) albo przebudowa obrazu
   w pierścieniach (sekcja 5 skilla); restart po łatce jądra zaplanowany, nie odkładany w nieskończoność.
9. **Ochrona punktu końcowego.** EDR albo agent wykrywania na hostach produkcyjnych (sekcja 3 skilla), kontrola
   integralności plików dla krytycznych ścieżek.
10. **Sprawdzenie i dryf.** Skan zgodności z linią bazową (OpenSCAP z profilem CIS, Lynis jako szybki przegląd) po
    zbudowaniu obrazu i okresowo; wynik w CI obrazu albo w raporcie. Maszyna budowana z IaC (Packer, Ansible,
    cloud-init), ręczne zmiany wykrywane i cofane — logowanie na maszynę, żeby „poprawić”, to dryf.

## Windows Server — skrót
CIS Benchmark lub Microsoft Security Baselines; Server Core tam, gdzie się da; wyłączone SMBv1 i zbędne role;
LAPS dla haseł lokalnych administratorów; zapora Windows włączona dla wszystkich profili; Defender (lub inny EDR)
i PowerShell logging (Script Block Logging) wysyłane do SIEM.

## Przykład
**Wejście:** „Trzy maszyny Ubuntu z API, SSH otwarty z internetu, logowanie hasłem, aktualizacje ręcznie raz na
kwartał.”
**Wynik:** obraz z Packer + Ansible wg CIS Ubuntu poziom 1, wyjątki w pliku wyjątków obok IaC; SSH tylko z
bastionu i tylko kluczami, bez roota; zapora: 443 z load balancera, 22 z bastionu; `unattended-upgrades` dla
łatek bezpieczeństwa z oknem restartu; auditd i journald do SIEM; OpenSCAP w pipeline obrazu, raport co tydzień;
zmiana konfiguracji tylko przez PR do IaC.

## Checklista
- [ ] linia bazowa (CIS/SCAP) wybrana, odchylenia zapisane
- [ ] tylko potrzebne usługi i porty; każdy port ma właściciela
- [ ] SSH: klucze lub certyfikaty, bez roota, bez dostępu z internetu
- [ ] konta imienne, sudo ograniczone, usługi na osobnych użytkownikach
- [ ] zapora hosta domyślnie odrzuca; ruch wychodzący ograniczony tam, gdzie można
- [ ] SELinux/AppArmor wymuszane; parametry jądra i montowania z linii bazowej
- [ ] auditd i logi poza hostem, czas zsynchronizowany
- [ ] łatki automatyczne lub przebudowa obrazu; restarty zaplanowane
- [ ] skan zgodności po budowie i okresowo; dryf wykrywany, zmiany tylko przez IaC

## Źródła
- NIST SP 800-123 *Guide to General Server Security* (final, 07.2008; strona nist.gov sprawdzona 2026-10-27, status na
  csrc.nist.gov [niezweryfikowane] — host niedostępny z sandboxu): https://csrc.nist.gov/pubs/sp/800/123/final
- CIS Benchmarks (lista per system): https://www.cisecurity.org/cis-benchmarks [niezweryfikowane: strony nie pobrano];
  CIS Controls v8.1 (06.2024, wg wyszukiwania 2026-10-27)
Opisane własnymi słowami.
