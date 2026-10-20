# Fakty sprzętowe: pewność i miejsce weryfikacji

Stan: 2026-10-20 (researcher). Pierwotne strony IEC, SAE, EUR-Lex, NIST i PTB były niedostępne; poziom W = źródło wtórne.

| Fakt | Poziom | Gdzie sprawdzić |
|---|---|---|
| CP: B +9 V, C +6 V, D +3 V, E zwarcie CP–PE | W | IEC 61851-1, SAE J1772 |
| CP: A +12 V, F −12 V | wiedza ogólna, niepotwierdzone | IEC 61851-1, SAE J1772 |
| PWM 1 kHz; I = D×0,6 A (10–85 %); I = (D−64)×2,5 A (85–96 %) | W (kopia J1772) | IEC 61851-1 Annex A, SAE J1772 |
| 3–7 % = komunikacja cyfrowa; 5 % dla ISO 15118 | W; ISO 15118 niepotwierdzone | ISO 15118-2/-3, IEC 61851-1 |
| PP Type 2: 1,5 kΩ/13 A, 680 Ω/20 A, 220 Ω/32 A, 100 Ω/63 A (3 fazy) lub 70 A (1 faza); ±3 % | W (forum) | IEC 61851-1 Annex B, IEC 62196-2 |
| Mode 1–4 i ich limity prądu | W | IEC 61851-1, IEC 61851-23 (DC) |
| Type 2 wybrany w UE (2013), CCS2, CCS1 150 A/600 V/90 kW, CHAdeMO bez normy międzynarodowej | W | IEC 62196-2/-3, SAE J1772 |
| SAE J3400: TIR 2023-12-18, RP J3400_202409 z 2024-09-30; J3400/1 i /2 niepotwierdzone | W | SAE J3400 (sae.org) |
| RCD typ B albo typ A + 6 mA DC; IEC 62955 (2018 lub 2023) | W | IEC 61851-1 §8.5, IEC 62955, IEC 60364-7-722 |
| MID 2014/32/UE obejmuje AC; DC przez (UE) 2026/706 (transpozycja do 2028-04-10, stosowanie od 2028-10-10) | W | EUR-Lex: 2014/32/UE, 2026/706 |
| Eichrecht dla DC | brak danych | PTB, MessEV |
| OCMF 1.4.1 (2025-01-15), podpis ECDSA-secp256r1-SHA256 | P (specyfikacja w repozytorium SAFE-eV) | OCMF-en.md |
| OCA Signed Meter Values v1.0 (2025) | W | openchargealliance.org |
| NIST HB44 §3.40 „Electric Vehicle Fueling Systems”, rozdzielczość AC 0,0001 kWh | W | NIST HB44 (wydanie 2026) |
