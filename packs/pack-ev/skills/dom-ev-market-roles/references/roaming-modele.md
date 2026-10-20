# Roaming: hub, peer-to-peer, hybryda

Źródło: `.claude/skills/dom-ev-charging/references/ocpi.md` §4–5 (import 2024–2025). Rzeczy spoza źródła: [do weryfikacji].

## Porównanie
| Cecha | Hub | Peer-to-peer (bilateralnie) | Hybryda |
|---|---|---|---|
| Liczba połączeń | jedno do huba | O(n×m) | hub + wybrani partnerzy |
| Umowy | z hubem (często wzorcowe) | z każdym partnerem | obie |
| Koszt pośrednika | opłata huba [do weryfikacji] | brak | tylko za ruch przez hub |
| Elastyczność cen i danych | ograniczona zakresem usług huba | pełna | pełna u największych partnerów |
| Rozliczenia | hub może agregować [do weryfikacji] | strony między sobą | zależnie od ścieżki |

## Kiedy co
- Mało partnerów, duży wolumen z każdym: P2P (brak opłat, własne warunki).
- Wielu partnerów po obu stronach, mały wolumen z każdym: hub.
- Rosnąca sieć: hybryda — duzi partnerzy bezpośrednio, reszta przez hub.

## Pytania do ustalenia przed integracją
1. Czy hub tylko przekazuje dane, czy też rozlicza? (zależy od usługi)
2. Który protokół hubu: OCPI czy OICP — wersje i moduły muszą się zgadzać z partnerem.
3. Czyją tożsamość widzi partner: `country_code` + `party_id` strony, nie huba (identyfikatory: `dom-ev-identifiers`).
4. Kto odpowiada za jakość danych Locations/Tariffs przy awarii po drodze: CPO jako właściciel, hub jako nośnik.

## Przykład
Operator z 3 dużymi eMSP i 40 małymi: 3 połączenia bezpośrednie (OCPI P2P), 40 przez hub — hybryda; w CSMS dwa kanały
publikacji tych samych Locations.
