# E 服务契约 0.5.1（2026-10-15）

0.5.1 新增 C 已验证产物加载、原文/索引版本及片段绑定；保留 0.5.0 视频接口。C 官方 0.2.0a2 的本机 Windows 原生存储及 wheel 回归通过，正式 C/MySQL 与 D Worker 联调仍待完成。详见 [正式交付与回执](docs/E051正式交付与CD回执.md)。

统一入口保持 `intelligent_analysis.service`。本版包含破坏性视频契约变更，D 必须同时注入队列与读回能力；仅修改模型字段不能自动完成联调。

## 1. 职责与绑定

D 唯一 Worker 领取、续租、恢复和分发；D 通过 C 持久化计算结果、失败、进度及作业状态；E 只计算。D 负责授权、上传、回放 Range、权限、CSRF、HTTP 与序列化。E 不运行独立的队列消费者。

```python
from intelligent_analysis import ServiceBindings, configure_services

configure_services(ServiceBindings(
    submit_job=d_submit_job,
    load_counts=d_load_visible_counts,
    validate_analysis=dm_counter.validate_config,
    knowledge_index_path=published_active_index_path,
))
```

绑定必须在每个 API 进程启动时完成；只注入服务端受信任函数，不能从用户请求接受 Python 调用对象。

| 绑定 | 签名和责任 |
|---|---|
| `submit_job` | `(kind: str, payload: dict) -> dict`；D 登记/去重并提交事务之后返回 `status=queued, job_id`，视频另有 `analysis_id`。这些 ID 必须指向真实 C 记录。 |
| `load_counts` | `(video_id: str, analysis_id: str) -> dict`；校验视频、分析和访问归属，读取双方确认的新口径存储；返回 `CountsResponse`，含两种粒度，E 负责过滤。未知对象由 D 报 404/403；旧 `entries/exits` 禁止作为新响应。 |
| `validate_analysis` | `(config: dict) -> None`；真实检查权重文件摘要、可加载性、模型版本和运行设备，不可用时抛 `UnsupportedAnalysis`。 |
| `knowledge_index_path` | D 提交成功后发布的完整活动索引 JSON。问答每次读取完整文件，原子替换确保不同 API 进程读到同一已发布快照。 |
| `knowledge_snapshot_loader` | 0.5.1 可选绑定 `() -> dict`，由 D 列举有权访问的活动文档 ID，再调用 `load_verified_knowledge_snapshot(store, ids, data_root)`；每次问答复验并加载。与 knowledge_index_path 互斥，任何产物损坏都返回不可用，不沿用旧内存。 |

异常映射：`DependencyUnavailable` → 503；`UnsupportedAnalysis` → 422 unsupported；配置校验异常由 D 映射其现有 400/422 约定。E 返回的 `analysis_not_ready` → 409；`data_insufficient`、`quality_insufficient`、`insufficient_evidence` → 200；`metric_tool_unavailable` → 503。日志错误摘要由 D 脱敏。

## 2. 视频三函数

```python
analyze_video(video_id: UUID, config: dict) -> dict
get_camera_counts(video_id: UUID, analysis_id: UUID,
                  start: str | None = None, end: str | None = None,
                  grain: str = "5min") -> dict
forecast_short_term(video_id: UUID, analysis_id: UUID, cutoff_at: str,
                    horizon_minutes: int, step_minutes: int = 5) -> dict
```

分析 config：`count_model="dm_count"`、`weights_version`、`roi={points:[{x,y},...]}`、`sample_interval_seconds`（默认10，整数1—600）、`aggregation_minutes=5`、`inference_engine=pytorch|openvino`、大写 `device`，仅 OpenVINO 请求携带非空 `openvino_version`。多余字段拒绝；ROI 为不自交、非零面积、顶点不重复的归一化多边形。

首个运行配置为 `weights_version=dm-count-qnrf-cc5f2132`、PyTorch CPU。权重 SHA-256 `16ef954a2cef40c66ee664f69273559553b735d5e2c9f90e2444f3c25dd45e05`。权重由 `demo/prepare_dm_count.py` 下载并验证，D 使用 `DMCountCounter(WeightSpec(path, sha256, version))` 注入。其他配置均拒绝；不得自动回退。

分析返回 `{job_id,analysis_id,status:"queued",video_id,count_metric:"camera_visible_people",inference_engine}`。

计数返回 `video_id,analysis_id,metric,status,roi,analysis,points,manual_validation`。`analysis` 是实际完整 config；`manual_validation` 未人工评估时为 null。每点包含 `metric,value,unit="人",grain,quality_status,source_ids,published_at,ingested_at`。`frame` 点使用 `recorded_at`；`5min` 点使用 `period_start,period_end,sample_count,aggregation_rule="median"`。时间必须带时区，聚合窗恰好 5 分钟；查询仅返回完全落在 start/end 内的点。

E 计算产物的 published/ingested 时间为空，由 D/C 在提交时填写真实值。`good` 表示抽样完整且计算数值有效，不表示人工验收准确。缺样为 `degraded`；零有效样本为 `unavailable,value=null,sample_count=0`，不能补零。最后不足 5 分钟的窗不输出聚合值。估计小数保留，逐帧人数不累加成人次。

预测返回 `metric,status,forecast_points,training_cutoff,input_window_minutes,model_version,validation_error,reason`；点含 `target_time,value,is_forecast=true,lower=null,upper=null`。方向参数和旧 `interval_minutes` 不再接受。只使用窗结束时间不晚于 cutoff 的 `good` 点；重复时刻拒绝，缺失/中断/过旧返回质量不足。

