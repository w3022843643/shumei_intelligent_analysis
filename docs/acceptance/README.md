# 验收证据导航

更新日期：2026-10-18。当前E0.6.2、C0.2.1a2，接收D6d8bb23、B5c27e5c。原始JSON保持原件；合成、隔离和部署范围以各报告标志为准。

## 当前主要证据

| 内容 | 记录 | 结论/边界 |
|---|---|---|
| E全流程自检 | [self-check](E062-self-check.json)、[tests](E062-tests.json) | 139通过、1历史对照跳过；外部验收待完成 |
| 仓库直接运行 | [repository-run](P2PNet-repository-run-2026-10-18.json) | 干净Git副本核对模型字节和CPU推理；复用已有Python依赖 |
| CPU/独立wheel | [CPU-062](P2PNet-CPU-062.json)、[wheel-installed](E062-wheel-installed.json) | 实际安装来源、31/41/31推理、C重启读取 |
| C a2原包接收 | [receipt](C021a2-receipt.json)、[Windows](C021a2-Windows-regression.json) | 完整性；C478通过/1平台跳过，非MySQL替代 |
| C a2真实知识 | [knowledge](E062-C021a2-knowledge.json) | 16份资料、严格加载/重启/语义故障保护 |
| D/E/C知识HTTP | [HTTP](E062-D-C021a2-HTTP.json) | 隔离SQLite/ASGI18项，D真实resolver及坏数值503 |
| D原套件 | [E062初始化后](E062-D-regression-empty-snapshot.json)、[此前原空环境](E061-D-regression-2026-10-18.json) | 初始化空快照405通过；原空环境400通过/5失败，两种前置条件 |
| D计数适配 | [visible-storage](E062-D-visible-storage.json) | D→E→真实C SQLite；帧和权限/时间是合成夹具 |
| 预测存储 | [forecast](E062-C021a2-forecast-storage.json) | 合成15/30 ready、60不足；非真实误差 |
| B/D/E契约 | [contract](E062-B-D-contract.json) | 8项纯TS/映射检查；非浏览器验收 |
| 问答题集 | [RAG](E062-RAG-question-suite.json) | 自动9项通过；人工语义复核待回传 |
| 五段实际试跑 | [fixed-camera](P2PNet-fixed-camera-2026-10-18.json) | 35帧模型估计；绝对时间/真值未提供 |
| 人工评估准备 | [evaluation-readiness](P2PNet-evaluation-readiness.json) | blocked、0已复核样本、MAE=null |

## 历史证据

E061/E060/E051、C019/C020/C020a2/C021a1、DMCount与Leader-comparison等原始JSON保留原路径。早期队列/resolver问题的记录已被新提交和新复验推进，不作为当前阻塞。历史模型比较已停止。

完整任务与剩余责任见 [E自检](../E全流程任务与自检-2026-10-18.md)，旧回执入口见 [历史索引](../history/README.md)。正式MySQL、部署视频HTTP、人工MAE、真实预测与浏览器联验保持未关闭。
