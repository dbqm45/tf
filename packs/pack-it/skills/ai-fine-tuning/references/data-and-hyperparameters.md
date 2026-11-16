# Dane, hiperparametry i narzędzia dostrajania

Fakty z dnia 2026-10-17 (wyszukiwanie; dokumentacji Hugging Face nie otwarto, bo strony były niedostępne
z środowiska pracy). Wartości traktuj jako **punkt startowy do sprawdzenia na własnym zbiorze**, nie regułę.

## Dane
- **Kolejność:** czyszczenie → deduplikacja → podział według jednostki → format czatu → próbka ręcznie.
- **Deduplikacja:** dokładna (skrót tekstu) i przybliżona (MinHash); Lee i in. (2022) znaleźli przybliżone duplikaty
  w popularnych zbiorach oraz nakładanie się zbioru treningowego z walidacyjnym. Deduplikuj także **między** treningiem
  a ewaluacją, bo to wyciek zawyżający wynik.
- **Podział:** po kliencie, rozmowie lub dokumencie źródłowym. Losowy podział wierszy wrzuca tę samą rozmowę
  do obu zbiorów.
- **Format czatu:** lista `messages` z rolami (`system`, `user`, `assistant`), renderowana szablonem czatu **tego**
  modelu (inny szablon = inny model niż przy serwowaniu). Strata tylko na odpowiedziach asystenta; w TRL służy do tego
  opcja `assistant_only_loss` [niezweryfikowane — nazwa z pamięci, sprawdź w dokumentacji wersji].
- **Etykiety:** zgodność oceniających (np. kappa Cohena) przy zadaniach subiektywnych; reguły oznaczania spisane;
  przykłady graniczne w osobnym zbiorze. Etykiety generowane modelem traktuj jak dane syntetyczne: próbka sprawdzona
  przez człowieka.
- **Ilość:** nie ma liczby „wystarczającej”; krzywa uczenia (25/50/100% danych) pokazuje, czy dane pomagają.
  Źródło wtórne radzi nie dostrajać, gdy zbiór ewaluacyjny ma poniżej ok. 100 przykładów [opinia, nie reguła].
- **Dane osobowe:** domyślnie wyklucz lub zanonimizuj przed treningiem. EDPB w opinii 28/2024 (grudzień 2024)
  stwierdza m.in., że model wytrenowany na danych osobowych nie jest automatycznie anonimowy, a uzasadniony interes
  wymaga testu trzech kroków (streszczenia kancelarii, 2026-10-17; opinii nie otwarto [niezweryfikowane]).
  Ocena skutków i podstawy: **arch-privacy-compliance**.

## Punkty startowe LoRA / QLoRA
| Parametr | Punkt startowy | Źródło i uwagi |
|---|---|---|
| warstwy | wszystkie macierze liniowe, w tym MLP | Thinking Machines, „LoRA Without Regret”: LoRA tylko na uwadze wypada gorzej, nawet przy tej samej liczbie parametrów (streszczenie z wyszukiwania 2026-10-17) |
| ranga `r` | 8–64 na start; więcej przy dużych zbiorach | domyślne `r=8` w PEFT [niezweryfikowane]; ranga ogranicza pojemność, więc przy dużym zbiorze zwiększ |
| `lora_alpha` | `alpha = 2r` jako częsta praktyka | samouczek apxml (2026-10-17); skala adaptera = alpha / r, z `use_rslora` alpha / sqrt(r) (dokumentacja PEFT, wyszukiwanie) |
| learning rate LoRA | ok. 10× większy niż w pełnym dostrajaniu | „LoRA Without Regret” (źródła wtórne: 10×, w krótkich przebiegach do ok. 15×); optymalny LR słabo zależy od rangi |
| learning rate QLoRA | rzędu 1e-4–2e-4 | z pracy QLoRA, z pamięci [niezweryfikowane] |
| dropout adaptera | 0–0,1 | praktyka [niezweryfikowane] |
| epoki | 1–3 | heurystyka; kończ po stagnacji walidacji |
| batch | mały efektywny batch bywa lepszy | LoRA gorzej znosi duże batche (Thinking Machines, wyszukiwanie) |
Pamięć: QLoRA ładuje model w 4 bitach (NF4), liczy w BF16; autorzy pokazali dostrajanie modelu 65B na jednej karcie 48 GB.
Ranga LoRA jest o 1–2 rzędy wielkości mniejsza niż rząd zmian w pełnym dostrajaniu (Biderman i in.), więc na zadaniach
wymagających dużo nowej wiedzy (ciągłe przedtrenowanie, kod, matematyka) LoRA uczy się mniej, ale też mniej zapomina.

