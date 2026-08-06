import { describe, expect, it } from 'vitest'
import { zeroSeriesData } from '@/utils/lazyChart'

describe('zeroSeriesData', () => {
  it('将数值型条形图数据归零', () => {
    const out = zeroSeriesData({
      series: [{ type: 'bar', data: [3, 7, 2] }],
    })
    const data = (out.series as Array<{ data: number[] }>)[0].data
    expect(data).toEqual([0, 0, 0])
  })

  it('保留 heatmap 坐标但归零数值', () => {
    const out = zeroSeriesData({
      series: [{ type: 'heatmap', data: [[0, 1, 5], [1, 2, 9]] }],
    })
    const data = (out.series as Array<{ data: number[][] }>)[0].data
    expect(data).toEqual([[0, 1, 0], [1, 2, 0]])
  })

  it('保留 {value} 对象的样式字段', () => {
    const out = zeroSeriesData({
      series: [
        {
          type: 'bar',
          data: [{ value: 8, itemStyle: { color: '#fff' } }],
        },
      ],
    })
    const data = (out.series as Array<{ data: Array<{ value: number; itemStyle: { color: string } }> }>)[0].data
    expect(data[0].value).toBe(0)
    expect(data[0].itemStyle.color).toBe('#fff')
  })

  it('归零雷达系列的多维 value', () => {
    const out = zeroSeriesData({
      series: [{ type: 'radar', data: [{ name: 'A', value: [10, 20, 30] }] }],
    })
    const data = (out.series as Array<{ data: Array<{ value: number[] }> }>)[0].data
    expect(data[0].value).toEqual([0, 0, 0])
  })

  it('保留 tooltip formatter 等函数（structuredClone 会抛错的场景）', () => {
    const formatter = (params: unknown) => String(params)
    const out = zeroSeriesData({
      tooltip: { formatter },
      series: [{ type: 'bar', data: [5, 9] }],
    })
    const tooltip = (out as { tooltip?: { formatter?: unknown } }).tooltip
    expect(tooltip?.formatter).toBe(formatter)
    expect(tooltip?.formatter).toBeTypeOf('function')
    const data = (out.series as Array<{ data: number[] }>)[0].data
    expect(data).toEqual([0, 0])
  })
})
