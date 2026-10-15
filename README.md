# E 智能分析包 0.6.0

正式算法按用户确认改为队长推荐的 **P2PNet**，停止DM-Count/P2PNet比较。新版视频接口只接受count_model=p2pnet，首个已验证运行配置为提供的SHTechA权重、PyTorch CPU。D/B需同步模型字段、阈值和计数器绑定后再联合发布，见 [0.6.0交付与D/B执行单](docs/E060-P2PNet正式交付与DB执行单.md)。

知识能力继承0.5.1：C官方0.2.0a2、原文/索引版本独立绑定、已校验加载及损坏时拒绝旧内存回退；解析/关键词算法版本保持原值。历史发布文件和证据保留，当前视频契约以0.6.0为准。

本版把录像指标升级为 `camera_visible_people`：指定固定画面 ROI 的估计可见人数。它不表示累计通行人次，也不表示全景区在园人数。原跟踪和越线文件仅保留用于旧方案回归，新流程不调用。

## 安装与验证

Python 3.13，在本目录执行：

```powershell
python -m pip install -e ".[dev,vision]"
python -m pytest -q
python -m ruff check intelligent_analysis tests demo
```

核心服务和合成验证不需要 PyTorch/OpenCV；真实 CPU 推理需要 `vision` 可选依赖。阻尼 Holt 使用本包内的标准递推及固定参数网格，不需要安装 statsmodels。历史 helper 的滚动均值实现已被替换。

```powershell
python demo/receive_c.py
python -X utf8 demo/accept_c_knowledge.py
python -X utf8 demo/check_p2pnet.py
```

C 官方 0.2.0a2 接收使用 `python demo/receive_c020.py --download`、`python demo/check_c020_windows.py` 和 `python -X utf8 demo/verify_c020_regression.py`。接收旧 0.1.9 后，设置 RUN_C_ACCEPTANCE=1 和 RUN_C020_ACCEPTANCE=1 可执行两套真实接收回归；后者只使用已安装的官方 a2 wheel，不使用候选补丁。历史 a1 问题与候选证据保留，当前状态以 a2 回执为准。

下载结果、原件、权重、索引和隔离 SQLite 均放在被 Git 忽略的 `artifacts/`；不会更新 C 仓库或连接团队 MySQL。中文资料的 C 校验脚本需要 Windows Python UTF-8 模式。真实 C 接收回归可通过 `$env:RUN_C_ACCEPTANCE="1"` 后执行 pytest 启用。

## 已实现的能力与交付边界

- 显式 D 队列/读取/运行能力注入；未登记真实任务不返回 `queued`，未接读取能力不冒充分析未完成。
- 知识解析、引用、适用时间提示、原 C 文档 ID、原子索引发布及跨进程加载；受约束数值工具保留来源和查询时间。
- P2PNet正式CPU点计数器，校验提供源码和权重摘要，固定多边形ROI内置信度>0.5的人头点计数、抽帧、5分钟中位数及缺帧质量状态。
- D 分发的纯计算入口，E 不领取混合队列、不续租、不写 C 的计数表；D 控制任务生命周期和发布。
- 阻尼 Holt 5 分钟预测，训练前缀参数选择、滚动起点回测及最近值基线对照；60 分钟暂不开放，区间为空。
- P2PNet配置、权重、设备不可用时明确报错；正式接口拒绝dm_count，不自动更换模型。原对照工具仅作为历史保留。

P2PNet人工MAE、真实15/30分钟预测及D/B正式视频联调仍待验收；队长短片已跑通CPU推理，但没有人工真值和完整5分钟窗口。GPU、NPU、AUTO、OpenVINO尚未开放。

## 对接资料

正式交接文件在 [release/](release/)：保留各版本 wheel、完整交接 ZIP 和 SHA-256 回执。原始资料与模型权重不随 Git 仓库上传，按上述脚本获取。

- [服务契约](E_SERVICE_CONTRACT.md)：D 的绑定、任务处理、读回和异常映射。
- [答复 D 的整合回执与故障复现](docs/致D-整合回执答复与故障复现-2026-10-15.md)：阈值、审计、原文/索引版本、重建职责确认及隔离故障注入入口；附 2026-10-15 新复跑证据，D/MySQL 仍待独立复验。
- [交付与缺口](docs/E050交付与联调说明.md)：C 新口径存储需求、D/B 联调步骤及验收状态。
- [C 真实知识接收证据](docs/acceptance/C019-knowledge.json)。
- [C 官方 a2 Windows 回归](docs/acceptance/C020a2-Windows-regression.json)、[真实资料与故障检查](docs/acceptance/C020a2-knowledge.json)、[实际 JSON 与 manifest](docs/fixtures/C020a2-historical-notice/)。
- [D/E 独立 SQLite 桥 HTTP 验证](docs/acceptance/D-E051-bridge.json)：不代表正式 C/MySQL 联调通过。
- [DM-Count 官方实现](https://github.com/cvlab-stonybrook/DM-Count)，[P2PNet 官方实现](https://github.com/TencentYoutuResearch/CrowdCounting-P2PNet)。

历史 `E致各角色对接说明.md`、旧需求确认清单和 `docs/D回复E_契约确认.md` 描述 0.4.0 越线方案，不能用作本版已完成状态或调用契约。

## 下一阶段准备工具

0.6.0工具见以下入口，既有0.5.1 wheel/ZIP保留原发布内容：

- [真实问答题集与联合验收](docs/真实问答题集与联合验收.md)：`python -X utf8 demo/check_rag_questions.py`；自动检查与人工语义、D意图路由/HTTP分别记录。
- [正式P2PNet配置与D/B适配](docs/E060-P2PNet正式交付与DB执行单.md)：`python -X utf8 demo/check_p2pnet.py`，依赖已接收的本地队长模型目录。
- [录像素材与人工标注清单](docs/录像素材与人工标注清单.md)：授权、资产、时间、固定ROI、四类场景、独立复核与预测连续时序要求。
- [队长P2PNet测试包接收](docs/队长P2PNet测试包接收说明.md)：提供权重已跑通本机CPU三帧；原视频/权重留在本地artifacts，人工精度及GPU仍待验收。
- [六帧人工素材](docs/六帧人工标注与对照执行单.md)：图片可继续用于P2PNet单模型人工误差核验；比较任务已停止，旧对照报告保持历史状态。
