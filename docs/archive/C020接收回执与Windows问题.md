# E 接收 C 0.2.0a1：回执与 Windows 阻塞

> 历史记录（a1）。2026-10-15 已接收官方 a2，当前结论见 [E051 正式交付与 C/D 回执](../E051正式交付与CD回执.md)。本页候选结果不作为当前正式验收。

日期2026-10-14。C提交ed0400e，E上一发布提交1e5ab65。本轮E代码版本0.5.1。仅操作E目录和隔离SQLite，没有修改C/D仓库，也没有连接正式MySQL。

## 接收结论

**原版C 0.2.0a1尚未在本机通过原生落盘验收。** ZIP、wheel、Git原始contents清单摘要和14个Python模块一致性验证通过；迁移仍0006。实际执行时发现Windows文件指纹误判，详见下节。C先前的Linux/MySQL验收结果不能替代本次Windows接收。

E已实现新加载器：取得get_index_artifact_ref，读取受管理根目录内的普通文件，再校验本次读取字节的大小/SHA256，最后检查JSON结构、文档/索引版本、解析器/算法版本、元数据及C已提交片段的编号、定位和文本。任一失败阻止回答，不沿用旧内存。

## 可复现的原版问题

运行环境Windows、Python3.13.13，C 0.2.0a1从已核验wheel解压至E隔离runtime。命令：

```powershell
python -X utf8 demo/receive_c020.py --version 0.2.0a1
python -X utf8 demo/check_c020_windows.py --version 0.2.0a1
```

C persist_file通过NamedTemporaryFile和os.replace落盘。C verify_artifact以os.fstat取得基准，VerifiedArtifact.ensure_unchanged却以Path.stat复核。本机该文件的st_dev、st_ino、st_size、st_mtime_ns一致，**st_ctime_ns不同**，因此未被修改的文件抛Conflict“索引产物在校验后发生变化”。直接新建文件偶尔可通过小样本，真实索引仍会失败，不能作为可靠规避方案。

真实元数据及报错在acceptance/C020-Windows-fingerprint.json。未删除ctime字段、未伪造摘要、未跳过ensure_unchanged，也未改C仓库。

## 给 C 的候选修复建议

在ensure_unchanged内，保留_path路径/符号链接检查和全部指纹字段，改为重新os.open并用os.fstat读取当前指纹，finally关闭描述符，使基准和复核使用同一API；继续拒绝非普通文件、变化文件、越界和旧租约。不要简单删掉ctime或捕获Conflict后继续发布。

E仅在artifacts/c-0.2.0a1/runtime-candidate这个wheel副本中试验上述修改。候选模块原/新SHA256在acceptance/C020-candidate-patch.json；原wheel及C仓库未变。请C审核并在自己的版本中修复，补Windows回归、重命名落盘、实际内容改变、替换文件和租约/竞争测试后重新交付。本候选不是获确认的C正式修复。

候选副本还运行了C自带54个索引文件用例：52通过，2失败。目录输入在Windows抛PermissionError后被映射为Conflict，测试及契约期望InvalidArgument；文件仍被拒绝，但错误分类不一致。FIFO用例直接调用Windows没有的os.mkfifo而失败，需要平台条件/等价覆盖。具体记录在acceptance/C020-candidate-regression.json；没有删改C测试使其变绿，因此也不能说候选修复的C全量回归通过。

## 候选副本上的实际验收

命令明确选择候选runtime，仍使用C原生persist_file：

```powershell
python -X utf8 demo/prepare_c020_candidate.py
$env:C_HANDOFF_DIR=(Resolve-Path artifacts/c-0.2.0a1/data_foundation).Path
$env:C_RUNTIME_DIR=(Resolve-Path artifacts/c-0.2.0a1/runtime-candidate).Path
python -X utf8 demo/accept_c_knowledge.py
```

已验证16份真实文档、655片段，每份均经新C引用加载；查询、历史提示和新进程重启加载通过。损坏/缺失文件阻止问答但不删除片段；新坏摘要保留旧活动版本；激活与任务完成异常整体回滚；旧执行尝试不能发布，新尝试重传片段去重后成功；SHA正确但文本与数据库不一致也被E拒绝。修复后的活动版本可重新加载。

报告acceptance/C020-knowledge.json的状态为**passed_on_isolated_c_candidate**，不能转写成“原版C 0.2.0a1接收通过”。原版问题修复并重新核验之前，正式接入保持待确认；MySQL/HTTP/队友Worker也未在本轮验收。

## E 产物格式回传

fixtures/C020-historical-notice/index.json与manifest.json是指定真实历史公告0c8e2020-2e0a-5842-bce9-d9193cf81095的实际单文件输出，3个片段；SHA256、字节数和索引版本见manifest。仅支持UTF-8 JSON关键词索引，**没有embedding向量或向量矩阵**；embedding_model_version字段沿C现有命名，实际值keyword-tfidf-0.5.0。parser_version仍text-parser-0.5.0，算法未变；artifact_schema_version=1用于新清单版本。

每个片段的chunk_id=document_id+序号、order/数据库chunk_no从0连续，对照C locator中的chunk_id/order与text逐项核验。旧无清单版本的0.5.0产物须重建才能进入新验证加载器。该检查不证明原始PDF/采录解析绝对正确，也不覆盖多文件向量、来源资产全文语义或完整G10。

新短时预测尚无真实录像或新计数存储，未提交save_short_forecast真实调用或伪效果；旧direction和entries/exits不能替代camera_visible_people。请C后续单独交付新画面人数存储与G18契约。
