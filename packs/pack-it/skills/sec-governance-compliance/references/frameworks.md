# Ramy zgodności — fakty i pułapki

Stan na 2026-10-17. Źródła wtórne; przed cytowaniem w umowie lub ofercie sprawdź tekst standardu.

## ISO/IEC 27001:2022
- System zarządzania bezpieczeństwem informacji (ISMS), certyfikowalny przez jednostkę certyfikującą.
- Klauzule 4–10 są obowiązkowe (bez wyłączeń): 4 kontekst i zakres, 5 przywództwo i polityka, 6 planowanie
  (ocena ryzyka, plan postępowania, cele), 7 wsparcie (zasoby, kompetencje, świadomość, informacja udokumentowana),
  8 działanie (realizacja oceny i postępowania z ryzykiem), 9 ocena (monitorowanie, audyt wewnętrzny, przegląd
  zarządzania), 10 doskonalenie (niezgodności, działania korygujące).
- Załącznik A: 93 kontrole w 4 tematach (organizacyjne, ludzkie, fizyczne, technologiczne), zastąpił 114 kontroli
  w 14 domenach z wydania 2013. Szczegóły kontroli: ISO/IEC 27002:2022.
- Kontrole z Załącznika A nie są listą „do odhaczenia”: wynikają z oceny ryzyka (proces: **sec-risk-management**),
  a **SoA** pokazuje, które stosujesz, dlaczego i czy wdrożone. Wyłączenie wymaga uzasadnienia.
- Amendment 1:2024 dodał do klauzul 4.1 i 4.2 kwestię zmian klimatu jako sprawy istotnej dla kontekstu.
- Okres przejściowy dla wydania 2013 zakończył się 2025-10-31 (źródła wtórne) — certyfikat musi dotyczyć wydania 2022.
- Pułapka: zakres certyfikatu wpisany w certyfikat; klient czyta zakres, a nie samo logo.

## NIST CSF 2.0
- Dobrowolna rama, bez certyfikacji; wydana w lutym 2024; adresowana do wszystkich organizacji.
- Funkcje: Govern (nowa: strategia, role, polityki, łańcuch dostaw), Identify, Protect, Detect, Respond, Recover →
  kategorie → podkategorie. Dobra do rozmowy z zarządem i do samooceny dojrzałości (profil bieżący i docelowy).
- Pułapka: „zgodny z CSF” nie istnieje jako status; mówisz „oceniliśmy się względem CSF 2.0, profil docelowy: …”.

## SOC 2 (AICPA)
- Raport niezależnego audytora (CPA) o kontrolach organizacji usługowej; nie certyfikat. Kryteria: *2017 Trust
  Services Criteria with Revised Points of Focus – 2022* (punkty uwagi zmieniono w 2022, kryteriów nie).
- Kategorie: Security (obowiązkowa; wspólne kryteria CC), Availability, Processing Integrity, Confidentiality, Privacy.
  Zakres kategorii wybierasz wg obietnic dla klientów.
- **Typ I**: czy projekt kontroli jest właściwy w dniu. **Typ II**: czy kontrole działały skutecznie w okresie
  (zwykle 6–12 mies.; pierwszy raport bywa krótszy [niezweryfikowane]). Klienci enterprise zwykle żądają typu II.
- Opis systemu i **kontrole uzupełniające użytkownika (CUEC)** oraz kontrole podwykonawców (carve-out lub inclusive)
  czyta klient — wpływa na jego ocenę ryzyka dostawcy.
- Pułapka: wyjątki (exceptions) w raporcie nie przekreślają go, ale klient je czyta; brak dowodu z okresu to wyjątek.

## PCI DSS v4.0.1
- Standard Rady PCI SSC dla podmiotów przechowujących, przetwarzających lub przesyłających dane kart albo
  wpływających na ich bezpieczeństwo. v4.0.1 opublikowano 2024-06-11 jako ograniczoną rewizję v4.0 (bez nowych
  wymagań); v4.0 wycofano 2024-12-31.
- Wymagania „przyszłościowe” z v4.0 stały się obowiązkowe od 2025-03-31; liczba wymagań w źródłach różni się (51 lub 52)
  [niezweryfikowane — sprawdź Summary of Changes].
- Poziom walidacji (QSA, SAQ, ROC/AOC) zależy od roli i wolumenu, ustala go acquirer lub marka kart.
- Dalsze zmiany: jedno źródło wspomina konsultację nad rewizją w 2026 [niezweryfikowane]; sprawdź pcisecuritystandards.org.
- Pułapka: zakres PCI to wszystko, co ma styk z danymi kart; tokenizacja i segmentacja zmniejszają go najskuteczniej.

## Inne ramy do rozpoznania (bez opisu)
NIS2, DORA — prawo UE, interpretuje prawnik; ISO 42001 i AI Act — **ai-governance-compliance**; RODO —
**arch-privacy-compliance**; ISO 27017/27018 — rozszerzenia dla chmury i danych osobowych w chmurze (do 27001).
