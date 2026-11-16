# Warstwy obrony (defence in depth) — mapa do przeglądu

Zasada: każda kontrola kiedyś zawiedzie, więc za nią stoi następna. Przegląd przechodzi warstwy po kolei i dla każdej
pyta o trzy rodzaje kontroli: **zapobiegawczą** (blokuje), **wykrywającą** (zauważa) i **naprawczą** (przywraca).
Warstwa bez kontroli to dziura albo świadoma decyzja — wtedy zapisz akceptację ryzyka z właścicielem i datą przeglądu
(procedura pkt 5).

| Warstwa | Typowe kontrole | Pytanie przeglądowe | Skill |
|---|---|---|---|
| sieć | segmentacja i mikrosegmentacja, filtrowanie ruchu (domyślnie odrzuca), WAF, ochrona DDoS, ograniczony ruch wychodzący | Jak daleko dojdzie napastnik po przejęciu jednej usługi (blast radius)? | sec-zero-trust-identity, ops-security-operations (sieć i chmura), ops-kubernetes (NetworkPolicy), ops-cloud-landing-zones |
| tożsamość i dostęp | MFA odporne na phishing, najmniejsze uprawnienia, krótkotrwałe poświadczenia, PAM i JIT, tożsamości maszyn | Kto i co może zrobić z tym zasobem i skąd to wiemy? | be-auth-security, sec-zero-trust-identity, ops-secrets-identities |
| host i środowisko uruchomieniowe | utwardzanie (linia bazowa CIS), łatki, inwentarz, EDR, kontener bez roota | Czy każdy host i obraz ma linię bazową i sprawdzany dryf? | ops-security-operations (utwardzanie hosta), ops-docker, sec-cloud-security |
| aplikacja | bezpieczny projekt (ten skill), walidacja wejścia, autoryzacja per obiekt, SAST/DAST/SCA, bezpieczne ustawienia domyślne | Które przepływy przez granicę zaufania nie mają kontroli i testu nadużycia? | sec-appsec-devsecops, be-auth-security, fe-web-platform, sec-llm-security |
| dane | klasy danych, szyfrowanie w ruchu i w spoczynku, kontrola dostępu do kluczy, kopie, cykl życia i usuwanie | Co wycieknie, gdy napastnik dostanie kopię bazy albo dostęp aplikacji? | sec-cryptography-pki (dane w spoczynku), arch-privacy-compliance, ops-sre-incidents (kopie) |
| łańcuch dostaw | lockfile, karencja wersji, SBOM, podpisy i provenance, uprawnienia CI | Czy wiemy, co wdrażamy i kto to zbudował? | ops-supply-chain-security, sec-appsec-devsecops (SLSA), ops-ci-cd |
| monitorowanie i wykrywanie | centralne logi bezpieczeństwa, reguły wykrywania z testem, SIEM, EDR, IDS | Po jakim czasie zauważymy nadużycie z tej ścieżki i kto dostanie alarm? | ops-security-operations, sec-detection-engineering, ops-observability |
| reagowanie i odtwarzanie | plan reagowania, playbooki i runbooki, ćwiczenia, kopie z testem odtworzenia | Kto co robi w pierwszej godzinie i ile danych stracimy? | ops-security-operations (NIST SP 800-61r3), ops-sre-incidents, sec-security-leadership (tabletop) |

## Jak użyć w modelu zagrożeń
1. Po STRIDE (procedura pkt 4) przypisz każde zagrożenie do warstw, które mogą je zatrzymać, wykryć i naprawić.
2. Zagrożenie zatrzymywane przez **jedną** kontrolę w **jednej** warstwie to kandydat na dodatkową kontrolę —
   zwłaszcza dla aktywów o wysokiej wartości.
3. W `threat-model.md` dodaj krótką tabelę: warstwa → kontrole obecne → luki → decyzja. Szczegóły kontroli opisują
   skille z kolumny „Skill”; ten plik tylko pilnuje, żeby żadna warstwa nie została pominięta.
