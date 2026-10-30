---
name: ops-linux-performance
description: Użyj przy wydajności Linuksa — metoda USE, perf, flame graphy, eBPF, pamięć, dysk, tuning jądra i cgroups.
metadata:
  przeglad: "2027-04-17"
  widocznosc: nazwa
  katalog: "Użyj przy badaniu wydajności i tuningu systemu Linux — metodyka (USE, RED), lista pierwszej minuty, profilowanie CPU (perf, flame graphy), eBPF (bcc, bpftrace), pamięć (page cache, swap, OOM, NUMA, huge pages), dysk (schedulery, opóźnienia, fio), podstawy stosu sieciowego i sysctl, cgroups v2, proces zmiany parametrów jądra, bezpieczeństwo narzędzi śledzących. Wynik to raport z badania wydajności. Nie do diagnozy awarii usług, DNS i TLS (ops-linux-networking), metryk i alertów (ops-observability), błędów w kodzie (eng-debugging) ani requests i limits w Kubernetes (ops-kubernetes)."
  slowa: "wolny serwer, serwer zwalnia, serwer muli, pierwsza diagnoza wydajności, obciążenie serwera, wolny serwer, wysokie obciążenie, load average, cpu 100%, flame graph, perf, ebpf, bpftrace, oom killer, swap, page cache, numa, huge pages, iowait, fio, scheduler dyskowy, sysctl, tuning jądra, cgroups, opóźnienia dysku, wąskie gardło, profilowanie"
---

# Wydajność Linuksa: badanie i tuning

Wynik: **raport z badania wydajności** (objaw, metoda, pomiary, wąskie gardło, rekomendacja, wynik po zmianie).
Pomiar jest tylko do odczytu; zmiana parametru jądra lub limitu na produkcji tylko jako plan (stan przed, zmiana,
test, wycofanie) i za zgodą człowieka. Awarie usług, DNS, TLS i narzędzia hosta (ss, dig, curl): ops-linux-networking.
Metryki i alerty w czasie: ops-observability. Błąd w logice kodu: eng-debugging. requests/limits podów: ops-kubernetes.

## Metodyka najpierw
- **USE** (B. Gregg): dla każdego zasobu (CPU, pamięć, dysk, sieć, także kolejki i blokady) sprawdź
  **wykorzystanie** (utilization), **nasycenie** (saturation: kolejka, oczekiwanie) i **błędy**. Zacznij od błędów
  i nasycenia — łatwiej je zinterpretować. Zapisuj, które zasoby wykluczyłeś.
- **RED** dla usług: tempo żądań (Rate), błędy (Errors), czas trwania (Duration, percentyle, nie średnia).
  RED mówi, **że** usługa cierpi; USE, **który zasób** jest przyczyną.
- Nie zgaduj i nie zaczynaj od narzędzia, które znasz („street light”). Najpierw pytanie: co jest wolne, od kiedy,
  co się zmieniło, jaki jest cel (SLO).

## Pierwsza minuta (lista Netflix/Gregg, 10 poleceń)
`uptime` (load: trend 1/5/15 min) → `dmesg -T | tail` (OOM, błędy dysku, throttling) → `vmstat 1` (kolejka `r`,
swap `si/so`, `wa`) → `mpstat -P ALL 1` (jeden gorący rdzeń = wątek jednowątkowy) → `pidstat 1` (kto zjada CPU)
→ `iostat -xz 1` (`await`/`aqu-sz`, `%util` wiarygodne głównie dla jednego dysku) → `free -m` (cache vs
available) → `sar -n DEV 1` (przepustowość) → `sar -n TCP,ETCP 1` (retransmisje) → `top`. Wymaga pakietu
`sysstat`. Dodatkowo `cat /proc/pressure/{cpu,memory,io}` (PSI: czas oczekiwania na zasób, także per cgroup).

## Profilowanie CPU
1. `perf top` / `perf record -F 99 -g -p <pid> -- sleep 30` (próbkowanie ~99 Hz, zwykle niski narzut), potem
   `perf report`. Symbole wymagają informacji debug lub ramek (Java, Node: opcje frame pointer/mapy symboli).
2. **Flame graph** z danych perf (`stackcollapse-perf.pl | flamegraph.pl`, narzędzia B. Gregga): szerokość = udział
   czasu, szukasz szerokich „plateau”. Porównuj dwa wykresy (przed/po, zdrowy/chory — różnicowy flame graph).
3. Czas poza CPU (blokady, I/O, sleep): off-CPU flame graph (eBPF), nie perf CPU.

## eBPF (bcc, bpftrace)
Jednolinijkowce zamiast zgadywania: `biolatency` (histogram opóźnień dysku), `biosnoop`, `execsnoop` (krótkie procesy),
`opensnoop`, `tcpretrans`, `tcplife`, `runqlat` (opóźnienie w kolejce CPU), `cachestat`, `offcputime`, `profile`;
`bpftrace -e` do własnych sond. Nazwy narzędzi i dostępność zależą od pakietu (`bcc-tools`, `bpftrace`) i jądra
[sprawdź `ls /usr/share/bcc/tools`]. Wymagają uprawnień root/CAP_BPF.

