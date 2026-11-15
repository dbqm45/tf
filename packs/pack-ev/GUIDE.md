# pack-ev — przewodnik nakładki

## Start
`claude --agent iwona` — dyspozytorka EV: opisz problem zwykłym tekstem, a rozpozna warstwę (pojazd, ładowarka,
CSMS, roaming, energia, prawo), dobierze persony i skille. Konsultanci EV (`ev-consult-*`) odpowiadają na pytania
z innych nakładek (np. backend z pack-it przy protokole ładowania).

## Obsada faz (core-delivery-lifecycle)
Uzupełnienie `references/obsada-nakladek.md` skilla core-delivery-lifecycle — numeracja faz jak w SKILL.md.
Obowiązuje to, co jest zainstalowane (`.claude/catalog.md`).

- **0** — Iwona
- **1** — Patrycja + Iwona
- **2** — Oskar lub Roman
- **3** — Iwona + Patrycja, Kamil przy kryteriach
- **4** — Oskar (CSMS), Roman (roaming), Teodor (firmware), Elżbieta (energia), Regina (zgodność), Dawid (dane)
- **5** — Oskar + Kamil
- **6** — persona wg warstwy (Oskar, Roman, Teodor, Elżbieta, Dawid) + Kamil
- **7** — Nadia + Kamil, Regina przy zgodności
- **8** — Nadia
- **9** — Nadia + Kamil, Dawid (KPI)

Przegląd gotowości do produkcji (faza 7): Nadia i Kamil. Onboarding modelu urządzenia: `docs/project/vendors/`.
