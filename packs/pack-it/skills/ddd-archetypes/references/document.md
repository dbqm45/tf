# Archetyp Document — mapper (dokumenty, wersje, obieg, retencja)

> **Spis treści:** Test dopasowania · Model (istota) · Pytania · Kroki mapowania · Decyzje do kontroli (R/A/X) · Format wyniku · Wzorce i pułapki · Kontrola jakości · Przykład (skrócony)

Zamienia wymagania o **dokumentach** (umowa, protokół, faktura jako plik, zgoda, załącznik) na model, w którym dokument
logiczny, jego niezmienne wersje, egzemplarze w formatach, dystrybucja i dyspozycja po terminie to osobne pojęcia.
Efekt: da się udowodnić, co dokładnie i kiedy zostało zapisane lub wysłane, i wiadomo, jak długo to przechowywać.
Protokół wspólny (pytania, „To zależy”, kontrola R/A/X, zapis): `SKILL.md` → „Mapper — wspólny protokół”.

## Test dopasowania
**Pytanie rdzeniowe:** *czy trzeba udowodnić, CO dokładnie zostało zapisane, uzgodnione lub wysłane i kiedy — i jak długo to przechowywać?*
Tak → pasuje. Plik jest tylko załącznikiem bez wartości dowodowej i bez terminu przechowywania → wystarczy pole w innym agregacie.

| Sygnał w wymaganiach | Pasuje? |
|---|---|
| „musimy pokazać, jaką wersję umowy podpisał klient” | ✅ |
| wersje, numeracja, „kto i kiedy zmienił”, zatwierdzanie | ✅ |
| podpis, pieczęć, znacznik czasu, skrót pliku jako dowód | ✅ |
| przechowywanie przez N lat, potem usunięcie lub przekazanie do archiwum | ✅ |
| wysłano kontrahentowi / klientowi; kto otrzymał którą wersję | ✅ |
| wstrzymanie usuwania przy sporze lub kontroli | ✅ |
| „jakie zobowiązania wynikają z umowy?” (strony, terminy, warunki) | ❌ → Agreement (`agreement.md`); dokument jest nośnikiem |
| „jaka jest kwota na fakturze i jak ją zaksięgować?” | ❌ → Accounting; dokument nie jest źródłem prawdy stanu |
| README, ADR, runbook w repozytorium | ❌ → docs-tech-writing |
| tożsamość i uprawnienia do czytania | ❌ autoryzacja (warstwa aplikacji) |
| wyszukiwanie pełnotekstowe, OCR | ⚠️ graniczny |

**Przypadki graniczne:**
- *Zwykły załącznik do zgłoszenia* — jeśli nikt nie pyta o wersję, integralność ani termin, to nie ten archetyp.
- *Treść zobowiązań vs plik* — reguły i terminy umowy żyją w Agreement; Document pilnuje, który plik jest dowodem której wersji.
- *Dane z formularza* — gdy ważne jest „co klient zobaczył i zatwierdził”, zamroź wersję treści jako dokument; sam formularz
  nie jest dokumentem.

## Model (istota)
Poniższy podział to wniosek modelowy fabryki; źródła w sekcji „Źródła” potwierdzają tylko to, co tam opisano.
### Dokument, wersja, egzemplarz
- **Document** (zasób informacyjny) — byt logiczny: identyfikator, typ (umowa, protokół, zgoda), klasyfikacja, powiązania
  z faktem biznesowym. Nie ma treści; wskazuje wersje. Obejmuje też nośniki inne niż tekst (zdjęcie, nagranie, e-mail).
- **DocumentVersion** — **niezmienna** treść: numer, autor, czas utworzenia, status (robocza, zatwierdzona, zastąpiona),
  skrót treści. Zmiana = nowa wersja, nigdy edycja; poprzednia pozostaje dostępna. Numeracja to polityka (kolejna liczba,
  główna.poboczna), nie data.
- **Rendition** (egzemplarz) — konkretny plik tej samej wersji w jakimś formacie: edytowalny, PDF, PDF/A do długiego przechowywania.
  Format długoterminowy jest decyzją retencyjną: wersja zatwierdzona dostaje rendycję archiwalną.
