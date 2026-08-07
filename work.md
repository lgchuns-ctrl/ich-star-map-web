# 开发过程日志（work.md）

> 本文件记录《非遗星图——国家级非物质文化遗产项目传承观察》开发过程中每一阶段的实际工作、命令、结果与问题。所有结论以仓库内代码、数据与文档为准。

## 2026-08-06 阶段A：工作区检查、竞赛调研、项目初始化

### 已完成

1. 检查工作区：初始仅存在空文件 `work.md`；后检测到新增参考文件《黑话.pptx》并已读取其全部 20 页文本。
2. 工具链确认：Python 3.13.2、Node v24.14.1、Git 2.53.0；requests/pandas/bs4/lxml/openpyxl/pydantic 已安装；npm 在 PowerShell 需使用 `npm.cmd`（执行策略限制）。
3. 竞赛调研（网络公开信息）：
   - 竞赛名称：全国大学生数字媒体科技作品及创意竞赛，官网 cmit.cn；
   - 2025 年为第十三届，主办中国人工智能学会；赛制为校赛→赛区赛→全国总决赛；自主命题/指定命题两大赛项；报名截止约 2025-09-21；2026 年通知未发布，以官网为准。
4. 数据源发现与探测：
   - 确认中国非物质文化遗产网公开 JSON 接口：`http://www.ihchina.cn/Article/Index/getProject.html`；
   - 接口返回 total=3610（国家级项目子项口径），支持 province/rx_time/type/cate/keywords/category_id/limit/p 参数；
   - 实测 limit=100 可正常返回 100 条；字段包含 num/title/type/cate/rx_time/project_num/province/address/city/area/content 等。
5. 项目初始化：Git 仓库初始化（尚无提交）；创建 data/scripts/tests/web/docs 目录骨架。

### 待办

- 探测接口筛选参数语义（type/cate/rx_time/province）并确定试点采集范围；
- 编写采集、清洗、验证、导出脚本；
- 采集 100–200 条真实记录；
- 创建 Vue 3 + TypeScript + Vite 前端并实现地图、类别筛选、项目详情；
- 构建验证、README、Git 提交。

## 2026-08-06 阶段A/B 完成记录

### 已完成（按顺序）

1. **接口探测**：确认官网页面 JS 传参使用数字 ID；核验 type(1-10)/rx_time(1,2,3,4,10)/cate(1,2)/province(行政区码)/category_id=16/limit 语义；确认详情页 `/project_details/{id}.html` 可达；确认 DataV GeoJSON 可达（35 要素）。
2. **采集器**：`scripts/collect/collect_ihchina.py`（UA/间隔/超时/指数退避/断点续传/缓存/日志/失败记录/去重/dry-run/`--no-resume`）；实测采集民间文学门类 251 条、3 请求 0 失败。
3. **GeoJSON 下载**：`scripts/collect/download_geojson.py` → `web/public/data/geojson/china.json`（582,522 bytes）。
4. **清洗**：`scripts/clean/clean_pilot.py` → `data/interim/pilot_projects.csv`（251 行）、`data/processed/subitems_pilot.csv`、`projects_pilot.csv`（167 独立项目）；必填字段 0 缺失。
5. **验证**：`scripts/validate/validate_pilot.py` → 采集报告 + 验证报告（8 项检查全部通过）+ 人工抽样清单 20 条。
6. **导出**：`scripts/export/export_pilot_json.py` → `web/public/data/*.json`（metadata/provinces/categories/batches/projects/subitems/search_index/methodology）。
7. **前端**：Vue 3 + TS + Vite 项目（web/），实现首页/全国分布/寻找一项非遗/数据与方法四个视图、ECharts 省级地图、筛选栏、详情抽屉、星空背景。
8. **构建验证**：`npm run type-check` 通过；`npm run build` 成功；headless Chrome 冒烟渲染首页与地图页无 JS 错误。
9. **测试**：Python pytest 18 项通过；前端 vitest 10 项通过。
10. **文档**：README、项目背景、数据源登记表、数据字典、采集说明、清洗说明、指标定义、数据质量报告、网页设计说明、部署说明、参赛作品说明书、答辩演示脚本。
11. **部署**：`.github/workflows/deploy.yml`（GitHub Pages Actions）。

