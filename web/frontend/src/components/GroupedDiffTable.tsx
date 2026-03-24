import { useMemo } from 'react'
import type { CompareRow } from '../types'
import { DiffTable } from './DiffTable'

type GroupedDiffTableProps = {
  rows: CompareRow[]
  importIds: number[]
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

function stageLabel(stage: string): string {
  if (stage === '_unmapped') {
    return '未分類'
  }
  return stage
}

function categoryLabel(category: string): string {
  if (category === '_none') {
    return 'other'
  }
  return category
}

export function GroupedDiffTable({ rows, importIds }: GroupedDiffTableProps) {
  const grouped = useMemo(() => {
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
        if (left === '_unmapped') {
          return 1
        }
        if (right === '_unmapped') {
          return -1
        }
        return left.localeCompare(right)
      })
      .map(([stage, categoryMap]) => {
        const categories: CategoryGroup[] = Array.from(categoryMap.entries())
          .sort(([left], [right]) => {
            if (left === '_none') {
              return 1
            }
            if (right === '_none') {
              return -1
            }
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
  }, [rows])

  if (rows.length === 0) {
    return <p className="empty">No comparison rows.</p>
  }

  return (
    <div className="grouped-diff">
      {grouped.flatRows.length > 0 ? (
        <details className="grouped-stage" open={grouped.flatRows.some((row) => row.is_diff)}>
          <summary>
            <span>其他（無製程階段）</span>
            <span className="grouped-count">
              {grouped.flatRows.filter((row) => row.is_diff).length} diff
            </span>
          </summary>
          <DiffTable rows={grouped.flatRows} importIds={importIds} />
        </details>
      ) : null}

      {grouped.stages.map((stage) => (
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
                <DiffTable rows={category.rows} importIds={importIds} />
              </details>
            ))}
          </div>
        </details>
      ))}
    </div>
  )
}
