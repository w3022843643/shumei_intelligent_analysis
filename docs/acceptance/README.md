# 验收证据导航

更新日期：2026-10-17。原始 JSON 保持原件；同名能力的旧版本记录不代表当前能力已经正式验收。

| 范围 | 原始记录 | 结论与限制 |
|---|---|---|
| 当前 E 源码 | [E061-readiness-tests](E061-readiness-tests.json) | 123 通过、1 历史对照跳过 |
| C a2 接收 | [receipt](C021a2-receipt.json)、[Windows](C021a2-Windows-regression.json) | 完整性校验；478 通过、1 平台跳过 |
| C a2 真实资料 | [knowledge](E061-C021a2-knowledge.json) | 16 份资料索引、严格加载与重启 |
| 知识故障矩阵 | [extended](E061-C021a2-failure-matrix-extended.json) | 正确摘要下语义篡改仍拒绝，租约和事务保护 |
| D 知识 HTTP | [HTTP](E061-D-C021a2-HTTP.json) | 隔离 SQLite / ASGI，15 项检查；保留 D 队列和 resolver 阻塞 |
| D 原回归 | [原环境](E061-D-regression.json)、[初始化快照后](E061-D-regression-empty-snapshot.json) | 分别 313 通过/6 失败、318 通过/1 失败，均未跳过；两次前置条件不同 |
| B/D/E 契约 | [contract](E061-B-D-contract.json) | 8 项纯 TS / 映射检查，无浏览器验收 |
| 合成预测存储 | [forecast](E061-C021a2-forecast-storage.json) | 15/30 分钟合成链路；60 分钟不足；非真实回测 |
| P2PNet CPU | [CPU-061](P2PNet-CPU-061.json) | 已接收权重的 CPU 推理，不证明准确率 |
| 人工评估准备 | [evaluation](P2PNet-evaluation-readiness.json) | blocked、0 样本、MAE=null，等待授权与独立复核 |
| E 0.6.1 发布时快照 | [tests](E061-tests.json)、[wheel](E061-wheel-installed.json) | 发布时证据，完整性以 [发布回执](../../release/E-visible-people-0.6.1-2026-10-17.receipt.json) 为准 |

C019/C020/C020a2/C021a1、E051/E060、DMCount 和 Leader-comparison 等历史 JSON 保留原路径，便于发布回执和旧链接追溯。历史比较已停止。

正式 MySQL、部署 HTTP、授权视频完整链路、人工 MAE 和真实分跨度预测仍待验收。详细环境、前置条件和待办见 [当前完成情况](../E当前完成情况与剩余依赖-2026-10-17.md)。
