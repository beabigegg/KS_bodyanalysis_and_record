export type ImportRecord = {
  id: number
  machine_type: string
  machine_id: string
  product_type: string
  bop: string
  wafer_pn: string
  recipe_datetime: string | null
  import_datetime: string
  recipe_name: string | null
}

export type ParamRow = {
  id: number
  recipe_import_id: number
  file_type: string
  param_name: string
  param_value: string | null
  unit: string | null
  min_value: string | null
  max_value: string | null
  default_value: string | null
  param_group: string | null
  stage: string | null
  category: string | null
  family: string | null
  feature: string | null
  instance: string | null
  description: string | null
  tunable: boolean | null
  process_step: string | null
}

export type CountOption = {
  value: string
  count: number
}

export type ImportDetailSummary = {
  import_id: number
  params_total: number
  file_types: Array<{
    file_type: string
    count: number
  }>
  sections: {
    has_app_spec: boolean
    bsg_rows: number
    rpm_limits: number
    rpm_reference: number
  }
}

export type ParamFacets = {
  file_types: CountOption[]
  param_groups_by_file_type: Record<string, CountOption[]>
  stages_by_file_type: Record<string, CountOption[]>
  categories_by_file_type: Record<string, CountOption[]>
  families_by_file_type: Record<string, CountOption[]>
  features_by_file_type: Record<string, CountOption[]>
}

export type ParamPage = {
  rows: ParamRow[]
  page: number
  page_size: number
  total_pages: number
}

export type WirGroupEntry = {
  parms_role: string
  wir_group_no: number
  prm_stem: string | null
  wire_site_count: number | null
}

export type CompareRow = {
  values: Record<string, string | number | null>
  is_diff: boolean
  stage: string | null
  category: string | null
  process_step: string | null
  param_group: string | null
  wir_group_no: number | null
  [key: string]: unknown
}

export type CompareParamKey = {
  file_type: string
  param_name: string
}

export type CompareCatalogRow = {
  file_type: string
  param_name: string
  process_step: string | null
  param_group: string | null
  stage: string | null
  category: string | null
  family: string | null
  feature: string | null
  instance: string | null
  description: string | null
  tunable: boolean | null
  present_count: number
  missing_count: number
  is_partial_presence: boolean
  present_import_ids: number[]
}

export type CompareCatalogFacets = {
  file_types: CountOption[]
  param_groups_by_file_type: Record<string, CountOption[]>
  process_steps_by_file_type: Record<string, CountOption[]>
  stages_by_file_type: Record<string, CountOption[]>
  categories_by_file_type: Record<string, CountOption[]>
  families_by_file_type: Record<string, CountOption[]>
  features_by_file_type: Record<string, CountOption[]>
}

export type CompareCatalogPayload = {
  imports: ImportRecord[]
  rows: CompareCatalogRow[]
  facets: CompareCatalogFacets
  page: number
  page_size: number
  total_pages: number
  total_rows: number
}

export type ComparePayload = {
  imports: ImportRecord[]
  section: 'params' | 'app_spec' | 'bsg' | 'rpm_limits' | 'rpm_reference'
  rows: CompareRow[]
  page: number
  page_size: number
  total_pages: number
  total_rows: number
  wire_group_context: Record<string, WirGroupEntry[]>
}