### 实际运行命令

```text
python scripts/collect/collect_ihchina.py --scope category --value 1 --dry-run
python scripts/collect/collect_ihchina.py --scope category --value 1 --max-records 300
python scripts/collect/download_geojson.py
python scripts/clean/clean_pilot.py
python scripts/validate/validate_pilot.py
python scripts/export/export_pilot_json.py
python -m pytest tests -q                 # 18 passed
cd web
npm.cmd install
npm.cmd run type-check                    # passed
npm.cmd test                              # 10 passed
npm.cmd run build                         # success
npm.cmd run preview -- --port 4173        # HTTP 200
chrome --headless=new --dump-dom ...      # 冒烟测试通过
```

### 测试结果

- Python：18/18 通过（编号/地区/批次/类型标准化、数据集成、去重、传承人匹配、指标计算、JSON 导出一致性）。
- 前端：type-check 0 错误；vitest 10/10 通过；生产构建成功。
- 冒烟：`/#/` 与 `/#/map` 渲染正常，地图 canvas 已生成，无页面级 JS 错误。

### 当前数据量

- 原始记录 251（民间文学门类全量）；清洗子项 251；独立项目 167；覆盖省级地区 31。

### 发现的问题

1. 官网接口传中文筛选参数会返回异常数据集（4234 条、字段缺失），必须用数字 ID（已写入文档与采集器参数设计）。
2. `keywords` 服务端检索行为不稳定，试点采用前端本地检索。
3. ECharts 全量引入导致 JS 约 1.16 MB（gzip 395 KB），后续按需引入优化。
4. PowerShell 下 `npm` 别名被执行策略拦截，需用 `npm.cmd`（已在文档注明）。

### 技术选择与依据

- 工作区根目录直接作为项目根（目录名即项目名，避免嵌套 `ich-star-map/` 冗余），保持原始/中间/清洗/网页数据与脚本、文档分离；
- 试点选择完整「民间文学」门类（251 条）而非 100-200 条随机页，换取完整结构验证（多批次、扩展、跨省子项），超出下限约 25% 属有意为之；
- 路由 hash 模式 + `base: './'`：GitHub Pages 非根路径与刷新可用；
- GeoJSON 使用 DataV 公开底图并登记来源与用途限制；
- 试点不引入 GSAP/Papa Parse（暂无用途），符合“不引入大量无实际用途依赖”。

### 需要人工核验

- `data/reports/manual_sample_review.csv`（20 条，核对编号/名称/批次/地区/保护单位）；
- 保护单位名称疑似同一单位的合并（全量阶段统一处理）；
- 地图底图授权范围与最终页面来源标注。

### 下一阶段（阶段C）

- 全量采集十大门类项目与子项（约 3610 条）；
- 采集国家级代表性传承人公开名单并建立关联；
- 输出全量数据质量报告与官方汇总差异报告。

### 如何查看当前效果

```bash
cd web
npm run dev          # 打开 http://localhost:5173
```

或运行 `npm run build && npm run preview` 查看构建产物。

## 2026-08-06 阶段C/D 完成记录（全量数据与分析）

### 已完成

