import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  emptyFilter,
  filterSubitems,
  loadDataset,
  matchKeyword,
} from '@/services/dataService'
import type { Subitem } from '@/types'

const items: Subitem[] = [
  {
    subitem_id: 's1',
    project_code: 'I-1',
    project_name: '苗族古歌',
    category: '民间文学',
    batch_no: 1,
    publish_year: 2006,
    entry_type: 'new',
    region_raw: '贵州省台江县',
    province: '贵州省',
    protection_unit: '台江县非物质文化遗产保护中心',
    source_url: 'http://example.com/1',
  },
  {
    subitem_id: 's2',
    project_code: 'I-1',
    project_name: '苗族古歌（簪汪传）',
    category: '民间文学',
    batch_no: 5,
    publish_year: 2021,
    entry_type: 'extension',
    region_raw: '贵州省贵阳市清镇市',
    province: '贵州省',
    protection_unit: '清镇市文化馆',
    source_url: 'http://example.com/2',
  },
  {
    subitem_id: 's3',
    project_code: 'IV-28',
    project_name: '京剧',
    category: '传统戏剧',
    batch_no: 1,
    publish_year: 2006,
    entry_type: 'new',
    region_raw: '北京市',
    province: '北京市',
    protection_unit: '北京京剧院',
    source_url: 'http://example.com/3',
  },
]

describe('filterSubitems', () => {
  it('按类别筛选', () => {
    const r = filterSubitems(items, { ...emptyFilter(), category: '传统戏剧' })
    expect(r.map((x) => x.subitem_id)).toEqual(['s3'])
  })

  it('按批次筛选', () => {
    const r = filterSubitems(items, { ...emptyFilter(), batch: 5 })
    expect(r.map((x) => x.subitem_id)).toEqual(['s2'])
  })

  it('按新增/扩展筛选', () => {
    const r = filterSubitems(items, { ...emptyFilter(), entryType: 'extension' })
    expect(r.map((x) => x.subitem_id)).toEqual(['s2'])
  })

  it('按地区筛选', () => {
    const r = filterSubitems(items, { ...emptyFilter(), province: '北京市' })
    expect(r.map((x) => x.subitem_id)).toEqual(['s3'])
  })

  it('按关键词匹配名称/编号/保护单位', () => {
    expect(filterSubitems(items, { ...emptyFilter(), keyword: '京剧' }).length).toBe(1)
    expect(filterSubitems(items, { ...emptyFilter(), keyword: 'i-1' }).length).toBe(2)
    expect(filterSubitems(items, { ...emptyFilter(), keyword: '清镇' }).length).toBe(1)
  })

  it('组合筛选与空结果', () => {
    const r = filterSubitems(items, {
      ...emptyFilter(),
      category: '民间文学',
      batch: 1,
      province: '北京市',
    })
    expect(r).toEqual([])
  })

  it('无筛选时返回全部', () => {
    expect(filterSubitems(items, emptyFilter()).length).toBe(3)
  })
})

describe('matchKeyword', () => {
  it('匹配名称与编号', () => {
    const entry = {
      id: 's1',
      name: '苗族古歌',
      code: 'I-1',
      category: '民间文学',
      batch_no: 1,
      year: 2006,
      entry_type: 'new',
      province: '贵州省',
      protection_unit: '台江县非物质文化遗产保护中心',
    }
    expect(matchKeyword(entry, '苗族')).toBe(true)
    expect(matchKeyword(entry, 'i-1')).toBe(true)
    expect(matchKeyword(entry, '北京')).toBe(false)
    expect(matchKeyword(entry, '')).toBe(true)
  })
})

describe('loadDataset', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('从本地 JSON 加载全部数据并解析', async () => {
    const mock = {
      './data/metadata.json': { data_version: 'v0.1.0-pilot', raw_record_count: 3 },
      './data/provinces.json': [{ province: '贵州省', map_name: '贵州省', subitem_count: 2 }],
      './data/categories.json': [{ category: '民间文学', subitem_count: 2 }],
      './data/batches.json': [{ batch_no: 1, publish_year: 2006, total: 1 }],
      './data/projects.json': [{ project_code: 'I-1', project_name: '苗族古歌' }],
      './data/subitems.json': items,
      './data/project_search_index.json': [],
      './data/methodology.json': { collection: 'test' },
      './data/geojson/china.json': { type: 'FeatureCollection', features: [] },
    } as Record<string, unknown>
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => ({
        ok: true,
        status: 200,
        json: async () => mock[url],
      })),
    )
    const ds = await loadDataset()
    expect(ds.metadata.data_version).toBe('v0.1.0-pilot')
    expect(ds.subitems.length).toBe(3)
    expect(ds.geoJson.features).toEqual([])
  })

  it('数据缺失时抛错', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) })),
    )
    await expect(loadDataset()).rejects.toThrow('加载数据失败')
  })
})
