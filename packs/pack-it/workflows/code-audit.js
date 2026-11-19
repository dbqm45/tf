export const meta = {
  name: 'code-audit',
  description: 'Full code audit (skill eng-code-audit): inventory, parallel reviews, ranking in code, report. Arguments: the scope approved by the human.',
  phases: [
    { title: 'Inventory', detail: 'one cheap executor: stack, modules, hotspots, tools, available skills' },
    { title: 'Reviews', detail: 'one executor per dimension, in parallel' },
    { title: 'Ranking', detail: 'duplicates, risk × reach ÷ cost, blockers, hypotheses — in code, without a model' },
    { title: 'Report', detail: 'a file in docs/project/07-review/ per the skill\'s template' },
  ],
}

// Arguments (the human approves the scope in step 1 of the eng-code-audit skill, before anything runs):
//   {date: 'YYYY-MM-DD', dimensions: [...], depth: 'quick'|'standard'|'full', limit: N, modules: [...],
//    exclude: [...], executors: {dimension: 'agent-type'}}
// limit = the most executor calls (reviews + verifications); the inventory and the report do not count.
const DIMENSIONS = {
  architecture: { agent: 'architect', skills: ['arch-quality-attributes', 'eng-module-depth', 'ddd-connascence-analysis'] },
  security: { agent: 'security-reviewer', skills: ['sec-appsec-devsecops', 'be-auth-security', 'arch-threat-modeling'] },
  quality: { agent: 'specialist', skills: ['eng-tech-debt-audit', 'eng-clean-code'] },
  tests: { agent: 'specialist', skills: ['qa-test-design', 'qa-regression'] },
  accessibility: { agent: 'specialist', skills: ['ux-accessibility'] },
  usability: { agent: 'specialist', skills: ['ux-feature-design'] },
  performance: { agent: 'specialist', skills: ['fe-web-platform', 'fe-architecture'] },
  legal: { agent: 'specialist', skills: ['arch-eu-product-law', 'arch-privacy-compliance', 'sec-eu-regulations'] },
}
const DEEP = ['architecture', 'security']   // full: these dimensions on opus
const COST = { S: 1, M: 2, L: 4 }

const a = args || {}
if (!/^\d{4}-\d{2}-\d{2}$/.test(a.date || '')) throw new Error('args.date (YYYY-MM-DD) is required: the script cannot read the clock')
const unknown = (a.dimensions || []).filter(d => !DIMENSIONS[d])
if (unknown.length) throw new Error(`unknown dimensions: ${unknown.join(', ')} (known: ${Object.keys(DIMENSIONS).join(', ')})`)
if (!(a.dimensions || []).length) throw new Error('args.dimensions is empty: the human chooses the dimensions first')
const depth = a.depth || 'standard'
const limit = Number.isInteger(a.limit) ? a.limit : a.dimensions.length
const scope = [
  a.modules && a.modules.length ? `Modules: ${a.modules.join(', ')}.` : 'Modules: the whole repository.',
  a.exclude && a.exclude.length ? `Do not touch: ${a.exclude.join(', ')}.` : '',
  'You do not change the code. You do not run active scans against running systems.',
].filter(Boolean).join(' ')
const dir = 'docs/project/07-review'
const notChecked = []

phase('Inventory')
const needed = [...new Set(a.dimensions.flatMap(d => DIMENSIONS[d].skills))]
const inventory = await agent(
  `Stage 0 of the code audit (skill eng-code-audit, section 2) — a cheap inventory for all reviewers. ${scope}\n` +
  `Do steps 1–5 of section 2 of the skill (stack, hotspots, dependency graph, project tools, module map) and save ` +
  `the result to ${dir}/${a.date}-code-audit-inventory.md. No global installs; a missing tool is "not checked".\n` +
  `Also check which of these skills are installed (the file .claude/skills/<name>/SKILL.md): ${needed.join(', ')}.`,
  {
    label: 'inventory', phase: 'Inventory', model: 'haiku', effort: 'low',
    schema: {
      type: 'object',
      properties: {
        path: { type: 'string' }, stack: { type: 'string' },
        modules: { type: 'array', items: { type: 'string' } },
        missing_tools: { type: 'array', items: { type: 'string' } },
        skills_present: { type: 'array', items: { type: 'string' } },
      },
      required: ['path', 'skills_present'],
    },
  })
if (!inventory) throw new Error('inventory agent failed — nothing to review against')
const present = new Set(inventory.skills_present)
for (const t of inventory.missing_tools || []) notChecked.push(`tool: ${t}`)

const runnable = []
for (const d of a.dimensions) {
  const skills = DIMENSIONS[d].skills.filter(s => present.has(s))
  const missing = DIMENSIONS[d].skills.filter(s => !present.has(s))
  if (!skills.length) notChecked.push(`${d}: missing skills ${missing.join(', ')} (overlay not installed)`)
  else runnable.push({ key: d, skills, missing })
}
const reviewed = runnable.slice(0, limit)
for (const d of runnable.slice(limit)) notChecked.push(`${d.key}: over the executor limit (${limit})`)
if (runnable.length > limit) log(`Limit ${limit}: skipped dimensions ${runnable.slice(limit).map(d => d.key).join(', ')}`)

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' }, file: { type: 'string' }, line: { type: ['integer', 'null'] },
          risk: { type: 'integer', minimum: 1, maximum: 4 }, reach: { type: 'integer', minimum: 1, maximum: 3 },
          cost: { type: 'string', enum: ['S', 'M', 'L'] }, evidence: { type: 'string' }, proposal: { type: 'string' },
          blocker: { type: 'string', enum: ['', 'leak', 'authz', 'legal'] },
        },
        required: ['title', 'file', 'risk', 'reach', 'cost', 'evidence', 'proposal', 'blocker'],
      },
    },
  },
  required: ['findings'],
}