1. **全量项目采集**：探测十大门类总量（1:251、2:431、3:356、4:473、5:213、6:166、7:417、8:629、9:182、10:492，合计 3610），按 type=1..10 逐类采集，47 次请求全部成功；修复采集器终止条件 bug（跨类别去重导致提前停止，改为按 `ceil(total/limit)` 页数终止 + 空页保护）。
2. **传承人采集**：发现官方接口 `/art/representative.html`（total=3995，含 2025 年第六批），40 次请求全部成功。
3. **采集器重构**：抽取 `scripts/lib/collector_base.py` 通用基类（UA/间隔/超时/指数退避/断点续传/缓存/日志/失败记录/去重/dry-run），项目与传承人两个采集脚本复用。
4. **全量清洗**：`scripts/clean/clean_full.py` 输出子项/项目/传承人三张表 + 关联匹配；匹配优先 child_num（子项 project_num）精确键，回退项目编号+省份。
5. **全量验证**：`scripts/validate/validate_full.py`，全部检查通过；发现并记录组合键去重口径调整（加入 project_name）；官方对比：子项 3610/3610、项目 1557/1557、传承人 3995 vs 官方 2023 口径 3059（差异说明：含第六批）。
6. **阶段D 分析**：`scripts/analyze/analyze_full.py` 输出省级/批次/类别/传承人批次/省份×批次热力图 + 7 条可追溯结论（`conclusions.json`）。
7. **全量导出**：`scripts/export/export_full_json.py` 重写 web/public/data（新增 inheritors.json、inheritor_batches.json、conclusions.json、province_comparison.json）。
8. **前端升级**：地图指标切换（子项数/项目数/传承人数/类别覆盖）；新增「传承资源观察」页（指标卡 + 柱状图 + 省级/类别表格 + 批次表 + 指标解释）；首页指标与搜索页文案更新；修复图表容器在数据加载后才渲染导致的初始化时序 bug。
9. **测试**：新增 `tests/test_full.py`（官方总量、调整后去重、匹配率、导出一致性）；pytest 23/23；前端 type-check/vitest 10/10/构建通过。
10. **文档**：数据质量报告、数据采集说明、指标定义、参赛作品说明书、数据源登记表更新为全量口径。

### 实际运行命令

```text
python scripts/collect/collect_ihchina.py --scope category --value {2..10} --max-records 1000
python scripts/collect/collect_inheritors.py --max-records 4200
python scripts/clean/clean_full.py
python scripts/validate/validate_full.py
python scripts/analyze/analyze_full.py
python scripts/export/export_full_json.py
python -m pytest tests -q                    # 23 passed
cd web && npm.cmd run type-check && npm.cmd test && npm.cmd run build
chrome --headless=new --dump-dom ...          # 首页/地图/传承资源/搜索 冒烟通过
```

### 测试结果

- Python 23/23；前端 type-check 0 错误、vitest 10/10、构建成功；4 个页面 headless 渲染无 JS 错误。

### 当前数据量

- 子项 3610（10 类、5 批次）；独立项目 1557；传承人 3995（6 个公布批次，2007/2008/2009/2012/2018/2025）；省级覆盖 33。
- 传承人-子项匹配率 99.35%（匹配 3969、多候选 26、未匹配 0）。

### 关键发现

- 省级子项 TOP：浙江 257、山东 186、山西 182、广东 165、河北 162、江苏 161。
- 类别：传统技艺最多（629 子项/287 项目）；传统戏剧传承人覆盖最高 84.14%，民俗最低 40.24%。
- 跨省项目：格萨(斯)尔 8 省、董永传说 5 省、梁祝传说 4 省。
- 每百子项传承人数省级差异：江苏 141.0、河北 116.1、广东 115.2 …（仅反映公开配置）。

### 需要人工核验

- `data/reports/manual_sample_review_full.csv`（30 条）；
- 传承人多候选 26 条（`data/processed/inheritor_matches.csv`）；
- 保护单位疑似同一单位合并清单（待建立）；
- 传承人 3995 与官方 3059 口径差异的进一步说明（是否含已故传承人，需官方文件核验）。

### 下一阶段（阶段E）

- 五批名录演化时间轴（地图播放 + 堆叠图 + 热力图）；
- 十大类别星系页；
- 省份对比实验室（基于 province_comparison.json）；
- 图表数据下载、分享/海报导出评估；
- ECharts 按需引入，压缩构建体积。

## 2026-08-06 视觉问题修复：首页指标卡中间的黄线

### 问题

用户反馈首页四个指标卡“中间有一条横穿的黄线”。

### 原因（已通过截图像素分析与代码定位确认）

