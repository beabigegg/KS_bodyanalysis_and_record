import { useMemo } from 'react'
import type { CompareRow, WirGroupEntry } from '../types'
import { formatParamGroupLabel } from '../lib/paramBrowse'
import { DiffTable } from './DiffTable'

type GroupedDiffTableProps = {
  rows: CompareRow[]
  importIds: number[]
  idToLabel?: Record<string, string>
  wireGroupContext?: Record<string, WirGroupEntry[]>
}

type CategoryGroup = {
  category: string
  rows: CompareRow[]
  diffCount: number
}

type StageGroup = {
  stage: string
  categories: CategoryGroup[]
  diffCount: number
}

type ParamGroupSection = {
  paramGroup: string | null
  flatRows: CompareRow[]
  stages: StageGroup[]
  diffCount: number
}

function stageLabel(stage: string): string {
  if (stage === '_unmapped') return 'Unmapped'
  if (stage === 'bond1') return 'Bond1'
  if (stage === 'bond2') return 'Bond2'
  if (stage === 'bump') return 'Bump'
  if (stage === 'bits_other') return 'BITS / Other'
  if (stage === 'quick_adjust') return 'Quick Adjust'
  return stage
}

function categoryLabel(category: string): string {
  if (category === '_none') return 'other'
  return category
}

function paramGroupLabel(
  key: string | null,
  wireGroupContext?: Record<string, WirGroupEntry[]>,
): string {
  if (key === null) return 'Other'
  const wirMatch = /^wir_(\d+)$/.exec(key)
  if (wirMatch) {
    const groupNo = parseInt(wirMatch[1], 10)
    if (wireGroupContext) {
      for (const entries of Object.values(wireGroupContext)) {
        const entry = entries.find((e) => e.wir_group_no === groupNo)
        if (entry) {
          const count = entry.wire_site_count
          const siteLabel = count != null ? `${count} wire${count !== 1 ? 's' : ''}` : ''
          return siteLabel ? `Bond Group ${groupNo} (${siteLabel})` : `Bond Group ${groupNo}`
        }
      }
    }
    return `Bond Group ${groupNo}`
  }
  return formatParamGroupLabel(key)
}

function rowGroupKey(row: CompareRow): string | null {
  if (typeof row.wir_group_no === 'number') {
    return `wir_${row.wir_group_no}`
  }
  return typeof row.param_group === 'string' ? row.param_group : null
}

function sortGroupKeys(a: string | null, b: string | null): number {
  if (a === null && b === null) return 0
  if (a === null) return 1
  if (b === null) return -1
  const wirA = /^wir_(\d+)$/.exec(a)
  const wirB = /^wir_(\d+)$/.exec(b)
  if (wirA && wirB) return parseInt(wirA[1], 10) - parseInt(wirB[1], 10)
  if (wirA) return -1
  if (wirB) return 1
  if (a === 'parms') return -1
  if (b === 'parms') return 1
  return a.localeCompare(b)
}

function buildStageGroups(rows: CompareRow[]): { flatRows: CompareRow[]; stages: StageGroup[] } {
  const flatRows: CompareRow[] = []
  const byStage = new Map<string, Map<string, CompareRow[]>>()

  for (const row of rows) {
    const stage = typeof row.stage === 'string' ? row.stage : null
    const category = typeof row.category === 'string' ? row.category : null

    if (stage === null) {
      flatRows.push(row)
      continue
    }

    let categoryMap = byStage.get(stage)
    if (!categoryMap) {
      categoryMap = new Map<string, CompareRow[]>()
      byStage.set(stage, categoryMap)
    }

    const categoryKey = category ?? '_none'
    const bucket = categoryMap.get(categoryKey) ?? []
    bucket.push(row)
    categoryMap.set(categoryKey, bucket)
  }

  const stages: StageGroup[] = Array.from(byStage.entries())
    .sort(([left], [right]) => {
      if (left === '_unmapped') return 1
      if (right === '_unmapped') return -1
      return left.localeCompare(right)
    })
    .map(([stage, categoryMap]) => {
      const categories: CategoryGroup[] = Array.from(categoryMap.entries())
        .sort(([left], [right]) => {
          if (left === '_none') return 1
          if (right === '_none') return -1
          return left.localeCompare(right)
        })
        .map(([category, categoryRows]) => ({
          category,
          rows: categoryRows,
          diffCount: categoryRows.filter((row) => row.is_diff).length,
        }))

      return {
        stage,
        categories,
        diffCount: categories.reduce((sum, item) => sum + item.diffCount, 0),
      }
    })

  return { flatRows, stages }
}

