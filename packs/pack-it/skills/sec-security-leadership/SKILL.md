---
name: sec-security-leadership
description: Użyj przy strategii i prowadzeniu bezpieczeństwa w firmie jako CISO — strategia, budżet, raport dla zarządu, kultura, kryzys i okup, ubezpieczenie, M&A.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy prowadzisz lub budujesz funkcję bezpieczeństwa na poziomie kierownictwa (CISO, szef bezpieczeństwa, pierwszy specjalista w firmie) — strategia powiązana z celami biznesu (stan obecny, docelowy, mapa drogowa na 1–3 lata, profile bieżący i docelowy NIST CSF 2.0), budżet i uzasadnienie biznesowe (koszt kontroli wobec redukcji ryzyka, priorytety, ostrożne benchmarki), organizacja i model operacyjny (struktura zespołu, RACI, model trzech linii IIA 2020), raportowanie do zarządu (KPI a KRI, apetyt na ryzyko, jednostronicowy pulpit, język skutków biznesowych), kultura i uświadamianie (szkolenia, symulacje phishingu, pomiar zachowań), zarządzanie kryzysem na poziomie zarządu (zespół kryzysowy, dziennik decyzji, komunikacja z prawnikami, regulatorem, klientami i mediami, proces decyzji o okupie, ćwiczenia tabletop), ubezpieczenie cyber, ryzyko dostawców i łańcucha dostaw na poziomie programu, bezpieczeństwo przy fuzjach i przejęciach, ryzyko AI w organizacji. Wynik: jednostronicowa strategia, szablon raportu dla zarządu, szkic playbooka kryzysowego. Nie do rejestru ryzyk, FAIR i ryzyka dostawcy w szczegółach (sec-risk-management), ISO 27001, SOC 2 i macierzy kontroli (sec-governance-compliance), technicznej obsługi incydentu (ops-security-operations), NIS2, DORA i CRA (sec-eu-regulations) ani planu projektu (proc-project-planning). Nie jest poradą prawną ani ubezpieczeniową."
  slowa: "CISO, szef bezpieczeństwa, dyrektor bezpieczeństwa, strategia bezpieczeństwa, strategia cyber, mapa drogowa bezpieczeństwa, budżet na bezpieczeństwo, uzasadnienie budżetu, CFO, raport dla zarządu, rada nadzorcza, pulpit dla zarządu, KPI, KRI, apetyt na ryzyko, trzy linie, model trzech linii, RACI, struktura zespołu bezpieczeństwa, kultura bezpieczeństwa, szkolenia z bezpieczeństwa, phishing symulacja, uświadamianie, kryzys, sztab kryzysowy, ransomware zarząd, okup, płacić okup, ćwiczenie tabletop, komunikacja kryzysowa, ubezpieczenie cyber, ryzyko dostawców program, łańcuch dostaw, fuzje i przejęcia, due diligence M&A, ryzyko AI w firmie, profil docelowy"
---

# Przywództwo w bezpieczeństwie — strategia, zarząd, kryzys

**Rola agenta:** przygotowuje szkice strategii, raportu, playbooka i pytania do zarządu. **Decyzje (budżet, apetyt na
ryzyko, okup, zgłoszenia, zakup polisy) podejmują ludzie** z mandatem; sprawy prawne i ubezpieczeniowe — prawnik
i broker. To nie jest porada prawna ani ubezpieczeniowa. Liczby i fakty zewnętrzne: [niezweryfikowane], dopóki
nie masz źródła (core-grounding).

Granice: rejestr ryzyk, FAIR i ryzyko dostawcy w szczegółach — sec-risk-management; ISO 27001, SOC 2, macierz kontroli
— sec-governance-compliance; techniczne reagowanie — ops-security-operations; NIS2, DORA, CRA i terminy zgłoszeń —
sec-eu-regulations. Tu: co z tego decyduje i mówi kierownictwo.

