# Event Storming session scripts

## Logistics (an in-person session)
- **Unlimited modelling space**: an 8–10 m paper roll on the wall; no table in the middle, chairs against the wall (people standing = more energy).
- Plenty of sticky notes in the notation colours, thick markers (one idea per note, readable from 2 m).
- A legend on the wall — extended when you introduce a new element.
- Invitation: the session goal in one sentence, the time, "no preparation needed". Invite people with questions and people with answers; without decision-makers who intimidate the rest, or warn them about their role.
- The facilitator is the first in the room and leaves last (photographs the wall after each stage).

## Big Picture (about 4–6 h with breaks)
| Time | Step | What you say / do |
|---|---|---|
| 10' | Check-in, goal, rules | "Today we want to understand X. Everyone is partly right, no one completely." Show only the orange note and the hot spot. |
| 30' | Chaotic exploration | "Write down everything that happens in the business, in the past tense. We do not discuss — we write." |
| 45' | Enforcing the timeline | "Are these two notes the same thing? What came earlier?" Take duplicates down, write synonyms on the side. |
| 20' | Pivotal events | "After which event does the world look different?" Mark them clearly, split the timeline into chapters. |
| 20' | Swimlanes, actors, systems | Only now introduce the yellow and the wide pink notes. |
| 30' | Walkthrough + reverse narrative | One person narrates; the rest call "stop". Then a few fragments from the end. |
| 20' | Problems and opportunities | Hot spots + green notes; voting with 3 dots per person. |
| 20' | Emerging contexts | Outline areas with a shared language/responsibility. |
| 10' | Check-out | "What did you understand today that you did not know this morning?" |

## Process Level (2–3 h, one process)
1. Place Begin and End (if the process is known) or pivotal events (if we are discovering).
2. Lay out the events between them.
3. Introduce the grammar: for each event "what caused it?" → command + actor; "what did the actor need to know?" → read model; "what happens automatically afterwards?" → policy.
4. Check that the chain closes for every path, including error and rejection paths.
5. Collect the rules (yellow constraints) and branching questions.
6. The to-be layer: a different lane/colour, mark the differences and opportunities.

## Design Level (2–3 h, one context)
1. Take a fragment of the process from Process Level.
2. At each command ask: "what rule can reject this?" → a constraint; "what data is needed to check it?"
3. Group the constraints that must be consistent immediately → an aggregate candidate. Name it in business language (not "Manager", not "Data").
4. Ask about concurrency: "can two people do this at the same time? what then?" (ddd-tactical-design).
5. Add rejection and compensation events.
6. Note the read models and their sources.

## The remote version
- A board (Miro/Mural/FigJam) with prepared columns and a legend; everyone has their own "scratchpad" for chaotic exploration.
- Shorter blocks (max 90'), more frequent breaks, cameras on, chat for hot spots.
- A facilitator + a helper ("producer") to tidy the board.

## The asynchronous version with an agent
1. The agent asks about the goal and scope and proposes a format.
2. The user provides events in batches; the agent orders them and sends back the timeline with questions.
3. The agent proposes pivotal events and swimlanes as **[proposals]**.
4. After each step the board is written to a file; hot spots as a task list with the owner of the question.