function StageSection({
  section,
  importIds,
  idToLabel,
}: {
  section: Pick<ParamGroupSection, 'flatRows' | 'stages'>
  importIds: number[]
  idToLabel?: Record<string, string>
}) {
  return (
    <>
      {section.flatRows.length > 0 && (
        <details className="grouped-stage" open={section.flatRows.some((r) => r.is_diff)}>
          <summary>
            <span>Other (no stage)</span>
            <span className="grouped-count">
              {section.flatRows.filter((r) => r.is_diff).length} diff
            </span>
          </summary>
          <DiffTable rows={section.flatRows} importIds={importIds} idToLabel={idToLabel} />
        </details>
      )}
      {section.stages.map((stage) => (
        <details key={stage.stage} className="grouped-stage" open={stage.diffCount > 0}>
          <summary>
            <span>{stageLabel(stage.stage)}</span>
            <span className="grouped-count">{stage.diffCount} diff</span>
          </summary>
          <div className="grouped-stage-body">
            {stage.categories.map((category) => (
              <details
                key={`${stage.stage}-${category.category}`}
                className="grouped-category"
                open={category.diffCount > 0}
              >
                <summary>
                  <span>{categoryLabel(category.category)}</span>
                  <span className="grouped-count">{category.diffCount} diff</span>
                </summary>
                <DiffTable rows={category.rows} importIds={importIds} idToLabel={idToLabel} />
              </details>
            ))}
          </div>
        </details>
      ))}
    </>
  )
}

export function GroupedDiffTable({ rows, importIds, idToLabel, wireGroupContext }: GroupedDiffTableProps) {
  const sections = useMemo<ParamGroupSection[]>(() => {
    const groupMap = new Map<string | null, CompareRow[]>()
    for (const row of rows) {
      const key = rowGroupKey(row)
      const bucket = groupMap.get(key) ?? []
      bucket.push(row)
      groupMap.set(key, bucket)
    }

    return Array.from(groupMap.entries())
      .sort(([a], [b]) => sortGroupKeys(a, b))
      .map(([paramGroup, pgRows]) => {
        const { flatRows, stages } = buildStageGroups(pgRows)
        const diffCount =
          flatRows.filter((r) => r.is_diff).length +
          stages.reduce((sum, s) => sum + s.diffCount, 0)
        return { paramGroup, flatRows, stages, diffCount }
      })
  }, [rows])

  if (rows.length === 0) {
    return <p className="empty">No comparison rows.</p>
  }

  const hasMultipleGroups =
    sections.length > 1 || (sections.length === 1 && sections[0].paramGroup !== null)

  if (!hasMultipleGroups) {
    return (
      <div className="grouped-diff">
        {sections.length > 0 && (
          <StageSection section={sections[0]} importIds={importIds} idToLabel={idToLabel} />
        )}
      </div>
    )
  }

  return (
    <div className="grouped-diff">
      {sections.map((section) => (
        <details
          key={section.paramGroup ?? '_other'}
          className="grouped-param-group"
          open={section.diffCount > 0}
        >
          <summary>
            <span>{paramGroupLabel(section.paramGroup, wireGroupContext)}</span>
            <span className="grouped-count">{section.diffCount} diff</span>
          </summary>
          <div className="grouped-param-group-body">
            <StageSection section={section} importIds={importIds} idToLabel={idToLabel} />
          </div>
        </details>
      ))}
    </div>
  )
}