## Procedura
1. **Kontekst biznesu.** Zapytaj o 3–5 celów firmy na 1–3 lata (wzrost, nowy rynek, klienci enterprise, przejęcia),
   „klejnoty” (dane, procesy, systemy, bez których firma staje) i dotychczasowe incydenty. Strategia bez celów
   biznesu jest listą narzędzi.
2. **Stan obecny i docelowy.** Oceń się względem NIST CSF 2.0 (sześć funkcji z Govern): **profil bieżący** →
   **profil docelowy** → analiza luk → plan działań (przebieg wg NIST SP 1301). „Zgodny z CSF” nie istnieje; mówisz
   „profil docelowy: …”. Szczegóły ram: sec-governance-compliance.
3. **Strategia i mapa drogowa.** 3–5 filarów, każdy z wynikiem biznesowym, inicjatywą, miernikiem i właścicielem; mapa
   w etapach (0–6, 6–18, 18–36 miesięcy), czego **nie** robimy. Termin i koszt jako przedziały (proc-project-planning).
   Szablon: `references/szablony.md`.
4. **Budżet i uzasadnienie.** Dla każdej inicjatywy: redukcja ryzyka (rozkład straty przed i po — sec-risk-management),
   koszt całkowity (licencje, ludzie, utrzymanie), alternatywa „nic nie robimy” i „ubezpieczamy”. Kolejność wg
   redukcji ryzyka na złotówkę oraz wymogów (klient, regulacja). Benchmarki (% budżetu IT, liczba etatów) tylko jako
   punkt odniesienia z źródłem i datą, nigdy jako uzasadnienie.
5. **Organizacja i role.** Model trzech linii (IIA 2020): zarząd odpowiada za nadzór, kierownictwo (1. i 2. linia)
   za działania i zarządzanie ryzykiem, niezależny audyt wewnętrzny daje zapewnienie. Bezpieczeństwo zwykle
   wspiera 1. linię i bywa 2. linią (nadzór nad ryzykiem); nie audytuje sam siebie. RACI dla decyzji: kto akceptuje
   ryzyko, kto ogłasza kryzys, kto kontaktuje się z regulatorem.
6. **Raport dla zarządu.** Jedna strona, język skutków (pieniądze, przestoje, klienci, prawo), nie alertów.
   **KPI** (czy program działa) i **KRI** (czy rośnie ryzyko) osobno, z progiem i trendem; ryzyka względem **apetytu**
   zatwierdzonego przez zarząd; na końcu **decyzje do podjęcia**. Rytm: kwartalnie plus zdarzenia. Szablon:
   `references/szablony.md`.
7. **Kultura i uświadamianie.** Mierz zachowania (odsetek zgłoszeń phishingu, czas zgłoszenia, powtarzalne
   błędy, użycie MFA), nie obecność na szkoleniu. Symulacje phishingu etycznie: zgoda zarządu i HR, bez
   upokarzania i listy „winnych” z nazwiskami, bez tematów wykorzystujących stres (premie, zwolnienia, choroba),
   uczenie zamiast kary, łatwy przycisk „zgłoś”.
8. **Kryzys.** Przed zdarzeniem: zespół kryzysowy z zastępcami, mandat, kanał poza zaatakowanymi systemami, playbook
   (`references/kryzys-i-ubezpieczenie.md`), ćwiczenie tabletop co najmniej raz w roku. W zdarzeniu: dziennik
   decyzji, rytm odpraw, jeden głos na zewnątrz, komunikacja przez prawnika tam, gdzie trzeba chronić poufność.
   **Okup:** decyzja zarządu po opinii prawnika (sankcje, zgłoszenia), organów ścigania i doradcy kryzysowego;
   płatność nie gwarantuje odzyskania danych ani nie zamyka sprawy.
9. **Ubezpieczenie cyber.** Co pokrywa, wyłączenia, limity, wymogi kontrolne (MFA, kopie, EDR), wybór doradców
   narzuconych przez ubezpieczyciela, termin powiadomienia. Polisa przenosi skutek finansowy, nie odpowiedzialność
   ani reputację (szczegóły ryzyka: sec-risk-management).