- 首页 hero 区原本设置 `border-bottom: 1px solid var(--line)`（`--line` 为金色半透明 rgba(217,184,119,0.18)）；
- `.metrics-section` 使用 `margin-top: -34px` 将指标卡上移压住 hero 底边，且卡片背景为半透明（rgba(255,255,255,0.035)），导致这条金色边框线从四个指标卡之间透出，看起来像一条横穿卡片的黄线。

### 修复

- `web/src/views/HomeView.vue` 移除 `.hero` 的 `border-bottom`；
- 重新构建：`npm run build` 成功，dist CSS 中已无 hero 边框（剩余 border-bottom 均为页头与表格的正常分隔样式）；
- 首页 headless 渲染正常（指标卡仍显示）。

### 验证

```text
npm.cmd run build   # 通过
chrome --headless=new --dump-dom http://localhost:4173/#/   # 首页渲染正常
```

## 2026-08-06 单页长滚动 + 内容丰富化升级

### 已完成

1. **单页架构**：移除 vue-router，全站改为一个上下滚动的长页面；顶部导航改为 8 个锚点（首页/全国分布/批次演化/类别星系/传承资源/省份对比/寻找非遗/数据与方法），滚动时自动高亮当前区块（IntersectionObserver scrollspy）。
2. **新增内容区块**：
   - 批次演化：新增/扩展堆叠柱 + 累计线、批次×类别堆叠柱、省份×批次热力图（TOP15）；
   - 类别星系：十类别彩色卡片（含迷你占比条）、类别规模分布图、传承人覆盖率对比图；
   - 省份对比实验室：双省选择、6 项对比数据卡、类别结构雷达（占比）、批次对比柱、自动生成的数据差异摘要（仅描述数据，不作因果）。
3. **动效与鼠标效果**：指标数字滚动递增（AnimatedNumber）、区块滚动淡入（Reveal）、卡片悬停上浮+金色描边（hoverable）、全局鼠标跟随微光（MouseGlow，触屏自动关闭）、星空背景、滚动提示。
4. **性能**：所有 ECharts 图表懒加载（进入视口才初始化，useLazyChart），首屏只加载 hero 星场与视口内图表。
5. **测试与构建**：type-check 0 错误、vitest 10/10、vite build 成功；headless 冒烟：8 个区块齐全、`#/timeline` 锚点定位正常、无页面 JS 错误。
6. **文档**：网页设计说明、部署说明、README 更新为单页锚点架构。

### 技术选择

- 移除 vue-router：单页长滚动用原生锚点即可，减少依赖与路由复杂度，深链/刷新仍可用；
- 动效全部用原生 CSS/IntersectionObserver/rAF 实现，不新增 GSAP 依赖（符合“不引入无实际用途依赖”）；
- 省份对比雷达使用“类别占比 %”而非绝对数，避免子项总量差异掩盖结构差异；
- 对比摘要文本由数据计算生成，仅描述数量差异并附免责声明，不写因果结论。

### 待办

- 图表数据下载、分享/海报导出评估；
- ECharts 按需引入压缩体积（当前 JS 约 1.16 MB）。

## 2026-08-06 动效增强 + 说明集中到底部

### 已完成

1. **卡片/文字入场跃动**：Reveal 支持方向（up/left/right）与逐项延迟；指标卡、问题卡、类别卡、特征卡等网格按序错峰滑入；首页 Hero 标题/副标题/按钮逐级上浮。
2. **条形图生长动画**：图表懒加载时机从“提前 240px 预初始化”改为“进入视口才初始化”，配合 ECharts animation（柱状图由 0 生长、热力图格渐显），不再出现条“静静躺着”的效果。
3. **其他动效**：地图与侧栏左右滑入、图表卡左右错峰滑入、比较卡逐项浮现。
4. **说明集中到底部**：删除各区块（首页/地图/演化/类别/传承/对比/搜索/数据）重复的 DataDisclaimer，新增页面最底部「口径说明」区块（锚点 #notes，导航栏新增入口），集中展示数据口径说明、指标定义、使用与版权、数据版本。

### 验证

- type-check 0 错误；vitest 10/10；vite build 成功；
- headless 冒烟：`数据口径说明` 全页仅出现 1 次且位于 `#notes`，动效类（reveal-up/rise）已挂载，无页面 JS 错误。

