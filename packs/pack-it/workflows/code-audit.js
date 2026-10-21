export const meta = {
  name: 'code-audit',
  description: 'Pełny audyt kodu (skill eng-code-audit): inwentarz, przeglądy równoległe, ranking w kodzie, raport. Argumenty: zakres zatwierdzony przez człowieka.',
  phases: [
    { title: 'Inwentarz', detail: 'jeden tani wykonawca: stack, moduły, hotspoty, narzędzia, dostępne skille' },
    { title: 'Przeglądy', detail: 'jeden wykonawca na wymiar, równolegle' },
    { title: 'Ranking', detail: 'duplikaty, ryzyko × zasięg ÷ koszt, blokery, hipotezy — w kodzie, bez modelu' },
    { title: 'Raport', detail: 'plik w docs/project/07-review/ według szablonu skilla' },
  ],
}

// Argumenty (zakres zatwierdza człowiek w kroku 1 skilla eng-code-audit, zanim cokolwiek się uruchomi):
//   {date: 'RRRR-MM-DD', dimensions: [...], depth: 'szybki'|'standard'|'pelny', limit: N, modules: [...],
//    exclude: [...], executors: {wymiar: 'typ-agenta'}}
// limit = najwięcej wywołań wykonawców (przeglądy + weryfikacje); inwentarz i raport się nie liczą.
const DIMENSIONS = {
  architektura: { agent: 'architect', skills: ['arch-quality-attributes', 'eng-module-depth', 'ddd-connascence-analysis'] },
  bezpieczenstwo: { agent: 'security-reviewer', skills: ['sec-appsec-devsecops', 'be-auth-security', 'arch-threat-modeling'] },
  jakosc: { agent: 'specialist', skills: ['eng-tech-debt-audit', 'eng-clean-code'] },
  testy: { agent: 'specialist', skills: ['qa-test-design', 'qa-regression'] },
  dostepnosc: { agent: 'specialist', skills: ['ux-accessibility'] },
  uzytecznosc: { agent: 'specialist', skills: ['ux-feature-design'] },
  wydajnosc: { agent: 'specialist', skills: ['fe-web-platform', 'fe-architecture'] },
  prawo: { agent: 'specialist', skills: ['arch-eu-product-law', 'arch-privacy-compliance', 'sec-eu-regulations'] },
}
const DEEP = ['architektura', 'bezpieczenstwo']   // pełny: te wymiary na opus
const COST = { S: 1, M: 2, L: 4 }

const a = args || {}
if (!/^\d{4}-\d{2}-\d{2}$/.test(a.date || '')) throw new Error('args.date (RRRR-MM-DD) is required: the script cannot read the clock')
const unknown = (a.dimensions || []).filter(d => !DIMENSIONS[d])
if (unknown.length) throw new Error(`unknown dimensions: ${unknown.join(', ')} (known: ${Object.keys(DIMENSIONS).join(', ')})`)
if (!(a.dimensions || []).length) throw new Error('args.dimensions is empty: the human chooses the dimensions first')
const depth = a.depth || 'standard'
const limit = Number.isInteger(a.limit) ? a.limit : a.dimensions.length
const scope = [
  a.modules && a.modules.length ? `Moduły: ${a.modules.join(', ')}.` : 'Moduły: całe repozytorium.',
  a.exclude && a.exclude.length ? `Nie ruszasz: ${a.exclude.join(', ')}.` : '',
  'Kodu nie zmieniasz. Skanów aktywnych wobec działających systemów nie uruchamiasz.',
].filter(Boolean).join(' ')
const dir = 'docs/project/07-review'
const notChecked = []

phase('Inwentarz')
const needed = [...new Set(a.dimensions.flatMap(d => DIMENSIONS[d].skills))]
const inventory = await agent(
  `Etap 0 audytu kodu (skill eng-code-audit, sekcja 2) — tani inwentarz dla wszystkich przeglądających. ${scope}\n` +
  `Zrób kroki 1–5 z sekcji 2 skilla (stack, hotspoty, graf zależności, narzędzia projektu, mapa modułów) i zapisz ` +
  `wynik do ${dir}/${a.date}-audyt-inwentarz.md. Bez globalnych instalacji; brakujące narzędzie to „nie sprawdzono”.\n` +
  `Sprawdź też, które z tych skilli są zainstalowane (plik .claude/skills/<nazwa>/SKILL.md): ${needed.join(', ')}.`,
  {
    label: 'inwentarz', phase: 'Inwentarz', model: 'haiku', effort: 'low',
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
for (const t of inventory.missing_tools || []) notChecked.push(`narzędzie: ${t}`)

const runnable = []
for (const d of a.dimensions) {
  const skills = DIMENSIONS[d].skills.filter(s => present.has(s))
  const missing = DIMENSIONS[d].skills.filter(s => !present.has(s))
  if (!skills.length) notChecked.push(`${d}: brak skilli ${missing.join(', ')} (nakładka niezainstalowana)`)
  else runnable.push({ key: d, skills, missing })
}
const reviewed = runnable.slice(0, limit)
for (const d of runnable.slice(limit)) notChecked.push(`${d.key}: poza limitem wykonawców (${limit})`)
if (runnable.length > limit) log(`Limit ${limit}: pominięte wymiary ${runnable.slice(limit).map(d => d.key).join(', ')}`)

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
          blocker: { type: 'string', enum: ['', 'wyciek', 'autoryzacja', 'prawo'] },
        },
        required: ['title', 'file', 'risk', 'reach', 'cost', 'evidence', 'proposal', 'blocker'],
      },
    },
  },
  required: ['findings'],
}