10. **Dostawcy, M&A, AI.** Dostawcy na poziomie programu: tiering wg krytyczności, zasady umów i monitoringu,
    plan wyjścia, kontrola kluczowych 4. stron (technika — ops-supply-chain-security; ocena pojedynczego dostawcy —
    sec-risk-management). M&A: przed podpisaniem krótka ocena celu (incydenty, tożsamość, długi techniczne,
    zgodność), zakres „dnia 1” (MFA, logowanie, dostęp), integracja w planie 100 dni. AI: inwentarz użycia
    (także nieoficjalnego), polityka dla pracowników, wyznaczony właściciel; obowiązki prawne — ai-governance-compliance,
    ryzyka aplikacji — sec-llm-security.

Wynik: `docs/project/security-strategy.md` (jednostronicowa strategia, mapa drogowa, budżet), `board-report.md`,
`crisis-playbook.md`; TL;DR i Przekazanie wg core-project-record. Pierwsza linia:
`Security leadership: <firma> — profil docelowy <rok>, decyzje do podjęcia: <n>`.

## Przykład
Wejście: „Software house, 600 osób, 3 duże przetargi enterprise w tym roku, brak CISO, MFA tylko dla administratorów.”
Wynik (fragment `security-strategy.md`):

```markdown
Security leadership: software house — profil docelowy 2028, decyzje do podjęcia: 2
Cele biznesu: wygrać 3 przetargi enterprise; zero przestoju produkcji >4 h.
Filar 1 Tożsamość: MFA odporne na phishing dla 100% kont uprzywilejowanych w 6 mies. (wynik: warunek przetargów).
KRI: odsetek kont uprzywilejowanych bez MFA (próg 0%), czas łatania krytycznych (próg 7 dni).
Budżet: 380–520 tys. zł/rok [przykład]; alternatywa „bez zmian”: ryzyko utraty przetargów wartych 12 mln zł [przykład].
Nie robimy: własnego SOC (usługa zewnętrzna). Decyzje: (1) etat CISO, (2) apetyt: brak ryzyka krytycznego >90 dni.
```

## Checklista
- [ ] strategia wynika z celów biznesu; profil bieżący i docelowy; lista „czego nie robimy”
- [ ] budżet: redukcja ryzyka, koszt całkowity, alternatywy; benchmarki z datą, nie jako argument
- [ ] raport: jedna strona, KPI i KRI osobno, apetyt, decyzje do podjęcia
- [ ] role (RACI) dla akceptacji ryzyka i ogłoszenia kryzysu; audyt niezależny od bezpieczeństwa
- [ ] kultura mierzona zachowaniami; symulacje phishingu etyczne
- [ ] playbook kryzysowy, ćwiczony; decyzja o okupie w procesie z prawnikiem
- [ ] [niezweryfikowane] przy faktach bez źródła

## Materiały dodatkowe
- `references/szablony.md` — jednostronicowa strategia, raport dla zarządu (KPI, KRI), RACI; czytaj przy pisaniu dokumentów.
- `references/kryzys-i-ubezpieczenie.md` — zespół kryzysowy, playbook, okup, komunikacja, tabletop, polisa; czytaj przy kryzysie.

## Źródła
- NIST CSF 2.0 (luty 2024) i NIST SP 1301, *Quick Start Guide for Creating and Using Organizational Profiles* (luty 2024):
  profil bieżący, docelowy, analiza luk (wyszukiwanie, dostęp 2026-10-17; dokumentów nie otwarto).
- IIA, *The IIA's Three Lines Model* (lipiec 2020; aktualizacja 2024 do słownika standardów) — sześć zasad, role organu
  nadzorczego, kierownictwa i audytu (wyszukiwanie, dostęp 2026-10-17; oryginału nie otwarto).
- OFAC, *Updated Advisory on Potential Sanctions Risks for Facilitating Ransomware Payments* (21.09.2021): odpowiedzialność
  bez winy, czynniki łagodzące (źródła wtórne, dostęp 2026-10-17).
Opisane własnymi słowami.
