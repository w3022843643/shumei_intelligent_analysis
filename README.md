# shumei_intelligent_analysis

E 负责的智能分析模块，包含 RAG 智能体、录像行人计数和入口短时客流预测。

## 模块范围

- RAG 文档解析、切分、索引与检索
- 带来源的智能体问答
- YOLOv8 + OpenVINO 录像行人检测
- 目标跟踪与虚拟线进出计数
- 指定入口未来 15—60 分钟短时客流预测

## 目录规划

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
└─ pyproject.toml
```

## 注意事项

- 授权录像、原始数据、模型权重和环境变量配置不得提交到仓库。
- 视频计数仅表示指定入口的估计通行人数，不表示全景区实时在园人数。
- 智能体回答必须保留数据来源和引用，证据不足时明确提示。
