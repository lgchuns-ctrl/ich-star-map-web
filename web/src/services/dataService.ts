import type {
  BatchRow,
  CategoryRow,
  Conclusion,
  EntryType,
  FilterState,
  Inheritor,
  InheritorBatchRow,
  Metadata,
  Methodology,
  ProjectRow,
  ProvinceRow,
  SearchIndexEntry,
  Subitem,
} from '@/types'

async function fetchJson<T>(url: string): Promise<T> {
  const resp = await fetch(url)
  if (!resp.ok) {
    throw new Error(`加载数据失败: ${url} (HTTP ${resp.status})`)
  }
  return (await resp.json()) as T
}

export interface Dataset {
  metadata: Metadata
  provinces: ProvinceRow[]
  categories: CategoryRow[]
  batches: BatchRow[]
  inheritorBatches: InheritorBatchRow[]
  projects: ProjectRow[]
  subitems: Subitem[]
  inheritors: Inheritor[]
  searchIndex: SearchIndexEntry[]
  conclusions: Conclusion[]
  methodology: Methodology
  geoJson: GeoJSON.FeatureCollection
}

export async function loadDataset(): Promise<Dataset> {
  const [
    metadata, provinces, categories, batches, inheritorBatches, projects, subitems,
    inheritors, searchIndex, conclusions, methodology, geoJson,
  ] =
    await Promise.all([
      fetchJson<Metadata>('./data/metadata.json'),
      fetchJson<ProvinceRow[]>('./data/provinces.json'),
      fetchJson<CategoryRow[]>('./data/categories.json'),
      fetchJson<BatchRow[]>('./data/batches.json'),
      fetchJson<InheritorBatchRow[]>('./data/inheritor_batches.json'),
      fetchJson<ProjectRow[]>('./data/projects.json'),
      fetchJson<Subitem[]>('./data/subitems.json'),
      fetchJson<Inheritor[]>('./data/inheritors.json'),
      fetchJson<SearchIndexEntry[]>('./data/project_search_index.json'),
      fetchJson<Conclusion[]>('./data/conclusions.json'),
      fetchJson<Methodology>('./data/methodology.json'),
      fetchJson<GeoJSON.FeatureCollection>('./data/geojson/china.json'),
    ])
  return {
    metadata, provinces, categories, batches, inheritorBatches, projects, subitems,
    inheritors, searchIndex, conclusions, methodology, geoJson,
  }
}

export function filterSubitems(items: Subitem[], f: FilterState): Subitem[] {
  return items.filter((it) => {
    if (f.category && it.category !== f.category) return false
    if (f.batch !== null && f.batch !== undefined && it.batch_no !== f.batch) return false
    if (f.entryType && it.entry_type !== f.entryType) return false
    if (f.province && it.province !== f.province) return false
    if (f.keyword) {
      const kw = f.keyword.trim().toLowerCase()
      const haystack = [it.project_name, it.project_code, it.protection_unit, it.region_raw]
        .join(' ')
        .toLowerCase()
      if (!haystack.includes(kw)) {
        return false
      }
    }
    return true
  })
}

export function matchKeyword(entry: SearchIndexEntry, kw: string): boolean {
  if (!kw.trim()) return true
  const key = kw.trim().toLowerCase()
  return [entry.name, entry.code, entry.province, entry.protection_unit]
    .join(' ')
    .toLowerCase()
    .includes(key)
}

export function emptyFilter(): FilterState {
  return { category: '', batch: null, entryType: '', province: '', keyword: '' }
}

export function entryTypeOf(value: string): EntryType {
  if (value === 'new' || value === 'extension' || value === 'unknown') return value
  return 'unknown'
}

export function normalizeEntryTypeLabel(value: string): string {
  if (value === 'new') return '新增项目'
  if (value === 'extension') return '扩展项目'
  return '未知'
}
