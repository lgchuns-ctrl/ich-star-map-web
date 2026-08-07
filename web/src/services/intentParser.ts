import { CATEGORY_ORDER } from '@/types'

export type QueryTemplate =
  | 'compare'
  | 'category-dist'
  | 'top'
  | 'batch-trend'
  | 'map'
  | 'inheritor-compare'
export type QueryMetric = 'subitem' | 'project' | 'inheritor' | 'coverage'

export interface IntentQuery {
  template: QueryTemplate
  regions: string[]
  category: string | null
  metric: QueryMetric
  note: string
  error: string | null
  suggestions: string[]
}

const REGION_ALIASES: Record<string, string> = {
  北京: '北京市',
  京: '北京市',
  天津: '天津市',
  津: '天津市',
  河北: '河北省',
  冀: '河北省',
  山西: '山西省',
  晋: '山西省',
  内蒙古: '内蒙古自治区',
  蒙: '内蒙古自治区',
  辽宁: '辽宁省',
  辽: '辽宁省',
  吉林: '吉林省',
  吉: '吉林省',
  黑龙江: '黑龙江省',
  黑: '黑龙江省',
  上海: '上海市',
  沪: '上海市',
  江苏: '江苏省',
  苏: '江苏省',
  浙江: '浙江省',
  浙: '浙江省',
  安徽: '安徽省',
  皖: '安徽省',
  福建: '福建省',
  闽: '福建省',
  江西: '江西省',
  赣: '江西省',
  山东: '山东省',
  鲁: '山东省',
  河南: '河南省',
  豫: '河南省',
  湖北: '湖北省',
  鄂: '湖北省',
  湖南: '湖南省',
  湘: '湖南省',
  广东: '广东省',
  粤: '广东省',
  广西: '广西壮族自治区',
  桂: '广西壮族自治区',
  海南: '海南省',
  琼: '海南省',
  重庆: '重庆市',
  渝: '重庆市',
  四川: '四川省',
  川: '四川省',
  蜀: '四川省',
  贵州: '贵州省',
  黔: '贵州省',
  云南: '云南省',
  滇: '云南省',
  西藏: '西藏自治区',
  藏: '西藏自治区',
  陕西: '陕西省',
  陕: '陕西省',
  甘肃: '甘肃省',
  甘: '甘肃省',
  青海: '青海省',
  青: '青海省',
  宁夏: '宁夏回族自治区',
  新疆: '新疆维吾尔自治区',
  台湾: '台湾省',
  香港: '香港特别行政区',
  澳门: '澳门特别行政区',
}

const CATEGORY_ALIASES: Record<string, string> = {
  民间文学: '民间文学',
  文学: '民间文学',
  传统音乐: '传统音乐',
  音乐: '传统音乐',
  传统舞蹈: '传统舞蹈',
  舞蹈: '传统舞蹈',
  传统戏剧: '传统戏剧',
  戏剧: '传统戏剧',
  曲艺: '曲艺',
  体育: '传统体育、游艺与杂技',
  游艺: '传统体育、游艺与杂技',
  杂技: '传统体育、游艺与杂技',
  传统体育: '传统体育、游艺与杂技',
  传统美术: '传统美术',
  美术: '传统美术',
  传统技艺: '传统技艺',
  技艺: '传统技艺',
  手工: '传统技艺',
  传统医药: '传统医药',
  医药: '传统医药',
  中医: '传统医药',
  民俗: '民俗',
}

const TEMPLATE_LABEL: Record<QueryTemplate, string> = {
  compare: '双省对比',
  'category-dist': '类别分布',
  top: '地区排名',
  'batch-trend': '批次趋势',
  map: '地图分布',
  'inheritor-compare': '传承资源对比',
}

