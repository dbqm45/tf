# Senior Frontend Engineer

Level: the owner of one feature/one repo from idea to production, a technical role model for more junior people
in the team. Lens: **one team, one application**.

The technical content from the original version of this file (Critical Rendering Path, Virtual DOM, SSR/hydration/RSC, Core Web
Vitals, Service Workers) has been moved to the technical skills — what stays here is **what we expect** from a Senior.

## Technical competencies — expected behaviours

| Area | A Senior can… | Knowledge in |
|---|---|---|
| Event loop, memory | **explain** why an operation blocks the main thread, and **diagnose** a leak (heap snapshot, detached nodes) — not only define the event loop | fe-web-platform `.claude/skills/fe-web-platform/references/rendering-pipeline.md` |
| Browser rendering | point out which CRP phase is the bottleneck (render-blocking CSS/JS, layout thrashing) and why we animate `transform`/`opacity` | fe-web-platform `.claude/skills/fe-web-platform/references/rendering-pipeline.md` |
| Performance | establish which metric (LCP/INP/CLS) is bad, find the cause in field data and verify the fix by measurement | fe-web-platform `.claude/skills/fe-web-platform/references/core-web-vitals.md` |
| Rendering model | choose CSR/SSR/SSG/ISR/RSC per route, recognize and fix a hydration mismatch, understand the cost of reconciliation vs signals | fe-architecture `.claude/skills/fe-architecture/references/rendering-models.md` |
| Offline/PWA | assess whether a service worker is needed, choose a cache strategy and a safe update | fe-web-platform `.claude/skills/fe-web-platform/references/service-workers.md` |
| Language and types | read/write types of medium complexity with ease; recognize when a type is more complicated than it is worth (an excess of generics is a smell, not a goal) | lang-typescript, lang-javascript |
| Framework | know the change model of their framework and its pitfalls (list keys, render purity, effects, signals/OnPush) | fw-angular, fe-architecture |
| Application architecture | **apply** a pattern to a named problem and **recognize the overuse** of a pattern | fe-architecture, eng-design-principles |
| Accessibility and security | deliver features compliant with WCAG AA and free of XSS by default, not "after the audit" | fe-web-platform, fe-architecture `references/security/` |
| Tests | write behaviour tests (not implementation tests) and match the test level to the risk | eng-testing, fe-architecture `references/testing/` |

## Mentoring and code review

At the Senior level, developing others becomes a real, assessed part of the job, not a side effect.

- **Code review** is effective when:
  - a comment points to a **concrete** problem and a **concrete** alternative (not "this is wrong");
  - it distinguishes **blocking** from **nice-to-have** (mark it e.g. `nit:`), and style disputes are settled by
    the formatter/linter, not a discussion in the PR;
  - it asks "why" instead of assuming bad intent — the author may have had context the reviewer does not see;
  - it concerns small changes (small PRs are a process decision — eng-continuous-delivery).
- **Mentoring** is effective when it leads the mentee to an **independent** solution (guiding questions, pair
  programming), not to the fastest solution by the mentor — otherwise the problem comes back without any growth in competence.
- **Feature ownership**: a Senior takes a feature to production together with observability (errors, metrics) and
  cleanup (feature flag removed, debt recorded).

## Senior vs Staff

A Senior optimizes, fixes and designs **within one application/team** and is the local quality role model.
When a decision concerns **many teams at once** (a shared design system, a security standard for a domain, tooling
for many repos) — that is already the Staff lens (`staff.md`).
