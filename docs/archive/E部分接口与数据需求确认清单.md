# E 部分接口与数据需求确认清单

> 历史归档：本清单为旧进出计数需求。0.5.0 已改为 `camera_visible_people`，最新接收与缺口见 `docs/E050交付与联调说明.md`。

> 负责人：E（RAG 智能体、授权录像计数、入口短时预测）
> E 仓库：<https://github.com/w3022843643/shumei_intelligent_analysis>
> 服务契约：仓库内 `E_SERVICE_CONTRACT.md`
> 当前版本：`0.4.0`，测试 **34 passed**（含 1 个对接真实 C store 的集成测试）
> 更新日期：2026-10-11

---

## 一、E 当前已提供（不依赖外部素材部分全部完成）

- 可安装 Python 包：`shumei-intelligence-analysis`
- 统一服务入口：`intelligent_analysis.service`
- 已导出函数：
  - `health()`
  - `answer_message()`
  - `index_document()` / `process_document_index()` / `reindex_documents()`
  - `save_knowledge_index()` / `load_knowledge_index()`
  - `analyze_video()` / `get_camera_counts()`
  - `forecast_short_term()` / `forecast_from_count_history()`
- 已实现能力：
  - PDF/TXT/MD 解析、切分、TF-IDF 检索、JSON 持久化
  - 带来源引用的问答、证据不足返回
  - 质心跟踪器、虚拟线越线进出计数、边界点处理
  - 人工标注 MAE 校验
  - YOLOv8 / OpenVINO / 视频读取延迟加载包装
  - 滚动基线预测、预测区间、walk-forward 回测
  - Worker 适配层，**已按 C v0.1.0 真实签名对齐**
    - 知识：`begin_index → write_chunks → activate_index`，与 `complete_job` 同事务
    - 视频：`write_counts（CountInput）→ complete_analysis`，与 `complete_job` 同事务
    - lease 用 C 的 `JobLease` 转换；无 detector 时只让该作业失败，Worker 不退出

---

## 二、D：已全部确认 ✅（无待办）

D 已正式回复《D 回复 E：函数契约确认与路由映射》，以下均确认、无修改意见：

| 事项 | 状态 |
|---|---|
| 9 个 E 函数签名 | ✅ 确认 |
| 6 条 HTTP 路由 ↔ E 函数映射 | ✅ 确认 |
| JobOut 补 `analysis_id` | ✅ 已补 |
| 错误状态 HTTP 映射 | ✅ 确认（见下） |
| 指标查询由 D 注入、E 不碰 SQL | ✅ 确认 |
| 5 个环境变量 | ✅ 定稿 |
| `new_auth_store/create_store` 不一致 | ✅ D 已修复（两者回退） |

错误 HTTP 映射（已定稿）：

| E 状态 | HTTP |
|---|---|
| `analysis_not_ready` | 409 |
| `data_insufficient` / `quality_insufficient` / `insufficient_evidence` | 200 |
| `metric_tool_unavailable` | 503 |

环境变量（已定稿）：`RAG_INDEX_PATH`、`DETECTOR_WEIGHTS_PATH`、`OPENVINO_DEVICE`、`VIDEO_TMP_DIR`、`COUNTS_STORAGE_PATH`。

**D 的下一步（D 负责，E 配合）：**
1. 六条路由从 503/pending 桩切换为实调 E 函数
2. D worker 启动 E `AnalysisWorker` 并注入 C store
3. 切实调时如遇字段/调用问题，E 即时配合

---

## 三、C：v0.1.0 已验收，仍欠真实素材 ⏳

**已完成：**
- E 已安装 C wheel，C 官方冒烟测试 `--part e` **10 项全过**
- E Worker 已与 C 真实存储打通，知识索引链路端到端集成测试通过

**C 仓库/交接包现状：** `source_registry.json` 为空，无真实文档、录像、标注、计数历史。以下为 E 仍需 C 交付的真实内容：

### 1. 知识文档（真实，含元数据）
- 文档原件（PDF/TXT/MD）
- 名称、发布单位、原始链接、发布日期、适用起止时间
- 使用权限/授权说明
- 对应景区 / 交通站点 / 机场 / 区域

### 2. 授权录像
- 视频文件及视频 ID、授权记录 ID
- 景区 ID、摄像头 ID、对应入口名称
- 录制开始/结束时间
- 虚拟线坐标（`x1,y1,x2,y2`，0—1）
- 镜头下进入方向（左/右）
- 是否允许页面回放

### 3. 人工标注样本
- 标注片段、时间窗口（`window_start/end`）
- 人工统计进入/离开人数、标注版本
- 遮挡、摄像头中断、重复经过等情况说明

### 4. 计数历史序列
- `camera_entries` / `camera_exits` 历史计数（同入口、连续窗口）
- 供 15—60 分钟短时预测训练和回测

> 指标口径 E 已按 C `metric_dictionary.json` v0.1.0 确认：
> `scenic_visits`、`rail_departures`、`airport_throughput`、`camera_entries`、`camera_exits`。

---

## 四、B：请确认页面展示（尚未回复）

### 1. 智能体对话页
- 回答正文、数据时间范围、文档/指标/事件引用、证据不足提示、限制说明、跳转入口

### 2. 引用字段
- 类型、标题、链接、日期（`date`）、片段 ID（`chunk_id`）

### 3. 录像回放页
- "录像回放"标识、录制起止时间、入口名称、时间轴、进入/离开人数、计数质量、短时预测、人工校验结果

### 4. 计数与预测图表
- 粒度 1/5/15 分钟、entries/exits 分开展示、预测与真实线型、区间阴影带（lower/upper）、空状态

### 5. 口径文案（必须遵守）
- 用：`录像回放`、`指定入口估计通行人数`、`指定入口未来15—60分钟通行人数`
- 禁用：`实时在园人数`、`全景区客流`、`全景区实时人数`

---

## 五、E 开发进度

| 项目 | 状态 |
|---|---|
| 包骨架与可安装 | ✅ |
| PDF/TXT/MD 解析、切分、TF-IDF、持久化 | ✅ |
| 带来源 RAG 问答 | ✅ |
| 跟踪 / 越线计数 / 边界处理 | ✅ |
| 人工标注 MAE 校验 | ✅ |
| 短时预测 + 区间 + 回测 | ✅ |
| YOLO/OpenVINO/视频读取包装 | ✅（待真实模型） |
| Worker 对接真实 C store | ✅（含集成测试） |
| D 契约确认 | ✅ |
| 真实文档建索引 | ⏳ 等 C |
| 授权视频真实计数 | ⏳ 等 C |
| 真实历史跑预测 | ⏳ 等 C |
| B 页面字段确认 | ⏳ 等 B |