- **Record** (rekord) — wersja zamrożona w roli dowodu: nie zmienia się, ma kontekst (sprawa, fakt biznesowy, kto i po co).
  Rekord ma wiarygodny charakter, gdy da się wykazać jego autentyczność, rzetelność, integralność i użyteczność — te
  cztery cechy to dobra lista kontrolna wymagań (nie schemat danych).

### Dowody integralności
- **IntegrityEvidence** — skrót treści (hash) zapisany osobno od pliku; opcjonalnie pieczęć elektroniczna, znacznik czasu,
  podpis. Poziom (zwykły, zaawansowany, kwalifikowany) i dostawca to **parametr polityki** zależny od typu dokumentu i
  ryzyka, nie stała w archetypie. Dowód należy do wersji, nie do dokumentu; po migracji formatu dowód liczy się na nowo albo
  zachowuje się go razem z oryginałem. Skutki prawne poziomów ocenia prawnik.

### Dystrybucja i dyspozycja
- **Distribution** — fakt przekazania konkretnej wersji (i rendycji) konkretnej stronie (→ Party): kanał, czas, potwierdzenie.
  Pozwala odpowiedzieć „kto dostał którą wersję”. Odwołanie lub zastąpienie wersji nie kasuje historii dystrybucji.
- **Disposition** — co z dokumentem po terminie: usunięcie, przekazanie do archiwum, ekspertyza. Wynika z reguły retencji
  zastosowanej do dokumentu, nie z ręcznej decyzji pliku.

### Retencja
- **RetentionRule** — klasyfikacja (kategoria dokumentu) → okres i dyspozycja. Reguła to dane, wersjonowana, z datą
  obowiązywania; dokument zapisuje, którą regułę zastosowano.
- **Termin liczony od zdarzenia, nie od utworzenia** — zwykle od zakończenia sprawy. Przykład z administracji PL: klasyfikacja
  według JRWA, kategoria archiwalna A (wieczyście), B z liczbą lat albo BE z liczbą lat (po okresie ekspertyza archiwalna);
  okres liczy się od 1 stycznia roku następnego po zakończeniu sprawy. Samo „B” bez liczby jest niepoprawne.
  Dla firm prywatnych okresy wynikają z innych przepisów (podatkowe, rachunkowe, pracownicze) — do potwierdzenia przez prawnika.
- **LegalHold** (wstrzymanie usunięcia) — osobny byt: powód, zakres (dokumenty, sprawy), zakładający, okres; dopóki trwa,
  disposition jest zablokowana mimo upływu terminu. To własny wniosek modelowy, nie element normy; wstrzymanie zdejmuje się jawnie.

### Powiązanie z faktem biznesowym
Dokument wskazuje fakt (`umowa → Agreement`, `faktura → Accounting`, `zgoda → Party`), ale **nie jest źródłem prawdy stanu**.
Stan zobowiązania, salda i uprawnień trzymają właściwe archetypy; dokument jest ich dowodem. Rozbieżność plik–stan to
sygnał do wyjaśnienia, nie do cichej korekty.

## Pytania
**A — decyzje standardowe:**
- Które typy dokumentów obejmujemy i które z nich są rekordami (dowodami), a które roboczymi?
- Kto i kiedy zamraża wersję (zatwierdzenie, podpis, wysyłka)? Czy po zamrożeniu dopuszczamy tylko nowe wersje?
- Jaki poziom dowodu integralności dla którego typu (skrót, pieczęć, znacznik czasu, podpis)? Kto jest dostawcą?
- Format długoterminowy (np. PDF/A) — dla jakich typów i kiedy powstaje rendycja?
- Jaka klasyfikacja i okres retencji per typ; od jakiego zdarzenia liczymy termin?
- Co robi disposition po terminie (usunąć, zarchiwizować, ekspertyza) i kto zatwierdza?

**B — luki** (przykłady): wstrzymanie usunięcia przy sporze? · dystrybucja do wielu odbiorców z potwierdzeniem? · tajemnica
i klasyfikacja dostępu (→ autoryzacja)? · migracja formatu po latach a ważność podpisu? · dokument papierowy zeskanowany
(oryginał vs kopia)? · zgody RODO a retencja (→ Party)? · anonimizacja treści przy zachowaniu rekordu?

