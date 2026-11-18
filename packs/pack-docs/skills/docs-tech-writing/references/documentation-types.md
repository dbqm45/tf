# Documentation types and documentation for developers

## Diátaxis — four types, do not mix them
Two axes: whether the reader **acts** or **understands**, and whether they **learn** or **work** (apply what they already know).
| Type | Serves | Form | Avoid |
|---|---|---|---|
| **tutorial** (learning by doing) | a new person's first success | a guided lesson with a guaranteed outcome, steps in order, few explanations, a link to them | choices ("you can also…"), digressions, requiring knowledge the reader does not have |
| **how-to guide** (work, action) | a concrete goal of a person who already knows the basics | the title "How to <reach the goal>", prerequisites, steps, result | teaching from zero, describing all options |
| **reference** (work, knowledge) | checking a fact: a parameter, an error code, a configuration option | descriptive, in the order of the system's structure, complete, generated from the sources when possible | instructions and opinions |
| **explanation** (learning, knowledge) | understanding: why so, how it works, trade-offs | prose with context, the history of decisions (a link to the ADR), alternatives | steps to perform |
- A page that tries to be everything at once serves no one — split it and connect with links.
- The structure of a documentation site can follow these four types or the product areas with a split into
  types inside. Both work; consistency is what matters.

## The developer journey and documentation for developers
Stages: discovery → evaluation (does this solve my problem?) → **first success** → integration → production → maintenance.
- **Quick start**: from zero to a working call in a few minutes — requirements, installation, a test key or token,
  one working command or code fragment, the expected result, "what next". Measure the time to first success.
- **Authentication** on a separate page, with an example in every supported language and typical errors.
- **API reference** generated from the specification (OpenAPI, GraphQL schema — be-api-design); every endpoint with an example
  request and response, errors and limits. Tools: Redoc, Swagger UI, Scalar; SDKs and libraries — TypeDoc,
  Compodoc (Angular), Javadoc.
- **Error list**: code, meaning, causes, what to do — this is the page developers land on from a search engine.
- **Code examples**: complete (with imports), tested in CI (an example that does not compile is worse than none),
  without real secrets.
- **Platform support**: a matrix of supported versions (languages, browsers, systems) with the end-of-support date.

## Help and support content
- **Troubleshooting**: organized by the **symptom** the user sees ("Payment rejected with code
  402"), then the causes from the most common and the repair steps; at the end, how to collect data for a ticket (request
  identifier, version, logs without secrets).
- **FAQ** only for really frequent questions (from support data) and short answers with a link to the right
  documentation. An FAQ as a dumping ground for content without a home is a sign of bad structure.
- **Release notes** (for users) are something other than a CHANGELOG (for developers, every commit or change):
  what is new and what benefit it gives, what changed in behaviour, what needs to be done (migration, breaking changes, deprecation
  dates — be-api-design), known problems. The user's language, not task names.
- **In-product content** (hints, empty states, error messages) you write together with the designer (ux-feature-design,
  `content-and-ethics.md`).

## Other forms
White papers (problem, data, analysis, recommendation — for decision-makers, with reliable sources), case studies
(the customer's situation → solution → measured results, with the customer's consent), research reports (open methodology, data
to check), e-books (a longer guide to a topic). These forms usually belong to marketing content
(`technical-content-and-seo.md`).

## Sources
- D. Procida, [Diátaxis](https://diataxis.fr/); Google Developer Documentation Style Guide; Microsoft Writing Style Guide
- [roadmap.sh — Technical Writer](https://roadmap.sh/technical-writer) (types of technical content, developer docs,
  developer journey, API reference, troubleshooting, FAQ, release notes, help content, platform support, white papers,
  case studies)
Described in our own words.
