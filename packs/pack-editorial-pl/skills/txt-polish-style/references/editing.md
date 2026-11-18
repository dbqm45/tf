# The editing workshop — principles and replacements

The overriding principle: **a good text is correct, short, concrete and guides the reader — only then does it sound nice.**
<!-- polish-lint: off -->

## 1. Simplification
| Instead of | Write |
|---|---|
| w celu | aby, żeby |
| z uwagi na fakt, że | ponieważ, bo |
| należy zaznaczyć, że / warto wspomnieć, że | (remove) |
| w ramach | podczas, przy, w |
| jest możliwe | można |
| dokonać analizy / przeprowadzić weryfikację / wykonać optymalizację | przeanalizować / zweryfikować / zoptymalizować |
| w związku z powyższym, w dniu dzisiejszym, niniejszym, przedmiotowy | dlatego, dziś, (remove), ten |
| posiadać (about things) | mieć |
- **One sentence = one thought.** More than 2–3 levels of subordination → split.
- A word in three consecutive sentences → rebuild the sentence (but **do not replace a technical term with a synonym**).
  In procedures, runbooks and specifications repeating a term is intended (the ASD-STE100 rules, the technical
  documentation skill from pack-docs) — there a fixed term beats variety.
- An adjective that adds nothing („ciekawy”, „nowoczesny”, „kompleksowy”) → remove.
<!-- polish-lint: on -->

## 2. Style
- **Active voice:** „Zespół wdrożył poprawkę.” instead of „Zostało wykonane wdrożenie poprawki.” Passive only when the doer
  is irrelevant or unknown („Plik zostaje usunięty po 30 dniach.”).
- **Concreteness:** „skróciliśmy czas odpowiedzi z 800 do 200 ms” instead of „nastąpiła optymalizacja wydajności”;
  „ponad 10 000 użytkowników” instead of „duża liczba użytkowników”.
- **Rhythm:** a short sentence = emphasis; a longer one = context. Several long ones in a row → split one.
- **Naturalness:** write the way you would explain it to a colleague at the desk — without official formulas and without marketing jargon.

## 3. Tone and perspective
| Perspective | When | Example |
|---|---|---|
| impersonal / imperative mood | instructions, runbooks | „Uruchom migrację.” / „Należy uruchomić…” — pick one |
| „ty” | guides, UI messages | „Możesz przywrócić wersję…” |
| „my” | team/company texts, ADR | „Wybraliśmy PostgreSQL, bo…” |
| neutral | reports, analyses | „System obsługuje…” |
Mixing („Użytkownik powinien… Możesz teraz… System umożliwia…”) is the most common error — unify it. Level of formality:
professional (documentation), semi-formal (articles), personal (blog) — one in the whole text.

## 4. Readability of instructions (text UX)
The reader always knows: **where they are** (context), **what to do** (action), **what will happen** (effect).
- Numbered steps, one step = one action; the condition before the action („Jeśli X, kliknij Y”).
- Operational verbs: kliknij, wybierz, wpisz, uruchom, sprawdź — instead of „można skorzystać z opcji”.
- No fog: „kliknij **Zapisz**, aby zakończyć” instead of „możliwe jest wykonanie operacji zapisu”.
- An error message: what happened + why (if known) + what to do. Without blaming the user.
- A button: verb + effect („Zapisz zmiany”, „Wyślij zaproszenie”), not „OK”/„Kliknij tutaj”.

## 5. Consistency (extended mode)
- Collect terms, proper names and abbreviations → one form in the whole (per the project glossary).
- Even out the level of detail of similar sections (one with an example, the other without → add or remove in both).
- Transitions: a section ends with what comes next, or the next one starts with the problem it solves.
- Uniform emphasis: button names always the same way (bold or quotation marks), code always in `kodzie`.

## 6. Imagery (premium mode, on request)
Sparingly and only when it strengthens: an image instead of a generality („reaguje, zanim zauważysz opóźnienie” instead of „działa szybko”),
stepping into the reader's situation, a before/after contrast („Wczoraj 10 minut. Dziś trzy kliknięcia.”), one short sentence after a long paragraph.

## 7. Heuristics
You read a sentence twice → rewrite it. A word can be removed without loss of meaning → remove it. It sounds official → make it human.
The reader does not know what to click → fix it. A paragraph adds nothing → shorten or remove it (with the author's consent, if it is substantive content).
