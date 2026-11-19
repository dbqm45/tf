# Risk register and uncertainty UX

## Risk register for an AI feature
| Risk | Scenario | Measure (examples) |
|---|---|---|
| hallucination | the model states an untrue fact with confidence | grounding in sources with a citation, refusal when data is missing, consistency evaluation |
| bias | worse results for a group of users or a language | evaluation by slices (language, segment), a review of examples |
| content safety | a harmful or inappropriate answer | filters, refusals, an adversarial set, escalation |
| privacy | personal data in prompts, logs or the vendor's data | minimization, anonymization, a data processing agreement (arch-privacy-compliance) |
| prompt injection | content from outside changes the model's behaviour | separation of data and instructions, minimal tool permissions (arch-threat-modeling) |
| vendor dependency | a change of version, price or withdrawal of the model | a pinned version, evaluation on a change, an exit plan |
| drift | quality drops because the data or the users' language changed | samples from traffic, alerts, periodic evaluation |
| regulatory class | the feature falls into a category with obligations | ai-governance-compliance establishes the classification and the obligations |

Every row: probability, effect, owner, review date. A risk without an owner does not exist.

## Uncertainty UX and human in the loop
1. **Expectations:** say at the start what the feature does and that it makes mistakes; call the result a "proposal" if it is one.
2. **Confidence:** show it only when it is calibrated (measured on the set); otherwise sources, citations
   and the possibility to check are better. A raw number "87%" without calibration is misleading.
3. **Degree of autonomy** by the cost of an error: suggestion → action after approval → action that can be undone → automatic.
4. **Fallback:** a path without AI (a form, contact with a human) always available and clearly visible.
5. **Correction:** editing the result with one gesture, "bad result" with a reason; corrections go to review and into the evaluation set
   (with consent and with privacy taken into account).
6. **Failure:** the error message says what happened and what next; the model does not apologize endlessly.
Guidelines: Microsoft HAX (four phases: initially, during interaction, when AI is wrong, over time) and Google PAIR (mental models,
explainability and trust, feedback and control, errors). Message copy: ux-content-design; flows: ux-feature-design.
