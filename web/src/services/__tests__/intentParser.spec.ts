import { describe, expect, it } from 'vitest'
import {
  parseIntent,
  type QueryMetric,
  type QueryTemplate,
} from '@/services/intentParser'

const PROVINCES = [
  '北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省',
  '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省',
  '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省',
  '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省',
  '青海省', '宁夏回族自治区', '新疆维吾尔自治区', '台湾省', '香港特别行政区', '澳门特别行政区',
]

interface Case {
  input: string
  template: QueryTemplate
  regions?: string[]
  category?: string | null
  metric?: QueryMetric
}

const CASES: Case[] = [
  // 双省对比
  { input: '对比浙江和山东的传统技艺', template: 'compare', regions: ['浙江省', '山东省'], category: '传统技艺' },
  { input: '比较广东和江苏', template: 'compare', regions: ['广东省', '江苏省'] },
  { input: '浙江和四川比一比', template: 'compare', regions: ['浙江省', '四川省'] },
  { input: '湖北还是湖南哪个多', template: 'compare', regions: ['湖北省', '湖南省'] },
  { input: '上海和北京对比一下', template: 'compare', regions: ['上海市', '北京市'] },
  { input: '福建 vs 江西', template: 'compare', regions: ['福建省', '江西省'] },
  { input: '把山东和山西的传统美术放一起比', template: 'compare', regions: ['山东省', '山西省'], category: '传统美术' },
  { input: '贵州与云南相比', template: 'compare', regions: ['贵州省', '云南省'] },
  { input: '新疆和西藏比一下', template: 'compare', regions: ['新疆维吾尔自治区', '西藏自治区'] },
  { input: '粤桂对比', template: 'compare', regions: ['广东省', '广西壮族自治区'] },
  // 地区排名
  { input: '哪个省份民间文学的子项最多', template: 'top', category: '民间文学', metric: 'subitem' },
  { input: '哪个省项目最多', template: 'top', metric: 'project' },
  { input: '传承人最多的省份', template: 'top', metric: 'inheritor' },
  { input: '覆盖率最高的省份', template: 'top', metric: 'coverage' },
  { input: '民间文学排名前十的省份', template: 'top', category: '民间文学' },
  { input: '子项数排第一的省', template: 'top', metric: 'subitem' },
  { input: '前五名的省份', template: 'top' },
  { input: '哪个地方非遗最多', template: 'top' },
  { input: '传统音乐最少的是哪个省', template: 'top', category: '传统音乐' },
  { input: '传统技艺前几名的省份', template: 'top', category: '传统技艺' },
  // 类别分布
  { input: '浙江省都有哪些类别的非遗', template: 'category-dist', regions: ['浙江省'] },
  { input: '全国的传统美术分布', template: 'category-dist', category: '传统美术' },
  { input: '曲艺的分布', template: 'category-dist', category: '曲艺' },
  { input: '民俗都有哪些', template: 'category-dist', category: '民俗' },
  { input: '北京有哪些非遗', template: 'category-dist', regions: ['北京市'] },
  { input: '四川是什么类别的多', template: 'category-dist', regions: ['四川省'] },
  { input: '广东省有多少项非遗', template: 'category-dist', regions: ['广东省'] },
  { input: '甘肃的构成', template: 'category-dist', regions: ['甘肃省'] },
  { input: '云南的类别占比', template: 'category-dist', regions: ['云南省'] },
  { input: '湖南都有哪些类别', template: 'category-dist', regions: ['湖南省'] },
  // 批次趋势
  { input: '传统戏剧五批的变化', template: 'batch-trend', category: '传统戏剧' },
  { input: '民间文学的批次趋势', template: 'batch-trend', category: '民间文学' },
  { input: '浙江非遗的历年变化', template: 'batch-trend', regions: ['浙江省'] },
  { input: '传统技艺演化', template: 'batch-trend', category: '传统技艺' },
  { input: '五批名录的发展', template: 'batch-trend' },
  { input: '曲艺的历史变化', template: 'batch-trend', category: '曲艺' },
  { input: '近几批的变化', template: 'batch-trend' },
  { input: '全国传统音乐逐年变化', template: 'batch-trend', category: '传统音乐' },
  // 地图
  { input: '全国地图', template: 'map' },
  { input: '看看地图', template: 'map' },
  { input: '民间文学在全国的分布地图', template: 'map', category: '民间文学' },
  { input: '地图上各省的子项', template: 'map', metric: 'subitem' },
  { input: '全国分布', template: 'map' },
  { input: '看下全国的传统美术', template: 'map', category: '传统美术' },
  // 传承资源对比
  { input: '对比浙江和山东的传承人', template: 'inheritor-compare', regions: ['浙江省', '山东省'], metric: 'inheritor' },
  { input: '江苏和安徽的传承资源', template: 'inheritor-compare', regions: ['江苏省', '安徽省'] },
  { input: '浙江省的传承人情况', template: 'inheritor-compare', regions: ['浙江省'] },
  { input: '广东的覆盖率', template: 'inheritor-compare', regions: ['广东省'], metric: 'coverage' },
  { input: '鲁苏的传承人', template: 'inheritor-compare', regions: ['山东省', '江苏省'] },
  { input: '川渝的传承资源', template: 'inheritor-compare', regions: ['四川省', '重庆市'] },
  // 地区别称
  { input: '齐鲁的传统美术', template: 'category-dist', regions: ['山东省'], category: '传统美术' },
  { input: '燕赵的民间文学', template: 'category-dist', regions: ['河北省'], category: '民间文学' },
  { input: '荆楚有多少非遗', template: 'category-dist', regions: ['湖北省'] },
  { input: '潇湘的曲艺', template: 'category-dist', regions: ['湖南省'], category: '曲艺' },
  { input: '八桂的民俗', template: 'category-dist', regions: ['广西壮族自治区'], category: '民俗' },
  { input: '陇的项目', template: 'category-dist', regions: ['甘肃省'], metric: 'project' },
  // 类别别名
  { input: '戏曲的分布', template: 'category-dist', category: '传统戏剧' },
  { input: '相声的分布', template: 'category-dist', category: '曲艺' },
  { input: '武术最多的省份', template: 'top', category: '传统体育、游艺与杂技' },
  { input: '民歌排名', template: 'top', category: '传统音乐' },
  { input: '剪纸的分布', template: 'category-dist', category: '传统美术' },
  { input: '陶瓷最多的省', template: 'top', category: '传统技艺' },
  { input: '传说最多的省份', template: 'top', category: '民间文学' },
  { input: '节庆的分布', template: 'category-dist', category: '民俗' },
  { input: '刺绣分布', template: 'category-dist', category: '传统美术' },
  // 指标与排行口语
  { input: '非遗数量排行榜', template: 'top', metric: 'subitem' },
  { input: '传承人数量排行', template: 'top', metric: 'inheritor' },
  { input: '前十名的省份', template: 'top' },
  { input: '哪个省最多的是民间文学', template: 'top', category: '民间文学' },
  // 趋势口语
  { input: '走势图', template: 'batch-trend' },
  { input: '这些年传统技艺的走势', template: 'batch-trend', category: '传统技艺' },
  { input: '从2006到现在的变化', template: 'batch-trend' },
  // 地图口语
  { input: '各地分布图', template: 'map' },
  { input: '地图上看看', template: 'map' },
  // 无效输入
  { input: '你好', template: 'top' },
  { input: '我想看看', template: 'top' },
  { input: '对比一下', template: 'top' },
]

describe('parseIntent', () => {
  it.each(CASES)('$input -> $template', (c) => {
    const q = parseIntent(c.input, PROVINCES)
    expect(q.template).toBe(c.template)
    if (c.regions) expect(q.regions).toEqual(c.regions)
    expect(q.category).toBe(c.category ?? null)
    if (c.metric) expect(q.metric).toBe(c.metric)
  })

  it('无效输入返回错误与示例', () => {
    const q = parseIntent('你好', PROVINCES)
    expect(q.error).toBeTruthy()
    expect(q.suggestions.length).toBeGreaterThan(0)
  })

  it('空输入返回错误', () => {
    const q = parseIntent('', PROVINCES)
    expect(q.error).toBeTruthy()
  })

  it('地区按原文顺序解析', () => {
    const q = parseIntent('山东省和江苏省比一比', PROVINCES)
    expect(q.regions).toEqual(['山东省', '江苏省'])
  })
})
