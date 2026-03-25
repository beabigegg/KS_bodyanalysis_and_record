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
}

export type CompareRow = {
  values: Record<string, string | number | null>
  is_diff: boolean
  stage: string | null
  category: string | null
  param_group: string | null
  [key: string]: unknown
}

export type ComparePayload = {
  imports: ImportRecord[]
  params: CompareRow[]
  app_spec: CompareRow[]
  bsg: CompareRow[]
  rpm_limits: CompareRow[]
  rpm_reference: CompareRow[]
}
