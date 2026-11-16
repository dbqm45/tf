# Macierz obowiązków i dowody

Numery artykułów AI Act pochodzą z tekstu rozporządzenia (UE) 2024/1689 znanego z wiedzy własnej; EUR-Lex był
niedostępny w sesji 2026-10-17 [niezweryfikowane u źródła]. Przed cytowaniem sprawdź je w EUR-Lex. Terminy stosowania
poszczególnych wierszy — tabela w SKILL.md. To nie jest porada prawna.

## Dostawca systemu wysokiego ryzyka
| Obowiązek | Art. | Dowód |
|---|---|---|
| System zarządzania ryzykiem w całym cyklu życia | 9 | rejestr ryzyk, decyzje o środkach, wyniki testów |
| Zarządzanie danymi (jakość, reprezentatywność, uprzedzenia) | 10 | karta zbioru danych, raport z analizy stronniczości |
| Dokumentacja techniczna | 11, zał. IV | dokument wersjonowany, karta modelu |
| Rejestrowanie zdarzeń (logi) | 12 | konfiguracja logów, okres przechowywania |
| Przejrzystość i instrukcja dla podmiotu stosującego | 13 | instrukcja użytkowania |
| Nadzór człowieka | 14 | opis mechanizmów, szkolenie operatorów, możliwość zatrzymania |
| Dokładność, odporność, cyberbezpieczeństwo | 15 | wyniki ewaluacji (ai-evals), testy odporności (arch-threat-modeling) |
| System zarządzania jakością | 17 | procedury, role |
| Ocena zgodności, deklaracja UE, znak CE | 43, 47, 48 | deklaracja zgodności, raport oceny |
| Rejestracja w bazie UE | 49 | numer wpisu |
| Monitorowanie po wprowadzeniu na rynek | 72 | plan monitorowania, metryki, przeglądy |
| Zgłaszanie poważnych incydentów | 73 | procedura, szablon zgłoszenia, terminy |

## Podmiot stosujący
| Obowiązek | Art. | Dowód |
|---|---|---|
| Użycie zgodnie z instrukcją, nadzór człowieka przez przeszkolone osoby | 26 | instrukcja, lista operatorów, szkolenia |
| Jakość danych wejściowych pod kontrolą wdrażającego | 26 | opis źródeł danych |
| Przechowywanie logów (co najmniej 6 miesięcy, o ile prawo nie stanowi inaczej) | 26 | polityka logów |
| Informowanie pracowników i osób, których dotyczą decyzje | 26 | treść komunikatu |
| Ocena skutków dla praw podstawowych (FRIA): organy publiczne, podmioty świadczące usługi publiczne i wdrażający scoring kredytowy lub wycenę ubezpieczeń | 27 | raport FRIA |
| Raportowanie incydentów dostawcy i organowi | 26, 73 | procedura |
| Kompetencje w zakresie AI (wszyscy) | 4 | plan szkoleń, lista uczestników |

## Przejrzystość (art. 50) i GPAI
- **Art. 50:** informowanie o kontakcie z AI (dostawca systemu), oznaczanie wyników syntetycznych w formacie
  maszynowym (dostawca), informowanie o deepfake i tekście publikowanym w sprawach publicznych (podmiot stosujący).
- **GPAI (art. 53):** dokumentacja techniczna modelu, informacje dla integratorów, polityka praw autorskich,
  publiczne streszczenie danych treningowych. **Ryzyko systemowe** (art. 51, domniemanie przy dużej mocy obliczeniowej
  treningu): ocena modelu, testy kontradyktoryjne, zgłaszanie poważnych incydentów, cyberbezpieczeństwo (art. 55).

## Terminy zgłoszenia poważnego incydentu (art. 73) [niezweryfikowane u źródła]
Zasada: do 15 dni od powzięcia wiadomości; krócej przy incydencie szeroko zakrojonym lub w infrastrukturze krytycznej
(do 2 dni) i przy zgonie (do 10 dni). O zgłoszeniu decyduje człowiek z prawnikiem.

## Kary (art. 99) [niezweryfikowane u źródła]
Praktyki zakazane do 35 mln EUR lub 7% światowego obrotu; inne obowiązki do 15 mln EUR lub 3%; nieprawdziwe informacje
dla organów do 7,5 mln EUR lub 1%; dla MŚP niższa z kwot.

## Lista dowodów do `ai-compliance.md`
Inwentarz; uzasadnienie roli i klasy; macierz z właścicielami; dokumentacja techniczna; karta modelu i zbioru; wyniki
ewaluacji i testów stronniczości; opis nadzoru człowieka; konfiguracja logów; polityka użycia AI; plan szkoleń;
procedura incydentu; FRIA/DPIA (jeśli dotyczą); umowy z dostawcami z gwarancjami zgodności; zatwierdzenie prawnika/IOD.
