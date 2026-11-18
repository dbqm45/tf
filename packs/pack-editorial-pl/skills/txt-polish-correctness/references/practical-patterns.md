# Practical patterns — the most common errors in functional texts
<!-- polish-lint: ignore-file (the file contains deliberate error examples) -->

A quick catalogue for analysis and self-check. In a conflict, `spelling.md` and `punctuation.md` decide
(the RJP PAN rule set 2024, in force from 1.01.2026). The examples are chosen for documentation, descriptions and interfaces.
The wrong/right pairs and the rules are the Polish norm and stay in Polish; the English in parentheses says what a rule is about.

## Spelling — traps of writing together/separately
| Wrong | Correct | Note |
|---|---|---|
| napewno, wogóle, narazie, conajmniej, poprostu, odrazu, przedewszystkim, wkońcu | na pewno, w ogóle, na razie, co najmniej, po prostu, od razu, przede wszystkim, w końcu | wyrażenia przyimkowe piszemy rozdzielnie (prepositional phrases are written separately) |
| z pośród, z pod, z nad | spośród, spod, znad | przyimki złożone łącznie (compound prepositions are written together) |
| nie + imiesłów przymiotnikowy rozdzielnie („nie działający”) | niedziałający, niezapisany | łącznie (bez względu na znaczenie; rozdzielnie tylko przy przeciwstawieniu: „nie zapisany, lecz odrzucony”) (together, whatever the meaning; separately only in a contrast) |
| niechcę, niema | nie chcę, nie ma | `nie` z czasownikiem rozdzielnie (*nie* with a verb is written separately) |
| dlatego, że / dlatego że | oba poprawne | przecinek przed całym spójnikiem albo w środku — konsekwentnie (a comma before the whole conjunction or inside it — consistently) |

## Punctuation
- Przecinek przed: `że`, `który/-a/-e`, `aby`, `żeby`, `ponieważ`, `gdyż`, `jeśli`, `gdy`, `chociaż`, `ale`, `lecz`, `więc`.
  Przy spójnikach złożonych (`mimo że`, `chyba że`, `zwłaszcza że`, `tak że`) przecinek stawiamy przed całością.
  (A comma before these conjunctions; with a compound conjunction, before the whole of it.)
- Wtrącenie wydzielone z **obu** stron (przecinkami albo myślnikami). (A parenthetical is set off on both sides.)
- Bez przecinka przed pojedynczym `i`, `oraz`, `lub`, `albo`, `ani` w obrębie jednego zdania. (No comma before a single coordinating conjunction in one clause.)
- Imiesłów na `-ąc`, `-wszy` z określeniami wydzielamy przecinkami. (An adverbial participle with its modifiers goes between commas.)

## Typographic characters
| Character | Use | Spaces |
|---|---|---|
| hyphen (*łącznik*) `-` | compound words: biało-czerwony, e-mail, 2-krotnie | no spaces |
| en dash (*półpauza*) `–` | ranges: 2020–2026, s. 23–45, 10–15 zł | no spaces |
| dash (*myślnik*) `–` or `—` | a parenthetical, a pause in the sentence | a space on both sides; one form in one document |
| quotation marks (*cudzysłów*) `„…”` | quotations, button names in the text, irony | nested: `„… »…« …”` |
| ellipsis (*wielokropek*) `…` | one character (U+2026) | no space before |
No space before `, . : ; ! ?` or after an opening parenthesis. A space before a unit: `10 GB`, `5 min`; percent `20%` or `20 %`
— both are acceptable, consistency within the document matters. Thousands: `10 000` (non-breaking space), decimals with a comma: `2,5`.

## Grammar
- **Liczebnik + rzeczownik** (numeral + noun): 1 plik · 2–4 pliki · 5–21 plików · 22–24 pliki · 25+ plików (decyduje ostatnia cyfra poza 12–14; the last digit decides, with the teens as the exception).
- **Imiesłów przysłówkowy** wymaga tego samego podmiotu co zdanie główne (an adverbial participle needs the same subject as the main clause):
  ❌ „Uruchamiając skrypt, pojawił się błąd.” → ✅ „Po uruchomieniu skryptu pojawił się błąd.” / „Uruchamiając skrypt, zobaczyłem błąd.”
- **Biernik żeński zaimka** (accusative feminine of the pronoun): „tę decyzję”, „tę funkcję” (nie „tą”); „tą” to narzędnik: „z tą funkcją”.
- **Rekcja** (government): korzystać **z** czegoś · szukać **czegoś** · dotyczyć **czegoś** (nie „o coś”) · wpływać **na** coś.
- **Zaprzeczenie → dopełniacz** (negation → genitive): „nie ma konfiguracji”, „nie widzę błędu” (nie „nie widzę błąd”).
- **ilość / liczba:** ilość dla niepoliczalnych (ilość pamięci), liczba dla policzalnych (liczba użytkowników, plików, błędów). (*ilość* for uncountable, *liczba* for countable nouns.)

## Semantics and phraseology
| Error | Correct | Kind |
|---|---|---|
| pełnić rolę | odgrywać rolę / pełnić funkcję | contamination |
| cofnąć się do tyłu, wracać z powrotem, kontynuować dalej, okres czasu, potencjalna możliwość, fakt autentyczny, akwen wodny | cofnąć się, wracać, kontynuować, okres, możliwość, fakt, akwen | pleonasm |
| na dzień dzisiejszy, w dniu dzisiejszym | dziś, obecnie | officialese |
| w każdym bądź razie | w każdym razie / bądź co bądź | contamination |
| efektywny ↔ efektowny | skuteczny ↔ robiący wrażenie | paronyms |
| adresować problem | zająć się problemem, rozwiązać problem | calque (address) |
| zrobić sens, zrobić różnicę | mieć sens, mieć znaczenie | calque |
| dedykowany (moduł) | przeznaczony, osobny | calque (dedicated) — colloquial in IT, avoid in documentation |
| na końcu dnia | ostatecznie | calque |
| wspierać (format, przeglądarkę) | obsługiwać | calque (support) |
| aplikować (na stanowisko) | ubiegać się, zgłosić się | calque |

## Consistency
- One term for one concept in the whole document (per the project glossary — `docs/project/02-domain/glossary.md`).
- An abbreviation spelled out at first use: „Architecture Decision Record (ADR)”.
- One form of address: impersonal („Uruchom…” / „Należy…” — pick one) or „ty”; do not mix it with „Państwo”.
- Foreign names (products, buttons): one spelling in the whole text, button names in quotation marks or bold — consistently.

## Readability (indicative thresholds for functional prose)
| Measure | Target | Warning signal |
|---|---|---|
| average sentence length | 12–20 words in documentation, up to 24 in an article | > 30 words → split |
| paragraph | 2–5 sentences | > 8 sentences → split |
| subheading | every 200–400 words | 600+ words without a subheading |
| emphasis | ≤ 10–15% of the text | bold in every paragraph |
