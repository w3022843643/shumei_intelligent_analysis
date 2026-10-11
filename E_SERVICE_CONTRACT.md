# E 服务函数契约

> 版本：0.4.0。HTTP 路由由 D 提供，E 只导出服务函数。未实现完成的功能返回明确状态，不伪造结果。

## 安装

在 `api_platform/` 的虚拟环境中执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ..\intelligent_analysis
```

## 统一入口

模块：`intelligent_analysis.service`

### `health()`

返回模块版本和就绪状态。

### `answer_message(message, conversation_id=None, context=None)`

对应 `POST /api/v1/assistant/chat`。

返回字段：

- `conversation_id`
- `answer`
- `status`: `answered | insufficient_evidence`
- `citations`: 包含 `type、id、title、url、date、chunk_id`
- `used_metric_queries`
- `limitations`

当前支持已授权 PDF/TXT/MD 文档的关键词检索；数值查询工具待 D 注入。

### `index_document(file_path, metadata)`

对应 `POST /api/v1/knowledge/documents` 的入队响应。

返回字段：

- `document_id`
- `index_status`: `pending`
- `job_id`
- `staged_file_path`
- `metadata`

`metadata` 字段：

- `title`
- `publisher`
- `source_url`
- `published_at`
- `valid_from`
- `valid_until`
- `permission_note`

### `process_document_index(file_path, metadata)`

供 Worker 调用：解析并立即索引 PDF/TXT/MD 文档。

返回字段：

- `document_id`
- `index_status`: `ready`
- `chunk_count`

### `reindex_documents(document_ids, reason)`

对应 `POST /api/v1/knowledge/reindex`。

返回字段：

- `job_id`
- `pending_count`

### `save_knowledge_index(path)` / `load_knowledge_index(path)`

将当前知识索引保存为 JSON，或从 JSON 恢复到进程内索引。

### `analyze_video(video_id, config)`

对应 `POST /api/v1/videos/{video_id}/analyses`。

`config` 字段：

- `detector_model_version`
- `openvino_version`
- `device`: `CPU | GPU | NPU | AUTO`
- `count_line`: `{x1, y1, x2, y2}`，坐标均为 0—1
- `entry_side`: `left | right`
- `interval_minutes`: `1 | 5 | 15`
- `tracker_config_id`

当前返回 `queued` 作业信息；实际视觉 Worker 后续接入。

### `get_camera_counts(video_id, analysis_id, start=None, end=None, interval_minutes=None)`

对应 `GET /api/v1/videos/{video_id}/counts`。

视觉 Worker 未接入前返回：

```json
{
  "analysis_id": "...",
  "status": "analysis_not_ready",
  "points": [],
  "manual_validation": null
}
```

正式计数点包含：

- `window_start`
- `window_end`
- `entries`
- `exits`
- `quality_status`
- `detector_model_version`
- `openvino_version`
- `device`

### `forecast_short_term(video_id, analysis_id, cutoff_at, horizon_minutes, step_minutes, direction)`

对应 `POST /api/v1/videos/{video_id}/short-forecast`。

- `horizon_minutes`: 15、30 或 60
- `step_minutes`: 5 或 15
- `direction`: `entries | exits`

缺少已验证计数历史时返回 `data_insufficient`，不输出预测点。

### `forecast_from_count_history(history, cutoff_at, horizon_minutes, step_minutes)`

供 D 在取得 C 提供的历史计数后调用。`history` 为 `[(timestamp, value), ...]`，至少 4 个点。

正式预测点包含：

- `target_time`
- `value`
- `lower`
- `upper`

## 内部视觉组件

以下组件不直接暴露 HTTP，供视觉 Worker 组合：

- `vision.tracker.CentroidTracker`：基于质心距离的临时跟踪
- `vision.line_counter.VirtualLineCounter`：虚拟线越线和进出方向判断
- `vision.validation.validate_counts()`：自动计数与人工标注窗口的 MAE 校验

## Worker 后台进程

E Worker 由 D 的后台进程启动，注入 C store，负责领取和处理后台作业。

```python
from intelligent_analysis.worker import AnalysisWorker, WorkerConfig

worker = AnalysisWorker(store=c_store, config=WorkerConfig(worker_id="e-1"))
worker.run_once()  # 领取并处理一个作业
# 或 worker.start()  # 阻塞轮询
```

支持的作业类型：

| 作业 type | 处理函数 | 说明 |
|---|---|---|
| `knowledge_index` | `worker.knowledge_worker.process_knowledge_job` | 解析文档 → write_chunks → activate_index |
| `video_analysis` | `worker.video_worker.process_video_job` | 检测跟踪 → 越线计数 → write_counts → complete_analysis |
| `short_forecast` | 返回 `data_insufficient` | 预测由 API 层同步调用，不走后台队列 |

Worker 不直接导入 C 包，store 由 D 注入。

## 变更规则

函数名、参数或返回结构变更前，先通知 D 并更新本文档。
