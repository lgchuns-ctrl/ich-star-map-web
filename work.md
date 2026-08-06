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
