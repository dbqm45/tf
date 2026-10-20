# Macierz obowiązków NIS2, DORA, CRA

Spis treści: NIS2 · DORA · CRA · Kary · Dowody. Wszystkie numery artykułów i kwoty: wiedza własna, w sesji niepotwierdzone
w EUR-Lex [niezweryfikowane u źródła]. Nie jest poradą prawną; ustawa krajowa i wytyczne organów mają pierwszeństwo.

## NIS2 (dyrektywa (UE) 2022/2555)
| Temat | Treść | Dowód |
|---|---|---|
| Zakres (art. 2–3) | średnie i duże podmioty z zał. I (energia, transport, bankowość, infrastruktura rynku finansowego, zdrowie, woda, infrastruktura cyfrowa, zarządzanie usługami ICT B2B, administracja, kosmos) i zał. II (poczta, odpady, chemikalia, żywność, wytwarzanie, dostawcy cyfrowi, badania) | analiza kwalifikacji, wpis do wykazu |
| Kluczowy a ważny | kluczowy: duży z zał. I i wyjątki niezależne od wielkości; ważny: pozostałe. Różnica to głównie nadzór (kluczowe także z góry) i górne kary | uzasadnienie klasy |
| Zarząd (art. 20) | zatwierdza środki z art. 21, nadzoruje, odpowiada za naruszenia, szkolenia | protokoły, listy szkoleń |
| Środki (art. 21 ust. 2) | analiza ryzyka i polityki; obsługa incydentów; ciągłość (kopie, zarządzanie kryzysowe); łańcuch dostaw; bezpieczeństwo nabywania, rozwoju i utrzymania, w tym obsługa podatności; ocena skuteczności; higiena i szkolenia; kryptografia; kadry, kontrola dostępu, zasoby; MFA i bezpieczna łączność | polityki, rejestry, testy |
| Zgłaszanie (art. 23) | incydent poważny: 24 h wczesne ostrzeżenie (czy podejrzenie czynu zabronionego, skutek transgraniczny), 72 h zgłoszenie z oceną, raport pośredni na żądanie, raport końcowy miesiąc po zgłoszeniu, przy trwającym incydencie raport z postępu | playbook, rejestr zgłoszeń |
| Kary (art. 34) | kluczowe do 10 mln euro lub 2% obrotu; ważne do 7 mln euro lub 1,4% obrotu (wyższa z kwot); ustawa krajowa może ustalać własne pułapy | — |
Krajowo (PL): ustawa o KSC po nowelizacji (Dz.U. 2026 poz. 252) — sprawdź w ISAP wykaz, terminy, krajowe kary, rolę CSIRT
(NASK, GOV, MON) i organów właściwych dla sektora [niezweryfikowane].

## DORA (rozporządzenie (UE) 2022/2554, od 2025-01-17)
| Filar | Treść |
|---|---|
| Zarządzanie ryzykiem ICT (rozdz. II) | ramy zatwierdzane i nadzorowane przez organ zarządzający, identyfikacja zasobów, ochrona, wykrywanie, reagowanie i odtwarzanie, kopie, uczenie się |
| Incydenty (rozdz. III) | proces, klasyfikacja wg kryteriów (klienci, straty danych, czas, zasięg geograficzny, krytyczność usług, skutki ekonomiczne), zgłaszanie poważnych incydentów: wstępne, pośrednie, końcowe; dobrowolne zgłaszanie istotnych cyberzagrożeń |
| Testy odporności (rozdz. IV) | program testów co najmniej raz w roku; TLPT (testy penetracyjne oparte na zagrożeniach) co najmniej co 3 lata dla wskazanych podmiotów; RTS (UE) 2025/1190 [niezweryfikowane] |
| Ryzyko dostawców ICT (rozdz. V) | strategia, rejestr informacji o ustaleniach umownych (pierwsze przekazanie organom 2025-04-30), obowiązkowe klauzule umowne (art. 30), strategie wyjścia, nadzór nad krytycznymi dostawcami ICT przez ESA (Lead Overseer) |
| Wymiana informacji | dobrowolna wymiana informacji o cyberzagrożeniach |
Kary: ustalają państwa członkowskie i organy nadzoru; dla krytycznych dostawców ICT okresowe kary pieniężne ESA [niezweryfikowane].

## CRA (rozporządzenie (UE) 2024/2847)
| Temat | Treść |
|---|---|
| Daty | w mocy 2024-12-10; przepisy o jednostkach oceniających zgodność od 2026-06-11 [niezweryfikowane]; zgłaszanie (art. 14) od 2026-09-11; większość obowiązków od 2027-12-11 |
| Producent | wymogi zasadnicze (zał. I): bezpieczeństwo w projekcie i domyślnie, brak znanych możliwych do wykorzystania podatności przy wprowadzeniu, aktualizacje bezpieczeństwa, SBOM, polityka koordynowanego ujawniania podatności; ocena ryzyka; dokumentacja techniczna; okres wsparcia co najmniej 5 lat, chyba że produkt krócej |
| Ocena zgodności | kategorie: domyślna (samoocena), ważne (klasa I i II), krytyczne; znak CE i deklaracja zgodności UE |
| Zgłaszanie (art. 14) | aktywnie wykorzystywana podatność i poważny incydent wpływający na bezpieczeństwo produktu: 24 h, 72 h, raport końcowy (podatność: 14 dni po poprawce; incydent: miesiąc), przez platformę ENISA do koordynatora CSIRT i ENISA |
| Importer, dystrybutor | weryfikują zgodność producenta, oznakowanie, współpracę z organami |
| Open source | steward z lżejszymi obowiązkami; komponenty OSS w produkcie nadal na producencie (due diligence) |
Kary: do 15 mln euro lub 2,5% obrotu (naruszenie wymogów zasadniczych), niższe progi za pozostałe [niezweryfikowane u źródła].

## Dowody (wspólne)
Rejestr zasobów i dostawców, polityki zatwierdzone przez zarząd, szkolenia zarządu, rejestr incydentów z osią czasu, protokoły
tabletop, raporty testów, umowy z klauzulami (NIS2 łańcuch dostaw, DORA art. 30), SBOM i polityka podatności (CRA).
Mapowanie na ISO 27001 — `.claude/skills/sec-governance-compliance/SKILL.md`.
