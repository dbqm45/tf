# A business brief without a solution

## Remove
names of modules/contexts/services as the structure of the text · who owns which data · integration mechanisms
("sends an event", "synchronises", API) · pattern names (aggregate, saga, CQRS) · the core/supporting/generic classification ·
the topology (how many services, which database) · information about which files the brief was made from.
Warning verbs: *sends, synchronises, owns, calls, publishes, stores in*.

## Keep
what the company does, for whom and why customers pay · where it earns, where it loses, what costs it money · the rules of the game (contracts, penalties, law) ·
what the organisation can already do (capabilities described as people's activities) · the business vocabulary · the scale (numbers, seasonality).

## Mirror test (mechanically)
1. List the headings and main nouns of the brief. 2. List the names of the modules/contexts from the map. 3. If the sections of the brief correspond
1:1 to the boxes of the map or the names overlap — rewrite the brief around **business activities** (e.g. "winning a contract", "settlement"),
not around modules. 4. Repeat.

## Invariance test
Would the brief sound the same for a monolith, for 20 microservices and for a company run on paper? If not — it contains a solution.