export function parseIntent(raw: string, provinces: string[]): IntentQuery {
  const text = raw.trim()
  const suggestions = [
    '对比浙江和山东的传统技艺',
    '哪个省份民间文学的子项最多',
    '浙江省都有哪些类别的非遗',
    '传承人最多的省份',
  ]
  if (!text) {
    return errorQuery('请先输入或说出你想看的内容。', suggestions)
  }

  const canonical = new Set(provinces)
  const entries: Array<{ alias: string; name: string }> = []
  for (const p of provinces) entries.push({ alias: p, name: p })
  for (const [alias, name] of Object.entries(REGION_ALIASES)) entries.push({ alias, name })
  entries.sort((a, b) => b.alias.length - a.alias.length)

  const found: Array<{ name: string; index: number }> = []
  for (const { alias, name } of entries) {
    const idx = text.indexOf(alias)
    if (idx >= 0 && canonical.has(name) && !found.some((f) => f.name === name)) {
      found.push({ name, index: idx })
    }
  }
  const regions = found.sort((a, b) => a.index - b.index).map((f) => f.name)

  let category: string | null = null
  const catEntries = Object.entries(CATEGORY_ALIASES).sort((a, b) => b[0].length - a[0].length)
  for (const [alias, name] of catEntries) {
    if (text.includes(alias)) {
      category = name
      break
    }
  }

  let metric: QueryMetric = 'subitem'
  if (/覆盖率|覆盖/.test(text)) metric = 'coverage'
  else if (/传承人/.test(text)) metric = 'inheritor'
  else if (/独立项目|项目数|项目/.test(text)) metric = 'project'
  else if (/子项/.test(text)) metric = 'subitem'

  const inheritorIntent = /传承人|传承资源|覆盖率/.test(text)
  const hasTop =
    /最多|最少|排名|排行|前\s*\d+|前[一二三四五六七八九十]+\s*名|top|榜首|第一|前几/.test(text)
  const hasTrend = /趋势|变化|演化|发展|逐年|历年|批次|历史|演进/.test(text)
  const hasMap = /地图|全国分布|分布在全国|看下全国|看看全国/.test(text)
  const hasCompare =
    regions.length >= 2 || /对比|比较|vs|和\s*.{0,8}比|与\s*.{0,8}相比|比一比/.test(text)
  const hasDist = /分布|构成|占比|有哪些|哪些|都是|有多少|几个/.test(text)

  let template: QueryTemplate
  if (regions.length >= 2 && inheritorIntent) template = 'inheritor-compare'
  else if (regions.length === 1 && inheritorIntent) template = 'inheritor-compare'
  else if (hasMap) template = 'map'
  else if (hasTrend) template = 'batch-trend'
  else if (regions.length >= 2 || hasCompare) template = 'compare'
  else if (hasTop) template = 'top'
  else if (category || regions.length === 1 || hasDist) template = 'category-dist'
  else template = 'top'

  const recognized =
    regions.length > 0 ||
    Boolean(category) ||
    hasTop ||
    hasTrend ||
    hasMap ||
    hasCompare ||
    hasDist ||
    inheritorIntent
  if (!recognized) {
    return errorQuery('没太听懂，试着用“对比 / 排名 / 分布 / 趋势 / 地图 / 传承人”来描述你想看的。', suggestions)
  }

  const parts: string[] = [TEMPLATE_LABEL[template]]
  if (regions.length) parts.push(`地区：${regions.join('、')}`)
  if (category) parts.push(`类别：${category}`)
  const metricLabel: Record<QueryMetric, string> = {
    subitem: '地区子项',
    project: '独立项目',
    inheritor: '传承人',
    coverage: '覆盖率',
  }
  parts.push(`指标：${metricLabel[metric]}`)

  return {
    template,
    regions,
    category,
    metric,
    note: parts.join(' · '),
    error: null,
    suggestions: [],
  }
}

function errorQuery(msg: string, suggestions: string[]): IntentQuery {
  return {
    template: 'top',
    regions: [],
    category: null,
    metric: 'subitem',
    note: '',
    error: msg,
    suggestions,
  }
}
