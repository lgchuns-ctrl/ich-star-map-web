# 非遗星图——国家级非物质文化遗产项目传承观察

《非遗星图》是一份面向全国大学生数字媒体科技作品及创意竞赛的数字人文数据研究作品。作品以国家级非物质文化遗产代表性项目名录（含扩展名录）与国家级代表性传承人公开名单为基础，构建可交互的“非遗星图”：通过全国地图、批次时间轴、十大类别星系、传承资源观察与省份对比实验室，回答“国家级非遗项目分布在哪里、类别结构如何、公开传承资源覆盖如何”等问题。

> 本项目为第一件参赛作品，也是后续批量开发交互数据网站的技术试验项目。

## 核心问题

1. 国家级非遗项目及子项主要分布在哪些地区？
2. 不同省级地区的类别结构有什么差异？
3. 不同批次的新增与扩展情况如何变化？
4. 十大类别在空间与时间上的分布有何特点？
5. 各地区国家级代表性传承人公开配置是否相对充足？
6. 项目数量、类别多样性与传承人配置之间有什么关系？

## 重要口径

- **独立项目**：国家级名录中拥有独立项目编号的条目（如 Ⅰ-1 苗族古歌）。
- **地区子项**：同一项目在不同申报地区形成的记录（3610 条口径）。
- **传承资源指标**：仅基于公开国家级名录与国家级代表性传承人数据构建，反映公开数据中的资源配置与覆盖情况，**不代表官方濒危等级或保护成效评价**。

## 技术栈

- 数据处理：Python 3.11+、requests、pandas、BeautifulSoup4、lxml、openpyxl、pydantic、tenacity、pytest
- 前端：Vue 3、TypeScript、Vite、ECharts、Pinia、Vue Router
- 部署：GitHub Pages（静态资源，运行时不依赖在线接口）

## 快速开始

### 1. Python 环境

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. 小规模采集（示例）

```bash
python scripts/collect/collect_ihchina.py --max-records 200 --interval 1.0
```

原始响应归档在 `data/raw/projects/`，原始记录流归档在 `data/raw/projects/projects_raw.jsonl`，请求日志在 `data/raw/request_logs/request_log.csv`。

### 3. 清洗与验证

```bash
python scripts/clean/clean_pilot.py
python scripts/validate/validate_pilot.py
python scripts/clean/clean_full.py          # 全量：子项/项目/传承人/关联
python scripts/validate/validate_full.py
```

输出：

- `data/interim/pilot_projects.csv`（清洗后试点数据）
- `data/reports/pilot_collection_report.json`（采集报告）
- `data/reports/validation_report.json`（验证报告）

### 4. 导出前端数据

```bash
python scripts/export/export_full_json.py
```

输出到 `web/public/data/`。

### 4b. 全量采集与数据分析

```bash
# 十大门类项目/子项（type=1..10，约 3610 条）
python scripts/collect/collect_ihchina.py --scope category --value 1 --max-records 1000
# 代表性传承人（约 3995 条）
python scripts/collect/collect_inheritors.py --max-records 4200
# 阶段D 分析（地区/批次/类别/传承资源 + 可追溯结论）
python scripts/analyze/analyze_full.py
```

### 5. 前端运行与构建

```bash
cd web
npm install
npm run dev        # 本地开发 http://localhost:5173
npm run build      # 产物在 web/dist
npm run preview    # 预览构建产物
```

### 6. 测试

```bash
python -m pytest tests -q
cd web
npm run type-check
npm test
npm run build
```

## 全量数据状态（阶段A-D）

- 真实公开数据：项目/子项 3610 条（1557 个独立项目）、传承人 3995 条，与官方汇总比对一致（传承人含第六批，口径差异见质量报告）；
- 数据清洗与验证：全部质量检查通过（0 缺失、0 重复、地区映射全部成功、传承人匹配率 99.35%）；
- 前端：单页长滚动（锚点导航 + 滚动高亮）+ 省级地图 + 批次演化 + 类别星系 + 传承资源观察 + 省份对比 + 搜索 + 数据方法；
- 冒烟测试：headless Chrome 渲染首页与地图页，无页面 JS 错误；
- 构建产物：`web/dist`（见 [网页设计说明](docs/网页设计说明.md) 中的体积分析）。

## 部署到 GitHub Pages

1. 将仓库推送到 GitHub，开启 Pages 并选择 `GitHub Actions` 部署。
2. 使用仓库内 `.github/workflows/deploy.yml`（构建 `web/dist` 并发布到 `gh-pages`）。
3. 若部署在非根路径，修改 `web/vite.config.ts` 中的 `base`。

## 目录结构

```text
├─ data/                # 原始/中间/清洗/网页数据与报告
│  ├─ raw/              # 原始数据（永久保留，不被覆盖）
│  ├─ interim/          # 中间数据
│  ├─ processed/        # 清洗后数据
│  ├─ manual_corrections/ # 人工修正记录
│  └─ reports/          # 数据质量报告
├─ scripts/             # collect/parse/clean/validate/analyze/export
├─ tests/               # Python 测试
├─ web/                 # Vue 3 + TypeScript + Vite 前端
├─ docs/                # 项目文档与参赛材料
└─ work.md              # 开发过程日志
```

## 文档索引

- [项目背景与竞赛调研](docs/项目背景.md)
- [数据源登记表](docs/数据源登记表.md)
- [数据字典](docs/数据字典.md)
- [数据采集说明](docs/数据采集说明.md)
- [数据清洗说明](docs/数据清洗说明.md)
- [指标定义](docs/指标定义.md)
- [数据质量报告](docs/数据质量报告.md)
- [网页设计说明](docs/网页设计说明.md)
- [部署说明](docs/部署说明.md)
- [参赛作品说明书](docs/参赛作品说明书.md)
- [答辩演示脚本](docs/答辩演示脚本.md)

## 免责声明

本项目相关指标基于公开国家级名录及国家级代表性传承人数据构建，仅反映公开数据中的资源配置与覆盖情况，不代表官方濒危等级或保护成效评价。本项目为高校学生竞赛作品，所有数据仅用于学术研究与展示。
