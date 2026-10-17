# 文档导航

当前版本 E 0.6.1，正式模型 P2PNet，已验证 PyTorch CPU。更新日期：2026-10-17。

## 当前交付和团队往来

- [给 C 的接收结果与下一步工作](致C-当前接收结论与下一步协作-2026-10-17.md)：直接写给C本人的数据交付、标注资料、连续录像与数据层验收要求，可单独转发。

- [本轮完成情况与剩余依赖](E当前完成情况与剩余依赖-2026-10-17.md)、[给B的分支接收回执](致B-P2PNet分支接收与联合验收-2026-10-17.md)：含D实测阻塞及原套件诊断，不把所有检查写成全绿。

- [C a2 最新接收回执](致C-021a2接收回执-2026-10-17.md)、[D a2 升级接线](致D-升级C021a2接线清单-2026-10-17.md)：最新证据；E0.6.1及历史发布原件不变。

- [0.6.1 接收 C021 与答复 D](E061-接收C021与答复D-2026-10-17.md)：本轮入口、版本、C 统一存储及最新证据。下方 0.6.0 表格是上一版证据索引。

- [服务契约](../E_SERVICE_CONTRACT.md)：服务函数、注入和严格结果结构。
- [0.6.0 正式交付与 D/B 执行单](E060-P2PNet正式交付与DB执行单.md)。
- [分角色需求](团队需求-2026-10-15/README.md)：可分别发给 A/B/C/D，另含 E 待办。
- [对 D 整合回执的正式答复](致D-整合回执答复与故障复现-2026-10-15.md)：阈值/审计映射、版本、重建职责与故障复现。
- [0.5.1 知识交付与 C/D 回执](E051正式交付与CD回执.md)：仍适用的知识加载背景；视频模型以 0.6.0 为准。
- [发布包目录](../release/README.md)：各版本 wheel、ZIP 和摘要回执。

## 素材和验收准备

- [录像素材与人工标注清单](录像素材与人工标注清单.md)：授权、机位、ROI、人工真值及预测连续数据。
- [队长 P2PNet 测试包接收说明](队长P2PNet测试包接收说明.md)：收到的原始材料和首次试跑背景；正式绑定见 0.6.0 交付。
- [六帧人工素材](六帧人工标注与对照执行单.md)：文件名保留历史来源，图像可用于 P2PNet 单模型人工评估；比较已停止。
- [真实问答题集与联合验收](真实问答题集与联合验收.md)。
- [合成录像结果](fixtures/visible-people-demo.json)：只用于接口/页面开发。
- [人工评估空模板](fixtures/video-evaluation/manifest.template.json)、[问答题集](fixtures/rag-acceptance/questions.json)。

## 当前主要证据

| 内容 | 入口 | 边界 |
|---|---|---|
| E 自动化测试 | [E060-tests](acceptance/E060-tests.json) | 104 通过，1 项旧对照测试跳过 |
| P2PNet CPU | [CPU-060](acceptance/P2PNet-CPU-060.json) | 三帧推理，无人工真值 |
| wheel 实装 | [wheel-installed](acceptance/E060-wheel-installed.json) | 安装、CPU 和知识恢复 |
| C 官方 a2 知识接收 | [knowledge](acceptance/E060-C020a2-knowledge.json) | E 隔离 SQLite，16 份真实公开资料 |
| 最新故障复跑 | [failure-recheck](acceptance/E060-D-reply-failure-recheck-2026-10-15.json) | 语义失败、租约、重试和事务；未代替 D/MySQL |
| C 官方 a2 Windows 回归 | [Windows-regression](acceptance/C020a2-Windows-regression.json) | C 包兼容性，非视频精度 |

`acceptance/` 的历史 JSON 和 `fixtures/` 的原始样例保留原路径，便于旧回执追溯；并非每份都代表当前版本已通过。早期方案文档统一在 [archive/](archive/README.md)。