## 2026-08-06 条形图生长动画修复（两阶段渲染）

### 问题

用户反馈条形图“生长”动画仍不生效。

### 根因（经验证定位）

1. 早期版本图表在进入视口前 240px 就提前初始化，ECharts 首次渲染动画（1000ms）在屏幕外已播完，用户滚动到图表时看到的是静止的满高柱子；
2. ECharts 首次渲染动画依赖初始化与数据渲染时机，单独设置 animation 字段并不可靠。

### 修复

- `web/src/utils/lazyChart.ts` 改为**两阶段渲染**：图表进入视口时先用 0 值数据（关闭动画）渲染一帧，下一帧再渲染真实数据并开启动画（duration 1100ms / update 900ms），强制触发“柱子从 0 长出来”的更新动画；
- 懒加载触发时机收紧为进入视口（rootMargin 0px 0px -40px），动画开始即用户可见；
- 新增 `zeroSeriesData`（数字/对象值/heatmap 三元组/雷达多维值归零）与 4 项单测。

### 验证（真实时间 CDP 采样）

- 编写 `web/scripts/verify_anim.mjs`（Chrome DevTools 协议），真实浏览器采样柱高：
  `t=300ms 21.5px → t=900ms 237.9px → t=2600ms 243px`，动画生长确认生效；
- 无头虚拟时间下 rAF 动画被冻结，不能用于验证动画，已改用真实时间验证；
- type-check 0 错误；vitest 14/14（新增 lazyChart 单测）；vite build 成功。

### 提醒

预览服务器与浏览器可能缓存旧 JS，查看效果前请强制刷新（Ctrl+F5）。

## 2026-08-06 图表空白 bug 修复（structuredClone 与函数）

### 问题

两阶段渲染上线后，以下四个图表变为空白（只剩背景）：
- 省份 × 批次子项热力图（TOP15）
- 类别规模分布
- 传承人覆盖率（按类别）
- 传承人公开数量 TOP15（省级）

### 根因

`zeroSeriesData` 使用 `structuredClone` 深拷贝 ECharts 配置，而配置中的 `tooltip.formatter` 等是**函数**；
`structuredClone` 遇到函数抛 `DataCloneError`，导致初始化中断、图表空白。正好这四个图表都带自定义 formatter，其余图表不受影响。

### 修复

- `web/src/utils/lazyChart.ts`：`zeroSeriesData` 改用保留函数的深拷贝（`cloneKeepFns`），不再抛错；
- 两阶段渲染整体加 try/catch 兜底：任何异常都回退为直接渲染真实数据，避免空白图表；
- 新增回归单测：确认 formatter 函数被保留且数据仍被归零（vitest 15/15 通过）。

### 验证（真实浏览器像素统计）

- `web/scripts/verify_charts.mjs`：滚动整页后统计各 canvas 不透明像素数：
  - 热力图 341833、类别规模 54205、覆盖率 68467、传承人 TOP15 166813、地图 55543、演化柱 54205/59072、对比雷达 28318/55349；
  - 星空画布仅 478（星星），其余图表均有大量绘制内容，空白问题确认解决；
- type-check 0 错误；vitest 15/15；vite build 成功；三个区块 headless 冒烟无 JS 错误。

## 2026-08-06 图表动画触发时机优化（滚动到才播）

### 问题

用户反馈：传承人公开数量 TOP15 条形图的生长动画在进站时就已经播完，没有等到滚动到该图表时才开始。

### 原因

图表懒加载原使用 `rootMargin: '0px 0px -40px 0px'`：图表刚进入视口边缘 40px 就初始化并播放 1.1s 动画；正常滚屏速度下，用户看到图表时动画已结束；浏览器滚动恢复（刷新后回到上次位置）时也会在页面加载阶段触发。

### 修复（web/src/utils/lazyChart.ts）

