# Technical content outside documentation: funnel, SEO and distribution

For blog articles, guides and comparisons that are meant to attract and convince a technical reader. The overriding
rule: **technical reliability before selling** — developers quickly reject content that promises more
than the product does.

## Reader and goal
- **Ideal customer profile** (which organization), **buyer persona** (who decides) and **reader persona**
  (who reads and implements — often a different person) — from research and sales data (proc-product-discovery).
- Every text has one goal and one reader intent: get to know the problem, compare solutions, implement a specific one.

## Content funnel
| Stage | Reader | Forms | Measure |
|---|---|---|---|
| **top** (awareness) | knows the problem, does not know the solutions | explanatory articles, trends, conceptual guides | traffic from search, reading time |
| **middle** (consideration) | compares approaches | comparisons, reference architectures, e-books, white papers | newsletter sign-ups, downloads, moving on to the documentation |
| **bottom** (decision) | chooses and implements | case studies, migration guides, quick start, the product's pricing and security | sign-ups, started trials |
- **Comparisons** fair: open criteria, data with a date and source, the weaknesses of your own product too; an outdated
  comparison with the competition is a legal and reputational risk (core-source-research).
- Gated content (e-books, reports) only when the value justifies handing over data; consent compliant with GDPR.
- **A call to action** at the end: one next step matched to the stage (documentation, trial), not five.
- Subtle selling: show the result and the time saved on a real example, without superlatives and advertising language
  (txt-polish-style, `ai-writing-traces.md`).

## SEO of technical content
- **Intent and keywords**: how people name the problem (search engine, communities, support tickets).
  Short phrases (e.g. "kubernetes") have a large volume and huge competition; long, specific phrases ("how to set
  a pod memory limit in kubernetes") — a smaller volume, a clear intent, a real chance. Search trends show
  growing topics.
- **Title**: concrete, with the reader's words, a promise consistent with the content; headings describe sections, they are not decoration.
- **Cluster structure**: a pillar page (a broad topic) links to detailed articles and the other way round.
- **Technical**: a canonical URL for content published in several places (e.g. a company blog and Dev.to — `canonical`
  points to the original), Open Graph metadata for previews in messengers, fast pages, structured data
  (fe-web-platform, `seo-public-pages.md`).
- **Inbound links** are earned with value: open source tools, reports with data, answers in communities.
  No buying links and no content farms.
- An SEO tool's topic coverage score is a hint — a text written for the metric instead of the reader loses both.

## Distribution
- The channels where the audience is: newsletter, communities (Reddit, Hacker News, Dev.to, product forums), GitHub
  (README, examples), LinkedIn, conferences. Every channel has its own rules — self-promotion without value is removed.
- Amplification: the team and experts share, partners quote, shorter versions for different channels; refreshing
  and republishing the best texts.
- Tracking: UTM parameters in links per channel (no personal data in the URL), conversions defined up front
  (sign-up, trial start) — analytics compliant with GDPR.
- Originality: you write the texts yourself; short quotes with attribution; a similarity check before publishing when
  the content was built from many sources.

## Sources
- [roadmap.sh — Technical Writer](https://roadmap.sh/technical-writer) (technical content marketing, buyer journey,
  ICP, funnel content, SEO keywords, pillar content, canonical, OpenGraph, backlinking, distribution, conversion
  tracking, subtle selling, call to actions, crafting titles)
Described in our own words.
