# E 服务函数契约

> 版本：0.3.0。HTTP 路由由 D 提供，E 只导出服务函数。未实现完成的功能返回明确状态，不伪造结果。

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

当前支持已授权 TXT/MD 文档的内存关键词检索；数值查询工具待 D 注入。

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

供 Worker 调用：解析并立即索引 TXT/MD 文档。

返回字段：

- `document_id`
- `index_status`: `ready`
- `chunk_count`

PDF 解析后续补充。

### `reindex_documents(document_ids, reason)`

对应 `POST /api/v1/knowledge/reindex`。

返回字段：

- `job_id`
- `pending_count`

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

缺少已验证计数历史时返回 `data_insufficient`，不输出预测点。正式预测点包含：

- `target_time`
- `value`
- `lower`
- `upper`

## 变更规则

函数名、参数或返回结构变更前，先通知 D 并更新本文档。
