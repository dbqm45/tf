---
name: ai-fine-tuning
description: Użyj przy dostrajaniu modelu na własnych danych — prompt, RAG czy fine-tuning, dane, SFT i LoRA, DPO, destylacja, ewaluacja przed i po, licencje.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy rozważasz lub prowadzisz dostrajanie modelu językowego na własnych danych — drabina prompt, RAG, fine-tuning i kiedy dostrajanie pomaga (format, styl, wąskie zadanie, mniejszy tańszy model) a kiedy nie (brak wiedzy), zbieranie, czyszczenie i deduplikacja danych, podział na zbiory, formaty czatu, jakość etykiet, SFT, metody oszczędne (LoRA, QLoRA, PEFT) z punktami startowymi hiperparametrów, strojenie preferencji (DPO, przegląd RLHF), destylacja z większego modelu (licencje wyników modelu nauczyciela), ewaluacja przed i po na zamrożonym zbiorze, przeuczenie i zapominanie, licencje danych i modeli, prywatność, API dostawcy czy własne trenowanie (TRL, PEFT, Unsloth, Axolotl). Nie do metody ewaluacji (ai-evals), RAG (ai-rag), potoku MLOps (ai-mlops), hostowania modelu (ops-ai-inference), potoków danych (data-engineering), RODO (arch-privacy-compliance) ani zmniejszania modelu po treningu (ai-model-optimization)."
  slowa: "fine-tuning, finetuning, dostrajanie modelu, dotrenować model, własny model, LoRA, QLoRA, PEFT, SFT, DPO, RLHF, destylacja, distillation, nauczyciel uczeń, dane treningowe, zbiór treningowy, jsonl, chat template, rank, alpha, learning rate, przeuczenie, overfitting, catastrophic forgetting, zapominanie, Unsloth, Axolotl, TRL, Hugging Face, adapter, czy dotrenować czy RAG, mały model zamiast dużego"
---

# Dostrajanie modeli — od decyzji do porównania przed i po

Dostrajanie zmienia **zachowanie** modelu (format, styl, wąskie zadanie), a nie dodaje mu aktualnej wiedzy.
Skill prowadzi od decyzji „czy w ogóle” do ewaluacji. Metodę oceny opisuje **ai-evals**, RAG — **ai-rag**,
potok produkcyjny — **ai-mlops**, serwowanie wyniku — **ops-ai-inference** (`.claude/skills/ops-ai-inference/SKILL.md`).

## Procedura
1. **Zbiór ewaluacyjny najpierw.** Zanim cokolwiek trenujesz, zbierz zamrożony zbiór z zadaniami z produkcji
   (metoda: **ai-evals**), policz wynik modelu bazowego z dobrym promptem. Bez tego „lepiej” nic nie znaczy.
2. **Drabina decyzji** — idź od najtańszego szczebla i schodź niżej dopiero z dowodem z zbioru z kroku 1:
   | Objaw | Pierwszy ruch |
   |---|---|
   | model nie zna faktów firmy, zmyśla, wiedza się zmienia | RAG (**ai-rag**), nie dostrajanie |
   | zły format, ton, niestabilne wyjście | lepszy prompt, przykłady w promptcie, structured output (**eng-llm-features**) |
   | prompt jest długi i drogi, a zadanie wąskie i powtarzalne | fine-tuning małego modelu |
   | opóźnienie lub koszt za duże przy dużym modelu | destylacja lub fine-tuning mniejszego modelu |
   | styl lub preferencje trudne do opisania, łatwe do porównania | SFT, potem ewentualnie DPO |
   Fine-tuning i RAG się nie wykluczają: dostrojony model może lepiej czytać wstawiony kontekst.
3. **Dane** (szczegóły: `references/dane-i-hiperparametry.md`):
   - źródło i podstawa prawna: dane osobowe bez podstawy odpadają, licencja źródła zapisana (krok 8);
   - czyszczenie (kodowanie, puste i ucięte odpowiedzi, szablony), **deduplikacja** dokładna i przybliżona;
   - **podział według jednostki** (klient, rozmowa, zgłoszenie), nie losowych wierszy, i dopiero po deduplikacji;
   - format czatu zgodny z szablonem modelu (`messages` z rolami), strata liczona tylko na odpowiedziach asystenta;
   - jakość etykiet ważniejsza niż liczba: przejrzyj losową próbkę ręcznie, przy ocenie ludzkiej dwóch oceniających
     i zgodność między nimi.
   Zacznij od małego zbioru i narysuj krzywą uczenia (25/50/100% danych); płaska krzywa oznacza, że problemem
   są dane lub zadanie, nie ich ilość.
