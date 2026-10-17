# 脚本导航

从 E 仓库根目录运行。当前正式算法为 P2PNet；脚本有不同前置条件，不应把全部脚本依次执行。

## 当前常用

新增独立验收：`accept_d_c021_http.py`（真实D知识ASGI/Worker+C隔离库）、`accept_forecast_storage.py`（合成预测保存）、`check_b_contract.py`（Node执行B纯TS契约）、`verify_d_regression.py`（D原套件，失败结果保留）、`evaluate_p2pnet.py`（正式P2P单模型人工评测，空模板等待不推理）。范围及复现命令见 [当前说明](../docs/E当前完成情况与剩余依赖-2026-10-17.md)。

| 脚本 | 用途 |
|---|---|
| `check_p2pnet.py` | 已接收队长包后的正式 CPU 推理验证 |
| `end_to_end_demo.py` | 明确标记 synthetic 的计算/预测流程 |
| `receive_c020.py` | C 官方 a2 接收，网络/包前置条件见脚本 |
| `receive_c021_zip.py` | 用户提供 C0.2.1a2 ZIP 的逐文件 manifest/CRC 校验及隔离解压，已有目标不覆盖 |
| `check_c020_windows.py` / `verify_c020_regression.py` | C 官方包兼容性及回归 |
| `accept_c_knowledge.py` / `accept_c020_failures.py` | 真资料、C 隔离库和语义/事务/租约检查，先设置 a2 路径 |
| `accept_c021_integration.py` | 官方 C021 wheel 接收后，新存储合成闭环、真实历史数值及 D 当前不足分支复验；需 C/D 本地仓库 |
| `check_rag_questions.py` | 问答题集检查，人工语义和正式 HTTP 另验 |
| `verify_release_wheel.py` / `package_release.py` | 当前包安装验收及发布打包；需要对应版本证据，不用于重写既有发布 |

故障复现的完整环境命令见 [D 答复](../docs/致D-整合回执答复与故障复现-2026-10-15.md)。运行输出放被 Git 忽略的 `artifacts/`。

## 历史与专用复现

保留这些脚本是为了回溯既有证据和支持旧版本回归。它们不进入当前正式工作顺序：

- `receive_c.py`：旧 C 0.1.9 接收。
- `prepare_c020_candidate.py`：历史 a1 候选修补；正式 a2 不使用该补丁。
- `accept_d_bridge.py`：D 旧 SQLite 桥验证，需要 D 源码与依赖，不能关闭正式 MySQL 验收。
- `verify_e051_wheel.py`：已发布 E 0.5.1 实装复现。
- `prepare_dm_count.py` / `check_dm_count.py`：历史 DM-Count。
- `benchmark_frames.py`、`prepare_leader_comparison.py`、`score_leader_comparison.py`：历史比较工具，比较任务已停止。
- `check_leader_p2pnet.py` / `leader_p2p_factory.py`：首次队长包试跑，当前正式绑定使用 `check_p2pnet.py` / `P2PNetCounter`。

历史工具的存在不表示需要再次下载 DM 权重、启动比较或开放未验证设备。其依赖仍被部分历史测试/证据使用，未在文档整理中删除。
