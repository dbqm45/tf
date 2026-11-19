# Literature and the path from a paper to a prototype

## Searching for and reading a paper critically
1. **Scope:** formulate the question and search terms; go through surveys, then frequently cited and the newest papers.
   Record the queries, dates and inclusion criteria so that the review can be repeated. Searching for facts on the web:
   **core-source-research**.
2. **A preprint vs a peer-reviewed paper:** a preprint has not been peer-reviewed; check whether the published version changed.
3. **Claim → evidence.** List the main claims and for each: on what data, what metric, how many runs,
   what baseline. Control questions:
   - was the baseline tuned just as carefully;
   - were the spread and significance reported, or a single run;
   - was the test set used for selection; is contamination possible;
   - does the improvement come from the method, or from more compute or data;
   - do the ablations point to the element responsible for the gain;
   - are the code and the data available.
4. **Transferability:** do our data, scale and constraints (latency, cost) resemble the conditions in the paper.
5. **Replication:** before deployment, reproduce the key result on the paper's data (or at least on a small version of it).
   It failed — that is also a result; record the differences in configuration.
6. **Note:** one page per paper: the claim, the evidence, credibility (high/medium/low) with a reason, an idea for
   use.

## Projects in scientific domains (biology, chemistry, medicine, materials)
When the project's assumptions depend on scientific knowledge from outside computer science (e.g. cell degradation, drug interactions, clinical
data), the literature review and the analysis of data from scientific databases are a separate step before the model:
1. **Tool:** Claude Science (an Anthropic desktop application, public beta; literature and over 60 scientific
   databases, reproducible notebooks, a background reviewer of citations and numbers — product page claude.com/product/claude-science,
   accessed 2026-11-08) is run by a human; the factory agent has no programmatic access to it. Without it: search
   per **core-source-research** and domain databases through their APIs.
2. **What comes back to the repository is a record of the evidence, not a summary of the conversation:** for each finding, the thesis, the source (DOI or
   address, the version of the preprint or paper, the access date), the conditions (sample, method, scope) and the path to the notebook or
   script that reproduces the number. The notebook and the intermediate data go next to it (e.g. a research directory in the project record, docs/project/02-domain/badania/),
   large data — only a description of where to get it from.
3. **Check before use in the project:** numbers and dates in the record via
   `python3 .claude/skills/core-grounding/scripts/claims_check.py`, references via `grounding_check.py`; a finding
   without a reproducible source has the status [unverified] and does not go into the requirements or into the model's features.
4. Medical, legal and safety decisions based on such findings are approved by a domain expert, not by the agent.

## From a paper to a product prototype
1. Start from the product decision and a metric aligned with it, not from the method.
2. Compare the method with the baseline on **your own** data with a split corresponding to the use (temporal/group).
3. A small-scale pilot, then a budget for the full run (SKILL.md, step 9).
4. Check the deployment requirements: latency, cost per prediction, memory (**ai-model-optimization**), dependence
   on data that does not exist in production or arrives late.
5. **Offline → online:** offline validation on historical data; then shadow (the result computed, not used) and
   A/B with a business metric (**data-analysis**). The offline↔online difference comes from drift, a feedback loop or
   a metric not aligned with the goal — establish which one, and record it.
6. Handover to production: the model registry, monitoring, rollback thresholds (**ai-mlops**).
7. Fine-tuning large models and the choice of prompt/RAG/fine-tuning: **ai-fine-tuning**; evaluation of LLM features: **ai-evals**.

## Ethical review of the data
- origin and licence (may it be used for training, may it be used commercially), consents and the original purpose;
- personal data and special categories → **arch-privacy-compliance** (DPIA);
- representativeness: who is missing from the data, results per subgroup, risk of harm to groups;
- labels: who assigned them, under what conditions, inter-rater agreement;
- secondary use and misuse: what the result may serve beyond the intention.