- 懒加载触发条件改为 `threshold: 0.6`（图表约 60% 进入视口才初始化）＋ `rootMargin: 0`，不再提前；
- 生长动画放慢并延后：duration 1600ms / update 1300ms，真实数据渲染延迟 180ms；
- 这样动画从“用户看到图表”的瞬间开始，滚得快也能看到大部分生长过程。

### 验证（真实浏览器 CDP 时序采样）

- 进站未滚动：TOP15 画布不存在（NO_CHART）→ 未提前初始化；
- 滚动到「传承资源」区块后：
  - +0/250ms：尚未初始化；
  - +600ms：画布出现，不透明像素 7,165（柱子刚起步）；
  - +1100ms：165,992（基本长满）；
  - +2000ms：166,813（完全长满）。
- type-check 0 错误；vitest 15/15；vite build 成功。

验证脚本：`web/scripts/verify_lazy.mjs`（进站懒加载检查）、`web/scripts/verify_timing.mjs`（动画时序采样）。

## 2026-08-06 部署上线记录（GitHub Pages）

### 经过

1. 推送到 GitHub 仓库 `lgchuns-ctrl/ich-star-map`：修复 git 代理（走 127.0.0.1:7892）、清除误提交的 57MB PPT（filter-repo，仓库 68.7MB→9.75MB）、修复 vitest 4 与 vite 5 不兼容导致的 CI EUSAGE（降级 vitest 3）。
2. GitHub Pages 的 GitHub Actions 部署管道在该账号下反复失败（queued 卡死 → in_progress 卡死 → deployment failed）。已排查并修复配置（Source=GitHub Actions、API 取消旧部署、configure-pages、cancel-in-progress:false、20 分钟超时、删除重建 Pages、新仓库测试）；产物结构验证正确（index.html 在根），邮箱已验证——判定为账号/管道级问题。
3. 最终改用 gh-pages 分支 + Deploy from a branch 传统管道：构建 web/dist 提交到独立 gh-pages 分支（含 .nojekyll），Pages Source 设为 gh-pages / (root)，部署成功。

### 上线地址

- 网站：https://lgchuns-ctrl.github.io/ich-star-map-web/
- 仓库：https://github.com/lgchuns-ctrl/ich-star-map-web

### 后续更新网站的流程（Actions 管道不可用时的替代）

```powershell
cd F:\大创\非遗星图——国家级非遗项目传承观察
cd web && npm run build && cd ..
git checkout gh-pages
Copy-Item -Recurse -Force web\dist\* .
git add -A
git commit -m "update site"
git push origin gh-pages
git checkout main
```

注意：推 main 会触发 Deploy to GitHub Pages 工作流，其 deploy 步骤在此账号下仍会失败（红色叉），不影响已上线站点；可到 Actions 设置中禁用该工作流避免噪音。

## 2026-08-07 流程复盘与复用手册

- 新增 `docs/开发流程复用手册.md`：从调研立项→数据管道→前端→测试构建→部署上线的完整流程 + 常见问题速查表 + 上线验收清单，供后续项目复用。

## 2026-08-07 全屏星空背景

- 星空层从首页 hero 提升为全局固定背景（`Starfield.vue` 改为 `position: fixed; inset: 0`，按 window 尺寸绘制），滚动到任何位置都持续显示；
- 内容层（main/页脚）置为 `position: relative; z-index: 1` 保证可读性；触屏设备与 prefers-reduced-motion 行为不变；
- 验证：type-check/build 通过；CDP 实测滚动前与滚动到页面底部，星空画布始终固定铺满视口（1262x748）。

## 2026-08-07 线上更新记录（全屏星空上线）

- 本地重新构建 → 更新 gh-pages 分支（31f7cc6）→ `git push origin gh-pages` 完成上线；同时推送 main（de66902）备份；
- 线上验证：https://lgchuns-ctrl.github.io/ich-star-map-web/ HTTP 200，bundle 为 index-CWevQMEc.js（星空版），数据文件正常；
- 从本次起，push 可在授权会话内由主代理直接完成，无需用户手动执行。

## 2026-08-07 语音交互定制可视化 MVP

