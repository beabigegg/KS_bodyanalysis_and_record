import { useMemo } from 'react'
import type { CompareRow } from '../types'
import { DiffTable } from './DiffTable'

type GroupedDiffTableProps = {
  rows: CompareRow[]
  importIds: number[]
  idToLabel?: Record<string, string>
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
  if (stage === '_unmapped') return '未分類'
  return stage
}

function categoryLabel(category: string): string {
  if (category === '_none') return 'other'
  return category
}

function paramGroupLabel(group: string | null): string {
  if (group === null) return 'Other'
  if (group === 'parms') return 'Param Group 1'
  const match = /^parms_(\d+)$/.exec(group)
  if (match) return `Param Group ${match[1]}`
  return group
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

export function GroupedDiffTable({ rows, importIds, idToLabel }: GroupedDiffTableProps) {
  const sections = useMemo<ParamGroupSection[]>(() => {
    const groupMap = new Map<string | null, CompareRow[]>()
    for (const row of rows) {
      const pg = typeof row.param_group === 'string' ? row.param_group : null
      const bucket = groupMap.get(pg) ?? []
      bucket.push(row)
      groupMap.set(pg, bucket)
    }

    return Array.from(groupMap.entries())
      .sort(([a], [b]) => {
        if (a === null) return 1   // null (other roles) last
        if (b === null) return -1
        if (a === 'parms') return -1
        if (b === 'parms') return 1
        return a.localeCompare(b)
      })
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
            <span>{paramGroupLabel(section.paramGroup)}</span>
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
