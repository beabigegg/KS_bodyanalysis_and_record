import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type ApiResponse } from '../lib/api'
import type { ImportRecord } from '../types'

type Filters = {
  machine_type: string
  machine_id: string
  product_type: string
  search: string
}

type FilterOptions = {
  machine_types: string[]
  machine_ids: string[]
  product_types: string[]
}

const defaultFilters: Filters = {
  machine_type: '',
  machine_id: '',
  product_type: '',
  search: '',
}

export function ImportListPage() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<Filters>(defaultFilters)
  const [items, setItems] = useState<ImportRecord[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [fetchTick, setFetchTick] = useState(0)
  const pageSize = 30
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    machine_types: [],
    machine_ids: [],
    product_types: [],
  })
  const [selected, setSelected] = useState<Set<number>>(new Set())

  useEffect(() => {
    void (async () => {
      try {
        const response = await api.get<ApiResponse<FilterOptions>>('/imports/filter-options')
        setFilterOptions(response.data.data)
      } catch {
        // fallback: options stay empty
      }
    })()
  }, [])

  useEffect(() => {
    setSelected(new Set())
  }, [page, filters])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      try {
        const response = await api.get<ApiResponse<ImportRecord[]>>('/imports', {
          params: {
            ...filters,
            page,
            page_size: pageSize,
          },
        })
        setItems(response.data.data)
        setTotal(response.data.total)
      } finally {
        setLoading(false)
      }
    })()
  }, [filters, page, fetchTick])

  const { machine_types: machineTypes, machine_ids: machineIds, product_types: productTypes } = filterOptions
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const allOnPageSelected = items.length > 0 && items.every((item) => selected.has(item.id))

  function toggleSelectAll() {
    if (allOnPageSelected) {
      setSelected((prev) => {
        const next = new Set(prev)
        items.forEach((item) => next.delete(item.id))
        return next
      })
    } else {
      setSelected((prev) => {
        const next = new Set(prev)
        items.forEach((item) => next.add(item.id))
        return next
      })
    }
  }

  function toggleRow(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleDeleteSingle(id: number) {
    if (!window.confirm(`Delete import record #${id}? This cannot be undone.`)) return
    await api.delete(`/imports/${id}`)
    setSelected((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setFetchTick((t) => t + 1)
  }

  async function handleDeleteBatch() {
    const ids = Array.from(selected)
    if (!window.confirm(`Delete ${ids.length} selected record(s)? This cannot be undone.`)) return
    await api.delete('/imports/batch', { data: { ids } })
    setSelected(new Set())
    setFetchTick((t) => t + 1)
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Recipe Import Records</h2>
        <p>Filter by machine and product, then drill into parameter details.</p>
      </header>

      <div className="panel controls">
        <select
          value={filters.machine_type}
          onChange={(e) => setFilters((prev) => ({ ...prev, machine_type: e.target.value }))}
        >
          <option value="">Machine Type</option>
          {machineTypes.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <select
          value={filters.machine_id}
          onChange={(e) => setFilters((prev) => ({ ...prev, machine_id: e.target.value }))}
        >
          <option value="">Machine ID</option>
          {machineIds.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <select
          value={filters.product_type}
          onChange={(e) => setFilters((prev) => ({ ...prev, product_type: e.target.value }))}
        >
          <option value="">Product Type</option>
          {productTypes.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <input
          value={filters.search}
          onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
          placeholder="Search product/bop/wafer/recipe"
        />
        {selected.size > 0 && (
          <button onClick={() => void handleDeleteBatch()}>
            Delete {selected.size} selected
          </button>
        )}
      </div>

      <div className="panel">
        {loading ? <p className="empty">Loading imports...</p> : null}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>
                  <input type="checkbox" checked={allOnPageSelected} onChange={toggleSelectAll} />
                </th>
                <th>ID</th>
                <th>Machine Type</th>
                <th>Machine ID</th>
                <th>Product Type</th>
                <th>BOP</th>
                <th>Wafer PN</th>
                <th>Recipe Time</th>
                <th>Import Time</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(item.id)}
                      onChange={() => toggleRow(item.id)}
                    />
                  </td>
                  <td>{item.id}</td>
                  <td>{item.machine_type}</td>
                  <td>{item.machine_id}</td>
                  <td>{item.product_type}</td>
                  <td>{item.bop}</td>
                  <td>{item.wafer_pn}</td>
                  <td className="mono">{item.recipe_datetime ?? ''}</td>
                  <td className="mono">{item.import_datetime}</td>
                  <td>
                    <button onClick={() => navigate(`/imports/${item.id}`)}>View</button>
                    {' '}
                    <button onClick={() => void handleDeleteSingle(item.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button disabled={page <= 1} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
          Prev
        </button>
        <span>
          Page {page} / {totalPages}
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}>
          Next
        </button>
        <span style={{ marginLeft: 'auto' }}>Total: {total}</span>
      </div>
    </section>
  )
}