const results = await pipeline(reviewed, d => agent(
  `Code audit, dimension: ${d.key}. ${scope}\nInventory (facts for everyone, do not read the repository from scratch): ` +
  `${inventory.path}.\nLoad the skills: ${d.skills.join(', ')}` +
  (d.missing.length ? ` (unavailable: ${d.missing.join(', ')} — record this in the findings as a limitation)` : '') + '.\n' +
  `Question: what are the most important problems of this dimension? At most 10 findings. Each with evidence: file:line, a command ` +
  `result or a quote. Risk 1–4, reach 1–3, fix cost S/M/L. The blocker field: "leak" (data or a secret), ` +
  `"authz" (a bypass), "legal" (an obligation with a deadline), otherwise empty. No significant problems is a correct ` +
  `result — an empty list; do not add findings for volume.`,
  {
    label: `review:${d.key}`, phase: 'Reviews', schema: FINDINGS,
    agentType: (a.executors || {})[d.key] || DIMENSIONS[d.key].agent,
    ...(depth === 'full' && DEEP.includes(d.key) ? { model: 'opus' } : {}),
  }).then(r => r ? r.findings.map(f => ({ ...f, dimension: d.key })) : (notChecked.push(`${d.key}: the executor returned no result`), [])))

phase('Ranking')
// The same cause = the same place (file:line); without a line — the file and the title. The most cautious values of the duplicates.
const merged = new Map()
for (const f of results.filter(Boolean).flat()) {
  const key = f.file ? `${f.file}:${f.line ?? f.title.toLowerCase()}` : `?:${f.title.toLowerCase()}`
  const m = merged.get(key)
  if (!m) { merged.set(key, { ...f, dimensions: [f.dimension], evidence: f.evidence ? [f.evidence] : [] }); continue }
  m.dimensions = [...new Set([...m.dimensions, f.dimension])]
  m.risk = Math.max(m.risk, f.risk); m.reach = Math.max(m.reach, f.reach)
  if (COST[f.cost] > COST[m.cost]) m.cost = f.cost
  if (f.evidence && !m.evidence.includes(f.evidence)) m.evidence.push(f.evidence)
  if (f.blocker && !m.blocker) m.blocker = f.blocker
}
const all = [...merged.values()].map(f => ({ ...f, score: f.risk * f.reach / COST[f.cost] }))
all.forEach(f => delete f.dimension)
const hypotheses = all.filter(f => !f.file || !f.evidence.length)
const proven = all.filter(f => f.file && f.evidence.length)
const byScore = (x, y) => y.score - x.score || y.risk - x.risk
let blockers = proven.filter(f => f.blocker).sort(byScore)
let ranking = proven.filter(f => !f.blocker).sort(byScore)

if (depth === 'full') {   // full: one sceptic per blocker and per top-10 finding, within the limit
  const budgetLeft = Math.max(0, limit - reviewed.length)
  const toCheck = [...blockers, ...ranking.slice(0, 10)]
  if (toCheck.length > budgetLeft) log(`Verification: ${budgetLeft} of ${toCheck.length} findings (executor limit)`)
  const checked = await parallel(toCheck.slice(0, budgetLeft).map(f => () => agent(
    `Try to refute this audit finding by checking the code yourself: "${f.title}" (${f.file}:${f.line ?? '?'}). ` +
    `Evidence: ${f.evidence.join(' | ')}. If the evidence does not hold up or is uncertain — refuted=true.`,
    {
      label: `verification:${f.file}:${f.line ?? ''}`, phase: 'Ranking', agentType: 'specialist',
      schema: { type: 'object', properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } }, required: ['refuted', 'reason'] },
    }).then(v => ({ f, v }))))
  for (const { f, v } of checked.filter(Boolean)) {
    if (v && v.refuted) { f.refuted = v.reason; hypotheses.push(f) }
  }
  blockers = blockers.filter(f => !f.refuted)
  ranking = ranking.filter(f => !f.refuted)
  for (const f of toCheck.slice(budgetLeft)) f.unverified = true
}
ranking.forEach((f, i) => { f.id = `A-${String(i + 1).padStart(2, '0')}` })
blockers.forEach((f, i) => { f.id = `B-${String(i + 1).padStart(2, '0')}` })
const quickWins = ranking.filter(f => f.cost === 'S' && f.risk >= 2).map(f => f.id)
log(`Findings: ${all.length} after merging, blockers ${blockers.length}, ranking ${ranking.length}, hypotheses ${hypotheses.length}`)

phase('Report')
const reportPath = `${dir}/${a.date}-code-audit.md`
const data = { depth, dimensions: reviewed.map(d => d.key), inventory, blockers, ranking, quick_wins: quickWins, hypotheses, not_checked: notChecked }
const report = await agent(
  `Write the code audit report to ${reportPath} per references/report-template.md of the eng-code-audit skill ` +
  `(section 5 of the skill: TL;DR, blockers, ranking and top 10, quick wins, "What was not checked", contradictions, cost). ` +
  `The ranking, the blockers and the hypotheses are already computed — copy them without changing the order or the values. Audit cost: ` +
  `python3 .tf/factory/cost_report.py --days 1. At the end python3 .claude/skills/core-grounding/scripts/grounding_check.py ` +
  `${reportPath} and fix the errors. Return only the report's path.\nData:\n${JSON.stringify(data)}`,
  { label: 'report', phase: 'Report' })

return { report: report ? reportPath : null, ...data }