4. **Metoda:**
   - **SFT** (uczenie na parach wejście → pożądane wyjście) to domyślny start.
   - **LoRA/QLoRA (PEFT)** trenuje małe adaptery zamiast wszystkich wag; QLoRA robi to na modelu zamrożonym w 4 bitach.
     Tańsze w pamięci i szybkie do iteracji. Punkty startowe: `references/dane-i-hiperparametry.md`.
   - **Pełne dostrajanie** tylko gdy LoRA o wysokiej randze mierzalnie nie wystarcza, a masz pamięć i dużo danych.
   - **DPO** (pary „lepsza / gorsza odpowiedź”, bez osobnego modelu nagrody) po SFT, gdy cel to preferencje.
     RLHF z modelem nagrody i uczeniem ze wzmocnieniem jest cięższy; sięgaj po niego z zespołem, który go utrzyma.
5. **Destylacja** (nauczyciel → uczeń): duży model generuje odpowiedzi na **prawdziwe prompty z domeny**, odfiltruj je
   weryfikatorem lub sędzią, uczeń trenuje SFT-em. Przed startem sprawdź warunki użycia wyników nauczyciela (krok 8)
   i czy prompty nie zawierają danych osobowych.
   Destylacja **agenta**: zamiast SFT na pełnych trajektoriach nauczyciela poprawiaj tylko błędne tury ucznia (korekta
   on-policy, jak DAgger) i oceniaj w docelowym harnessie — w jednym preprincie pełne trajektorie obniżyły wynik
   z 78% do 63%, a korekta tur dała ok. 80% (źródło niżej; jedno badanie, ramiona różniły się też danymi).
6. **Trening:** zapisuj konfigurację, ziarno, wersję danych (skrót) i bibliotek; jedna zmiana na przebieg.
   Obserwuj stratę treningową **i** walidacyjną oraz metrykę zadania. Rozjazd (trening spada, walidacja rośnie lub stoi)
   to przeuczenie: mniej epok (zwykle 1–3 [heurystyka]), więcej danych, niższy learning rate, mniejsza ranga.
7. **Ewaluacja przed i po** na tym samym zamrożonym zbiorze (**ai-evals**): model bazowy z promptem vs dostrojony,
   wynik na zadaniu **i** na zbiorze regresji ogólnych umiejętności (zapominanie katastroficzne: model świetny w zadaniu,
   gorszy gdzie indziej). Zbiór ewaluacyjny nigdy nie trafia do treningu; sprawdź też wyciek (przybliżone duplikaty
   między treningiem a ewaluacją). Dostrojony model wygrywa dopiero, gdy poprawa przekracza próg ustalony **przed** treningiem.
8. **Licencje i prywatność:**
   - **dane:** licencja i prawa do użycia w treningu; dane klientów i pracowników — podstawa, minimalizacja,
     anonimizacja przed treningiem (**arch-privacy-compliance**); model może zapamiętać dane i trudno je z niego usunąć;
   - **model bazowy:** licencja pozwala na dostrajanie i dystrybucję pochodnej? Wymogi nazewnictwa lub progi użytkowników;
   - **wyniki nauczyciela:** regulaminy dostawców API często zabraniają trenowania na wynikach modeli konkurencyjnych;
     licencje otwartych modeli bywają różne. Czytaj aktualny tekst, nie pamięć (`references/dane-i-hiperparametry.md`).
9. **Gdzie trenować:** API dostawcy (mało pracy, brak wag, uzależnienie, zmienna dostępność) czy własne trenowanie
   (TRL + PEFT, Unsloth, Axolotl — kontrola i wagi, ale GPU i utrzymanie). Stan oferty sprawdź w dokumentacji
   w dniu decyzji; zapisz decyzję jako ADR z kosztem. Wdrożenie i wersjonowanie adaptera: **ai-mlops**, **ops-ai-inference**.

