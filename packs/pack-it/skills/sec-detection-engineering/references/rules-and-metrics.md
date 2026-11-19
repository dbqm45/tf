# Details: the Sigma rule, the test and metrics

Contents: 1. Rule template · 2. Field values · 3. Repository structure and CI · 4. Technique card · 5. Metrics

## 1. Rule template (an illustration, the behaviour, not the tool name)
```yaml
title: Office launches PowerShell with an encoded command
id: 00000000-0000-4000-8000-000000000000   # [example] generate your own UUID
status: experimental
description: An Office process creates powershell.exe with a parameter that encodes the command.
references:
  - https://attack.mitre.org/techniques/T1059/001/
author: Detection team
date: 2026-10-17
tags:
  - attack.execution
  - attack.t1059.001
logsource:
  category: process_creation
  product: windows
detection:
  parent:
    ParentImage|endswith: ['\winword.exe', '\excel.exe']
  child:
    Image|endswith: '\powershell.exe'
    CommandLine|contains: ['-enc', '-EncodedCommand']
  condition: parent and child
falsepositives:
  - Company macros deploying configuration (a narrow exception by document path)
level: high
```
The `logsource` fields (`category`, `product`, `service`) are mapped automatically by converters; `definition` is informational.

## 2. Field values (Sigma Rules Specification 2.1.0, read 2026-10-17)
- `status`: `stable`, `test`, `experimental`, `deprecated`, `unsupported`.
- `level`: `informational`, `low`, `medium`, `high`, `critical`.
- `condition`: `and`, `or`, `not`, `1 of selection*`, `all of them`, parentheses; precedence from the weakest: `or`, `and`, `not`, `x of`.
- `tags`: lowercase letters, digits, `_`, `-`, namespaces after a dot (`attack.t1234`).
- `related` (with `id` and `type`: `derived`, `obsolete`, `merged`, `renamed`, `similar`) and `name` (for correlation).
- The `sigma check` command for validation: [unverified] (the sigma-cli README documents `sigma convert`, `sigma list`, `sigma plugin`).

## 3. Repository structure and CI
```
rules/<source>/<technique-or-behaviour>.yml
tests/positive/<rule-id>.json   # events that MUST raise an alert
tests/negative/<rule-id>.json   # normal-work events that MUST NOT raise an alert
pipelines/                        # field mapping onto the SIEM schema
```
CI stages: schema validation → a check of mandatory fields and `id` uniqueness → conversion → a positive and negative test
on the engine or in a query on test data → an artifact (the target queries). Deployment from the artifact, not by hand.
Test data without personal data (anonymized or from the lab).

## 4. Technique card (one per priority technique)
Technique (ID, ATT&CK version) · data source and its state · rules · last test (date, result, time to detect) ·
gaps · owner · next review date.

## 5. Metrics (definitions)
- **Time to detect** = alert time − time the technique was executed in the test; median and p90, not the mean.
- **Tested coverage** = priority techniques with a "detected" result in the last test / all priority ones.
- **False positives** = alerts closed as benign / all alerts of the rule in a window [example: 30 days].
- **Rule health**: the share with a test, a runbook and a review in the last 12 months.
