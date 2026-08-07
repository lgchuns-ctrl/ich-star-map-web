import { describe, expect, it } from 'vitest'
import { parseIntent } from '@/services/intentParser'

const PROVINCES = [
  '北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省',
  '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省',
  '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省',
  '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省',
  '青海省', '宁夏回族自治区', '新疆维吾尔自治区', '台湾省', '香港特别行政区', '澳门特别行政区',
]

describe('parseIntent', () => {
  it('识别双省对比', () => {
    const q = parseIntent('对比浙江和山东的传统技艺', PROVINCES)
    expect(q.template).toBe('compare')
    expect(q.regions).toEqual(['浙江省', '山东省'])
    expect(q.category).toBe('传统技艺')
    expect(q.error).toBeNull()
  })

  it('识别地区排名（最多）', () => {
    const q = parseIntent('哪个省份民间文学的子项最多', PROVINCES)
    expect(q.template).toBe('top')
    expect(q.category).toBe('民间文学')
    expect(q.metric).toBe('subitem')
  })

  it('识别单省类别分布', () => {
    const q = parseIntent('浙江省都有哪些类别的非遗', PROVINCES)
    expect(q.template).toBe('category-dist')
    expect(q.regions).toEqual(['浙江省'])
  })

  it('识别传承人指标', () => {
    const q = parseIntent('传承人最多的省份', PROVINCES)
    expect(q.template).toBe('top')
    expect(q.metric).toBe('inheritor')
  })

  it('识别省份简称', () => {
    const q = parseIntent('对比粤和桂的传统音乐', PROVINCES)
    expect(q.regions).toEqual(['广东省', '广西壮族自治区'])
    expect(q.category).toBe('传统音乐')
  })

  it('识别全国类别分布', () => {
    const q = parseIntent('传统技艺的分布', PROVINCES)
    expect(q.template).toBe('category-dist')
    expect(q.category).toBe('传统技艺')
    expect(q.regions).toEqual([])
  })

  it('空输入返回错误与示例', () => {
    const q = parseIntent('', PROVINCES)
    expect(q.error).toBeTruthy()
    expect(q.suggestions.length).toBeGreaterThan(0)
  })

  it('两个简称加对比词也走对比模板', () => {
    const q = parseIntent('江苏和安徽比一比', PROVINCES)
    expect(q.template).toBe('compare')
    expect(q.regions).toEqual(['江苏省', '安徽省'])
  })
})