## Wynik
Karta dostrajania (w repo, np. `docs/project/…`): Decyzja (szczebel drabiny, dlaczego) · Dane (źródło, rozmiar, skrót,
podstawa prawna) · Metoda i hiperparametry · Wynik przed i po (zadanie + regresja) · Ryzyka i licencje · Co dalej.

## Przykład
Wejście: „Klasyfikator zgłoszeń Fakturki (12 kategorii) na dużym modelu API kosztuje 2 400 zł miesięcznie i trwa 3 s.”
Wynik karty:
- **Decyzja:** zadanie wąskie, prompt już dobrany, brak braków wiedzy → fine-tuning małego modelu 8B zamiast RAG.
- **Ewaluacja:** 400 zgłoszeń ze zbioru zamrożonego (podział po kliencie), baseline: duży model 0,87 F1 [liczby przykładowe].
- **Dane:** 5 200 zgłoszeń po deduplikacji (z 6 100), dane osobowe zamaskowane, etykiety z próbki 100 sztuk sprawdzone.
- **Metoda:** QLoRA, wszystkie warstwy liniowe, 2 epoki; próg: ≥ 0,85 F1 i brak spadku na zbiorze regresji.
- **Wynik:** 0,88 F1, 0,4 s [przykład]; zapisane w karcie razem ze skrótem zbioru i konfiguracją.

## Checklista
- [ ] zamrożony zbiór ewaluacyjny i wynik bazowy policzone przed treningiem
- [ ] drabina prompt → RAG → fine-tuning przejdzie się z dowodem na każdym szczeblu; brak wiedzy nie jest powodem do dostrajania
- [ ] dane: podstawa prawna, deduplikacja, podział po jednostce, format zgodny z szablonem, próbka etykiet sprawdzona
- [ ] hiperparametry z uzasadnionego punktu startowego, jedna zmiana na przebieg, konfiguracja zapisana
- [ ] ewaluacja przed i po, także regresja ogólnych umiejętności; próg ustalony wcześniej
- [ ] licencje: dane, model bazowy, wyniki nauczyciela; dane osobowe zanonimizowane
- [ ] decyzja API vs własne trenowanie z kosztem; adapter wersjonowany

## Materiały dodatkowe
- `references/dane-i-hiperparametry.md` — przygotowanie danych, punkty startowe LoRA/QLoRA/DPO ze źródłami, narzędzia, licencje.

## Źródła
- Dettmers i in., „QLoRA” (arXiv 2305.14314, 2023) — NF4, podwójna kwantyzacja, optymalizatory stronicowane, model 65B na
  jednej karcie 48 GB; wyszukiwanie 2026-10-17, treści pracy nie otwarto [niezweryfikowane].
- Rafailov i in., „Direct Preference Optimization” (NeurIPS 2023) — DPO bez modelu nagrody i uczenia ze wzmocnieniem;
  streszczenie z wyszukiwania 2026-10-17.
- Biderman i in., „LoRA Learns Less and Forgets Less” (TMLR 2024) — LoRA zapomina mniej, ale też uczy się mniej
  niż pełne dostrajanie, „nie zawsze”; streszczenia z wyszukiwania 2026-10-17.
- Lee i in., „Deduplicating Training Data Makes Language Models Better” (ACL 2022) — duplikaty, nakładanie się
  zbioru treningowego i walidacyjnego; wyszukiwanie 2026-10-17.
- OpenAI wygasza samoobsługowe dostrajanie (komunikat z maja 2026, daty szczegółowe z wtórnych źródeł),
  wyszukiwanie 2026-10-17 [niezweryfikowane — sprawdź stronę dostawcy].
- Yu i in. (Salesforce AI), arXiv:2609.09134, preprint v1 z 8.09.2026, omówiony przez J. Wasowskiego („Model–Harness
  Fit: Why A Better Teacher Makes A Worse Agent”, Medium, ok. 12.10.2026); preprintu nie otwarto, liczby z artykułu
  [niezweryfikowane] — destylacja agenta, dopasowanie modelu do harnessu.
Opisane własnymi słowami.
