#!/usr/bin/env node
/**
 * Optional official FSRS parameter optimization for a Wisteria full backup.
 *
 * Usage:
 *   npm install
 *   npm run optimize-fsrs -- JLPT紫藤完整备份_2027-01-01.json
 */
import { readFile, writeFile } from 'node:fs/promises'
import { basename, dirname, join } from 'node:path'
import * as bindingModule from '@open-spaced-repetition/binding'

const source = process.argv[2]
if (!source) {
  console.error('Usage: npm run optimize-fsrs -- <Wisteria full backup.json>')
  process.exit(2)
}

const binding = bindingModule.default ?? bindingModule
const { computeParameters, FSRSBindingItem, FSRSBindingReview } = binding
if (![computeParameters, FSRSBindingItem, FSRSBindingReview].every(Boolean)) {
  throw new Error('The installed official FSRS binding does not expose the expected optimizer API.')
}

const data = JSON.parse(await readFile(source, 'utf8'))
const logs = data?.srs?.reviews ?? data?.reviews
if (!Array.isArray(logs)) throw new Error('No Wisteria review log was found in this JSON file.')

const grouped = new Map()
for (const log of logs) {
  if (!log?.cardId || ![1, 2, 3, 4].includes(Number(log.rating))) continue
  const list = grouped.get(log.cardId) ?? []
  list.push(log)
  grouped.set(log.cardId, list)
}

const utcDayDifference = (earlier, later) => {
  const a = new Date(earlier)
  const b = new Date(later)
  const ua = Date.UTC(a.getUTCFullYear(), a.getUTCMonth(), a.getUTCDate())
  const ub = Date.UTC(b.getUTCFullYear(), b.getUTCMonth(), b.getUTCDate())
  return Math.max(0, Math.floor((ub - ua) / 86400000))
}

const items = []
let reviewCount = 0
for (const sequence of grouped.values()) {
  sequence.sort((a, b) => new Date(a.reviewedAt) - new Date(b.reviewedAt))
  if (sequence.length < 2) continue
  let previous = null
  const reviews = sequence.map((log, index) => {
    let delta = Number(log?.after?.elapsedDays)
    if (!Number.isFinite(delta) || delta < 0) {
      delta = index === 0 || !previous ? 0 : utcDayDifference(previous.reviewedAt, log.reviewedAt)
    }
    previous = log
    reviewCount += 1
    return new FSRSBindingReview(Number(log.rating), Math.round(delta))
  })
  items.push(new FSRSBindingItem(reviews))
}

if (!items.length) throw new Error('There are not enough multi-review card histories to optimize.')
if (reviewCount < 400) {
  console.warn(`Warning: only ${reviewCount} reviews were found. Keeping the official defaults is usually safer until more history exists.`)
}

console.log(`Optimizing ${reviewCount} reviews across ${items.length} cards with the official FSRS binding...`)
const result = await computeParameters(items, {
  enableShortTerm: true,
  numRelearningSteps: 1,
  timeout: 500,
  progress(current, total) {
    if (current === total || current % Math.max(1, Math.floor(total / 20)) === 0) {
      process.stdout.write(`\r${current}/${total}`)
    }
  },
})
process.stdout.write('\n')

const weights = Array.isArray(result)
  ? result
  : result?.parameters ?? result?.weights ?? result?.w
if (!Array.isArray(weights) || weights.length !== 21 || weights.some(x => !Number.isFinite(Number(x)))) {
  const rawPath = join(dirname(source), `${basename(source, '.json')}_optimizer-raw.json`)
  await writeFile(rawPath, JSON.stringify(result, null, 2), 'utf8')
  throw new Error(`The optimizer returned an unfamiliar shape. Raw output was saved to ${rawPath}`)
}

const output = {
  app: 'JLPT Wisteria',
  scheduler: 'FSRS-6',
  optimizedAt: new Date().toISOString(),
  reviewCount,
  cardCount: items.length,
  weights: weights.map(Number),
}
const outputPath = join(dirname(source), `${basename(source, '.json')}_FSRS优化参数.json`)
await writeFile(outputPath, JSON.stringify(output, null, 2), 'utf8')
console.log(`Saved: ${outputPath}`)
console.log('Paste the 21 weights into Settings > FSRS-6 Parameters, or import the JSON with a future compatible build.')
