# shumei_intelligent_analysis

E 负责的智能分析模块，包含 RAG 智能体、录像行人计数和入口短时客流预测。

## 模块范围

- PDF/TXT/MD 文档解析、切分、关键词索引与检索
- 知识索引 JSON 持久化
- 带来源的智能体问答
- YOLOv8 + OpenVINO 录像行人检测
- 质心跟踪、虚拟线进出计数和人工标注 MAE 校验
- 指定入口未来 15—60 分钟短时客流预测

## 当前状态

- 统一服务入口：`intelligent_analysis.service`
- 文档流水线支持 PDF/TXT/MD
- 问答支持证据引用和证据不足状态
- 已实现质心跟踪、越线方向判断和计数校验算法
- 已实现滚动基线、预测区间和 walk-forward 回测
- 真实视频分析仍等待 C 提供授权录像、入口信息和人工标注样本

## 目录

```text
intelligent_analysis/
├─ intelligent_analysis/
│  ├─ agent/
│  ├─ knowledge/
│  ├─ vision/
│  ├─ short_forecast/
│  └─ service.py
├─ artifacts/
├─ tests/
├─ E_SERVICE_CONTRACT.md
└─ pyproject.toml
```

## 注意事项

- 授权录像、原始数据、模型权重和环境变量配置不得提交到仓库。
- 视频计数仅表示指定入口的估计通行人数，不表示全景区实时在园人数。
- 智能体回答必须保留数据来源和引用，证据不足时明确提示。