## Kroki mapowania
1. **Typy dokumentów** — rzeczowniki z wymagań (umowa, protokół, aneks) → typ i klasyfikacja; oddziel dokument od faktu biznesowego.
2. **Wersje** — kiedy powstaje nowa, numeracja, statusy, kto zatwierdza.
3. **Rendycje** — formaty i moment tworzenia formatu archiwalnego.
4. **Dowody integralności** — poziom per typ jako parametr polityki.
5. **Dystrybucja** — komu, którą wersję, jakim kanałem, z potwierdzeniem czy bez.
6. **Retencja** — reguła, zdarzenie startowe, okres, disposition; wersjonowanie reguł.
7. **LegalHold** — czy potrzebny, kto zakłada i zdejmuje.
8. **Powiązanie z faktem** — do którego archetypu odsyła dokument; kierunek zależności.

## Decyzje do kontroli (R/A/X)
typy i rekordy · moment zamrożenia · numeracja wersji · poziom dowodu per typ · format archiwalny · zdarzenie startu retencji ·
okres i disposition · legal hold · dystrybucja i potwierdzenie · migracja formatu · powiązanie z faktem biznesowym.

## Format wyniku
```markdown
# Model Document: <obszar>
## Mapowanie pojęć    — | Pojęcie domeny | Element archetypu | Uzasadnienie |
## Niezmapowane pojęcia
## Typy dokumentów    — | Typ | Klasyfikacja | Rekord? | Fakt biznesowy (archetyp) |
## Wersje i rendycje  — | Typ | Numeracja | Statusy | Moment zamrożenia | Formaty |
## Dowody integralności — | Typ | Skrót | Pieczęć/znacznik/podpis (poziom) | Parametr polityki |
## Dystrybucja        — | Typ | Odbiorca (Party) | Kanał | Potwierdzenie |
## Retencja           — | Klasyfikacja | Okres | Zdarzenie startu | Disposition | Reguła (wersja) |
## Wstrzymania (legal hold) — | Powód | Zakres | Kto zakłada/zdejmuje |
## Decyzje (R/A/X)    — | Decyzja | Źródło |
## Uwagi              — założenia (X), przypadki brzegowe, parametry polityk zmiennych
```

## Wzorce i pułapki
- **Nadpisywanie pliku pod tą samą nazwą** — traci dowód. Każda zmiana to nowa wersja; zatwierdzona jest niezmienna.
- **Dokument jako źródło prawdy stanu** — „kwota z PDF-a” zamiast z Accounting, „termin z umowy” zamiast z Agreement. Dokument
  dokumentuje; stan pochodzi z właściwego archetypu.
- **Retencja liczona od daty utworzenia pliku** — termin biegnie od zdarzenia (zakończenie sprawy, koniec roku obrachunkowego).
- **Hash razem z plikiem w jednym polu bez wersji algorytmu** — zapisz algorytm i datę; algorytmy się starzeją.
- **Usuwanie po terminie bez sprawdzenia wstrzymań** — disposition zawsze pyta o aktywne LegalHold.
- **Format edytowalny jako archiwum** — dla długiego przechowywania osobna rendycja w formacie przeznaczonym do archiwizacji.
- **Poza archetypem:** „kto może zobaczyć umowę?” (autoryzacja), „co z niej wynika?” (Agreement), „jak ją zaksięgować?”
  (Accounting). Dokumentacja techniczna w repozytorium to docs-tech-writing.
- **Polityki zmienne jako parametry:** poziom podpisu i okres retencji zależne od typu i kraju → archetyp dostaje gotowe wartości.

## Kontrola jakości
- [ ] dokument, wersja, rendycja, dystrybucja i dyspozycja to osobne pojęcia
- [ ] wersja zatwierdzona jest niezmienna; zmiana to nowa wersja
- [ ] dowód integralności należy do wersji; poziom jako parametr polityki
- [ ] retencja z klasyfikacją, zdarzeniem startu, okresem i disposition; kategorie A/B/BE poprawnie (B i BE z liczbą lat)
- [ ] legal hold rozstrzygnięty (jest lub jawnie nie jest potrzebny)
- [ ] dokument odsyła do faktu biznesowego, nie jest źródłem prawdy stanu
- [ ] tabela mapowania i „Niezmapowane pojęcia” obecne; brak materialnych (X)

## Przykład (skrócony)
**Wejście:** „Firma usługowa zawiera umowy i spisuje protokoły odbioru z podpisami obu stron. Umowy mają aneksy. Klient
dostaje podpisaną wersję e-mailem. Dokumenty trzymamy 10 lat od zakończenia umowy [przykład]. Przy sporze nic nie można usuwać.”

