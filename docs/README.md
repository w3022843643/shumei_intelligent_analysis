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

完整范围及原始 JSON 见 [验收证据导航](acceptance/README.md)。

| 内容 | 入口 | 边界 |
|---|---|---|
| E 当前源码回归 | [readiness-tests](acceptance/E061-readiness-tests.json) | 123 通过、1 项历史对照跳过 |
| C 0.2.1a2 接收 | [receipt](acceptance/C021a2-receipt.json)、[Windows-regression](acceptance/C021a2-Windows-regression.json) | 包完整性；C Windows 478 通过、1 跳过 |
| D/E/C 知识 HTTP | [HTTP](acceptance/E061-D-C021a2-HTTP.json) | 隔离 SQLite / ASGI；D resolver、混合队列仍有阻塞 |
| 知识故障保护 | [failure-matrix](acceptance/E061-C021a2-failure-matrix-extended.json) | 五类语义篡改、租约和事务检查 |
| B/D/E 结果契约 | [B-D-contract](acceptance/E061-B-D-contract.json) | 8 项纯契约检查；非浏览器验收 |
| 短时预测存储 | [forecast-storage](acceptance/E061-C021a2-forecast-storage.json) | 合成连续窗，非真实误差报告 |
| P2PNet CPU / 人工评估 | [CPU](acceptance/P2PNet-CPU-061.json)、[evaluation](acceptance/P2PNet-evaluation-readiness.json) | CPU 推理已验证；真值未到位，MAE=null |

历史 JSON、样例和已发布包保留原路径，方便旧回执追溯；历史记录不能代替当前验收。早期方案在 [archive/](archive/README.md)，本次目录整理见 [整理记录](文件整理记录-2026-10-17.md)。
