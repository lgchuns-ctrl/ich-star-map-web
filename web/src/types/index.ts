export interface SourceInfo {
  name: string
  url: string
  accessed_at: string
  type: string
  role: string
}

export interface Metadata {
  data_version: string
  updated_at: string
  scope: string
  raw_record_count: number
  raw_inheritor_record_count: number
  cleaned_subitem_count: number
  distinct_project_count: number
  inheritor_count: number
  inheritor_match_rate: number
  sources: SourceInfo[]
  indicators: Record<string, string>
  disclaimer: string
  notes: string[]
}

export interface ProvinceRow {
  province: string
  map_name: string
  subitem_count: number
  project_count: number
  categories_covered: number
  new_count: number
  extension_count: number
  protection_unit_count: number
  inheritor_count: number
  matched_subitem_count: number
  inheritor_coverage: number | null
  inheritors_per_100_subitems: number | null
}

export interface CategoryRow {
  category: string
  subitem_count: number
  project_count: number
  batch_count: number
  province_count: number
  new_count: number
  extension_count: number
  inheritor_count: number
  matched_subitem_count: number
  inheritor_coverage: number | null
  inheritors_per_100_subitems: number | null
}

export interface BatchRow {
  batch_no: number
  publish_year: number
  new_count: number
  extension_count: number
  total: number
  cumulative: number
}

export interface ProjectRow {
  project_code: string
  project_name: string
  category: string
  first_publish_year: number
  batches: string
  provinces: string
  subitem_count: number
}

export type EntryType = 'new' | 'extension' | 'unknown'

export interface Subitem {
  subitem_id: string
  project_code: string
  project_name: string
  category: string
  batch_no: number
  publish_year: number
  entry_type: EntryType
  region_raw: string
  province: string
  protection_unit: string
  source_url: string
}

export interface Inheritor {
  inheritor_id: string
  name: string
  gender: string
  ethnicity: string
  project_code: string
  project_name: string
  category: string
  province: string
  batch_no: number
  publish_year: number
  match_status: string
}

export interface InheritorBatchRow {
  batch_no: number
  publish_year: number
  inheritor_count: number
}

export interface Conclusion {
  结论: string
  对应指标: string
  使用字段: string[]
  筛选条件: string
  数据版本: string
  生成日期: string
}

export interface SearchIndexEntry {
  id: string
  name: string
  code: string
  category: string
  batch_no: number
  year: number
  entry_type: string
  province: string
  protection_unit: string
}

export interface Methodology {
  data_sources: SourceInfo[]
  collection: string
  cleaning: string
  indicators: Record<string, string>
  limitations: string[]
  ethics: string
}

export interface FilterState {
  category: string
  batch: number | null
  entryType: EntryType | ''
  province: string
  keyword: string
}

export const BATCH_LABELS: Record<number, { year: number; label: string }> = {
  1: { year: 2006, label: '第一批 (2006)' },
  2: { year: 2008, label: '第二批 (2008)' },
  3: { year: 2011, label: '第三批 (2011)' },
  4: { year: 2014, label: '第四批 (2014)' },
  5: { year: 2021, label: '第五批 (2021)' },
}

export const ENTRY_TYPE_LABELS: Record<string, string> = {
  new: '新增项目',
  extension: '扩展项目',
  unknown: '未知',
}

export type MapMetric = 'subitem' | 'project' | 'inheritor' | 'category'

export const MAP_METRIC_LABELS: Record<MapMetric, string> = {
  subitem: '地区子项数',
  project: '独立项目数',
  inheritor: '传承人数',
  category: '类别覆盖数',
}