```markdown
## Mapowanie pojęć
| umowa, protokół | Document (typy) + klasyfikacja | fakt biznesowy: umowa → Agreement |
| aneks | nowa DocumentVersion tego samego Document albo osobny Document powiązany | decyzja (A) |
| podpisana wersja | Record = zamrożona DocumentVersion + IntegrityEvidence | niezmienna |
| e-mail do klienta | Distribution (wersja, odbiorca z Party, kanał) | pozwala wykazać, co wysłano |
| 10 lat | RetentionRule (start: zakończenie umowy) | [przykład] |
| spór | LegalHold | blokuje disposition |
## Dowody integralności — umowa: skrót + podpis (poziom: parametr polityki, A); protokół: skrót + znacznik czasu
## Retencja — umowa | 10 lat [przykład] | zakończenie umowy | usunięcie po akceptacji | reguła v1
## Decyzje
| retencja 10 lat od zakończenia | R |
| aneks jako wersja czy osobny dokument | A: osobny dokument powiązany z umową |
| poziom podpisu | A: „To zależy” od wartości umowy → parametr |
| format archiwalny | X → hot spot (PDF/A?) |
## Niezmapowane pojęcia — termin płatności z umowy (→ Agreement), faktura za usługę (→ Accounting), klient (→ Party)
```

## Źródła
Odczyt 2026-10-17.
- Hay, „Enterprise Model Patterns: Describing the World (UML Version)”, Technics Publications, 2011 (ISBN 978-1-935504-05-4) —
  bierzemy: rozdział „Documents and other Information Resources” obejmuje zasoby informacyjne, ich relacje, pojęcia, dystrybucję
  i dispositions oraz media (zdjęcia, nagrania, e-maile). Ranga: pierwotne (opis wydawcy).
- ISO 15489-1:2016, „Records management — Concepts and principles” — bierzemy: cztery cechy wiarygodnego rekordu (autentyczność,
  rzetelność, integralność, użyteczność) jako listę kontrolną. Ranga: pierwotne (iso.org).
- ISO 16175-1:2020 i ISO 16175-2:2020 — bierzemy: tylko wskazanie aktualnych części jako dalszej lektury (treści nie opisujemy). Część 2 bywa opisywana jako specyfikacja techniczna (TS) — bez zastrzeżenia nie cytować jej jako normy;
  część 3 (2010) wycofana. Ranga: pierwotne, zweryfikowane częściowo.
- MoReq2010 (DLM Forum, 2011) — bierzemy: tylko wskazanie jako dalszej lektury; aktualność [niezweryfikowane] (następcy nie znaleziono).
  Ranga: pierwotne.
- ISO 19005-4:2020 (PDF/A-4, na bazie ISO 32000-2) — bierzemy: format przeznaczony do długiego przechowywania; wcześniejsze części
  -1 (2005), -2 (2011), -3 (2012). Ranga: pierwotne (iso.org).
- Rozporządzenie (UE) 2024/1183 z 11.04.2024 zmieniające eIDAS 910/2014 (w życiu od 20.05.2024) — bierzemy: kontekst dla pieczęci
  elektronicznej, znacznika czasu i poziomów podpisu (zwykły, zaawansowany, kwalifikowany), bez numerów artykułów. Ranga: wtórne.
  Skutki prawne do potwierdzenia przez prawnika, nie porada.
- Rozporządzenie Prezesa Rady Ministrów z 18.01.2011 w sprawie instrukcji kancelaryjnej, JRWA i instrukcji archiwalnej (Dz.U. 2011
  nr 14 poz. 67) — bierzemy: klasyfikacja JRWA, kategorie A, B + lata, BE + lata, liczenie od 1 stycznia roku następnego po
  zakończeniu sprawy. Ranga: pierwotne (ELI; status „obowiązujący”, zmiany [niezweryfikowane]). Dotyczy administracji; dla firm
  prywatnych — kontekst do potwierdzenia przez prawnika.

Rozdział na dokument, wersję, rendycję, dystrybucję i dyspozycję w tej postaci, dowody integralności jako parametr polityki oraz
LegalHold to wnioski modelowe fabryki, nie tezy autorów ani norm.
Opisane własnymi słowami; treść książek i norm nie była cytowana.