## DPO
- Dane: kolumny `prompt`, `chosen`, `rejected`; TRL przyjmuje prompt jawny i niejawny, zaleca jawny.
- Start: `beta = 0,1` (zakres 0,1–0,5), learning rate o rząd lub dwa niższy niż w SFT, rzędu 5e-7–1e-6
  (przykłady dokumentacji EasyDeL i Liquid AI, wyszukiwanie 2026-10-17; dokumentacji TRL nie otwarto).
- Beta reguluje odejście od modelu odniesienia (kara KL). Zbyt wysoki LR lub zbyt niska beta psują model.
- DPO wykonuj po SFT na tej samej dziedzinie; pary muszą różnić się jakością, nie długością lub stylem.
- RLHF (model nagrody + PPO) bywa usuwany z bibliotek; w TRL 1.x ponoć usunięto PPO [niezweryfikowane].

## Narzędzia (stan wg wyszukiwania 2026-10-17, głównie źródła wtórne)
- **TRL + PEFT (Hugging Face):** SFT, DPO, adaptery; podstawowy wybór, gdy chcesz kontroli i zgodności z ekosystemem.
- **Unsloth:** szybkość i pamięć na jednej karcie; wtórne źródła deklarują oszczędność ok. 40% VRAM i 2–5× szybciej,
  ale liczby się wykluczają; wsparcie wielu GPU ograniczone [niezweryfikowane].
- **Axolotl:** konfiguracja w YAML, wiele GPU i węzłów (DeepSpeed, FSDP).
- **LLaMA-Factory:** szeroki zasięg modeli, interfejs WWW.
- **torchtune:** wg jednego źródła wygaszony w 2025 [niezweryfikowane].
- **API dostawców:** OpenAI wygasza samoobsługowe dostrajanie (nowi użytkownicy zablokowani; istniejące zadania
  do 2027-01-06 wg źródeł wtórnych) — sprawdź stronę dostawcy. Claude 3 Haiku na Amazon Bedrock miało dostrajanie
  (GA 2024-11-01, region Oregon); aktualny stan nieznany [niezweryfikowane]. Together AI i Fireworks oferują dostrajanie
  modeli otwartych (Fireworks z serwowaniem wielu adapterów LoRA na jednym modelu bazowym; źródła wtórne).

## Licencje wyników nauczyciela
- Anthropic: warunki zabraniają używania wyników do trenowania modeli konkurencyjnych wobec Anthropic (centrum pomocy Claude,
  wyszukiwanie 2026-10-17). OpenAI: podobny zakaz w warunkach (streszczenie wtórne; sprawdź aktualny dokument).
- Llama 3.1: licencja dopuszcza użycie wyników do ulepszania innych modeli, ale nazwa udostępnianego modelu ma zaczynać się
  od „Llama” i obowiązuje „Built with Llama” (streszczenie wtórne; Llama 3 miała zakaz).
- Modele na Apache 2.0 lub MIT zwykle takich ograniczeń nie mają; i tak przeczytaj licencję konkretnego modelu.
- Wyniki generowane maszynowo mogą nie podlegać prawu autorskiemu, lecz ograniczenia umowne nadal obowiązują
  (komentarz prawniczy; to nie porada prawna) — decyzję zatwierdza dział prawny.
