# D 回复 E：函数契约确认与路由映射

> 写的人：D（后端 api_platform）
> 日期：2026-10-11
> 依据：E 契约 v0.4.0
> 存档位置：E 仓库 docs/

---

## 一、D 确认内容

1. **E 服务函数签名：确认。** 全部函数签名满足后端调用，已 pip install -e 安装核对，无修改意见。
2. **HTTP 路由映射：确认。**
3. **作业状态字段：确认。** JobOut 已补 analysis_id。
4. **错误状态映射：确认。**
5. **指标查询注入方式：确认。** 按 D 注入受约束查询函数执行。

## 二、HTTP 路由 ↔ E 函数映射（确认版）

| 路由 | E 函数 |
|---|---|
| `POST /assistant/chat` | `answer_message()` |
| `POST /knowledge/documents` | `index_document()` |
| `POST /knowledge/reindex` | `reindex_documents()` |
| `POST /videos/{video_id}/analyses` | `analyze_video()` |
| `GET /videos/{video_id}/counts` | `get_camera_counts()` |
| `POST /videos/{video_id}/short-forecast` | `forecast_short_term()` |

Worker 侧：`process_document_index` / `save_knowledge_index` / `load_knowledge_index` / `forecast_from_count_history`。

## 三、错误状态 HTTP 映射

| E 状态 | HTTP 返回 |
|---|---|
| `analysis_not_ready` | 409 |
| `data_insufficient` | 200 |
| `quality_insufficient` | 200 |
| `insufficient_evidence` | 200 |
| `metric_tool_unavailable` | 503 |

## 四、环境变量

| 变量 | 默认 |
|---|---|
| `RAG_INDEX_PATH` | `./data/rag_index.json` |
| `DETECTOR_WEIGHTS_PATH` | `./data/weights` |
| `OPENVINO_DEVICE` | `CPU` |
| `VIDEO_TMP_DIR` | `./data/video_tmp` |
| `COUNTS_STORAGE_PATH` | `./data/counts` |

## 五、new_auth_store / create_store

D 侧已修复：按 `new_auth_store()` → `create_store()` 顺序回退取用。
C 需确认 `create_store()` 返回对象直接实现认证四方法。

## 六、D 侧优先级

1. P0：六条路由从 503 桩切换为实调 E 函数
2. P0：worker 领作业 → 调 E 组件 → 写回 C store
3. P1：指标查询注入函数
4. P1：GET /knowledge/documents/{document_id}（D 从 C store 读，不找 E）
5. P2：视频上传与回放（依赖 C 授权记录）
