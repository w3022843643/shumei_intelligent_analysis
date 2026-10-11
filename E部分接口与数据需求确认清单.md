# E 部分接口与数据需求确认清单

> 发给：B、C、D  
> 负责人：E（RAG 智能体、录像计数、入口短时预测）  
> E 仓库：<https://github.com/w3022843643/shumei_intelligent_analysis>  
> 服务契约：仓库内 `E_SERVICE_CONTRACT.md`  
> 当前版本：`0.4.0`，测试 `26 passed`

E 侧已提供可安装、可导入的 Python 包。为避免后续返工，请 B、C、D 分别确认以下内容；如有修改，请直接写明字段或原因。

## 一、E 当前已提供

- 包名：`shumei-intelligent-analysis`
- 安装方式：在 `api_platform/` 环境执行 `pip install -e ..\intelligent_analysis`
- 统一服务入口：`intelligent_analysis.service`
- 已导出函数：
  - `health()`
  - `answer_message()`
  - `index_document()` → 返回 `pending + job_id`
  - `process_document_index()` → Worker 调用，解析 PDF/TXT/MD 并建索引
  - `reindex_documents()` → 返回 `job_id + pending_count`
  - `save_knowledge_index()` / `load_knowledge_index()` → JSON 持久化
  - `analyze_video()` → 返回 `queued` 作业和完整配置
  - `get_camera_counts()` → 当前返回 `analysis_not_ready`
  - `forecast_short_term()` → 当前返回 `data_insufficient`
  - `forecast_from_count_history()` → 有历史计数时返回 ready 预测点
- 已实现：
  - PDF/TXT/MD 文档解析、切分、TF-IDF 关键词检索
  - 知识索引 JSON 保存与加载
  - 引用（含 `date` 字段）和证据不足返回
  - `used_metric_queries` 字段预留
  - 质心跟踪器（`CentroidTracker`）
  - 虚拟线越线判断与左右侧进出方向计数（`VirtualLineCounter`）
  - 人工标注 MAE 校验（`validate_counts()`）
  - YOLOv8 检测包装、OpenVINO 延迟加载、视频读取包装
  - 滚动基线预测、预测区间（lower/upper）、walk-forward 回测
  - 全部算法均有单元测试，不伪造真实结果

## 二、请 C 确认：数据、资料与授权

> 说明：E 已检查 C 仓库 `anhui-tourism-transport-visualization`。当前 C 的 `source_registry.json` 为空，仓库内无知识文档原件、无视频文件、无人工标注样本。以下为 E 仍需 C 提供或确认的内容。

### 1. 知识文档

请提供或确认：

- 文档名称
- 发布单位
- 原始链接
- 发布日期
- 适用起止时间
- 文件格式：PDF/TXT/MD
- 使用权限或授权说明
- 文档对应景区、交通站点、机场或区域

### 2. 授权录像

请提供或确认：

- 视频文件
- 视频 ID 或命名规则
- 景区 ID
- 摄像头 ID
- 摄像头对应入口名称
- 录制开始和结束时间
- 虚拟线建议位置（`x1,y1,x2,y2`，0—1 归一化坐标）
- 镜头视角下进入景区的方向：左/右
- 授权记录 ID
- 视频是否允许在页面回放

### 3. 人工标注样本

请提供：

- 标注视频片段
- 时间窗口（`window_start` / `window_end`）
- 人工统计的进入人数
- 人工统计的离开人数
- 标注人或标注版本
- 是否存在遮挡、摄像头中断、重复经过等情况

### 4. 指标查询范围

C 的 `metric_dictionary.json` 已定义以下指标，E 确认口径：

| 指标 code | 名称 | 单位 | 适用实体 |
|---|---|---|---|
| `scenic_visits` | 景区接待人次 | 人次 | scenic |
| `rail_departures` | 铁路发送人次 | 人次 | rail_station |
| `airport_throughput` | 机场旅客吞吐量 | 人次 | airport |
| `camera_entries` | 入口估计进入人次 | 人次 | camera |
| `camera_exits` | 入口估计离开人次 | 人次 | camera |

请确认 E 是否可通过 D 注入的查询函数读取 `camera_entries` / `camera_exits` 的历史计数序列，用于短时预测。

### 5. C 包导出方式

C 仓库 `04-DE调用契约.md` 写明对外导出 `create_store(settings.database_url)`。请确认：
- D 环境安装 C 包后，`from data_foundation import create_store` 是否可用
- E 的 Worker 是否通过 D 注入的 C store 接口读写知识片段、计数和预测，而不是直接连数据库

## 三、请 D 确认：函数调用、作业与错误状态

### 1. 服务函数签名

请确认 `E_SERVICE_CONTRACT.md` 中以下函数是否满足后端调用：

- `answer_message()`
- `index_document()` / `process_document_index()`
- `reindex_documents()`
- `analyze_video()`
- `get_camera_counts()`
- `forecast_short_term()`
- `forecast_from_count_history()`

如不满足，请指出需要修改的函数名、参数或返回结构。

### 2. HTTP 路由与函数映射

请确认以下路由分别调用哪个 E 函数：

- `POST /assistant/chat` → `answer_message()`
- `POST /knowledge/documents` → `index_document()`（入队）+ `process_document_index()`（Worker）
- `POST /knowledge/reindex` → `reindex_documents()`
- `POST /videos/{video_id}/analyses` → `analyze_video()`
- `GET /videos/{video_id}/counts` → `get_camera_counts()`
- `POST /videos/{video_id}/short-forecast` → `forecast_short_term()`

