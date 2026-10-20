# Szablony: ai-architecture.md, koszt, ADR

## Szablon ai-architecture.md
```
# Architektura AI — <system>
TL;DR: wzorzec, źródło modelu, koszt na żądanie, p95, główne ryzyko.
Przekazanie: otwarte decyzje, kryteria rewizji.
1. Osie wymagań (świeżość, trafność, opóźnienie, koszt, dane, wyjaśnialność) — liczby i źródło
2. Wzorzec i odrzucone alternatywy (z dowodem z ewaluacji)
3. Źródło modelu, region, retencja, plan zmiany modelu
4. Komponenty i diagram z granicami zaufania
5. Budżet opóźnienia, timeouty, fallback, cache
6. Koszt i pojemność (tabela poniżej)
7. Izolacja najemców
8. Ryzyka, ADR-y
```

## Koszt żądania i miesiąca
Wartości w nawiasach to **symbole**; ceny bierzesz z cennika dostawcy z datą, nie z pamięci.

```
koszt_wywołania_bez_cache = (T_wej × C_wej + T_wyj × C_wyj)
koszt_wywołania_z_cache   = (T_stały × C_odczyt + T_zmienny × C_wej + T_wyj × C_wyj)
                            + zapis przy chybieniu: T_stały × C_zapis
C_odczyt = m_odczyt × C_wej   (mnożnik zależy od modelu)
C_zapis  = m_zapis × C_wej    (mnożnik zależy od TTL)
koszt_żądania = Σ wywołań (kroki workflow, ponowienia, ewaluacja online)
              + wyszukiwanie + narzędzia
koszt_miesiąca = koszt_żądania × żądania_dziennie × dni
```
Trafienia: `h` = udział wywołań z odczytem z cache; koszt średni = h × z_cache + (1 − h) × (bez_cache + zapis).
Przy ruchu rzadszym niż TTL cache `h` spada, więc szacuj `h` z realnego rozkładu odstępów między żądaniami.

| Pozycja | Symbol | Wartość [przykład] | Źródło i data |
|---|---|---|---|
| tokeny stałe (instrukcje, narzędzia) | T_stały | 6 000 | pomiar |
| tokeny zmienne wejścia | T_zmienny | 800 | pomiar |
| tokeny wyjścia | T_wyj | 400 | pomiar |
| cena wejścia / wyjścia | C_wej / C_wyj | z cennika | dostawca, data |
| wolumen dzienny | | 200 000 | wymagania |
| udział trafień cache | h | 0,8 | pomiar po pilotażu |

Pojemność: równoległe żądania w szczycie ≈ żądania/s × średni czas trwania (prawo Little'a, **proc-lean**);
porównaj z limitami tokenów na minutę u dostawcy. Własny model: **ops-ai-inference**.

## Szablon ADR dla decyzji AI
```
# ADR-NNN: <decyzja>
Status: proposed | accepted | superseded
Kontekst: osie wymagań, ograniczenia (region, licencja, zespół)
Opcje: min. 2–3, w tym „nudna”; fakty ze źródłem i datą
Decyzja: wybrana opcja i dlaczego
Konsekwencje: koszt (z i bez cache), opóźnienie, lock-in, ryzyka
Dowód: wynik ewaluacji (zbiór, metryka, wersja modelu i promptu)
Kryterium rewizji: np. jakość poniżej progu, cena zmieniona o X%, wycofanie modelu
```
Decyzje, które zasługują na ADR: wzorzec (workflow czy agent), źródło modelu i region, polityka retencji u dostawcy,
fallback i routing, izolacja najemców, zakres akcji bez zatwierdzenia człowieka.
