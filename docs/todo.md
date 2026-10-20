# TODO

## Tłumaczenie treści fabryki na angielski

Treść fabryki jest dziś po polsku. Chodzi o:
- skille (`SKILL.md`, `references/`) rdzenia i wszystkich nakładek;
- persony, role i cechy;
- prompty agentów wspólnych, tabelę routingu i kontrakt raportu (`core/factory/config.yaml`);
- komunikaty hooków i skryptów skilli kierowane do agenta.

Po co: żeby `tf language en` dawało w pełni angielską fabrykę, a nie tylko angielskie odpowiedzi przy polskich
instrukcjach (mieszany język w prompcie potrafi „przeciekać” do odpowiedzi).

Jak:
- nakładka po nakładce; pole `content_language` w `pack.yaml` mówi, w jakim języku jest treść nakładki;
- kolejność: rdzeń, `pack-docs`, potem pozostałe według potrzeb;
- odpowiednik `pack-editorial-pl` dla angielskiego (`pack-editorial-en`) i wpis w `language_packs` w
  `core/factory/config.yaml`.

Do rozstrzygnięcia wtedy:
- czy tłumaczenie zastępuje treść polską, czy obie wersje żyją równolegle (wtedy `build.py` i instalator wybierają
  wersję według `language`);
- czy nazwy pól metadanych skilli (`metadata.katalog`, `przeglad`, `slowa`, `widocznosc`) też zmieniają się na
  angielskie (zmiana publicznego API rdzenia — MAJOR).

Warunek gotowości: ewaluacje skilli (`tests/skill_evals`) przechodzą także na wersji angielskiej.

## Inne

- Przewodnik użytkownika (`PRZEWODNIK.md`, `FAQ.md` z claude-team-factory) nie został przeniesiony — opisywał jedną
  fabrykę bez nakładek. Napisać nowy, gdy będzie można ujawnić opis projektu.
- Baza wiedzy z rejestrem źródeł (`dom-ev-knowledge-base`, w pack-ev) ma ogólny mechanizm (`kb.py`) i dane EV.
  Rozważyć przeniesienie mechanizmu do rdzenia, a rejestrów źródeł do nakładek.
- Targety innych narzędzi niż Claude Code (Codex, Gemini CLI): `build.py` ma listę `TARGETS` i ustawienie projektu
  `targets`, zaimplementowany jest tylko target `claude`. Kolejny target = renderer agentów i instrukcji (`AGENTS.md`,
  `GEMINI.md`), mapa tierów na modele dostawcy i adaptery hooków. Fakty o formatach innych narzędzi sprawdzić
  w dokumentacji przed implementacją.