const results = await pipeline(reviewed, d => agent(
  `Audyt kodu, wymiar: ${d.key}. ${scope}\nInwentarz (fakty dla wszystkich, nie czytaj repozytorium od nowa): ` +
  `${inventory.path}.\nWczytaj skille: ${d.skills.join(', ')}` +
  (d.missing.length ? ` (niedostępne: ${d.missing.join(', ')} — zapisz to w ustaleniach jako ograniczenie)` : '') + '.\n' +
  `Pytanie: jakie są najważniejsze problemy tego wymiaru? Najwyżej 10 ustaleń. Każde z dowodem: plik:linia, wynik ` +
  `polecenia albo cytat. Ryzyko 1–4, zasięg 1–3, koszt naprawy S/M/L. Pole blocker: „wyciek” (dane lub sekret), ` +
  `„autoryzacja” (obejście), „prawo” (obowiązek z terminem), inaczej pusty. Brak istotnych problemów to poprawny ` +
  `wynik — pusta lista; nie dopisuj ustaleń dla objętości.`,
  {
    label: `przegląd:${d.key}`, phase: 'Przeglądy', schema: FINDINGS,
    agentType: (a.executors || {})[d.key] || DIMENSIONS[d.key].agent,
    ...(depth === 'pelny' && DEEP.includes(d.key) ? { model: 'opus' } : {}),
  }).then(r => r ? r.findings.map(f => ({ ...f, dimension: d.key })) : (notChecked.push(`${d.key}: wykonawca nie zwrócił wyniku`), [])))

phase('Ranking')
// Ta sama przyczyna = to samo miejsce (plik:linia); bez linii — plik i tytuł. Wartości najostrożniejsze z duplikatów.
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

if (depth === 'pelny') {   // pełny: jeden sceptyk na bloker i na ustalenie z top 10, w ramach limitu
  const budgetLeft = Math.max(0, limit - reviewed.length)
  const toCheck = [...blockers, ...ranking.slice(0, 10)]
  if (toCheck.length > budgetLeft) log(`Weryfikacja: ${budgetLeft} z ${toCheck.length} ustaleń (limit wykonawców)`)
  const checked = await parallel(toCheck.slice(0, budgetLeft).map(f => () => agent(
    `Spróbuj obalić to ustalenie audytu, sprawdzając kod samodzielnie: „${f.title}” (${f.file}:${f.line ?? '?'}). ` +
    `Dowody: ${f.evidence.join(' | ')}. Jeśli dowód nie wytrzymuje sprawdzenia albo jest niepewny — refuted=true.`,
    {
      label: `weryfikacja:${f.file}:${f.line ?? ''}`, phase: 'Ranking', agentType: 'specialist',
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
log(`Ustalenia: ${all.length} po scaleniu, blokery ${blockers.length}, ranking ${ranking.length}, hipotezy ${hypotheses.length}`)

phase('Raport')
const reportPath = `${dir}/${a.date}-audyt-kodu.md`
const data = { depth, dimensions: reviewed.map(d => d.key), inventory, blockers, ranking, quick_wins: quickWins, hypotheses, not_checked: notChecked }
const report = await agent(
  `Napisz raport audytu kodu do ${reportPath} według references/szablon-raportu.md skilla eng-code-audit ` +
  `(sekcja 5 skilla: TL;DR, blokery, ranking i top 10, szybkie wygrane, „Czego nie sprawdzono”, sprzeczności, koszt). ` +
  `Ranking, blokery i hipotezy są już policzone — przepisz je bez zmiany kolejności i wartości. Koszt audytu: ` +
  `python3 factory/cost_report.py --days 1. Na koniec python3 .claude/skills/core-grounding/scripts/grounding_check.py ` +
  `${reportPath} i popraw błędy. Zwróć samą ścieżkę raportu.\nDane:\n${JSON.stringify(data)}`,
  { label: 'raport', phase: 'Raport' })

return { report: report ? reportPath : null, ...data }
