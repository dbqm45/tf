# Ryzyko dostawców (third-party risk)

Spis treści: 1. Tiering · 2. Due diligence · 3. Czytanie raportu SOC 2 · 4. Klauzule umowne · 5. Monitoring · 6. Wyjście

## 1. Tiering
| Tier | Kryterium | Głębokość |
|---|---|---|
| 1 | dostęp do danych wrażliwych/osobowych na dużą skalę albo awaria zatrzymuje biznes | kwestionariusz pełny, raport SOC 2 typu II lub ISO 27001, przegląd umowy, roczny przegląd |
| 2 | ograniczony dostęp do danych, awaria uciążliwa | kwestionariusz skrócony, certyfikat lub raport |
| 3 | bez dostępu do danych, zastępowalny | samooświadczenie, warunki standardowe |

## 2. Due diligence
Kwestionariusz proporcjonalny (standardowe formaty branżowe zamiast autorskich 300 pytań [niezweryfikowane: dobór wg firmy]).
Obszary: zarządzanie bezpieczeństwem, dostęp i MFA, szyfrowanie, kopie i ciągłość, zarządzanie podatnościami,
incydenty i zgłaszanie, podwykonawcy, lokalizacja danych, usuwanie danych. Odpowiedź bez dowodu ma niższą wagę.
Wynik: ocena dostawcy, luki, warunki zakupu, ryzyka do rejestru (właściciel po stronie biznesu).

## 3. Czytanie raportu SOC 2
Sprawdź: typ (II dla tier 1), **okres** (aktualny, bez długiej luki do dziś — „bridge letter” wypełnia lukę), kategorie
Trust Services (czy obejmują to, na czym Ci zależy), **zakres systemu** (czy dotyczy usługi, którą kupujesz),
**opinię** (bez zastrzeżeń czy z zastrzeżeniem), **wyjątki** i odpowiedź kierownictwa, **kontrole uzupełniające
użytkownika (CUEC)** — to Twoje obowiązki, i wykorzystanie podwykonawców (carve-out). Raport jest poufny; chroń go
umową o zachowaniu poufności. Certyfikat ISO 27001: zakres, SoA (poproś o wersję), jednostka certyfikująca, ważność.

## 4. Klauzule umowne
Wymogi bezpieczeństwa (załącznik) · zgłaszanie incydentów w ustalonym terminie · prawo do audytu lub raportów ·
zarządzanie podwykonawcami i zgoda na zmiany · lokalizacja i transfer danych · zwrot i usunięcie danych przy
wyjściu · ciągłość i RTO/RPO · odpowiedzialność i ubezpieczenie · umowa powierzenia, gdy dane osobowe
(arch-privacy-compliance). Treść klauzul i odpowiedzialność opiniuje prawnik.

## 5. Monitoring ciągły
Roczny (tier 1) przegląd raportów i certyfikatów, kalendarz ważności; śledzenie incydentów dostawcy i zmian
właścicielskich; zmiana zakresu użycia → ponowna ocena; wyniki do KRI (dostawcy bez ważnej oceny). Dostawca z krytycznym
ustaleniem: plan naprawczy z terminem albo akceptacja ryzyka (rejestr-i-akceptacja.md).

## 6. Wyjście z dostawcą
Plan zastępstwa dla tier 1 przed umową: eksport danych w użytecznym formacie, okres przejściowy, potwierdzenie usunięcia.
