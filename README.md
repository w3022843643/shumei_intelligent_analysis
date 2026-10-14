# E 智能分析包 0.5.0

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
python demo/prepare_dm_count.py
python -X utf8 demo/check_dm_count.py
```

下载结果、原件、权重、索引和隔离 SQLite 均放在被 Git 忽略的 `artifacts/`；不会更新 C 仓库或连接团队 MySQL。中文资料的 C 校验脚本需要 Windows Python UTF-8 模式。真实 C 接收回归可通过 `$env:RUN_C_ACCEPTANCE="1"` 后执行 pytest 启用。

## 已实现的能力与交付边界

- 显式 D 队列/读取/运行能力注入；未登记真实任务不返回 `queued`，未接读取能力不冒充分析未完成。
- 知识解析、引用、适用时间提示、原 C 文档 ID、原子索引发布及跨进程加载；受约束数值工具保留来源和查询时间。
- DM-Count 官方结构与权重的 PyTorch CPU 实现，固定多边形 ROI、抽帧、5 分钟中位数、缺帧与完整性质量状态。
- D 分发的纯计算入口，E 不领取混合队列、不续租、不写 C 的计数表；D 控制任务生命周期和发布。
- 阻尼 Holt 5 分钟预测，训练前缀参数选择、滚动起点回测及最近值基线对照；60 分钟暂不开放，区间为空。
- 实验性 P2PNet CPU 模型适配器和相同标注帧/ROI 的分场景 MAE 对照器。正式 `count_model` 仍只接受 `dm_count`。

真实录像计数 MAE、P2PNet 实测比较及真实 15/30 分钟预测仍待获准录像和标注；合成测试不构成这些验收。GPU、NPU、AUTO 和 OpenVINO 尚未开放。

## 对接资料

正式交接文件在 [release/](release/)：包含 0.5.0 wheel、完整交接 ZIP 和 SHA-256 回执。原始资料与模型权重不随 Git 仓库上传，按下方脚本获取。

- [服务契约](E_SERVICE_CONTRACT.md)：D 的绑定、任务处理、读回和异常映射。
- [交付与缺口](docs/E050交付与联调说明.md)：C 新口径存储需求、D/B 联调步骤及验收状态。
- [C 真实知识接收证据](docs/acceptance/C019-knowledge.json)。
- [DM-Count 官方实现](https://github.com/cvlab-stonybrook/DM-Count)，[P2PNet 官方实现](https://github.com/TencentYoutuResearch/CrowdCounting-P2PNet)。

历史 `E致各角色对接说明.md`、旧需求确认清单和 `docs/D回复E_契约确认.md` 描述 0.4.0 越线方案，不能用作本版已完成状态或调用契约。