15/30 分钟最低训练点数分别为12/24；还需要至少3个完整滚动起点回测折，因此常数连续样本至少分别17/32个点才能满足完整验证。每折在自己的训练前缀用固定 alpha/beta/phi 网格选择一阶 SSE 最低的阻尼 Holt 参数；分跨度 MAE 不优于最近值基线时不输出曲线。60分钟一律保持不足状态，直到另行验收。没有可靠区间时保持 null。

## 3. D 的计算与发布流程

```python
from intelligent_analysis.worker import dispatch_analysis_job, publish_knowledge_snapshot

# D 已在短事务内领取并取得租约；长计算期间由 D 续租。
prepared = dispatch_analysis_job(job_type, payload, counter=dm_counter)
# D 在新 write 事务校验当前租约、写业务数据、完成任务；同事务提交。
# 知识提交之后，由 D 在单一发布锁下重建完整活动快照：
publish_knowledge_snapshot(full_committed_snapshot, published_active_index_path)
```

视频 payload：`video_id,analysis_id,file_path,recorded_start_at,recorded_end_at,source_ids,config`。帧输入为 RGB uint8；E 读取 OpenCV 录像时执行 BGR→RGB，帧率无效时拒绝推导时间。返回完整 `CountsResponse`，不调用 C 的旧 `write_counts()`。

知识 payload：`document_id,document_version,version,file_path,metadata`。document_version 是 C 原文版本；version 是本次索引版本。也可在 metadata.document_version 提供原文版本；两处同时提供必须一致，不从索引版本推导原文版本。metadata 至少有标题、发布方、使用说明，可含 URL、发布时间、适用起止与 applicability_note。E 返回 `chunks`（C chunk_no/text/locator）、`artifact_bytes`、SHA256、标准索引 `snapshot`，并返回 document_version/index_version/parser_version/embedding_model_version；均为未发布计算结果，含 bytes 的结果不能直接作为公共 HTTP JSON。

0.5.1 正式单文档产物根为 schema_version=1、parser_version、embedding_model_version；documents[document_id] 独立记录 document_version 和 index_version。解析器与关键词算法未改变，仍使用 text-parser-0.5.0 / keyword-tfidf-0.5.0；这是关键词 JSON 索引，没有 embedding 向量。load_verified_knowledge_snapshot(store, document_ids: list[str], data_root: str | Path) 返回 {documents: {id: {document_version,index_version,metadata,chunks}}}，逐项核对 C 原文版本、活动索引版本、元数据、连续 chunk_no、文本、chunk_id/order locator、文件路径及 SHA/大小。损坏、缺失、版本或内容不一致均抛 DependencyUnavailable；重复文档 ID 属调用参数错误，抛 ValueError。旧无版本清单以及未发布草案 artifact_schema_version/version 格式须重建。该校验不证明源资料解析正确，也未关闭 C 的完整 G10。

D 在事务外用 C 原生 persist_file 落盘 artifact_bytes 后，先用短事务 begin_index，再逐批 write_chunks（每批不超过1000，分别提交）；最后单独的短 write 事务执行 activate_index+complete_job，一起提交或回滚，激活时附 expected_artifact_byte_size 和当前 lease。解析、推理、文件持久化在长事务之外，D 在阶段之间保持续租。失败与重试由 D 根据 C 真实接口处理，过期租约禁止发布。推荐注入 knowledge_snapshot_loader 直接从 C 活动引用读取；旧 publish_knowledge_snapshot 接收完整活动版本集合而非单文档增量，D 重启须从 C 重建。外层调度不得在知识处理器已原子完成后再次 complete_job。

## 4. 知识服务与数值查询

`index_document(file_path, metadata)` 要求 metadata 的 `document_id`、`document_version` 由 C 登记确定；返回 D 真实任务 ID。`reindex_documents(ids, reason)` 向 D 提交 `knowledge_reindex` 操作；D 需展开为每个文档的 `knowledge_index` 任务并返回其管理作业 ID，不能把批量 payload 直接交给单文档处理器。

`process_document_index(file_path,metadata,document_id=None)` 是同步本地索引 helper，不登记任务或写 C；D 的正式异步流程使用上述 worker 产物及提交后发布。`load_knowledge_index/save_knowledge_index` 保持导出。

`answer_message(message,conversation_id=None,context=None)` 的 D 侧数值路由传入：

```python
context = {"metric_query": constrained_query_dict, "metric_tool": trusted_d_query_callable}
```

查询白名单、实体/指标/时间粒度校验由 D 实施；E 不生成 SQL。工具结果必须带 `metric,value,source_ids,period_start,period_end,queried_at`，完整保存在 metric_result；缺来源时拒绝给出数值结论。未注入工具返回 metric_tool_unavailable。无 metric_query 时走文档检索，历史/未生效材料在回答正文与 limitations 中提示，绝不将旧公告当作当前运营规定。该入口不隐式执行任意自然语言数据库查询，D 需确定数值意图并注入受约束 query。

## 5. 实验与验收

P2PNet 仅在 `vision.benchmark` 中用于对照。`P2PNetAdapter` 接收调用方加载并记录来源的官方兼容 PyTorch 模型，使用 CPU 和新版 Pillow API，输出归一化人头点/置信度。`compare_counters` 用同一组独立标注 RGB 帧与 ROI，按场景计算 MAE，并保留耗时与两模型 provenance。正式接口不接受 p2pnet；未取得权重、标签或场景样本时不能发布实测比较结论。