- 新增「自定义观察」区块（锚点 custom）：文字/语音输入 → 本地规则意图解析 → 真实数据生成定制图表。
- 实现：`web/src/services/intentParser.ts`（地区/类别/指标/模板识别 + 同义词表）、`web/src/sections/CustomObservationSection.vue`（输入、Web Speech API 语音、示例卡、结果面板、三模板图表）、导航与 App 挂载。
- 首批模板：双省对比（类别柱状 + 指标卡）、类别分布（单省类别图/全国类别TOP）、地区排名（按指标 TOP10）。
- 验证：type-check 0 错误；vitest 23/23（新增 8 项解析测试）；构建成功；CDP 端到端点击示例 → 三个模板均正确解析并绘制图表（绘制像素 9.9万/14.6万/11.6万）。
- 语音识别用浏览器 Web Speech API（zh-CN），不支持/无权限时自动提示并降级文字输入，核心功能离线可用。

## 2026-08-07 语音定制可视化版本上线

- 重新构建 → 更新 gh-pages 分支（7f3168b）→ 推送 gh-pages 上线 + 推送 main（32dad6b）备份；
- 线上验证：https://lgchuns-ctrl.github.io/ich-star-map-web/ HTTP 200，bundle 为 index-D1UZAm4j.js，部署 JS 含「自定义观察」导航项；
- 用户确认后由主代理独立完成构建→上线→验证闭环。

## 2026-08-07 自定义观察功能扩充（模板/导出/材料）

1. **意图解析扩充**：新增 批次趋势/地图分布/传承资源对比 三个模板；支持更多口语表达（“前五名/历年/看下全国/粤桂/鲁苏”等）；无效输入返回错误与示例；地区按原文顺序解析。测试用例扩至 **55 项**（总数 70 全绿）。
2. **新模板图表**：批次趋势折线（可限定类别/地区）、全国地图高亮（可限定类别/指标）、传承资源对比（传承人/覆盖率/每百子项卡片 + 柱状图）。
3. **导出**：结果面板新增「导出图片」（PNG，2x）与「导出数据」（JSON，含口径与免责声明）。
4. **参赛材料**：参赛作品说明书与答辩脚本更新，把「语音意图驱动的定制化可视化」列为核心创新点，答辩路线加入自定义观察演示段。
5. 验证：type-check 0 错误；vitest 70/70；构建成功；CDP 端到端三个新模板均正确解析并绘制（像素 13.8万/3.4万/17.2万），导出按钮齐全。

## 2026-08-07 自定义观察扩充版上线

- 重新构建 → 更新 gh-pages 分支（3d91a1e）→ 推送上线；
- 线上验证：HTTP 200，bundle index-zpsNEVnt.js；部署 JS 中含 批次趋势/地图分布/传承资源对比/导出图片/导出数据（Unicode 转义校验 6/6 True）；
- main 同步备份（eb71481 已推送，本次 docs 提交随后推送）。

## 2026-08-07 解析词典扩充 + 分享/海报导出

1. **解析词典扩充**：新增地区别称（齐鲁/燕赵/荆楚/潇湘/八桂/陇）、类别别名（戏曲/相声/评书/武术/民歌/剪纸/陶瓷/传说/节庆/刺绣）；指标口语（数量/多少/总数）；排行/趋势/地图口语（排行榜/榜单/走势/分布图/地图上/这些年/哪个最多…）；单地区对比给出错误提示。测试用例 **55 → 80 项**（总数 95 全绿）。
2. **分享链接**：结果面板「分享」按钮生成 `?q=原话#custom` 链接（Web Share API 或复制剪贴板），打开该链接自动解析并生成对应图表。
3. **海报导出**：「导出海报」用 canvas 绘制 1080×1440 海报（标题、解析结果、图表、数据版本、来源与免责声明）下载 PNG，无新增依赖。
4. 验证：type-check 0 错误；vitest 95/95；构建成功；CDP 端到端：分享链接自动加载 ✓、别名“齐鲁和燕赵比一比”正确解析 ✓、按钮（导出图片/数据/海报/分享/清除）齐全 ✓、海报导出无异常。
