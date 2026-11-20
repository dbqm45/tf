# Reviewing a skill

Use this list when you take over a skill, review one in a pull request, or consider adopting one from outside the factory.
Answer each point in a sentence or two with evidence (a line of the skill, a scenario id, a gate result). A point you
cannot answer is a finding.

## Before reading the content
- **Origin and safety.** For a foreign skill run `python3 .tf/factory/skill_audit.py <dir>` first and read every script it
  ships. High or medium findings stop the review until they are explained (core-agent-security covers the adoption
  procedure and the human's consent).
- **Evidence it helps.** Is there a scenario file? Does the gate pass? Was a trial without the skill or a baseline run
  recorded? No evidence means the review judges text, not effect - say so.

## The checklist
1. **Purpose.** One task, stated in one sentence. Several independent jobs -> propose a split.
2. **Selection.** Does the description read as a "Use when ..." rule in users' words? Does the catalog name the neighbours it
   must not cover ("Not for ...")? Is there a `no-trigger` scenario for the closest neighbour?
3. **Inputs and outputs.** What does the skill expect (files, arguments, state of the repository) and what does it leave
   behind (files, a report, a verdict line)? What happens when an input is missing?
4. **Structure.** SKILL.md within the size limit; detail one level down in `references/`; long references with a table of
   contents; scripts for deterministic work, with a `Network:` line when they connect anywhere.
5. **What actually drives behaviour.** Mark the sentences that change what the model does by default. The rest is a candidate
   for removal (see slimming in SKILL.md). Rules without an example usually do less than one example.
6. **Reasons for key decisions.** A non-obvious rule (a limit, an order of steps, a ban) should say why, so the next editor does
   not remove it by accident. Look for a source or a factory measurement behind numbers.
7. **Cost of renaming.** List what depends on the skill's names: other skills citing its sections, roles and personas,
   hooks or scripts parsing its output lines, eval scenarios naming it as a neighbour. Renaming any of these is a breaking
   change for those dependents.
8. **Freshness.** `metadata.review` date set; external facts dated in `## Sources`; nothing that only held for an old version.

## Report shape
```
Skill: <name>   Gate: pass|fail (<date>)   Evidence: scenarios <n>, baseline <yes/no>
Findings:
- [blocking] <point> - <evidence> - <proposed change>
- [improve]  <point> - <evidence> - <proposed change>
Verdict: adopt | adopt after fixes | do not adopt
```

## Example
A skill `ops-log-triage` from another team: the audit is clean; it has 4 scenarios but none `no-trigger`, and its
description "Log helper" never matches users' wording ("why is the service throwing 502s"). Its script counts errors per
service and the counts go straight into incident notes, but there is no test against a hand-counted sample.

```
Skill: ops-log-triage   Gate: fail (no neighbour scenario)   Evidence: scenarios 4, baseline no
Findings:
- [blocking] selection - description "Log helper" - rewrite as "Use when service logs must be triaged for an error spike ..."
- [blocking] script output copied into notes - no test vs a hand-counted sample - add a test on a real log file first
- [improve]  reasons - limit "last 2000 lines" without a reason - state why or make it an argument
Verdict: adopt after fixes
```
