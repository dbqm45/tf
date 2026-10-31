# AI w obsłudze dużego wolumenu spraw

Wzorzec złożony z elementów, które fabryka ma osobno (złoty zbiór i kalibracja — ai-evals; saga — ddd-tactical-design;
idempotencja — be-messaging-outbox). Opis S. Yegge'a („Counting House”, 2026-10) powstał z rozmów z firmami, bez
danych z wdrożeń — traktuj go jako projekt do sprawdzenia, nie wynik.

## 1. Tabela polityki per intencja
Każda intencja (typ sprawy) ma osobny próg autonomii:
| Próg | Co robi model | Kto decyduje |
|---|---|---|
| off | nic | człowiek |
| shadow | odpowiada równolegle do człowieka, odpowiedź oceniana, niewidoczna dla klienta | człowiek |
| assist | podpowiedź dla człowieka | człowiek |
| contain | odpowiada klientowi | model, bez zmian stanu |
| transact | zmienia stan przez orkiestrator | model w limicie polityki |

Awans intencji na wyższy próg tylko po ewaluacji na złotym zbiorze z ocen ludzi i po podpisach właścicieli
(operacje, finanse, prawo). To ta sama logika co „uprawnienia rosną z dowodem” w core-async-delegation §5.

## 2. Macierz pomyłek z kosztem
Trafność nie wystarcza. Dla intencji łatwych do pomylenia każda komórka poza przekątną ma koszt: pomyłka kierunku
do kolejki to co innego niż pominięta pomoc dla klienta w trudnej sytuacji. Dla wypłat liczy się precyzja, dla spraw
krzywdzących klienta — czułość. Porównujesz tę samą macierz dla ludzi (koszt błędów + koszt pracy), nie tylko model
z zerem błędów.

## 3. Model proponuje, orkiestrator wykonuje
- Model wydaje **intencję zapisu** w schemacie (np. `{"action": "refund", "order_id": …, "amount": …}`).
- Orkiestrator (kod) sprawdza uprawnienie na **żywym systemie źródłowym**, nie na kopii, którą czytał model; nadaje
  klucz idempotencji z pól żądania; zatwierdza automatycznie do progu z polityki, powyżej — człowiek.
- Wykonanie jako saga z akcjami kompensującymi i odczytem po zapisie.
- Odmowa z kodem przyczyny trafia do właściwej kolejki ludzi.
- Model nie ma poświadczeń do systemów i nie widzi PII (bramka tokenizująca PII odwracalnie).

## 4. Sędzia i złoty zbiór
Sędzia LLM tylko tam, gdzie zgadza się z ludźmi tak często jak ludzie między sobą, nigdy nie strojony na złotym
zbiorze (ai-evals, `references/zbiory-i-graderzy.md` §7). Złoty zbiór i ewaluacje są własnością firmy — to one
pozwalają zmienić model na tańszy.

Z artykułu bez wpisu: wątek „dobrostanu modelu”. Zostaje praktyka: prompt prawdomówny, bez gróźb i fałszywej
pilności, a model ma prawo do odmowy z kodem przyczyny i propozycją poprawki procedury.