## Pamięć, dysk, sieć, cgroups
- **Pamięć**: `available` w `free` jest ważniejsze niż „free”; page cache jest zwracalny. Swapowanie
  (`si/so` trwale > 0) i `dmesg | grep -i oom` (OOM killer: kto, dlaczego, limit cgroup czy system). NUMA:
  `numactl -H`, `numastat` (zdalna pamięć, niezbalansowane węzły). Huge pages: Transparent Huge Pages bywa źródłem
  skoków opóźnień w bazach — zmieniaj tylko wg zaleceń dostawcy bazy i z pomiarem.
- **Dysk**: patrz na opóźnienie i kolejkę (`await`, `aqu-sz`, `biolatency` — percentyle), nie samo MB/s. Scheduler
  (`none`, `mq-deadline`, `kyber`, `bfq`) dobierz do urządzenia: NVMe zwykle `none`; zmiana tylko po teście.
  Benchmark `fio` na **kopii/ środowisku testowym**, nigdy na produkcyjnym wolumenie pod ruchem; wynik zależy
  od `direct=1`, `bs`, `iodepth`, `rw`, profilu zbliżonego do aplikacji.
- **Sieć (stos hosta)**: `ss -ti` (rtt, cwnd, retrans), `nstat`, `ethtool -S` (drop na kartach), `sar -n`. Sysctl
  (`net.core.somaxconn`, `tcp_rmem/wmem`, `tcp_congestion_control`) zmieniasz, gdy pomiar pokazuje konkretny objaw
  (np. przepełniona kolejka accept), a nie według listy z internetu. Sieć fabryki: ops-datacenter-networking.
- **cgroups v2**: limity i metryki w `/sys/fs/cgroup/<grupa>/` (`cpu.max`, `cpu.stat` → `nr_throttled`,
  `memory.max`, `memory.events` → `oom_kill`, `io.max`, `*.pressure`). Częsty objaw: throttling CPU mimo wolnych
  rdzeni hosta albo OOM kontenera poniżej pamięci hosta. Wartości w Kubernetes: ops-kubernetes.

## Proces zmiany parametru (bez cargo cultu)
1. **Zmierz** stan wyjściowy (te same metryki i obciążenie, powtórzone ≥3 razy, zapisane wartości).
2. **Hipoteza**: „parametr X zmniejszy Y, bo mechanizm Z”.
3. **Jedna zmiana naraz**, tymczasowo (`sysctl -w`), z gotowym wycofaniem.
4. **Zmierz ponownie** w tych samych warunkach; poprawa mniejsza od szumu = brak efektu.
5. **Udokumentuj** (wartość, powód, pomiar przed/po, wersja jądra) i utrwal w kodzie (IaC, `/etc/sysctl.d/`),
   nie ręcznie na serwerze. Zmiany bez wpływu cofnij. Parametry jądra z linii bazowej bezpieczeństwa (CIS) zostają —
   utwardzanie hosta opisuje ops-security-operations.

## Bezpieczeństwo narzędzi śledzących
Narzut: `perf record` próbkowaniem — niski; `strace` — duży (zwalnia proces wielokrotnie), `tcpdump`/`bpftrace`
z sondą na każde zdarzenie — potencjalnie wysoki. Zasady: najpierw narzędzia próbkujące, krótko (10–30 s), jedna
maszyna lub instancja kanarkowa, wyjście do pliku w `/tmp` z czyszczeniem, dane mogą zawierać wrażliwe argumenty
i treści. Za zgodą człowieka na produkcji; core-agent-security dla poleceń z internetu.

## Przykład
**Wejście:** API `/search` p99 2,4 s (RED), p50 stabilne; `app-2`.
**Badanie:** `uptime` load 14 na 8 rdzeni; `vmstat 1` `r`=16, `wa`=0 → nasycenie CPU; `mpstat` równomierne;
`pidstat` → `search-worker` 780%; `perf record -F 99 -g` + flame graph → 41% w `regex_compile` [przykład].
**Wynik raportu:** przyczyna — kompilacja wyrażenia przy każdym żądaniu; rekomendacja: cache skompilowanego
wzorca (zmiana kodu, test, wdrożenie przez ops-ci-cd); pomiar po zmianie p99 < 300 ms [przykład]. Żadnych zmian sysctl.

## Checklista
- [ ] objaw, zakres i cel (SLO) zapisane; RED dla usługi, USE dla zasobów
- [ ] lista pierwszej minuty wykonana, wykluczone zasoby odnotowane
- [ ] wniosek oparty na pomiarze (perf/flame graph/eBPF), nie na przeczuciu
- [ ] zmiana parametru: pomiar → hipoteza → jedna zmiana → pomiar → dokumentacja
- [ ] narzędzia śledzące o niskim narzucie, krótko, za zgodą na produkcji
- [ ] raport: przyczyna, dowód, rekomendacja, wynik po zmianie

## Źródła
- B. Gregg — The USE Method (brendangregg.com/usemethod.html) i Netflix TechBlog, „Linux Performance Analysis in 60,000 Milliseconds” (2015; 10 poleceń potwierdzone wyszukiwaniem 2026-10-17)
- Linux kernel documentation — PSI, Pressure Stall Information (docs.kernel.org/accounting/psi, dostęp 2026-10-17); cgroup v2 (docs.kernel.org/admin-guide/cgroup-v2) — pliki i pola [niezweryfikowane]
- Nazwy narzędzi bcc/bpftrace, domyślne schedulery i zalecenia THP — wiedza własna, bez ponownego sprawdzenia [niezweryfikowane]
Opisane własnymi słowami.
