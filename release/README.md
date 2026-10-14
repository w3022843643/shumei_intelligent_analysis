# E 0.5.0 发布文件

日期：2026-10-14。

- `shumei_intelligent_analysis-0.5.0-py3-none-any.whl`：D 可安装的 Python 包。
- `E-visible-people-0.5.0-2026-10-14.zip`：安装包、源码、测试、服务契约和验收记录。
- `E-visible-people-0.5.0-2026-10-14.receipt.json`：wheel/ZIP 的 SHA-256 和验证边界。

在 D 使用的 Python 3.13 环境中安装 wheel 后，还需按 [服务契约](../E_SERVICE_CONTRACT.md) 注入 D 的真实任务、读取和索引路径，安装本身不代表联调已完成。

```powershell
python -m pip install ./release/shumei_intelligent_analysis-0.5.0-py3-none-any.whl
```

49 项测试通过，包括独立 SQLite 的 C 0.1.9 真实资料接收；16 份文档、655 片段及重启问答验证通过。DM-Count CPU 与官方实现输出一致。

授权录像/标注、新画面人数存储、P2PNet 真实对照、真实预测和 D/B 正式联调仍待验收。原件、环境配置、录像和权重不包含在本发布目录中。详见 [交付与联调说明](../docs/E050交付与联调说明.md)。