### 3. C 包导入不一致问题

D 的 `app/core/providers.py` 中期望 C 导出 `new_auth_store()`，但 C 仓库 `04-DE调用契约.md` 和代码实际导出的是 `create_store()`。请 D 确认：
- 是 D 侧改名适配 C 的 `create_store()`，还是 C 需要补一个 `new_auth_store()` 别名
- 这个问题会导致 D worker 启动时导入 C 包失败

### 4. 作业状态

请确认 E 返回 `queued` 后，D 的作业表和 `/jobs/{job_id}` 需要哪些字段：

- `job_id`
- `analysis_id`
- `status`
- `type`
- `started_at`
- `finished_at`
- `processed_count`
- `error_summary`

### 5. 未就绪状态处理

请确认以下状态如何通过 HTTP 返回：

- `analysis_not_ready`
- `data_insufficient`
- `quality_insufficient`
- `insufficient_evidence`
- `metric_tool_unavailable`

### 6. 指标查询注入

请确认 E 的智能体如何获得数值查询能力：

- 由 D 注入受约束查询函数
- 查询白名单由 C/D 提供
- E 不直接拼接 SQL
- 数值回答必须保留查询时间、指标和来源

### 7. Worker 对接 C store

按 C 的 DE 契约，E Worker 需要：
- 领 `knowledge_index` 作业 → 调 `knowledge.begin_index` → 解析后 `write_chunks` → `activate_index_version`
- 领 `video_analysis` 作业 → 调 `video.begin_analysis` → 跑计数后 `write_counts` → `complete_analysis`
- 预测完成后调 `forecasts.save_short_forecast`

请 D 确认：E Worker 是直接调用 C store 的这些方法，还是通过 D 封装的接口调用？

### 8. 环境变量

E 不直接负责 MySQL 迁移。后续如需要以下配置，请确认变量命名：

- RAG 索引路径
- 模型权重路径
- OpenVINO 设备
- 视频处理临时目录
- 计数结果存储路径

## 四、请 B 确认：页面展示与交互

### 1. 智能体对话页

请确认是否展示：

- 回答正文
- 数据时间范围
- 文档引用
- 指标引用
- 事件引用
- 证据不足提示
- 限制说明
- 跳转图表或来源详情入口

### 2. 引用展示格式

每条引用字段：

- 类型：文档/指标/事件
- 标题
- 链接
- 日期（`date`）
- 片段 ID（`chunk_id`）

### 3. 录像回放页

请确认是否展示：

- "录像回放"标识
- 录制开始和结束时间
- 摄像头/入口名称
- 视频时间轴
- 进入人数
- 离开人数
- 计数质量
- 短时预测
- 人工校验结果

### 4. 计数与预测图表

请确认：

- 时间粒度：1/5/15 分钟
- `entries` 和 `exits` 是否分开展示
- 预测值和真实值的线型
- 数据不足或质量不足的空状态
- 是否需要预测区间（lower/upper 阴影带）

### 5. 口径文案

页面必须使用以下表述：

- 视频模块：`录像回放`
- 视频计数：`指定入口估计通行人数`
- 短时预测：`指定入口未来15—60分钟通行人数`

不得写成：

- 实时在园人数
- 全景区客流
- 全景区实时人数

## 五、请各方按此格式回复

### C 回复

```text
C 确认：
1. 知识文档：已提供/未提供，预计时间：
2. 授权视频：已提供/未提供，预计时间：
3. 人工标注：已提供/未提供，预计时间：
4. camera_entries/exits 历史计数：已提供/未提供，预计时间：
5. create_store 导出方式：确认/需修改：
```

### D 回复

```text
D 确认：
1. E 服务函数签名：确认/需修改：
2. HTTP 路由映射：确认/需修改：
3. new_auth_store vs create_store 不一致：D 适配/C 补别名：
4. 作业状态字段：确认/需修改：
5. 错误状态映射：确认/需修改：
6. 指标查询注入方式：确认/需修改：
7. Worker 对接 C store 方式：直接调/经 D 封装：
```

### B 回复

```text
B 确认：
1. 对话页展示字段：确认/需修改：
2. 引用展示格式：确认/需修改：
3. 录像回放页字段：确认/需修改：
4. 计数与预测图表格式：确认/需修改：
5. 口径文案：确认/需修改：
```

## 六、E 开发进度

| 项目 | 状态 |
|---|---|
| Python 包骨架与可安装 | ✅ 完成 |
| PDF/TXT/MD 解析与切分 | ✅ 完成 |
| TF-IDF 索引与 JSON 持久化 | ✅ 完成 |
| 带来源的 RAG 问答 | ✅ 完成 |
| 虚拟线越线与进出计数算法 | ✅ 完成 |
| 质心跟踪器 | ✅ 完成 |
| 人工标注 MAE 校验 | ✅ 完成 |
| 滚动基线预测 + 区间 + 回测 | ✅ 完成 |
| YOLOv8/OpenVINO/视频读取包装 | ✅ 完成（待真实模型和视频） |
| Worker 对接 C store（write_chunks/write_counts/save_forecast） | 🔄 开发中 |
| 接入真实知识文档建索引 | ⏳ 等 C 提供文档 |
| 接入授权视频跑真实计数 | ⏳ 等 C 提供视频和标注 |
| 用真实计数历史跑预测 | ⏳ 等 C 提供历史序列 |
