# Conventional Commits 1.0.0 — the full specification (16 rules) and FAQ

> **Contents:** The 16 rules of the specification · Why use Conventional Commits (from the "Why Use… · FAQ (questions and answers in the original, with a comment) · Reading and parsing commits

Source: conventionalcommits.org/en/v1.0.0 (CC BY 3.0). The rules are given in their original English
wording (this is the normative text of the specification), with a comment where it helps.

## The 16 rules of the specification

1. "Commits MUST be prefixed with a type, which consists of a noun, `feat`, `fix`, etc., followed
   by the OPTIONAL scope, OPTIONAL `!`, and REQUIRED terminal colon and space."
2. "The type `feat` MUST be used when a commit adds a new feature to your application or library."
3. "The type `fix` MUST be used when a commit represents a bug fix for your application."
4. "A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of
   the codebase surrounded by parenthesis, e.g., `fix(parser):`"
5. "A description MUST immediately follow the colon and space after the type/scope prefix. The
   description is a short summary of the code changes, e.g., `fix: array parsing issue when
   multiple spaces were contained in string`."
6. "A longer commit body MAY be provided after the short description, providing additional
   contextual information about the code changes. The body MUST begin one blank line after the
   description."
7. "A commit body is free-form and MAY consist of any number of newline separated paragraphs."
8. "One or more footers MAY be provided one blank line after the body. Each footer MUST consist of
   a word token, followed by either a `:<space>` or `<space>#` separator, followed by a string
   value (this is inspired by the git trailer convention)."
9. "A footer's token MUST use `-` in place of whitespace characters, e.g., `Acked-by` (this helps
   differentiate the footer section from a multi-paragraph body). An exception is made for
   `BREAKING CHANGE`, which MAY also be used as a token."
10. "A footer's value MAY contain spaces and newlines, and parsing MUST terminate when the next
    valid footer token/separator pair is observed."
11. "Breaking changes MUST be indicated in the type/scope prefix of a commit, or as an entry in the
    footer."
12. "If included as a footer, a breaking change MUST consist of the uppercase text BREAKING
    CHANGE, followed by a colon, space, and description, e.g., `BREAKING CHANGE: environment
    variables now take precedence over config files`."
13. "If included in the type/scope prefix, breaking changes MUST be indicated by a `!` immediately
    before the `:`. If `!` is used, `BREAKING CHANGE:` MAY be omitted from the footer section, and
    the commit description SHALL be used to describe the breaking change."
14. "Types other than `feat` and `fix` MAY be used in your commit messages, e.g., `docs: update ref
    docs.`"
15. "The units of information that make up Conventional Commits MUST NOT be treated as
    case-sensitive by implementors, with the exception of BREAKING CHANGE which MUST be uppercase."
16. "BREAKING-CHANGE MUST be synonymous with BREAKING CHANGE, when used as a token in a footer."

**Comment on rule 13:** if `!` is in the prefix, `BREAKING CHANGE:` in the footer is
optional — the description after `:` alone can be enough as the description of the breaking change. There is no need to repeat it in the
footer if the description in the first line already explains it (see the example `feat!: send an email...` in
`SKILL.md`, without a footer).

**Comment on rules 15/16:** letter case does not matter for `type`, `scope`, `description` —
`Fix:` and `fix:` are equivalent for spec-compliant tools. The only exception is `BREAKING CHANGE`
(or `BREAKING-CHANGE`) in the footer, which MUST be upper case for tools to recognise it.

## Why use Conventional Commits (from the "Why Use Conventional Commits" section)

- "Automatically generating CHANGELOGs."
- "Automatically determining a semantic version bump (based on the types of commits landed)."
- "Communicating the nature of changes to teammates, the public, and other stakeholders."
- "Triggering build and publish processes."
- "Making it easier for people to contribute to your projects, by allowing them to explore a more
  structured commit history."

## FAQ (questions and answers in the original, with a comment)

**Q: How should I deal with commit messages in the initial development phase?**
A: "We recommend that you proceed as if you've already released the product. Typically somebody,
even if it's your fellow software developers, is using your software. They'll want to know what's
fixed, what breaks etc." — do not treat the early phase of a project as an exception to the convention.

**Q: Are the types in the commit title uppercase or lowercase?**
A: "Any casing may be used, but it's best to be consistent." — check which letter case convention
the repo already has (`git log`), and stick to it.

**Q: What do I do if the commit conforms to more than one of the commit types?**
A: "Go back and make multiple commits whenever possible. Part of the benefit of Conventional
Commits is its ability to drive us to make more organized commits and PRs." — do not try to cobble
one commit together with two types (e.g. `feat+fix:`); split it into two commits.

**Q: Doesn't this discourage rapid development and fast iteration?**
A: "It discourages moving fast in a disorganized way. It helps you be able to move fast long term
across multiple projects with varied contributors."

**Q: Might Conventional Commits lead developers to limit the type of commits they make because
they'll be thinking in the types provided?**
A: "Conventional Commits encourages us to make more of certain types of commits such as fixes.
Other than that, the flexibility of Conventional Commits allows your team to come up with their own
types and change those types over time." — the list of types is not closed; a project can have its own.

**Q: How does this relate to SemVer?**
A: "fix type commits should be translated to PATCH releases. feat type commits should be translated
to MINOR releases. Commits with BREAKING CHANGE in the commits, regardless of type, should be
translated to MAJOR releases."

**Q: How should I version my extensions to the Conventional Commits Specification?**
A: "We recommend using SemVer to release your own extensions to this specification (and encourage
you to make these extensions!)" — a project's extensions of the convention (e.g. its own list of types, scope
= ticket) should themselves be versioned with SemVer, if they are formally documented/published.

**Q: What do I do if I accidentally use the wrong commit type?**
A (for a type from the spec's list, chosen wrongly): "Prior to merging or releasing the mistake, we
recommend using git rebase -i to edit the commit history."
A (for a type outside the spec altogether): "In a worst case scenario, it's not the end of the world if a
commit lands that does not meet the Conventional Commits specification. It simply means that
commit will be missed by tools that are based on the spec."
— **in this environment:** `git rebase -i` is not available (see `SKILL.md`, the section "Fixing a wrong type") — treat this FAQ answer as a description of an ideal world; here you ask the user
first.

**Q: Do all my contributors need to use the Conventional Commits specification?**
A: "No! If you use a squash based workflow on Git lead maintainers can clean up the commit
messages as they're merged—adding no workload to casual committers."

**Q: How does Conventional Commits handle revert commits?**
A: "Conventional Commits does not make an explicit effort to define revert behavior. Instead we
leave it to tooling authors to use the flexibility of types and footers to develop their logic for
handling reverts." — for reverts check whether the repo already has its own convention (e.g. `type: revert`,
or the footer `Reverts: <sha>`), instead of guessing.

## Reading and parsing commits

The first line of a spec-compliant commit: `^(\w+)(\([^)]+\))?(!)?: (.+)$` — group 1 = `type`, 2 = `(scope)` (with the parentheses),
3 = `!` (breaking), 4 = `description`. Look for `BREAKING CHANGE:` / `BREAKING-CHANGE:` as a separate footer after a blank
line in the full message (`git log -1 --format=%B`), not only in the first line.

```bash
git log --format='%s'                  # first lines — quick classification by type
git log -1 --format='%B'               # the full message of the last commit — footers
git log --grep='^feat' --format='%s'   # feat commits (an approximation by the first line)
```
