# A surrogate model in optimization and a hypothesis register

## 1. A surrogate model in an optimization loop
A fast model (e.g. a network) replaces an expensive simulator, and an algorithm searches it for the best design:
1. **Augmentation and the split:** examples from augmentation (reflection, rotation) go into the same set as the original,
   otherwise the test result is inflated (`leakage-and-splits.md`). Averaging the predictions for symmetric versions
   at test time is a cheap gain.
2. **Optimization searches out the model's errors to its own advantage.** The winner always looks better than it is. You check the result
   with the real simulator or an experiment, and the report gives **both numbers**: predicted and measured.
3. **A target outside the range of the training data** (including a physically impossible one) gives a confident, wrong answer. First you compute
   the feasibility limit, then you search.
4. **An evolutionary algorithm:** too large a mutation turns the search into random drawing; the operators' parameters are also
   hyperparameters to check.
Source: A. Janmohamed, "How I Recreated a Research Paper…" (2026-10-22); the author's numbers [unverified].

## 2. A hypothesis register as a graph with verdicts
- A hypothesis that cannot be attached to a node of the ontology (a mechanism, a violated assumption, who is on the other
  side) is dropped before an expensive experiment.
- **A node's status follows from the experiment results** (confirmed / buried), not from the author's declaration.
- A buried node has a **reopening condition** recorded in advance (a new construction, an independent confirmation) —
  without it the team comes back to the same ideas every quarter.
- The record "tried, it failed this way" has the scope and conditions of the experiment. The broader the claim, the more
  independent failures are needed to reject it.
- Gaps are shown by the topology of the graph (families without mechanisms), not by a question to the model.
- A simple implementation: SQLite with the tables `nodes` and `edges` (the edge key = the whole triple), an in-memory graph for
  reading only. The choice of the ontology's backbone decides which questions are cheap.
