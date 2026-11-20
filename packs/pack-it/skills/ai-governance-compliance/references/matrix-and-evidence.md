# Obligations matrix and evidence

The AI Act article numbers come from the text of Regulation (EU) 2024/1689 known from our own knowledge; EUR-Lex was
unavailable in the session of 2026-10-17 [unverified at the source]. Before quoting, check them in EUR-Lex. The application dates
of individual rows — the table in SKILL.md. This is not legal advice.

## Provider of a high-risk system
| Obligation | Art. | Evidence |
|---|---|---|
| A risk management system across the whole life cycle | 9 | a risk register, decisions on measures, test results |
| Data governance (quality, representativeness, biases) | 10 | a dataset card, a bias analysis report |
| Technical documentation | 11, Annex IV | a versioned document, a model card |
| Record-keeping (logs) | 12 | log configuration, the retention period |
| Transparency and instructions for the deployer | 13 | instructions for use |
| Human oversight | 14 | a description of the mechanisms, operator training, the ability to stop |
| Accuracy, robustness, cybersecurity | 15 | evaluation results (ai-evals), robustness tests (arch-threat-modeling) |
| A quality management system | 17 | procedures, roles |
| Conformity assessment, EU declaration, CE marking | 43, 47, 48 | the declaration of conformity, the assessment report |
| Registration in the EU database | 49 | the entry number |
| Post-market monitoring | 72 | a monitoring plan, metrics, reviews |
| Reporting serious incidents | 73 | a procedure, a notification template, deadlines |

## Deployer
| Obligation | Art. | Evidence |
|---|---|---|
| Use in accordance with the instructions, human oversight by trained persons | 26 | the instructions, a list of operators, training |
| Quality of the input data under the deployer's control | 26 | a description of the data sources |
| Keeping logs (at least 6 months, unless the law provides otherwise) | 26 | a log policy |
| Informing employees and the persons whom the decisions concern | 26 | the text of the notice |
| Fundamental rights impact assessment (FRIA): public bodies, entities providing public services and deployers of credit scoring or insurance pricing | 27 | a FRIA report |
| Reporting incidents to the provider and the authority | 26, 73 | a procedure |
| AI literacy (everyone) | 4 | a training plan, a list of participants |

## Transparency (Art. 50) and GPAI
- **Art. 50:** informing about interaction with AI (the provider of the system), marking synthetic outputs in a machine-readable
  format (the provider), disclosing deepfakes and text published on matters of public interest (the deployer).
- **GPAI (Art. 53):** the technical documentation of the model, information for integrators, a copyright policy,
  a public summary of the training data. **Systemic risk** (Art. 51, presumed with a large amount of training
  compute): model evaluation, adversarial testing, reporting serious incidents, cybersecurity (Art. 55).

## Deadlines for reporting a serious incident (Art. 73) [unverified at the source]
The rule: within 15 days of becoming aware; shorter for a widespread incident or one in critical infrastructure
(within 2 days) and in the case of a death (within 10 days). A human with a lawyer decides on the notification.

## Penalties (Art. 99) [unverified at the source]
Prohibited practices up to EUR 35 million or 7% of worldwide turnover; other obligations up to EUR 15 million or 3%; incorrect information
to authorities up to EUR 7.5 million or 1%; for SMEs the lower of the amounts.

## The list of evidence for `ai-compliance.md`
The inventory; the justification of the role and the class; the matrix with owners; the technical documentation; the model and dataset cards; the results of
evaluations and bias tests; a description of human oversight; the log configuration; the AI use policy; the training plan;
the incident procedure; FRIA/DPIA (if applicable); contracts with providers with compliance guarantees; the approval of the lawyer/DPO.
