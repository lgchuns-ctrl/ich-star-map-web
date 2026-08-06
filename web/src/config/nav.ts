export interface NavSection {
  id: string
  label: string
}

export const NAV_SECTIONS: NavSection[] = [
  { id: 'hero', label: '首页' },
  { id: 'map', label: '全国分布' },
  { id: 'timeline', label: '批次演化' },
  { id: 'categories', label: '类别星系' },
  { id: 'inheritors', label: '传承资源' },
  { id: 'comparison', label: '省份对比' },
  { id: 'search', label: '寻找非遗' },
  { id: 'data', label: '数据与方法' },
]
